import secrets

from schemas.data import User
from state.config import (
    GUEST_GENERATION_ATTEMPTS,
    GUEST_USERNAME_DIGITS,
    GUEST_USERNAME_PREFIX,
)


def is_guest_username(username: str) -> bool:
    return username.casefold().startswith(GUEST_USERNAME_PREFIX.casefold())


def generate_guest_username(reserved_usernames: set[str]) -> str:
    upper_bound = 10**GUEST_USERNAME_DIGITS
    for _ in range(GUEST_GENERATION_ATTEMPTS):
        suffix = secrets.randbelow(upper_bound)
        username = f"{GUEST_USERNAME_PREFIX}{suffix:0{GUEST_USERNAME_DIGITS}d}"
        if username not in reserved_usernames:
            return username
    raise RuntimeError("Could not generate a guest username")


def create_guest_user(reserved_usernames: set[str]) -> User:
    return User(
        username=generate_guest_username(reserved_usernames),
        email="",
        elo=0,
        is_guest=True,
    )
