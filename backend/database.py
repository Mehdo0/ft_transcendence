import sqlite3
import random
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

    conn.row_factory = sqlite3.Row  # factorise le resultat en dictionnaire
    cursor = conn.cursor()
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
                email TEXT UNIQUE,
                elo INTEGER
            )
        """)

        # creation du super user (modo)
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, email, elo)
            VALUES ("modo", "modo_mdp", "modo@modo.com", 9999)
        """)

setup_database()

def add_user(username: str, password: str, email: str) -> User:
    with db_cursor(writable=True) as cursor:
        if username == "drawer":
            username = f"drawer{random.randint(1000, 9999)}"
        hashed_password = get_password_hash(password)
        try:
            cursor.execute(
                """
                INSERT INTO users (username, password, email, elo)
                VALUES (?, ?, ?, 0)
                """,
                (username, hashed_password, email),
            )
        except sqlite3.IntegrityError:
            raise ValueError("Username or email already in use")
        return User(username=username, email=email)


def get_user_elo(username: str):
    with db_cursor() as cursor:
        cursor.execute("SELECT elo FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
    return row[0]


def get_user(username: str) -> User | None:
    with db_cursor() as cursor:
        cursor.execute("SELECT username, password, email FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row is None:
            return None  # User not found
        return UserInDB(username=row["username"], hashed_password=row["password"], email=row["email"])
