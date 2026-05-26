import random
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from core.database import get_user, add_user
from core.exceptions import UserAlreadyExistsError
from fastapi import Depends, HTTPException, WebSocketException, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from schemas.data import ImagePayload, Token, User, UserRegister
from services.ai_service import internal_make_ai_guess, load_word_list
from state.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    DUMMY_HASH,
    SECRET_KEY,
    cookie_scheme,
)


async def get_random_word() -> str:
    data = load_word_list()
    return random.choice(data)


async def make_ai_guess(payload: ImagePayload, target_word: str):
    base64_str = payload.base64_string
    if "data:image" not in base64_str:
        raise ValueError("wrong payload")
    results = internal_make_ai_guess(base64_str, target_word)
    if not results:
        raise ValueError("Bad AI output")
    return results


async def get_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    try:
        user = authenticate_user(form_data.username, form_data.password)
    except Exception:
        raise ValueError("couldnt authenticate")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


async def register_user(user_register: UserRegister):
    username_test = get_user(user_register.username)
    if username_test:
        raise UserAlreadyExistsError
    user = add_user(user_register)
    return {"user_created": user.username}


### auth


def authenticate_user(username: str, hashed_password: str):
    user = get_user(username)
    if not user:
        hashed_password != DUMMY_HASH  # preventing timing attack
        raise ValueError("User doesnt exist")
    if hashed_password != user.hashed_password:
        raise ValueError("Passwords dont match")
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


async def get_current_user(token: Annotated[str, Depends(cookie_scheme)]):
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
    user = get_user(username)
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
