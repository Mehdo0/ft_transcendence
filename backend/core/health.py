from sqlalchemy import text

from core.database import engine


def check_database() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
