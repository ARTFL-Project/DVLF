from datetime import datetime
from typing import Dict, List, Tuple, Set
from html import unescape

import orjson
import psycopg2
import psycopg2.extras
import regex as re
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from humps import camelize, decamelize
from Levenshtein import ratio
from psycopg2 import pool
from starlette.middleware.cors import CORSMiddleware
from unidecode import unidecode
import requests
import bleach

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
    headwords.sort(key=lambda word: word.lower())
    headword_hash: Dict[str, int] = {word: pos for pos, word in enumerate(headwords)}
    return headwords, headword_hash


HEADWORD_LIST, HEADWORD_MAP = get_all_headwords()


def load_words_of_the_day() -> Dict[str, str]:
    with open("words_of_the_day.json", encoding="utf-8") as words:
        words_of_the_day: List[Dict[str, str]] = orjson.loads(words.read())
    date_to_words: Dict[str, str] = {
        word_element["date"]: word_element["headword"] for word_element in words_of_the_day
    }
    return date_to_words


WORDS_OF_THE_DAY = load_words_of_the_day()


def get_similar_headwords(headword: str) -> List[FuzzyResult]:
    results: List[FuzzyResult] = []
    norm_headword = unidecode(headword)
    for word in HEADWORD_LIST:
        norm_word = unidecode(word)
        score = ratio(norm_headword, norm_word)
        if score >= 0.7 and score < 1.0:
            results.append(FuzzyResult(word, score))
    results.sort(key=lambda x: x.score, reverse=True)
    return results


def highlight_examples(examples: List[Dict[str, str | int | bool]], query_term: str) -> List[Example]:
    forms: List[str] = [query_term]
    with POOL.getconn() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT headword FROM word2lemma WHERE lemma=%s", (query_term,))
        for row in cursor:
            forms.append(row["headword"])
    form_regex = re.compile(rf"\b({'|'.join(forms)})\b", re.IGNORECASE)
    new_examples: List[Example] = []
    for example in examples:
        matches = set(form_regex.findall(example["content"]))
        for match in matches:
            example["content"] = example["content"].replace(match, f'<span class="highlight">{match}</span>')
        new_examples.append(Example(**camelize(example)))
    return new_examples


def order_dictionaries(dictionaries: Dict[str, List[str]], user_submissions: List[UserSubmit]) -> DictionaryData:
    displayed = 0
    show: bool
    total_entries = 0
    total_dicos = 0
    new_dicos: List[Dictionary] = []
    for dico in DICO_ORDER:
        if dico not in dictionaries or len(dictionaries[dico]) == 0:
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


def sort_examples(examples: List[Example]) -> List[Example]:
    """Sort examples"""
    ordered_examples: List[Example] = []
    other_examples: List[Example] = []
    user_examples_with_no_score: List[Example] = []
    for example in examples:
        if example.score > 0:
            ordered_examples.append(example)
        elif example.userSubmit and example.score == 0:
            user_examples_with_no_score.append(example)
        elif example.score == 0:
            other_examples.append(example)
    ordered_examples.sort(key=lambda example: example.id)
    ordered_examples.extend(user_examples_with_no_score)
    ordered_examples.extend(other_examples)
    if len(ordered_examples) > 30:
        return ordered_examples[:30]
    return ordered_examples


def validate_recaptcha(token: str):
    response = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data={
            "secret": GLOBAL_CONFIG["recaptchaSecret"],
            "response": token,
        },
    )
    result = response.json()
    return result.get("success", False)


@app.get("/api/vote/{headword}/{example_id}/{vote}")
def vote(headword: str, example_id: int, vote: str):
    new_score: int = 0
    with POOL.getconn() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT examples FROM headwords WHERE headword=%s", (headword,))
        examples: List[Dict[str, str | int | bool]] = cursor.fetchone()["examples"]

        new_examples: List[Dict[str, str | int | bool]] = []
        for example in examples:
            if example["id"] == example_id:
                if vote == "up":
                    example["score"] += 1
                else:
                    example["score"] -= 1
                new_score = example["score"]
            new_examples.append(example)
        cursor.execute(
            "UPDATE headwords SET examples=%s WHERE headword=%s", (orjson.dumps(new_examples).decode("utf-8"), headword)
        )
        conn.commit()
    return {"message": "success", "score": new_score}


@app.post("/api/submit")
def submit_definition(term: str, source: str, link: str, definition: str, recaptcha_token: str):
    repatcha_response = validate_recaptcha(recaptcha_token)
    if repatcha_response is False:
        return {"message": "Recaptcha error"}
    term = bleach.clean(term, tags=[], strip=True)
    source = bleach.clean(source, tags=[], strip=True)
    link = bleach.clean(link, tags=[], strip=True)
    definition = bleach.clean(definition, tags=["i", "b"], strip=True)
    definition = unescape(definition)
    timestamp = str(datetime.now()).split()[0]
    new_submission = UserSubmit(content=definition, source=source, link=link, date=timestamp)
    with POOL.getconn() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if term in HEADWORD_MAP:
            cursor.execute("SELECT user_submit FROM headwords WHERE headword=%s", (term,))
            row = cursor.fetchone()
            user_submission = row["user_submit"]
            user_submission.append(new_submission)
            user_submission: str = orjson.dumps([new_submission]).decode("utf-8")
            cursor.execute("UPDATE headwords SET user_submit=%s WHERE headword=%s", (user_submission, term))
        else:
            user_submission: str = orjson.dumps([new_submission]).decode("utf-8")
            dictionaries = "{}"
            synonyms = "[]"
            antonyms = "[]"
            examples = "[]"
            cursor.execute(
                "INSERT INTO headwords (headword, dictionaries, synonyms, antonyms, user_submit, examples) VALUES (%s, %s, %s, %s, %s, %s)",
                (term, dictionaries, synonyms, antonyms, user_submission, examples),
            )
            HEADWORD_LIST.append(term)
            HEADWORD_LIST.sort(key=lambda word: word.lower())
            HEADWORD_MAP = {word: pos for pos, word in enumerate(HEADWORD_LIST)}
        conn.commit()
    return {"message": "success"}


