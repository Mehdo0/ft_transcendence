import asyncio

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
    is_guest: bool = False


class ReplayPoint(BaseModel):
    x: float
    y: float


class ReplayStroke(BaseModel):
    points: list[ReplayPoint] = Field(default_factory=list)


class ReplayAction(str, Enum):
    APPEND_STROKE = "append_stroke"
    APPEND_POINTS = "append_points"
    REMOVE_STROKE = "remove_stroke"
    CLEAR = "clear"
    REPLACE = "replace"
    SCORE = "score"


class ReplayEvent(BaseModel):
    elapsed: float
    score: float
    action: ReplayAction
    points: list[ReplayPoint] = Field(default_factory=list)
    strokes: list[ReplayStroke] = Field(default_factory=list)


class RoundResult(BaseModel):
    round_number: int
    winner: str | None
    is_tie: bool
    match_complete: bool
    duration: float
    final_hold_duration: float
    timeline_duration: float
    drawings: dict[str, list[ReplayStroke]] = Field(default_factory=dict)
    timelines: dict[str, list[ReplayEvent]] = Field(default_factory=dict)
    scores: dict[str, float] = Field(default_factory=dict)
    round_wins: dict[str, int] = Field(default_factory=dict)


class Game(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    id: str
    game_state: GameState = GameState.CONNECTING
    players: list[str] = Field(default_factory=list)
    player_data: dict[str, User] = Field(default_factory=dict)
    word: str
    scores: dict[str, float] = Field(default_factory=dict)
    ai_scores: dict[str, float] = Field(default_factory=dict)
    score_bonuses: dict[str, float] = Field(default_factory=dict)
    round_wins: dict[str, int] = Field(default_factory=dict)
    drawings: dict[str, list[ReplayStroke]] = Field(default_factory=dict)
    replay_timelines: dict[str, list[ReplayEvent]] = Field(default_factory=dict)
    round_number: int = 1
    round_active: bool = True
    round_result: RoundResult | None = None
    countdown_duration: int
    starts_at: float
    ends_at: float
    is_ranked: bool = False
    timer: asyncio.Task | None = None


class Lobby(BaseModel):
    id: str
    host: str
    players: list[str]


class ImagePayload(BaseModel):
    base64_string: str


class UserRegister(BaseModel):
    username: str
    password: str
    email: str
