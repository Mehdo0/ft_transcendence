import os
from backend.database import setup_database

# DB var
setup_database()
os.makedirs("data", exist_ok=True)
