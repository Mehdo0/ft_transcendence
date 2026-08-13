import asyncio
import json

from fastapi import WebSocket, WebSocketException, status

from game.game_logic import (
    ai_guess,
    end_game,
    get_game_info,
    start_game,
    surrender_game,
)
from game.lobby_logic import (
    cleanup_lobby_on_disconnect,
    create_lobby,
    get_lobby_info,
    join_lobby,
)
from schemas.data import Game, User
from utils.getters import get_opponents, get_user
from utils.utils import disconnect, remove_from_matchmaking, send_msg_to_opponents


class WSManager:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.connections: dict[str, WebSocket] = {}
        self._setup_events()

    def _setup_events(self):
        gm = self.game_manager

        gm.on("broadcast_to_players", self._on_broadcast_to_players)

    async def _on_broadcast_to_players(self, event, data):
        payloads = data["payloads"]
        for item in payloads:
            ws = self.connections.get(item["username"])
            if ws:
                try:
                    await ws.send_json(item["payload"])
                except RuntimeError:
                    pass

    async def connect(self, user: User, websocket: WebSocket):
        if user.username in self.connections:
            try:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "already connected — close your other tab first",
                    }
                )
            except RuntimeError:
                pass
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Only one connection allowed",
            )

        self.connections[user.username] = websocket

        if user.username in self.game_manager.disconnected_players:
            self.game_manager.disconnected_players.remove(user.username)

        if user.username in self.game_manager.player_games:
            await self._reconnect_user(user, websocket)

    async def disconnect(self, user: User):
        self.connections.pop(user.username, None)

        if user.username in self.game_manager.player_games:
            game_id = self.game_manager.player_games[user.username]
            game = self.game_manager.games[game_id]
            await send_msg_to_opponents(
                game,
                user,
                {
                    "type": "opponent_disconnected",
                    "username": user.username,
                },
            )
            asyncio.create_task(self._handle_disconnect_grace_period(user, game))
            return

        await cleanup_lobby_on_disconnect(user)
        disconnect(user)

    async def handle_message(self, user: User, payload: dict):
        message_type = payload.get("type")
        print("WS: received msg, type: " + str(message_type))
        if message_type != "guess":
            print("WS: user " + user.username + ", msg " + json.dumps(payload))
        else:
            print("WS: user " + user.username + " guessed")

        match message_type:
            case "create_lobby":
                await create_lobby(user, self.connections[user.username])
            case "join_lobby":
                code = payload.get("code", "").upper().strip()
                await join_lobby(user, code, self.connections[user.username])
            case "get_lobby":
                ws = self.connections[user.username]
                await get_lobby_info(payload, ws, user)
            case "start_game":
                await start_game(payload, user)
            case "find_player":
                await self.game_manager.find_player(user)
            case "guess":
                await ai_guess(user, payload)
            case "surrender":
                await surrender_game(user, payload.get("leave_lobby", False))
            case "leave":
                await cleanup_lobby_on_disconnect(user)
                remove_from_matchmaking(user.username)
            case "get_info":
                get_game_info(user)
            case _:
                print("unknown msg type:", message_type)

    async def _reconnect_user(self, user: User, websocket: WebSocket):
        game_id = self.game_manager.player_games[user.username]
        game = self.game_manager.games[game_id]
        opponents = get_opponents(user, game)
        loop = asyncio.get_running_loop()
        time_left = max(0, round(game.ends_at - loop.time())) if game.ends_at else None

        await websocket.send_json(
            {
                "type": "reconnect_game",
                "game_id": game.id,
                "opponent": opponents,
                "players": game.players,
                "me": user.username,
                "word": game.word,
                "scores": game.scores,
                "round_wins": game.round_wins,
                "is_ranked": game.is_ranked,
                "time_left": time_left,
            }
        )

        await send_msg_to_opponents(
            game,
            user,
            {
                "type": "opponent_reconnected",
                "username": user.username,
            },
        )

    async def _handle_disconnect_grace_period(self, user: User, game: Game):
        self.game_manager.disconnected_players.append(user.username)
        print("user", user.username)
        await asyncio.sleep(10)

        if user.username not in self.game_manager.disconnected_players:
            return

        await surrender_game(user, True)
        if user.username in self.game_manager.disconnected_players:
            self.game_manager.disconnected_players.remove(user.username)
