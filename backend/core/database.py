import random

from models.models import Base, UserModel
from schemas.data import User, UserRegister
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError
from core.exceptions import UserAlreadyExistsError, EmailAlreadyTakenError

DB_NAME = "data/game_data.db"
DATABASE_URL = f"sqlite+pysqlite:///{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    echo=False,  # debug logs
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


def add_user(user: UserRegister) -> User:
    with SessionLocal() as session:
        user = UserModel(
            username=user.username,
            password=user.password,
            email=user.email,
            elo=500,
        )
        try:
            session.add(user)
            session.commit()

            return User(
                username=user.username,
                email=user.email,
                elo=user.elo,
            )
        except IntegrityError:
            session.rollback()

            raise EmailAlreadyTakenError("This email is already taken.")


def get_ranking():
    with SessionLocal() as session:
        stmt = (
            select(UserModel.username, UserModel.elo)
            .order_by(UserModel.elo.desc())
            .limit(10)
        )
        rows = session.execute(stmt).mappings().all()
        return list(rows)


def get_user(username: str) -> User | None:
    with SessionLocal() as session:
        user = session.get(UserModel, username)
        if user is None:
            return None
        return User(
            username=user.username,
            email=user.email,
            elo=user.elo,
        )


def get_user_password(user: User) -> str:
    with SessionLocal() as session:
        user = session.get(UserModel, user.username)
        assert user is not None
        return user.password


def update_user_elo(user: User, new_elo: int):
    with SessionLocal() as session:
        userInDb = session.get(UserModel, user.username)
        if userInDb is None:
            return
        userInDb.elo = new_elo
        session.commit()
