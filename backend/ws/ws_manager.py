import asyncio
import json

from fastapi import WebSocket, status

from core.config import ROUND_DURATION, WS_DISCONNECT_GRACE_PERIOD
from game.game_logic import (
    ai_guess,
    end_game,
    get_countdown_left,
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
from utils.getters import get_opponents
from utils.utils import disconnect, remove_from_matchmaking, send_msg_to_opponents


class WSManager:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.connections: dict[str, WebSocket] = {}
        self._disconnect_tasks: dict[str, asyncio.Task] = {}
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
        previous_websocket = self.connections.get(user.username)

        self.connections[user.username] = websocket
        self.game_manager.connected_users[user.username] = user
        if user.is_guest:
            self.game_manager.guest_usernames.add(user.username)

        self._cancel_disconnect_task(user.username)
        if user.username in self.game_manager.disconnected_players:
            self.game_manager.disconnected_players.remove(user.username)

        await websocket.send_json({"type": "connection_ready"})

        if previous_websocket is not None and previous_websocket is not websocket:
            await self._close_replaced_connection(previous_websocket)

        if user.username in self.game_manager.player_games:
            await self._reconnect_user(
                user,
                websocket,
                notify_opponents=previous_websocket is None,
            )

    async def _close_replaced_connection(self, websocket: WebSocket):
        try:
            await websocket.send_json({"type": "connection_replaced"})
        except RuntimeError:
            pass

        try:
            await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
        except RuntimeError:
            pass

    def owns_connection(self, user: User, websocket: WebSocket) -> bool:
        return self.connections.get(user.username) is websocket

    def _cancel_disconnect_task(self, username: str):
        task = self._disconnect_tasks.pop(username, None)
        if task is not None:
            task.cancel()

    async def disconnect(self, user: User, websocket: WebSocket):
        if not self.owns_connection(user, websocket):
            return

        self.connections.pop(user.username, None)
        self.game_manager.connected_users.pop(user.username, None)

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
            self._cancel_disconnect_task(user.username)
            if user.username not in self.game_manager.disconnected_players:
                self.game_manager.disconnected_players.append(user.username)
            self._disconnect_tasks[user.username] = asyncio.create_task(
                self._handle_disconnect_grace_period(user, game)
            )
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
                if user.is_guest:
                    await self.connections[user.username].send_json(
                        {
                            "type": "error",
                            "message": "Create an account to play ranked games",
                        }
                    )
                else:
                    await self.game_manager.find_player(user)
            case "guess":
                await ai_guess(user, payload)
            case "surrender":
                await surrender_game(user, payload.get("leave_lobby", False))
            case "leave":
                await cleanup_lobby_on_disconnect(user)
                remove_from_matchmaking(user.username)
            case "cancel_matchmaking":
                remove_from_matchmaking(user.username)
                await self.connections[user.username].send_json(
                    {"type": "matchmaking_cancelled"}
                )
            case "get_info":
                await get_game_info(user)
            case _:
                print("unknown msg type:", message_type)

    async def _reconnect_user(
        self,
        user: User,
        websocket: WebSocket,
        notify_opponents: bool,
    ):
        game_id = self.game_manager.player_games[user.username]
        game = self.game_manager.games[game_id]
        opponents = get_opponents(user, game)
        loop = asyncio.get_running_loop()
        time_left = max(0, game.ends_at - loop.time()) if game.ends_at else None

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
                "round_number": game.round_number,
                "round_result": (
                    game.round_result.model_dump() if game.round_result else None
                ),
                "is_ranked": game.is_ranked,
                "time_left": time_left,
                "duration": ROUND_DURATION,
                "countdown": game.countdown_duration,
                "countdown_left": get_countdown_left(game),
            }
        )

        if notify_opponents:
            await send_msg_to_opponents(
                game,
                user,
                {
                    "type": "opponent_reconnected",
                    "username": user.username,
                },
            )

    async def _handle_disconnect_grace_period(self, user: User, game: Game):
        try:
            await asyncio.sleep(WS_DISCONNECT_GRACE_PERIOD)
        except asyncio.CancelledError:
            return

        task = asyncio.current_task()
        if self._disconnect_tasks.get(user.username) is not task:
            return
        self._disconnect_tasks.pop(user.username, None)

        if user.username not in self.game_manager.disconnected_players:
            return

        await surrender_game(user, True)
        if user.username in self.game_manager.disconnected_players:
            self.game_manager.disconnected_players.remove(user.username)
