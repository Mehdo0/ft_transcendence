import sqlite3

# Define the DB name as a constant so you only have to type it once
DB_NAME = "game_data.db"

def setup_database():
    conn = sqlite3.connect(DB_NAME) # on ce connect a la db (ceci creer la db si elle n'existe pas)
    cursor = conn.cursor()
    
    #ici ca ajoute les tables si elles n'existent pas encore
    cursor.execute('''  
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            wins INTEGER,
            losses INTEGER
        )
    ''')
    
    #creation du super user (modo)
    cursor.execute('''
        INSERT OR IGNORE INTO users (id, username, wins, losses) 
        VALUES (1, "modo", 999, 0)
    ''')
    
    #et ca degage 
    conn.commit()
    conn.close()

def fetch_user_stats(user_id: int):
    """Connects to DB, fetches the user by ID, and returns the row."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row #factorise le resultat en dictionnaire 
    cursor = conn.cursor()
    #le '?' est une protection contre les attaques par injection SQL
    cursor.execute("SELECT id, username, wins, losses FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone() 
    
    #et ca degage
    conn.close()
    return row

def add_user(username: str):
    """Connects to DB, fetches the user by ID, and create a new one."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    #ici on trouve l'id max pour mettre le nouveau user a la fin de la table
    cursor.execute("SELECT MAX(id) FROM users") 
    max_id = cursor.fetchone()[0] #on isole l'id
    new_user_id = 1 if max_id is None else max_id + 1 #on assigne la max + 1
    if username == "drawer":
        username = username + str(new_user_id) #username par defaut
    cursor.execute('''
        INSERT INTO users (id, username, wins, losses) 
        VALUES (?, ?, 0, 0)
    ''', (new_user_id, username)) #on add a la db
    conn.commit()
    conn.close()
    return new_user_id #on return son id

def reset_database(): #debug purpose, SUPPRIMER AVANT DE RENDRE LE PROJET
    """Destroys the table entirely and rebuilds a fresh one. Resets all IDs."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    
    conn.commit()
    conn.close()
    setup_database()