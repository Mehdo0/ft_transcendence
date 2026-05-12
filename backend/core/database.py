import sqlite3
from contextlib import contextmanager

from state.config import DB_NAME


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
                elo INTEGER
            )
        """)

        # creation du super user (modo)
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, elo) 
            VALUES ("modo", "modo_mdp", 9999)
        """)
