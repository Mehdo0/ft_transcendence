from fastapi.security import APIKeyCookie
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

from utils.env import read_bool, read_non_empty_string, read_positive_int


def read_secret_key():
    try:
        with open("/run/secrets/secret_key") as f:
            return f.read().strip()
    except FileNotFoundError:
        return os.urandom(32).hex()


DB_NAME = "data/game_data.db"
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = read_secret_key()
ALGORITHM = read_non_empty_string("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = read_positive_int("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
GUEST_ACCESS_TOKEN_EXPIRE_MINUTES = read_positive_int(
    "GUEST_ACCESS_TOKEN_EXPIRE_MINUTES", 1440
)
GUEST_USERNAME_PREFIX = read_non_empty_string("GUEST_USERNAME_PREFIX", "Guest")
GUEST_USERNAME_DIGITS = read_positive_int("GUEST_USERNAME_DIGITS", 6)
GUEST_GENERATION_ATTEMPTS = read_positive_int("GUEST_GENERATION_ATTEMPTS", 100)
LEADERBOARD_LIMIT = read_positive_int("LEADERBOARD_LIMIT", 10)
cookie_scheme = APIKeyCookie(name="access_token")
WORD_LIST = read_non_empty_string("WORD_LIST", "list.txt")
COOKIE_SECURE = read_bool("COOKIE_SECURE", True)

limiter = Limiter(key_func=get_remote_address)
