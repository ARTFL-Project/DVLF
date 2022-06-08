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
import regex as re
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
