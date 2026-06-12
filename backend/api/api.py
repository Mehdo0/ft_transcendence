from datetime import timedelta
from typing import Annotated

from core.database import (
    get_ranking,
    get_user,
)
from core.exceptions import UserAlreadyExistsError
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from schemas.data import User, UserRegister
from services.services import (
    create_access_token,
    get_access_token,
    get_current_active_user,
    register_user,
)
from state.config import ACCESS_TOKEN_EXPIRE_MINUTES, COOKIE_SECURE

router = APIRouter()


# get user stats
@router.get("/api/users/{username}/stats")
async def API_get_user_stats(username: str):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "Elo": user.elo}


@router.get("/api/get_ranking")
async def API_get_ranking():
    try:
        return get_ranking()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/token")
async def API_get_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
):
    try:
        token = await get_access_token(form_data)
    except ValueError as e:
        raise HTTPException(401, str(e))
    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        samesite="strict",
        secure=COOKIE_SECURE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return {"ok": True}


@router.get("/api/users/me/")
async def API_get_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user


@router.post("/api/register/")
async def API_register(payload: UserRegister, response: Response):
    try:
        result = await register_user(payload)
    except Exception as e:
        error_msg = str(e).lower()
        raise HTTPException(status_code=409, detail=error_msg)
    except Exception as e:
        raise HTTPException(500, str(e))
    access_token = create_access_token(
        data={"sub": payload.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="strict",
        secure=COOKIE_SECURE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return result


@router.post("/api/logout")
async def logout(response: Response):
    # unprotected -> cookie expiry
    response.delete_cookie("access_token")
    return {"ok": True}
