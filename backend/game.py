import secrets

from backend.data import Game, GameType, PlayerState, GameState, MATCHMAKING_QUEUE
from backend.auth import User, Depends, get_current_user

def start_solo(player: User, game: Game):
    # start game
    return game


def start_two_player(player: User, game: Game):
    # game.game_state = GameState.SEARCHING_OPPONENT
    # opponent: Player = find_player()

    # opponent.state = PlayerState.PLAYING
    # game.players.append(opponent)

    # start game
    return game


def start_four_player(player: User, game: Game):
    # game.game_state = GameState.SEARCHING_OPPONENT
    # opponent: Player = find_player()

    # opponent.state = PlayerState.PLAYING
    # game.players.append(opponent)

    # start game
    return game


def create_game(game_type: GameType) -> Game:
    game: Game = Game.__init__()
    game.id = secrets.token_urlsafe(8)
    game.game_state = GameState.CONNECTING
    game.game_type = game_type

    # add player to lobby TODO

    match game_type:
        case GameType.SOLO_AI:
            return start_solo(player, game)
        case GameType.TWO_PLAYER_AI:
            return start_two_player(player, game)
        case GameType.FOUR_PLAYER:
            return start_four_player(player, game)

async def fill_game():
    if len(MATCHMAKING_QUEUE) < 2:
        return 
    elif:
    #TODO : make the filling logic 