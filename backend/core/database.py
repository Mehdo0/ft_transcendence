import random

from models.models import Base, UserModel
from schemas.data import User, UserInDB
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

DB_NAME = "data/game_data.db"
DATABASE_URL = f"sqlite+pysqlite:///{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    echo=True,  # debug logs
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def setup_database():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        existing_user = session.get(UserModel, "modo")
        if existing_user is None:
            modo = UserModel(
                username="modo",
                password="",
                elo=9999,
                email="modo@example.com",
            )

            session.add(modo)
            session.commit()


setup_database()


# Dependency/helper
def get_session() -> Session:
    with SessionLocal() as session:
        yield session


def add_user(username: str, hashed_password: str, email: str) -> User:
    if username == "drawer":
        username = f"drawer{random.randint(1000, 9999)}"
    with SessionLocal() as session:
        existing_user = session.get(UserModel, username)

        if existing_user:
            raise ValueError("This username is already taken.")

        user = UserModel(
            username=username,
            password=hashed_password,
            email=email,
            elo=0,
        )

        session.add(user)
        session.commit()

        return User(
            username=user.username,
            email=user.email,
            hashed_password=user.password,
        )


def get_ranking():
    with SessionLocal() as session:
        stmt = (
            select(UserModel.username, UserModel.elo)
            .order_by(UserModel.elo.desc())
            .limit(10)
        )

        rows = session.execute(stmt).mappings().all()

        return list(rows)


def get_user_elo(username: str) -> int | None:
    with SessionLocal() as session:
        user = session.get(UserModel, username)

        if user is None:
            return None
        return user.elo


def get_user(username: str) -> User | None:
    with SessionLocal() as session:
        user = session.get(UserModel, username)
        if user is None:
            return None
        return UserInDB(
            username=user.username,
            email=user.email,
            hashed_password=user.password,
        )
