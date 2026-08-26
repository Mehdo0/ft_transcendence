import bcrypt

from models.models import Base, UserModel
from schemas.data import User, UserRegister
from sqlalchemy import and_, create_engine, func, or_, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from core.exceptions import EmailAlreadyTakenError

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
        session.commit()


def add_user(user: UserRegister) -> User:
    # hash the password using a random salt.
    # the salt is stored directly inside the hash
    hashed_salted_password: str = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")
    with SessionLocal() as session:
        user_model = UserModel(
            username=user.username,
            hashed_password=hashed_salted_password,
            email=user.email,
            elo=500,
        )
        try:
            session.add(user_model)
            session.commit()

            return User(
                username=user_model.username,
                email=user_model.email,
                elo=user_model.elo,
            )
        except IntegrityError:
            session.rollback()

            raise EmailAlreadyTakenError("This email is already taken.")


def get_ranking(limit: int) -> list[dict[str, str | int]]:
    with SessionLocal() as session:
        stmt = (
            select(UserModel.username, UserModel.elo)
            .order_by(UserModel.elo.desc(), UserModel.username.asc())
            .limit(limit)
        )
        rows = session.execute(stmt).mappings().all()
        return [
            {"rank": index, "username": row.username, "elo": row.elo}
            for index, row in enumerate(rows, start=1)
        ]


def get_user_rank(username: str) -> dict[str, str | int] | None:
    with SessionLocal() as session:
        user = session.get(UserModel, username)
        if user is None:
            return None

        preceding_users = select(func.count()).select_from(UserModel).where(
            or_(
                UserModel.elo > user.elo,
                and_(UserModel.elo == user.elo, UserModel.username < user.username),
            )
        )
        rank = session.scalar(preceding_users) or 0
        return {"rank": rank + 1, "username": user.username, "elo": user.elo}


def get_usernames_by_prefix(prefix: str) -> set[str]:
    with SessionLocal() as session:
        usernames = session.scalars(select(UserModel.username)).all()
        normalized_prefix = prefix.casefold()
        return {
            username
            for username in usernames
            if username.casefold().startswith(normalized_prefix)
        }


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


def get_user_hashed_password(user: User) -> str:
    with SessionLocal() as session:
        user_model = session.get(UserModel, user.username)
        assert user_model is not None
        return user_model.hashed_password


def update_user_elo(user: User, new_elo: int):
    with SessionLocal() as session:
        userInDb = session.get(UserModel, user.username)
        if userInDb is None:
            return
        userInDb.elo = new_elo
        session.commit()
