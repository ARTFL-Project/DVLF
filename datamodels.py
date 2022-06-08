from dataclasses import dataclass, field
from typing import List, Dict
from time import time


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
    synonyms: List[Nym] = field(default_factory=list)
    antonyms: List[Nym] = field(default_factory=list)
    examples: List[Example] = field(default_factory=list)
    timeSeries: List[List[float]] = field(default_factory=list)
    collocates: List[Collocates] = field(default_factory=list)
    nearestNeighbors: List = field(default_factory=list)
    fuzzyResults: List[FuzzyResult] = field(default_factory=list)
