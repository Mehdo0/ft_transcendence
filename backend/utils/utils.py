from schemas.data import Game, User
from core.setup  import manager
from state.state import (
    connections,
    disconnected_players,
    game_timers,
    games,
    matchmaking_queue,
    player_games,
)


def cancel_timer(game_id: str) -> None:
    task = manager.game_timers.pop(game_id, None)
    # assert task is not None  # this is the only place where we cancel the task
    task.cancel()


async def calculate_new_elo(player1: User, player2: User, result: int):
    average = (player1.elo + player2.elo) / 2
    coefficient = 40 - round(average / 50)
    expected = 1 / (1 + 10 ** ((player2.elo - player1.elo) / 400))
    new_elo = round(player1.elo + (coefficient * (result - expected)))
    diff = new_elo - player1.elo
    return diff, new_elo


def cleanup_game(game: Game) -> None:
    for user in game.players:
        player_games.pop(user, None)
        if user in manager.disconnected_players:
            manager.disconnected_players.remove(user)
    games.pop(game.id)


def disconnect(user: User):
    connections.pop(user.username, None)
    player_games.pop(user.username, None)
    remove_from_matchmaking(user.username)


def remove_from_matchmaking(username: str):
    if username in manager.matchmaking_queue:
        manager.matchmaking_queue.remove(username)



