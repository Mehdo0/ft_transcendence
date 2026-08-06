import os
from fastapi import APIRouter
from game.game_manager import GameManager
from ws.ws_manager import WSManager

os.makedirs("data", exist_ok=True)

game_manager = GameManager()
ws_manager = WSManager(game_manager)
manager = game_manager

import state.state as state_module
state_module.connections = ws_manager.connections

router = APIRouter()
