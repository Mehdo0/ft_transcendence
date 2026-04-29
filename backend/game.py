import secrets

from backend.data import OnlinePlayer, Game, GameType, PlayerState


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
