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


# class OfflinePlayer(BaseModel):  # may not be useful as offline players are stored in DB
#     name: str  # name is unique and used as ID
#     state: PlayerState = PlayerState.OFFLINE


class OnlinePlayer(BaseModel):
    name: str  # name is unique and used as ID
    state: PlayerState
    session: Session


class Game(BaseModel):
    id: str
    game_state: GameState = GameState.CONNECTING
    game_type: GameType
    players: list[OnlinePlayer] = Field(default_factory=list)
