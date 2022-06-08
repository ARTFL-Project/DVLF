from typing import Dict, List, Tuple

import orjson
import psycopg2
import psycopg2.extras
import regex as re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from Levenshtein import ratio
from psycopg2 import pool
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from unidecode import unidecode

from datamodels import *

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/css", StaticFiles(directory="public/dist/css"), name="css")
app.mount("/js", StaticFiles(directory="public/dist/js"), name="js")
app.mount("/img", StaticFiles(directory="public/dist/img"), name="img")

with open("config.json", encoding="utf-8") as config_file:
    GLOBAL_CONFIG = orjson.loads(config_file.read())

POOL = pool.ThreadedConnectionPool(
    1,
    100,
    user=GLOBAL_CONFIG["user"],
    password=GLOBAL_CONFIG["password"],
    database=GLOBAL_CONFIG["databaseName"],
)

TOKEN_REGEX = re.compile(r"(?i)([\p{L}]+)|([\.?,;:'’!\-]+)|([\s]+)|([\d]+)")

DICO_LABELS: Dict[str, Dict[str, str]] = {
    "feraud": {
        "label": "Féraud: Dictionaire critique de la langue française (1787-1788)",
        "shortLabel": "Féraud (1787-1788)",
    },
    "nicot": {
        "label": "Jean Nicot: Thresor de la langue française (1606)",
        "shortLabel": "Jean Nicot (1606)",
    },
    "acad1694": {
        "label": "Dictionnaire de L'Académie française 1re édition (1694)",
        "shortLabel": "Académie française (1694)",
    },
    "acad1762": {
        "label": "Dictionnaire de L'Académie française 4e édition (1762)",
        "shortLabel": "Académie française (1762)",
    },
    "acad1798": {
        "label": "Dictionnaire de L'Académie française 5e édition (1798)",
        "shortLabel": "Académie française (1798)",
    },
    "acad1835": {
        "label": "Dictionnaire de L'Académie française 6e édition (1835)",
        "shortLabel": "Académie française (1835)",
    },
    "littre": {
        "label": "Émile Littré: Dictionnaire de la langue française (1872-1877)",
        "shortLabel": "Littré (1872-1877)",
    },
    "acad1932": {
        "label": "Dictionnaire de L'Académie française 8e édition (1932-1935)",
        "shortLabel": "Académie française (1932-1935)",
    },
    "tlfi": {
        "label": "Le Trésor de la Langue Française Informatisé",
        "shortLabel": "Trésor Langue Française",
    },
    "bob": {
        "label": "BOB: Dictionaire d'argot",
        "shortLabel": "BOB: Dictionaire d'argot",
    },
}

DICO_ORDER: List[str] = [
    "tlfi",
    "acad1932",
    "littre",
    "acad1835",
    "acad1798",
    "feraud",
    "acad1762",
    "acad1694",
    "nicot",
    "bob",
]


def get_all_headwords() -> Tuple[List[str], Dict[str, int]]:
    """Get all headwords"""
    headwords: List[str]
    with POOL.getconn() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT headword FROM headwords")
        headwords = [row["headword"] for row in cursor]
    headwords.sort()
    headword_hash: Dict[str, int] = {word: pos for pos, word in enumerate(headwords)}
    return headwords, headword_hash


HEADWORD_LIST, HEADWORD_MAP = get_all_headwords()


def load_words_of_the_day() -> Dict[str, str]:
    """Load words of the day"""
    with open("words_of_the_day.json", encoding="utf-8") as input:
        word_list: List[wordOfTheDay] = orjson.loads(input.read())
    date_to_words: Dict[str, str] = {}
    for word_element in word_list:
        date_to_words[word_element.date] = word_element.headword
    return date_to_words


def get_similar_headwords(headword: str) -> List[FuzzyResult]:
    results: List[FuzzyResult] = []
    norm_headword = unidecode(headword)
    for word in HEADWORD_LIST:
        norm_word = unidecode(word)
        score = ratio(norm_headword, norm_word)
        if score >= 0.7 and score < 1.0:
            results.append(FuzzyResult(word, score))
    results.sort(key=lambda x: x.Score, reverse=True)
    return results


