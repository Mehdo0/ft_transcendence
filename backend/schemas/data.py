from enum import Enum

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


class PlayerState(str, Enum):
    IDLE = "idle"
    PLAYING = "playing"


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


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str
    state: PlayerState | None = None
    elo: int


class Game(BaseModel):
    id: str
    game_state: GameState = GameState.CONNECTING
    game_type: GameType = GameType.TWO_PLAYER_AI
    players: list[str] = Field(default_factory=list)
    word: str
    scores: dict[str, float] = Field(default_factory=dict)
    ai_scores: dict[str, float] = Field(default_factory=dict)
    score_bonuses: dict[str, float] = Field(default_factory=dict)
    round_wins: dict[str, int] = Field(default_factory=dict)
    ends_at: float | None = None
    is_ranked: bool = False


class ImagePayload(BaseModel):
    base64_string: str


class UserRegister(BaseModel):
    username: str
    password: str
    email: str
