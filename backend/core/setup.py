import os
from fastapi import APIRouter
from game.game_manager import GameManager
from ws.ws_manager import WSManager
import state.state as state_module


os.makedirs("data", exist_ok=True)

manager = GameManager()
ws_manager = WSManager(manager)
manager.connections = ws_manager.connections


state_module.connections = ws_manager.connections

router = APIRouter()
