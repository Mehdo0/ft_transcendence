from fastapi import WebSocket

from schemas.data import Game

matchmaking_queue = {
    "TWO_PLAYER_AI": [],  # List of players waiting for 1v1
    "FOUR_PLAYER": [],  # List of players waiting for a 4-player
}

disconnected_players = {} # list of the disconnected player to reconnect them gracely ;)

# Auth var
connections: dict[str, WebSocket] = {}  # username of the player  and his websocket id
games: dict[str, Game] = {}  # list of games with their players usernames
player_games: dict[str, str] = {} # username of the player and the game id
lobbies: dict[str, dict] = {} #list of actives lobbies 