from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from core.database import (
    get_ranking,
    get_user,
    get_user_rank,
    get_usernames_by_prefix,
)
from core.exceptions import (
    BadUsername,
    EmailAlreadyTakenError,
    ImpossibleEmail,
    UserAlreadyExistsError,
    UsernameAlreadyTakenError,
    WeakPassword,
)
from core.setup import manager
from game.game_logic import surrender_game
from schemas.data import User, UserRegister
from services.guest_service import create_guest_user
from services.services import (
    create_access_token,
    get_access_token,
    get_session,
    register_user,
)
from state.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_SECURE,
    GUEST_ACCESS_TOKEN_EXPIRE_MINUTES,
    GUEST_USERNAME_PREFIX,
    LEADERBOARD_LIMIT,
    limiter,
)

router = APIRouter()


def set_access_cookie(response: Response, token: str, max_age_minutes: int) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        path="/",
        httponly=True,
        samesite="strict",
        secure=COOKIE_SECURE,
        max_age=max_age_minutes * 60,
    )


def get_reserved_usernames() -> set[str]:
    usernames = (
        set(manager.connected_users)
        | set(manager.player_games)
        | manager.guest_usernames
        | get_usernames_by_prefix(GUEST_USERNAME_PREFIX)
    )
    for lobby in manager.lobbies.values():
        usernames.update(lobby.players)
    return usernames


@router.get("/api/users/{username}/stats")
async def API_get_user_stats(username: str):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "Elo": user.elo}


@router.get("/api/get_ranking")
async def API_get_ranking(
    current_user: Annotated[User | None, Depends(get_session)],
):
    try:
        current_rank = None
        if current_user is not None and not current_user.is_guest:
            current_rank = get_user_rank(current_user.username)
        return {
            "players": get_ranking(LEADERBOARD_LIMIT),
            "current": current_rank,
            "limit": LEADERBOARD_LIMIT,
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/guest")
@limiter.limit("30/minute")
async def API_create_guest(
    request: Request,
    response: Response,
    current_user: Annotated[User | None, Depends(get_session)],
):
    if current_user is not None:
        if current_user.is_guest:
            manager.guest_usernames.add(current_user.username)
        return {"user": current_user}

    try:
        guest = create_guest_user(get_reserved_usernames())
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))

    manager.guest_usernames.add(guest.username)
    token = create_access_token(
        data={"sub": guest.username, "guest": True},
        expires_delta=timedelta(minutes=GUEST_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    set_access_cookie(response, token, GUEST_ACCESS_TOKEN_EXPIRE_MINUTES)
    return {"user": guest}


@router.post("/api/token")
@limiter.limit("10/minute")
async def API_login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
):
    try:
        token = await get_access_token(form_data)
    except ValueError as e:
        print(str(e))
        raise HTTPException(401, str(e))
    set_access_cookie(response, token.access_token, ACCESS_TOKEN_EXPIRE_MINUTES)
    return {"ok": True}


@router.get("/api/session/")
@limiter.limit("120/minute")
async def API_session_is_authenticated(
    request: Request,
    current_user: Annotated[User | None, Depends(get_session)],
):
    if current_user is None:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": current_user}


@router.get("/api/reconnect/")
@limiter.limit("120/minute")
async def API_reconnect(
    request: Request,
    current_user: Annotated[User | None, Depends(get_session)],
):
    if current_user is None:
        return {"reconnect": False}
    id = manager.player_games.get(current_user.username)
    if id:
        return {"reconnect": True, "id": id}
    else:
        return {"reconnect": False}


@router.get("/api/surrender")
@limiter.limit("120/minute")
async def API_surrender(
    request: Request,
    current_user: Annotated[User | None, Depends(get_session)],
):
    if current_user is None:
        return {"success": False}
    id = manager.player_games.get(current_user.username)
    if id:
        try:
            await surrender_game(current_user)
        except Exception as e:
            raise HTTPException(404, e)
        return {"success": True}
    else:
        return {"success": False}


@router.post("/api/register/")
@limiter.limit("30/minute")
async def API_register(request: Request, payload: UserRegister, response: Response):
    try:
        result = await register_user(payload)
    except (
        UserAlreadyExistsError,
        UsernameAlreadyTakenError,
        EmailAlreadyTakenError,
        BadUsername,
        ImpossibleEmail,
        WeakPassword,
    ) as e:
        raise HTTPException(status_code=409, detail=str(e).lower())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    access_token = create_access_token(
        data={"sub": payload.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    set_access_cookie(response, access_token, ACCESS_TOKEN_EXPIRE_MINUTES)
    return result


@router.post("/api/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}
