import random
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
import bcrypt
from core.database import get_user, get_user_hashed_password, add_user
from core.exceptions import (
    UserAlreadyExistsError,
    UsernameAlreadyTakenError,
)
from fastapi import Depends, HTTPException, WebSocketException, status, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from schemas.data import Token, User, UserRegister
from services.ai_service import internal_make_ai_guess, load_word_list
from state.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    cookie_scheme,
)
from utils.validators import validate_email


async def get_random_word() -> str:
    data = load_word_list()
    return random.choice(data)


async def make_ai_guess(strokes: list, target_word: str):
    assert isinstance(strokes, list)
    results = internal_make_ai_guess(strokes, target_word)
    if not results:
        raise ValueError("Bad AI output")
    return results


async def get_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = get_authenticated_user(
        form_data.username,
        form_data.password,
    )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


def validate_password_stength(password: str) -> None:
    SpecialSym = ["$", "@", "#", "%"]
    if len(password) < 8 or len(password) > 64:
        raise ValueError("Password must be between 8 and 64 characters")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one digit")
    if not any(char.isupper() for char in password):
        raise ValueError("Password should contain at least one uppercase letter")
    if not any(char.islower() for char in password):
        raise ValueError("Password should contain at least one lowercase letter")
    if not any(char in SpecialSym for char in password):
        raise ValueError("Password should have at least one of the symbols $@#%")


async def register_user(user_register: UserRegister):
    try:
        validate_email(user_register.email)
    except Exception:
        raise ValueError("Email is invalid")
    validate_password_stength(user_register.password)
    user_exists = get_user(user_register.username)
    if user_exists:
        if user_exists.username == user_register.username:
            if user_exists.email == user_register.email:
                raise UserAlreadyExistsError("This user already exists")
            else:
                raise UsernameAlreadyTakenError("This username is already taken")
    user = add_user(user_register)
    return {"user_created": user.username}


### auth


def get_authenticated_user(username: str, password: str) -> User:
    user = get_user(username)
    if not user:
        raise ValueError("User doesnt exist")
    hashed_password = get_user_hashed_password(user)
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password is too long (max 64 characters)")
    if not bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8")):
        raise ValueError("Passwords dont match")
    return user

async def get_session(access_token: str | None = Cookie(default=None)):
    if not access_token:
        return None
        
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
    except InvalidTokenError:
        return None
        
    user = get_user(username)
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=365)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_from_ws_token(token: str) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        user = get_user(username)
        if user is None:
            raise WebSocketException(code=status.HTTP_404_NOT_FOUND)
        return user
    except jwt.InvalidTokenError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

