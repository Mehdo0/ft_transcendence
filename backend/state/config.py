from os import getenv
import secrets
from pwdlib import PasswordHash
from fastapi.security import APIKeyCookie
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address

DB_NAME = "data/game_data.db"
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
cookie_scheme = APIKeyCookie(name="access_token")
WORD_LIST = "list.txt"
COOKIE_SECURE = True

limiter = Limiter(key_func=get_remote_address)
