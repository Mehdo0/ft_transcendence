from dataclasses import dataclass
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


class ConnectionManager:
    def __init__(self):
        # This dictionary links a username to their open WebSocket
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()  # This creates a Websocket
        self.active_connections[username] = (
            websocket  # And here we bind the user to the socket
        )

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[
                username
            ]  # We simply remove the connection in the dictionary

    async def send_personal_message(self, message: dict, username: str):
        # Send a JSON message to one specific player
        if username in self.active_connections:
            websocket = self.active_connections[username]
            await websocket.send_json(message)
