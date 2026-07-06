from enum import Enum
import asyncio, uuid, random
from fastapi import WebSocket
from pydantic import BaseModel, Field


class GameState(str, Enum):
    CONNECTING = "connecting"
    SEARCHING_OPPONENT = "searching_opponent"
    STARTED = "started"
    FINISHED = "finished"


class GameType(str, Enum):
    SOLO_AI = "solo_ai"
    TWO_PLAYER_AI = "two_player_ai"
    FOUR_PLAYER = "four_player"


class ClientWebsocketMessageType(str, Enum):
    DRAWING = "drawing"
    QUIT = "quit"


class ServerWebsocketMessageType(str, Enum):
    GAME_START = "game_start"
    GAME_END = "game_end"
    AI_GUESS = "ai_guess"
    PLAYER_GUESS = "player_guess"


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    email: str
    elo: int


class Game(BaseModel):
    id: str
    game_state: GameState = GameState.CONNECTING
    players: list[str] = Field(default_factory=list)
    word: str
    scores: dict[str, float] = Field(default_factory=dict)
    ai_scores: dict[str, float] = Field(default_factory=dict)
    score_bonuses: dict[str, float] = Field(default_factory=dict)
    round_wins: dict[str, int] = Field(default_factory=dict)
    ends_at: float
    is_ranked: bool = False


class GameInstance:
    game: Game
    lock: asyncio.Lock

    async def broadcast_to_game(
        self,
        payload: dict,
        exclude: str | None = None,
    ):
        """Sends a message to everyone in a specific game."""
        for username in self.game.players:
            if username == exclude:
                continue
            ws = ConnectionManager.get_ws(username)
            if ws:
                await ws.send_json(payload)


class GameManager:
    lock: asyncio.Lock

    def __init__(self):
        # 1. Active Connections
        self.connections: dict[str, WebSocket] = {}

        # 2. Game & Lobby State
        self.games: dict[str, GameInstance] = {}
        self.player_games: dict[str, str] = {}
        self.lobbies: dict[str, dict] = {}

        # 3. Matchmaking & Disconnects
        self.matchmaking_queue: list[str] = []
        self.disconnected_players: dict[str, dict] = {}
        self.game_timers: dict[str, asyncio.Task] = {}

    def _random_word(self) -> str:
        from services.ai_service import load_word_list
        return random.choice(load_word_list())

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

    async def find_player(self, user: User):
        if (
            user.username in self.player_games
            or user.username in self.matchmaking_queue
        ):
            return

        # Defensive queue checking
        while len(self.matchmaking_queue) > 0:
            opponent_name = self.matchmaking_queue.pop(0)
            if opponent_name in self.connections:
                await self.create_game([opponent_name, user.username], is_ranked=True)
                return

        # Nobody available, join the queue
        self.matchmaking_queue.append(user.username)
        if user.username in self.connections:
            await self.connections[user.username].send_json({"type": "waiting"})

    async def create_game(self, usernames: list[str], is_ranked: bool):
        game_id = str(uuid.uuid4())

        for name in usernames:
            self.player_games[name] = game_id

        # Broadcast match_found using the helper
        await self.broadcast_to_game(
            game_id, {"type": "match_found", "game_id": game_id}
        )
        loop = asyncio.get_running_loop()

        # 1. Properly instantiate the Game model
        game = Game(
            id=game_id,
            players=usernames,
            word=self._random_word(),
            ends_at=loop.time() + 60,
            is_ranked=is_ranked,
        )

        # Initialize zero values for all players
        for name in usernames:
            game.scores[name] = 0.0
            game.round_wins[name] = 0

        # 2. Correct dictionary assignment
        self.games[game_id] = game

        # 3. Assign players to the game
        for name in usernames:
            self.player_games[name] = game_id

        # 4. Broadcast to the lobby
        await self.broadcast_to_game(
            game_id,
            {
                "type": "match_found",
                "game_id": game_id,
                "word": game.word,
                "duration": 60,
                "round_wins": game.round_wins,
            },
        )


class ImagePayload(BaseModel):
    base64_string: str


class UserRegister(BaseModel):
    username: str
    password: str
    email: str
