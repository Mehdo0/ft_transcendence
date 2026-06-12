from schemas.data import Game, User
from state.state import (
    connections,
    disconnected_players,
    game_timers,
    games,
    matchmaking_queue,
    player_games,
)

def should_finish_round(game: Game, score: float) -> bool:
    return score >= 100

def cancel_timer(game_id: str):
    task = game_timers.pop(game_id, None)
    if task is not None:
        task.cancel()
        
async def calculate_new_elo(player1: User, player2: User, result: int):
    average = (player1.elo + player2.elo) / 2
    coefficient = 40 - round(average / 50)
    expected = 1 / (1 + 10 ** ((player2.elo - player1.elo) / 400))
    new_elo = round(player1.elo + (coefficient * (result - expected)))
    diff = new_elo - player1.elo
    return diff, new_elo

def cleanup_game(game_id: str, *users: User):
    games.pop(game_id, None)
    for user in users:
        player_games.pop(user.username, None)
        disconnected_players.pop(user.username, None)


def ensure_round_wins(game: Game):
    for player in game.players:
        game.round_wins[player] = game.round_wins.get(player, 0)

def disconnect(user: User):
    connections.pop(user.username, None)
    player_games.pop(user.username, None)
    remove_from_matchmaking(user.username)


def remove_from_matchmaking(username: str):
    if username in matchmaking_queue:
        matchmaking_queue.remove(username)