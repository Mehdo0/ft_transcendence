from dataclasses import dataclass
from enum import Enum
from random import randint

from pydantic import BaseModel, Field

import secrets


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


def start_solo(player: OnlinePlayer, game: Game):
    # start game
    return game


def start_two_player(player: OnlinePlayer, game: Game):
    # game.game_state = GameState.SEARCHING_OPPONENT
    # opponent: Player = find_player()

    # opponent.state = PlayerState.PLAYING
    # game.players.append(opponent)

    # start game
    return game


def start_four_player(player: OnlinePlayer, game: Game):
    # game.game_state = GameState.SEARCHING_OPPONENT
    # opponent: Player = find_player()

    # opponent.state = PlayerState.PLAYING
    # game.players.append(opponent)

    # start game
    return game


def create_game(player: OnlinePlayer, game_type: GameType) -> Game:
    game: Game = Game.__init__()
    game.id = secrets.token_urlsafe(8)
    game.game_state = GameState.CONNECTING
    game.game_type = game_type

    # add player to lobby TODO

    player.state = PlayerState.PLAYING
    game.players.append(player)

    match game_type:
        case GameType.SOLO_AI:
            return start_solo(player, game)
        case GameType.TWO_PLAYER_AI:
            return start_two_player(player, game)
        case GameType.FOUR_PLAYER:
            return start_four_player(player, game)
