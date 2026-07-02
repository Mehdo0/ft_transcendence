import asyncio
from schemas.data import Game, User
from state.state import (
    connections,
    disconnected_players,
    game_timers,
    games,
    matchmaking_queue,
    player_games,
)

GRACE_PERIOD = 10


def cancel_timer(game_id: str) -> None:
    task = game_timers.pop(game_id, None)
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
        if user in disconnected_players:
            disconnected_players.remove(user)
    games.pop(game.id)


def disconnect(user: User):
    connections.pop(user.username, None)
    player_games.pop(user.username, None)
    remove_from_matchmaking(user.username)


async def run_disconnect_grace_period(username: str, on_timeout):
    disconnected_players.append(username)
    await asyncio.sleep(GRACE_PERIOD)
    if username not in disconnected_players:  # reconnected in the meantime
        return
    disconnected_players.remove(username)
    await on_timeout()


def remove_from_matchmaking(username: str):
    if username in matchmaking_queue:
        matchmaking_queue.remove(username)


async def send_msg_to_opponents(
    game: Game,
    user: User,
    msg: dict[str, str],
):
    for p in game.players:
        if p != user.username:  # message all opponents
            assert p in connections  # opponent should be connected
            await connections[p].send_json(msg)


async def send_msg_to_players(
    game: Game,
    msg: dict[str, str],
):
    for p in game.players:
        assert p in connections  # opponent should be connected
        await connections[p].send_json(msg)
