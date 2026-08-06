import os
from fastapi import APIRouter
from game.game_manager import GameManager
from ws.ws_manager import WSManager

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Initialize the global manager instances here!
game_manager = GameManager()
ws_manager = WSManager(game_manager)
manager = game_manager

router = APIRouter()