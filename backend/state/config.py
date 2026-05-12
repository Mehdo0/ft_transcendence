from os import getenv
import secrets
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer
from pathlib import Path

DB_NAME = "data/game_data.db"
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DUMMY_HASH = PasswordHash.recommended().hash("dummy_password")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
WORD_LIST = "list.txt"
COOKIE_SECURE = getenv("COOKIE_SECURE", "false").lower() == "true"
