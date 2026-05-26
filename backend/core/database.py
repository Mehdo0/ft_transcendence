import random

from models.models import Base, UserModel
from schemas.data import User, UserRegister
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

DB_NAME = "data/game_data.db"
DATABASE_URL = f"sqlite+pysqlite:///{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    echo=True,  # debug logs
    connect_args={"check_same_thread": False},  # Necessary for fastAPI
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


def add_user(user: UserRegister) -> User:
    with SessionLocal() as session:
        user = UserModel(
            username=user.username,
            password=user.password,
            email=user.email,
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
        return User(
            username=user.username,
            email=user.email,
            hashed_password=user.password,
        )
