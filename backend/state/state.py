from fastapi import WebSocket

from data import ConnectionManager, Game

# manage socket connection
manager = ConnectionManager()

matchmaking_queue = {
    "TWO_PLAYER_AI": [],  # List of players waiting for 1v1
    "FOUR_PLAYER": [],  # List of players waiting for a 4-player
}

# Auth var
connections: dict[str, WebSocket] = {}  # username of the player  and his websocket id
games: dict[str, Game] = {}  # list of games with their players usernames
