import sqlite3
from contextlib import contextmanager

from backend.data import User, UserInDB
from backend.hash_service import get_password_hash

DB_NAME = "data/game_data.db"


# provide `cursor` context,
# takes boolean to specify write or read-only access
@contextmanager
def db_cursor(
    writable=False,
):
    if writable:
        conn = sqlite3.connect(DB_NAME)
    else:
        conn = sqlite3.connect(f"file:{DB_NAME}?mode=ro", uri=True)

    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row  # factorise le resultat en dictionnaire
    try:
        yield cursor
        if writable:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def setup_database():
    with db_cursor(writable=True) as cursor:
        # ajoute les tables si elles n'existent pas encore
        cursor.execute("""  
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                elo INTEGER
            )
        """)

        # creation du super user (modo)
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, elo) 
            VALUES ("modo", 9999)
        """)


def add_user(username: str, password: str):
    with db_cursor(writable=True) as cursor:
        # ici on trouve l'id max pour mettre le nouveau user a la fin de la table
        cursor.execute("SELECT MAX(id) FROM users")
        max_id = cursor.fetchone()[0]  # on isole l'id
        new_user_id = 1 if max_id is None else max_id + 1  # on assigne la max + 1
        if username == "drawer":
            username = username + str(new_user_id)  # username par defaut
        password = get_password_hash(password)
        cursor.execute(
            """
            INSERT INTO users (username, password, elo) 
            VALUES (?, ?, 0)
        """,
            (username, password),
        )  # on add a la db
        return User(username=username)


def get_user_elo(username: str):
    with db_cursor() as cursor:
        cursor.execute("SELECT elo FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
    return row[0]


def get_user(username: str) -> User | None:
    with db_cursor() as cursor:
        # Connects to DB, fetches the user by ID, and returns the row.
        # le '?' est une protection contre les attaques par injection SQL
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row is None:
            return None  # User not found
        return UserInDB(username=row["username"], hashed_password=row["password"])
