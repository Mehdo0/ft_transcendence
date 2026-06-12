import random
from core.database import get_user
from schemas.data import Game, User
from services.ai_service import load_word_list
from state.state import games


def get_random_word():
    data = load_word_list()
    return random.choice(data)


def get_opponents(user: User, game_id: str) -> list[str]:
    return [player for player in games[game_id].players if player != user.username]


def get_users(usernames: list[str]) -> list[User]:
    users = []
    for username in usernames:
        user = get_user(username)
        if user is None:
            raise ValueError("lobby player not found")
        users.append(user)
    return users


def get_total_score(game: Game, username: str) -> float:
    return min(
        100,
        game.score_bonuses.get(username, 0) + game.ai_scores.get(username, 0),
    )
