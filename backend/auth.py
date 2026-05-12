import jwt
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, WebSocketException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError

from data import TokenData, User, UserRegister
from database import add_user, get_user
from state import (
    DB_NAME,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    DUMMY_HASH,
    SECRET_KEY,
    app,
    cookie_scheme,
    password_hash,
    COOKIE_SECURE,
)


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        verify_password(password, DUMMY_HASH)  # preventing timing attacks
        return False
    if not verify_password(password, user.hashed_password):
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
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=token_data.username)
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


@app.post("/api/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response,
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="strict",
        secure=COOKIE_SECURE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return {"ok": True}


@app.get("/api/users/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user


@app.post("/api/register/")
async def registering(payload: UserRegister, response: Response):
    username_test = get_user(payload.username)
    if username_test:
        raise HTTPException(status_code=406, detail="Username already used")

    add_user(payload.username, payload.password, payload.email)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": payload.username}, expires_delta=access_token_expires
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="strict",
        secure=COOKIE_SECURE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    if get_user(payload.username):
        return {"user_created": payload.username}
    else:
        raise HTTPException(status_code=500, detail="Error while adding user")


@app.post("/api/logout")
async def logout(response: Response):
    # unprotected -> cookie expiry
    response.delete_cookie("access_token")
    return {"ok": True}
