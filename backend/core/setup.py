import os
from fastapi import APIRouter
from game.game_manager import GameManager


os.makedirs("data", exist_ok=True)

manager = GameManager()

from ws.ws_manager import WSManager

ws_manager = WSManager(manager)
manager.connections = ws_manager.connections

router = APIRouter()
