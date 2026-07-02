import os
from fastapi import APIRouter
from game.game_manager import GameManager

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Initialize the global manager instance here!
manager = GameManager()

router = APIRouter()