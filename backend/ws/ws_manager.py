from fastapi import WebSocket
from game.game_manager import GameManager
from schemas.data import User, Game


class Ws_Manager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}
        self.gameManager = GameManager

    async def connect(self, user: User, websocket: WebSocket):
            await websocket.accept()
            self.connections[user.username] = websocket
            
            # Handle grace period recovery natively
            if user.username in self.disconnected_players:
                self.disconnected_players[user.username]["reconnected"] = True
                del self.disconnected_players[user.username]

    def disconnect(self, user: User):
            # Only remove the active socket connection. 
            self.connections.pop(user.username, None)
            
            # Pull them out of the queue so they don't match while offline
            if user.username in self.matchmaking_queue:
                self.matchmaking_queue.remove(user.username)

    async def broadcast_to_game(self, game_id: str, payload: dict, exclude: str = None):
            """Sends a message to everyone in a specific game."""
            game = self.games.get(game_id)
            if not game:
                return
                
            for username in game.players:
                if username == exclude:
                    continue
                ws = self.connections.get(username)
                if ws:
                    await ws.send_json(payload) 

    async def send_end_game(
    self, username: str, status: str, elo_diff: int, new_elo: int, reason: str | None = None
    ):
        websocket = self.connections.get(username)
        if websocket is None:
            return

        payload = {
            "type": "end_game",
            "status": status,
            "elo_diff": elo_diff,
            "new_elo": new_elo,
        }
        if reason is not None:
            payload["reason"] = reason
        await websocket.send_json(payload)

    async def broadcast_player_score(
        self,
        game: Game,
        username: str,
        score: float,
        guess: dict | None = None,
        include_self: bool = False,
    ):
        for player in game.players:
            player_ws = self.connections.get(player)
            assert player_ws is not None
            if player == username and not include_self:
                continue
            payload = {
                "type": "player_guess",
                "username": username,
                "score": score,
            }
            if guess is not None:
                payload["guess"] = guess
            await player_ws.send_json(payload)

    async def send_msg_to_opponents(
        self,
        game: Game,
        user: User,
        msg: dict[str, str],
    ):
        for p in game.players:
            if p != user.username:  # message all opponents
                assert p in self.connections  # opponent should be connected
                await self.connections[p].send_json(msg)


    async def send_msg_to_players(
        self,
        game: Game,
        msg: dict[str, str],
    ):
        for p in game.players:
            assert p in self.connections  # opponent should be connected
            await self.connections[p].send_json(msg)
