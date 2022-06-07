from dataclasses import dataclass
from time import time
from typing import Dict, List

import orjson
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from psycopg2 import pool
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

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


@dataclass
class config:
    """App config"""

    databaseName: str
    user: str
    password: str
    debug: bool
    twitterUser: str
    twitterPassword: str
    recaptchaSecret: str


@dataclass
class wordOfTheDay:
    """Word of the day"""

    headword: str
    date: str


@dataclass
class Nym:
    """Generic nym type"""

    label: str
    UserSubmit: bool
    date: str


@dataclass
class Example:
    """Example for headwords"""

    content: str
    link: str
    score: int
    id: int
    source: str
    userSubmit: bool
    date: str


@dataclass
class Collocates:
    """Collocates Type"""

    key: str
    value: int


@dataclass
class NearestNeighbors:
    """NearestNeighbors Type"""

    word: str


@dataclass
class AutoCompleteHeadword:
    """AutoCompleteHeadword is just the object in the AutoCompleteList"""

    headword: str


@dataclass
class Wordwheel:
    """Wordwheel data"""

    words: List[str]
    startIndex: int
    endIndex: int


@dataclass
class UserSubmit:
    """UserSubmit fields"""

    content: str
    source: str
    link: str
    date: str


@dataclass
class RecaptchaResponse:
    """RecaptchaResponse from Google"""

    success: bool
    challenge_ts: time
    hostname: str
    error_codes: List[str]


@dataclass
class FuzzyResult:
    """FuzzyResult is the result of fuzzy searching"""

    word: str
    score: float


@dataclass
class Dictionary:
    """Dictionary to export"""

    name: str
    label: str
    shortLabel: str
    contentObj: List[Dict[str, str]]
    show: bool


@dataclass
class DictionaryData:
    """DictionaryData to export"""

    data: List[Dictionary]
    totalDicos: int
    totalEntries: int


@dataclass
class Results:
    """Results to export"""

    headword: str
    dictionaries: DictionaryData
    synonyms: List[Nym]
    antonyms: List[Nym]
    examples: List[Example]
    timeSeries: List[List[float]]
    collocates: List[Collocates]
    nearestNeighbors: List
    fuzzyResults: List[FuzzyResult]


@dataclass
class AutoCompleteList:
    """AutoCompleteList is the top 10 words"""

    List[AutoCompleteHeadword]


@app.get("/")
def home():
    """DVLF landing page"""
    with open("public/dist/index.html", encoding="utf-8") as index_file:
        index_html = index_file.read()
    return HTMLResponse(index_html)
