import os
import secrets

from fastapi import FastAPI
from fastapi import WebSocket
from fastapi.security import APIKeyCookie
from pwdlib import PasswordHash
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from data import Game

from data import ConnectionManager

# fastapi app + limiter init
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# manage socket connection
manager = ConnectionManager()

# DB var
DB_NAME = "data/game_data.db"
os.makedirs("data", exist_ok=True)

# Useful to find the file directory no matter where he is
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

matchmaking_queue = {
    "TWO_PLAYER_AI": [],  # List of players waiting for 1v1
    "FOUR_PLAYER": [],  # List of players waiting for a 4-player
}

# Auth var
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummy_password")
cookie_scheme = APIKeyCookie(name="access_token")

CONNECTIONS: dict[str, WebSocket] = {}  # username of the player  and his websocket id
GAMES: dict[str, Game] = {}  # list of games with their players usernames
PLAYER_GAMES: dict[str, str] = {} # username of the player and the game id he is in

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
