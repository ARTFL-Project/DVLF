"""DVLF WEB Application"""

import re
from datetime import datetime
from html import unescape
from typing import Dict, List, Set

import bleach
import orjson
import psycopg2
import psycopg2.extras
import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from humps import camelize, decamelize
from Levenshtein import ratio
from starlette.middleware.cors import CORSMiddleware
from unidecode import unidecode

from datamodels import (
    DICO_LABELS,
    DICO_ORDER,
    GLOBAL_CONFIG,
    HEADWORD_LIST,
    HEADWORD_MAP,
    WORDS_OF_THE_DAY,
    Definition,
    Dictionary,
    DictionaryData,
    Example,
    ExampleSubmission,
    FuzzyResult,
    NymSubmission,
    Results,
    UserSubmit,
    Wordwheel,
)

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
    with psycopg2.connect(
        user=GLOBAL_CONFIG["user"], password=GLOBAL_CONFIG["password"], database=GLOBAL_CONFIG["databaseName"]
    ) as conn:
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
            content.append(
                {"content": entry["content"], "source": entry["source"], "link": entry["link"], "date": entry["date"]}
            )
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
    with psycopg2.connect(
        user=GLOBAL_CONFIG["user"], password=GLOBAL_CONFIG["password"], database=GLOBAL_CONFIG["databaseName"]
    ) as conn:
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
def submit_definition(definition: Definition):
    global HEADWORD_MAP
    repatcha_response = validate_recaptcha(definition.recaptchaResponse)
    if repatcha_response is False:
        return {"message": "Recaptcha error"}
    term = bleach.clean(definition.term, tags=[], strip=True)
    source = bleach.clean(definition.source, tags=[], strip=True)
    link = bleach.clean(definition.link, tags=[], strip=True)
    if not re.search(r"https?:\/\/", link):
        link = f"https://{link}"
    definition = bleach.clean(definition.definition, tags=["i", "b"], strip=True)
    definition = unescape(definition)
    timestamp = str(datetime.now()).split()[0]
    new_submission = UserSubmit(content=definition, source=source, link=link, date=timestamp)
    with psycopg2.connect(
        user=GLOBAL_CONFIG["user"], password=GLOBAL_CONFIG["password"], database=GLOBAL_CONFIG["databaseName"]
    ) as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if term in HEADWORD_MAP:
            cursor.execute("SELECT user_submit FROM headwords WHERE headword=%s", (term,))
            row = cursor.fetchone()
            user_submission = row["user_submit"]
            user_submission.append(new_submission)
            cursor.execute(
                "UPDATE headwords SET user_submit=%s WHERE headword=%s",
                (orjson.dumps(user_submission).decode("utf-8"), term),
            )
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
def submit_example(payload: ExampleSubmission):
    repatcha_response = validate_recaptcha(payload.recaptchaResponse)
    if repatcha_response is False:
        return {"message": "Recaptcha error"}
    term = bleach.clean(payload.term, tags=[], strip=True)
    source = bleach.clean(payload.source, tags=[], strip=True)
    link = bleach.clean(payload.link, tags=[], strip=True)
    if not re.search(r"https?:\/\/", link):
        link = f"https://{link}"
    example = bleach.clean(payload.example, tags=["i", "b"], strip=True)
    example = unescape(example)
    if term in HEADWORD_MAP:
        with psycopg2.connect(
            user=GLOBAL_CONFIG["user"], password=GLOBAL_CONFIG["password"], database=GLOBAL_CONFIG["databaseName"]
        ) as conn:
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


@app.post("/api/submitNym")
def submit_nym(payload: NymSubmission):
    repatcha_response = validate_recaptcha(payload.recaptchaResponse)
    if repatcha_response is False:
        return {"message": "Recaptcha error"}
    term = bleach.clean(payload.term, tags=[], strip=True)
    nym = bleach.clean(payload.nym, tags=[], strip=True)
    term = unescape(term)
    timestamp = str(datetime.now()).split()[0]
    nym_submission = {"label": unescape(nym), "userSubmit": True, "date": timestamp}
    if term in HEADWORD_MAP:
        with psycopg2.connect(
            user=GLOBAL_CONFIG["user"], password=GLOBAL_CONFIG["password"], database=GLOBAL_CONFIG["databaseName"]
        ) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(f"SELECT {payload.type} FROM headwords WHERE headword=%s", (term,))
            nyms = cursor.fetchone()[payload.type]
            stored_nyms: Set[str] = {stored_nym["label"] for stored_nym in nyms}
            if nym in stored_nyms:
                return {"message": "error"}
            nyms.append(nym_submission)
            cursor.execute(
                f"UPDATE headwords SET {payload.type}=%s WHERE headword=%s", (orjson.dumps(nyms).decode("utf8)"), term)
            )
        return {"message": "success"}
    return {"message": "error"}


@app.get("/api/autocomplete/{prefix}")
def autocomplete(prefix):
    headwords: List[str] = []
    prefix = prefix.strip().lower()
    prefix_regex = re.compile(rf"({prefix})(.*)", re.I)
    with psycopg2.connect(
        user=GLOBAL_CONFIG["user"], password=GLOBAL_CONFIG["password"], database=GLOBAL_CONFIG["databaseName"]
    ) as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT headword FROM headwords WHERE headword ~* %s ORDER BY headword LIMIT 10", (rf"^{prefix}.*\M",)
        )
        headwords = [
            {
                "headword": row["headword"],
                "html": prefix_regex.sub(r'<span class="highlight">\1</span>\2', row["headword"]),
            }
            for row in cursor
        ]
    return headwords


@app.get("/api/wordoftheday")
def word_of_the_day():
    date = str(datetime.now()).split()[0]
    return WORDS_OF_THE_DAY[date]


@app.get("/api/wordwheel")
def wordwheel(
    headword: None | str = None, startIndex: None | int = None, endIndex: None | int = None, position: None | str = None
):
    if headword is not None:
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
    elif position == "before":
        index_before = startIndex - 500
        if index_before < 0:
            index_before = 0
        return Wordwheel(words=HEADWORD_LIST[index_before:startIndex], startIndex=index_before, endIndex=endIndex)
    else:
        index_after = endIndex + 500
        return Wordwheel(words=HEADWORD_LIST[endIndex:index_after], startIndex=startIndex, endIndex=index_after)


@app.get("/api/explore/{headword}")
def explore_vectors(headword):
    with psycopg2.connect(
        user=GLOBAL_CONFIG["user"], password=GLOBAL_CONFIG["password"], database=GLOBAL_CONFIG["databaseName"]
    ) as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT vectors from explore_vectors where headword=%s", (headword,))
        results = cursor.fetchone()
        if results is None:
            return {1600: [], 1700: [], 1800: [], 1900: []}
        vectors = results["vectors"]
    return vectors


@app.get("/api/mot/{headword}")
def query_headword(headword: str):
    results: Results
    with psycopg2.connect(
        user=GLOBAL_CONFIG["user"], password=GLOBAL_CONFIG["password"], database=GLOBAL_CONFIG["databaseName"]
    ) as conn:
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
