from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field
from fastapi import WebSocket


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
    # email: str
    state: PlayerState | None = None
    disabled: bool | None = None


class UserInDB(User):
    username: str
    hashed_password: str
    # email: str


class Game(BaseModel):
    id: str
    game_state: GameState = GameState.CONNECTING
    game_type: GameType
    players: list[User] = Field(default_factory=list)


class ImagePayload(BaseModel):
    base64_string: str


class UserRegister(BaseModel):
    username: str = "drawer"
    password: str
    # email: str


class ConnectionManager:
    def __init__(self):
        # This dictionary links a username (string) to their open WebSocket
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        # Accept the incoming phone call
        await websocket.accept()
        # Save their phone line in our dictionary
        self.active_connections[username] = websocket

    def disconnect(self, username: str):
        # Remove them from the dictionary when they hang up
        if username in self.active_connections:
            del self.active_connections[username]

    async def send_personal_message(self, message: dict, username: str):
        # Send a JSON message to one specific player
        if username in self.active_connections:
            websocket = self.active_connections[username]
            await websocket.send_json(message)
