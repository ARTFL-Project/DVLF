from dataclasses import dataclass, field
from time import time
from typing import Dict, List, Tuple

import orjson
import psycopg2
import psycopg2.extras
from pydantic import BaseModel


with open("config.json", encoding="utf-8") as config_file:
    GLOBAL_CONFIG = orjson.loads(config_file.read())


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
    with psycopg2.connect(
        user=GLOBAL_CONFIG["user"],
        password=GLOBAL_CONFIG["password"],
        database=GLOBAL_CONFIG["databaseName"],
    ) as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT headword FROM headwords")
        headwords = [row["headword"] for row in cursor]
    headwords.sort(key=lambda word: word.lower())
    headword_hash: Dict[str, int] = {word: pos for pos, word in enumerate(headwords)}
    return headwords, headword_hash


def load_words_of_the_day() -> Dict[str, str]:
    with open("words_of_the_day.json", encoding="utf-8") as words:
        words_of_the_day: List[Dict[str, str]] = orjson.loads(words.read())
    date_to_words: Dict[str, str] = {
        word_element["date"]: word_element["headword"] for word_element in words_of_the_day
    }
    return date_to_words


HEADWORD_LIST, HEADWORD_MAP = get_all_headwords()

WORDS_OF_THE_DAY = load_words_of_the_day()


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

    name: str = ""
    label: str = ""
    shortLabel: str = ""
    contentObj: List[Dict[str, str]] = field(default_factory=list)
    show: bool = True


@dataclass
class DictionaryData:
    """DictionaryData to export"""

    data: List[Dictionary]
    totalDicos: int
    totalEntries: int


@dataclass
class Results:
    """Results to export"""

    headword: str = ""
    dictionaries: DictionaryData = field(default_factory=list)
    synonyms: List = field(default_factory=list)
    antonyms: List = field(default_factory=list)
    examples: List[Example] = field(default_factory=list)
    timeSeries: List[List[float]] = field(default_factory=list)
    collocates: List = field(default_factory=list)
    nearestNeighbors: List = field(default_factory=list)
    fuzzyResults: List[FuzzyResult] = field(default_factory=list)


class Definition(BaseModel):
    """Definition object for posting definitions"""

    term: str
    definition: str
    source: str = ""
    link: str = ""
    recaptchaResponse: str


class ExampleSubmission(BaseModel):
    """Example object for posting examples"""

    term: str
    example: str
    source: str = ""
    link: str = ""
    recaptchaResponse: str


class NymSubmission(BaseModel):
    """Synonym or antonym object for posting nyms"""

    term: str
    nym: str
    type: str
    recaptchaResponse: str
