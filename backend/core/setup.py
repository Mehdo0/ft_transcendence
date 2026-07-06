import os
from core.database import setup_database
from schemas.data import GameManager
from fastapi import APIRouter

# DB var
setup_database()
os.makedirs("data", exist_ok=True)
setup_database()
manager = GameManager()

router = APIRouter()
ROUND_DURATION = 60
ROUND_WIN_TARGET = 2
SCORE_INCREMENT_PER_SECOND = 0.5