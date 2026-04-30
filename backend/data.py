from dataclasses import dataclass
from enum import Enum

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
    OFFLINE = "offline"
    IDLE = "idle"
    PLAYING = "playing"


@dataclass
class Session(BaseModel):
    ip_address: str
    session_id: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    state: PlayerState
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


class Game(BaseModel):
    id: str
    game_state: GameState = GameState.CONNECTING
    game_type: GameType
    players: list[User] = Field(default_factory=list)

MATCHMAKING_QUEUE = {
    "TWO_PLAYER_AI": [],  # List of players waiting for 1v1
    "FOUR_PLAYER": []     # List of players waiting for a 4-player
}