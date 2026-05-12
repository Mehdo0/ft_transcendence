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
