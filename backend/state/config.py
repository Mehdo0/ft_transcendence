from fastapi.security import APIKeyCookie
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address
from os import getenv
import os


def read_secret_key():
    try:
        with open("/run/secrets/secret_key") as f:
            return f.read().strip()
    except FileNotFoundError:
        return os.urandom(32).hex()


DB_NAME = "data/game_data.db"
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = read_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
cookie_scheme = APIKeyCookie(name="access_token")
WORD_LIST = "list.txt"
COOKIE_SECURE = getenv("COOKIE_SECURE", "true").lower() not in ("false", "0", "no")

limiter = Limiter(key_func=get_remote_address)
