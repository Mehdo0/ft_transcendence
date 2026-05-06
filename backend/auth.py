import sqlite3
import jwt
import random
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, WebSocketException, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError

from backend.data import Token, TokenData, User, UserInDB
from backend.global_var import (
    DB_NAME,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    DUMMY_HASH,
    SECRET_KEY,
    app,
    oauth2_scheme,
    password_hash,
)

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ici ca ajoute les tables si elles n'existent pas encore
    cursor.execute("""  
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            elo INTEGER
        )
    """)

    # creation du super user (modo)
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, elo) 
        VALUES ("modo", 9999)
    """)

    # et ca degage
    conn.commit()
    conn.close()

# Initialize DB on script load
setup_database()

def add_user(username: str, password: str) -> User:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if username == "drawer":
        username = f"drawer{random.randint(1000, 9999)}"
    hashed_password = get_password_hash(password)
    try:
        cursor.execute(
            """
            INSERT INTO users (username, password, elo) 
            VALUES (?, ?, 0)
            """,
            (username, hashed_password)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # This triggers if the username already exists
        conn.close()
        raise ValueError("This username is already taken.")
    conn.close()
    return User(username=username)


def get_user_elo(username: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT elo FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0]

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def get_user(username: str) -> User | None:
    # Connects to DB, fetches the user by ID, and returns the row.
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # factorise le resultat en dictionnaire
    cursor = conn.cursor()
    # le '?' est une protection contre les attaques par injection SQL
    cursor.execute("SELECT username, password FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    # et ca degage
    conn.close()
    if row is None:
        return None  # User not found
    return UserInDB(username=row["username"], hashed_password=row["password"])

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
    if hasattr(current_user, 'disabled') and current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
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
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user


@app.post("/api/register/")
async def registering(username: str, password: str):
    username_test = get_user(username)
    if username_test:
        raise HTTPException(status_code=406, detail="Username already used")
    
    add_user(username, password)
    
    if get_user(username):
        return {"user_created": username}
    else:
        raise HTTPException(status_code=500, detail="Error while adding user")