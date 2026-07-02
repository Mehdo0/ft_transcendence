from fastapi.security import APIKeyCookie
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address


def read_secret_key() -> str:
    file = open("/run/secrets/secret_key", "r")

    content = file.read()
    file.close()

    return content


DB_NAME = "data/game_data.db"
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = read_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
cookie_scheme = APIKeyCookie(name="access_token")
WORD_LIST = "list.txt"
COOKIE_SECURE = True

limiter = Limiter(key_func=get_remote_address)
