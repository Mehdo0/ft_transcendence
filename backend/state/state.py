from fastapi import WebSocket
from schemas.data import Game

matchmaking_queue: list[str] = []
disconnected_players: list[str] = []
connections: dict[str, WebSocket] = {}
games: dict[str, Game] = {}
player_games: dict[str, str] = {}
lobbies: dict[str, dict] = {}
game_timers = {}
