from backend.data import User
from backend.database import get_user_elo



def define_K(elo1: int, elo2: int):
    moyenne = (elo1 + elo2) / 2
    K = 40 - round(moyenne / 50)
    return K


def calculate_new_elo(user1: User, enemy: User, result: int):
    elo1 = get_user_elo(user1.username)
    elo2 = get_user_elo(enemy.username)
    K = define_K(elo1, elo2)
    E = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
    new_elo = round(elo1 + (K * (result - E)))
    return new_elo

