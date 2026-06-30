from enum import Enum

from fastapi import WebSocket
from pydantic import BaseModel, Field, field_validator


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


class ImagePayload(BaseModel):
    base64_string: str


class UserRegister(BaseModel):
    username: str
    password: str
    email: str

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        from utils.validators import validate_email
        validate_email(v)
        return v
