from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from services.services import (
    get_random_word,
    get_user_elo,
    add_user,
    make_ai_guess,
    get_ranking,
    get_access_token,
    register_user,
    get_current_active_user,
    create_access_token,
)
from state.config import COOKIE_SECURE, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi import HTTPException, APIRouter, Depends, Response
from schemas.data import UserRegister, ImagePayload, Token, User

router = APIRouter()


@router.get("/api/")
async def API_root():
    return {"message": "Hello World"}


@router.get("/api/word_list/get_word/")
async def API_get_word():
    try:
        word = await get_random_word()
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
    return {"word": word}


# get user stats
@router.get("/api/users/{username}/stats")
async def API_get_user_stats(username: str):
    # Ask the database file to do the heavy lifting
    try:
        elo = await get_user_elo(username)
    except Exception as e:
        raise HTTPException(status_code=404, detail=e)
    return {"username": username, "Elo": elo}


@router.post("/api/ai_guess/")
async def API_ai_guess(payload: ImagePayload):
    try:
        results = await make_ai_guess(payload)  # get game and target word TODO
    except Exception as e:
        if e == "wrong payload":
            raise HTTPException(400, e)
        else:
            raise HTTPException(500, e)
    return {"guesses": results}


@router.get("/api/get_ranking")
async def API_get_ranking():
    try:
        return await get_ranking()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/token")
async def API_get_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    try:
        token = await get_access_token(form_data)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            samesite="strict",
            secure=COOKIE_SECURE,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, e)


@router.get("/users/me/")
async def API_get_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user


@router.post("/api/register/")
async def API_register(email: str, password: str, username: str):
    try:
        response = await register_user(username, password, email)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await create_access_token(
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

    except Exception as e:
        raise HTTPException(400, e)


@router.post("/api/logout")
async def logout(response: Response):
    # unprotected -> cookie expiry
    response.delete_cookie("access_token")
    return {"ok": True}
