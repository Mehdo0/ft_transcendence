import random
from core.database import get_user
from schemas.data import Game, User
from services.ai_service import load_word_list


def get_random_word():
    data = load_word_list()
    return random.choice(data)


def get_opponents(user: User, game: Game) -> list[str]:
    opponents = game.players.copy()
    opponents.remove(user.username)
    return opponents


def get_game_user(game: Game, username: str) -> User | None:
    return game.player_data.get(username) or get_user(username)


def get_game_users(game: Game) -> list[User]:
    users = []
    for username in game.players:
        user = get_game_user(game, username)
        if user is None:
            raise ValueError(f"Player {username} does not exist")
        users.append(user)
    return users


def get_total_score(game: Game, username: str) -> float:
    return min(
        100,
        game.score_bonuses.get(username, 0) + game.ai_scores.get(username, 0),
    )
