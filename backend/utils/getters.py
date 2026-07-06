import random
from core.database import get_user
from schemas.data import Game, User
from services.ai_service import load_word_list
from state.state import games
from core.setup import manager


def get_random_word():
    data = load_word_list()
    return random.choice(data)


def get_opponents(user: User, game: Game) -> list[str]:
    print("getting opponents for game id: ", game.id, " and user ", user.username)
    print("players: ", manager.games[game.id].players)
    opponents = manager.games[game.id].players.copy()
    opponents.remove(user.username)  # keep all but queried user
    print("opponents: ", manager.games[game.id].players)
    return opponents


def get_users_unsafe(usernames: list[str]) -> list[User]:
    users = []
    assert len(usernames) >= 1
    for username in usernames:
        assert get_user(username) is not None
        user = get_user(username)
        users.append(user)
    return users


def get_total_score(game: Game, username: str) -> float:
    return min(
        100,
        game.score_bonuses.get(username, 0) + game.ai_scores.get(username, 0),
    )
