import os
import sqlite3
from backend.data import User
from backend.auth import get_password_hash


# Define the DB name as a constant so you only have to type it once
DB_DIR = "data"
DB_NAME = f"{DB_DIR}/game_data.db"
os.makedirs(DB_DIR, exist_ok=True)


def setup_database():
    conn = sqlite3.connect(
        DB_NAME
    )  # on ce connect a la db (ceci creer la db si elle n'existe pas)
    cursor = conn.cursor()

    # ici ca ajoute les tables si elles n'existent pas encore
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

    # et ca degage
    conn.commit()
    conn.close()


def add_user(username: str, password: str):
    # Connects to DB, fetches the user by ID, and create a new one.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()
    return User(username=username)

def get_user_elo(username: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT elo FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0]