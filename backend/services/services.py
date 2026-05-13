import datetime
import random
import sqlite3
from datetime import timedelta, timezone
from typing import Annotated
import jwt
from jwt import InvalidTokenError, encode, decode

from fastapi import Depends, HTTPException, status, WebSocketException
from fastapi.security import OAuth2PasswordRequestForm

from services.ai_service import internal_make_ai_guess, load_word_list
from schemas.data import ImagePayload, Token, User, UserInDB
from core.database import db_cursor
from state.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    DUMMY_HASH,
    oauth2_scheme,
    ALGORITHM,
    SECRET_KEY,
)


async def get_user_elo(username: str):
    with db_cursor() as cursor:
        cursor.execute("SELECT elo FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row[0] is None:
            raise ValueError("User not found")


async def get_random_word() -> str:
    data = load_word_list()
    return random.choice(data)


def add_user(username: str, hashed_password: str, email: str) -> User:
    with db_cursor(writable=True) as cursor:
        if username == "drawer":
            username = f"drawer{random.randint(1000, 9999)}"
        try:
            cursor.execute(
                """
                INSERT INTO users (username, password, email, elo)
                VALUES (?, ?, ?, 0)
                """,
                (username, hashed_password, email),
            )
        except sqlite3.IntegrityError:
            raise ValueError("Username or email already in use")
        return User(username=username, email=email, hashed_password=hashed_password)


async def make_ai_guess(payload: ImagePayload, target_word: str):
    base64_str = payload.base64_string
    if "data:image" not in base64_str:
        raise ValueError("wrong payload")
    results = internal_make_ai_guess(base64_str, target_word)
    if not results or len(results) != 3:
        raise ValueError("Bad AI output")
    return results


async def get_ranking():
    with db_cursor() as cursor:
        try:
            cursor.execute("SELECT username, elo FROM users ORDER BY elo DESC LIMIT 10")
            row = cursor.fetchall()
            result = [
                {"username": player["username"], "elo": player["elo"]} for player in row
            ]
        except Exception as e:
            print("Error:", e)
        return result


async def get_user(username: str) -> User | None:
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT username, password FROM users WHERE username = ?", (username,)
        )
        row = cursor.fetchone()
        if row is None:
            return None  # User not found
        return UserInDB(username=row["username"], hashed_password=row["password"])


async def get_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise ValueError("couldnt authenticate")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


async def register_user(username: str, password: str):
    username_test = await get_user(username)
    if username_test:
        raise ValueError("Username already used")
    await add_user(username, password)
    if await get_user(username):
        return {"user_created": username}
    else:
        raise ValueError("Error while adding user")


### auth


async def authenticate_user(username: str, hashed_password: str):
    user = await get_user(username)
    if not user:
        hashed_password != DUMMY_HASH  # preventing timing attack
        return False
    if hashed_password != user.hashed_password:
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = await get_user(username)
    if user is None:
        raise credentials_exception
    return user


def get_username_from_ws_token(token: str) -> str:
    try:
        # Decode the token exactly like we did in the HTTP bouncer
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        return username
    except jwt.InvalidTokenError:
        # If the token is fake or expired, instantly kill the connection
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    # Note: Ensure the User model has a 'disabled' attribute or adjust accordingly
    if hasattr(current_user, "disabled") and current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
