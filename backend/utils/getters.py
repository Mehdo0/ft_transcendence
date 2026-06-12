import random
from core.database import get_user
from schemas.data import Game, GameType, User
from services.ai_service import load_word_list
from state.state import games

def get_game_type(player_count: int) -> GameType:
    if player_count <= 1:
        return GameType.SOLO_AI
    if player_count >= 4:
        return GameType.FOUR_PLAYER
    return GameType.TWO_PLAYER_AI

def get_random_word():
    data = load_word_list()
    return random.choice(data)

def get_opponent(user: User, game_id: str) -> User:
    opponents = get_opponents(user, game_id)
    if not opponents:
        raise ValueError("opponent does not exist")
    opponent = get_user(opponents[0])
    if opponent is None:
        raise ValueError("opponent does not exist")
    return opponent


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