@app.post("/api/submitExample")
def submit_example(term: str, source: str, link: str, example: str, recaptcha_token: str):
    repatcha_response = validate_recaptcha(recaptcha_token)
    if repatcha_response is False:
        return {"message": "Recaptcha error"}
    term = bleach.clean(term, tags=[], strip=True)
    source = bleach.clean(source, tags=[], strip=True)
    link = bleach.clean(link, tags=[], strip=True)
    example = bleach.clean(link, tags=["i", "b"], strip=True)
    example = unescape(example)
    if term in HEADWORD_MAP:
        with POOL.getconn() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT examples FROM headwords WHERE headword=%s", (term,))
            examples = cursor.fetchone()["examples"]
            new_id = max(example["id"] for example in examples) + 1
            timestamp = str(datetime.now()).split()[0]
            examples.append(
                {
                    "content": example,
                    "link": link,
                    "score": 0,
                    "source": source,
                    "date": timestamp,
                    "userSubmit": True,
                    "id": new_id,
                }
            )
            cursor.execute(
                "UPDATE headwords SET examples=%s WHERE headword=%s", (orjson.dumps(examples).decode("utf-8"), term)
            )
            conn.commit()
        return {"message": "success"}
    return {"message": "error"}


@app.get("/api/submitNym")
def submit_nym(term: str, nym: str, type: str, recaptchaResponse: str):
    repatcha_response = validate_recaptcha(recaptchaResponse)
    if repatcha_response is False:
        return {"message": "Recaptcha error"}
    term = bleach.clean(term, tags=[], strip=True)
    nym = bleach.clean(nym, tags=[], strip=True)
    term = unescape(term)
    timestamp = str(datetime.now()).split()[0]
    nym = {"label": unescape(nym), "userSubmit": True, "date": timestamp}
    if term in HEADWORD_MAP:
        with POOL.getconn() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(f"SELECT {type} FROM headwords WHERE headword=%s", (term,))
            nyms = cursor.fetchone()[type]
            stored_nyms: Set[str] = {stored_nym["label"] for stored_nym in nyms}
            if nym in stored_nyms:
                return {"message": "error"}
            nyms.append(nym)
            cursor.execute(
                f"UPDATE headwords SET {type}=%s WHERE headword=%s", (orjson.dumps(nyms).decode("utf8)"), term)
            )
        return {"message": "success"}
    return {"message": "error"}


@app.get("/api/autocomplete/{prefix}")
def autocomplete(prefix):
    headwords: List[str] = []
    prefix = prefix.strip().lower()
    prefix_regex = re.compile(rf"({prefix})(.*)", re.I)
    with POOL.getconn() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT headword FROM headwords WHERE headword ~* %s ORDER BY headword LIMIT 10", (rf"^{prefix}.*\M",)
        )
        headwords = [prefix_regex.sub(r'<span class="highlight">\1</span>\2', row["headword"]) for row in cursor]
    return headwords


@app.get("/api/wordoftheday")
def word_of_the_day():
    date = str(datetime.now()).split()[0]
    return WORDS_OF_THE_DAY[date]


# TODO: ACCOUNT FOR WHEN YOU ADD A WORD
@app.get("/api/wordwheel")
def wordwheel(headword: str, startIndex: None | int = None, endIndex: None | int = None):
    if headword in HEADWORD_MAP:
        index = HEADWORD_MAP[headword]
        startIndex = index - 100
        if startIndex < 0:
            startIndex = 0
        endIndex = index + 100
        if endIndex > len(HEADWORD_LIST):
            endIndex = len(HEADWORD_LIST) - 1
        return Wordwheel(words=HEADWORD_LIST[startIndex:endIndex], startIndex=startIndex, endIndex=endIndex)
    temp_headword_list = HEADWORD_LIST[:]
    temp_headword_list.append(headword)
    temp_headword_list.sort()
    for index, word in enumerate(temp_headword_list):
        if word == headword:
            startIndex = index - 99
            endIndex = index + 100
            break
    return Wordwheel(words=temp_headword_list[startIndex:endIndex], startIndex=startIndex, endIndex=endIndex)


@app.get("/api/explore/{headword}")
def explore_vectors(headword):
    with POOL.getconn() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT vectors from explore_vectors where headword=%s", (headword,))
        vectors = cursor.fetchone()["vectors"]
    return vectors


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
        sorted_examples = sort_examples(highlighted_examples)
        all_dictionaries = order_dictionaries(row["dictionaries"], row["user_submit"])
        fuzzy_results: List[FuzzyResult] = []
        if all_dictionaries.totalEntries < 2:
            fuzzy_results = get_similar_headwords(headword)
        results = Results(
            headword=headword,
            dictionaries=all_dictionaries,
            synonyms=row["synonyms"],
            antonyms=row["antonyms"],
            examples=sorted_examples,
            timeSeries=row["time_series"],
            collocates=decamelize(row["collocations"]),
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
