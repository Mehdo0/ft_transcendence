from schemas.data import Game, User
from core.setup import manager

GRACE_PERIOD = 10


def cancel_timer(game_id: str) -> None:
    task = manager.game_timers.pop(game_id, None)
    if task is not None:
        task.cancel()


async def calculate_new_elo(player1: User, player2: User, result: int):
    average = (player1.elo + player2.elo) / 2
    coefficient = max(5, 40 - round(average / 50))
    expected = 1 / (1 + 10 ** ((player2.elo - player1.elo) / 400))
    new_elo = round(player1.elo + (coefficient * (result - expected)))
    diff = new_elo - player1.elo
    return diff, new_elo


def cleanup_game(game: Game) -> None:
    for user in game.players:
        manager.player_games.pop(user, None)
        if user in manager.disconnected_players:
            manager.disconnected_players.remove(user)
    manager.games.pop(game.id, None)


def disconnect(user: User):
    manager.connections.pop(user.username, None)
    manager.player_games.pop(user.username, None)
    try:
        manager.disconnected_players.remove(user.username)
    except ValueError:
        pass
    remove_from_matchmaking(user.username)


def remove_from_matchmaking(username: str):
    if username in manager.matchmaking_queue:
        manager.matchmaking_queue.remove(username)


async def send_msg_to_opponents(
    game: Game,
    user: User,
    msg: dict[str, str],
):
    ws = None

    for player in game.players:
        if player != user.username:
            ws = manager.connections.get(player)
            if ws is not None:
                try:
                    await ws.send_json(msg)
                except Exception as e:
                    print(f"send_msg_to_opponents failed: {e}")