def highlight_examples(examples: List[Example], query_term: str) -> List[Example]:
    forms: List[str] = [query_term]
    with POOL.getconn() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT headword FROM word2lemma WHERE lemma=%s", (query_term,))
        for row in cursor:
            forms.append(row["headword"])
    form_regex = re.compile(rf"(?i)^({'|'.join(forms)})$")
    new_examples: List[Example] = []
    for example in examples:
        new_content: List[str] = []
        matches = form_regex.findall(example.content)
        for match in matches:
            if form_regex.search(match):
                new_content.append(f'<span class="highlight">{match}</span>')
            else:
                new_content.append(match)
        example.content = "".join(new_content)
        new_examples.append(example)
    return new_examples


def order_dictionaries(dictionaries: Dict[str, List[str]], user_submissions: List[UserSubmit]) -> DictionaryData:
    displayed = 0
    show: bool
    total_entries = 0
    total_dicos = 0
    new_dicos: List[Dictionary] = []
    for dico in DICO_ORDER:
        if len(dictionaries[dico]) == 0:
            continue
        total_dicos += 1
        displayed += 1
        if displayed < 3:
            show = True
        else:
            show = False
        total_entries += len(dictionaries[dico])
        content: List[Dict[str, str]] = []
        for entry in dictionaries[dico]:
            content.append({"content": entry})

        new_dicos.append(
            Dictionary(
                name=dico,
                label=DICO_LABELS[dico]["label"],
                shortLabel=DICO_LABELS[dico]["shortLabel"],
                contentObj=content,
                show=show,
            )
        )

    if len(user_submissions) > 0:
        total_entries += len(user_submissions)
        displayed += 1
        if displayed < 3:
            show = True
        else:
            show = False
        content: List[Dict[str, str]] = []
        for entry in user_submissions:
            content.append({"content": entry.Content, "source": entry.Source, "link": entry.Link, "date": entry.Date})
        new_dicos.append(
            Dictionary(
                name="userSubmit",
                label="Définition(s) d'utilisateurs/trices",
                shortLabel="Définition(s) d'utilisateurs/trices",
                contentObj=content,
                show=show,
            )
        )
    else:
        new_dicos.append(
            Dictionary(
                name="userSubmit",
                label="Définition(s) d'utilisateurs/trices",
                shortLabel="Définition(s) d'utilisateurs/trices",
            )
        )

    all_dictionaries = DictionaryData(data=new_dicos, totalDicos=total_dicos, totalEntries=total_entries)
    return all_dictionaries


@app.get("/api/autocomplete/{prefix}")
def autocomplete(prefix):
    headwords: List[str] = []
    prefix = prefix.strip().lower()
    prefix_regex = re.compile(rf"(?i)({prefix})(.*)")
    with POOL.getconn() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT headword FROM headwords WHERE headword ~* %s ORDER BY headword LIMIT 10", (f"^{prefix}.*\\M",)
        )
        headwords = [prefix_regex.sub(row["headword"], r'<span class="highlight">\1</span>\2') for row in cursor]
    return headwords


@app.get("/api/mot/{headword}")
def query_headword(headword: str):
    results: Results
    with POOL.getconn() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT user_submit, dictionaries, synonyms, antonyms, examples, time_series, collocations, nearest_neighbors FROM headwords WHERE headword=%s",
            (headword,),
        )
        row = cursor.fetchone()
        if row is None:
            fuzzy_results = get_similar_headwords(headword)
            return Results(fuzzyResults=fuzzy_results)
        highlighted_examples = highlight_examples(row["examples"], headword)
        sorted_examples = sorted(highlighted_examples)
        all_dictionaries = order_dictionaries(row["dictionaries"], row["user_submit"])
        fuzzy_results: List[FuzzyResult] = []
        if len(all_dictionaries) < 2:
            fuzzy_results = get_similar_headwords(headword)
        results = Results(
            headword=headword,
            dictionaries=all_dictionaries,
            synonyms=row["synonyms"],
            antonyms=row["antonyms"],
            examples=sorted_examples,
            timeSeries=row["time_series"],
            collocates=row["collocations"],
            nearestNeighbors=row["nearest_neighbors"],
            fuzzyResults=fuzzy_results,
        )
    return results


# TODO: log


@app.get("/")
@app.get("/mot/{word}:path")
@app.get("/apropos")
@app.get("/definition")
@app.get("/exemple")
@app.get("/synonyme")
@app.get("/antonyme")
def home():
    """DVLF landing page"""
    with open("public/dist/index.html", encoding="utf-8") as index_file:
        index_html = index_file.read()
    return HTMLResponse(index_html)
