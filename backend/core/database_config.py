from pathlib import Path

from utils.env import read_non_empty_string


DATABASE_PATH = Path(read_non_empty_string("DB_PATH", "data/game_data.db"))
DATABASE_URL = f"sqlite+pysqlite:///{DATABASE_PATH.as_posix()}"
