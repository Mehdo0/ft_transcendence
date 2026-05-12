from data import User
from database import get_user_elo

# This function applies the chess elo formula to determine the new player elo after a game
# We use the chances to win and the elo difference to decide how much the player gains or losses elo


def calculate_new_elo(user1: User, enemy: User, result: int):
    elo1 = get_user_elo(user1.username)
    elo2 = get_user_elo(enemy.username)
    moyenne = (elo1 + elo2) / 2
    K = 40 - round(moyenne / 50)
    E = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
    new_elo = round(elo1 + (K * (result - E)))
    return new_elo
