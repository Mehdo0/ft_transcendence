from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from services.services import (
    get_random_word,
    make_ai_guess,
    get_access_token,
    register_user,
    get_current_active_user,
    create_access_token,
)
from core.database import (
    get_user_elo,
    add_user,
    get_ranking,
)
from core.exceptions import UserAlreadyExistsError
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
        elo = get_user_elo(username)
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
    except UserAlreadyExistsError as e:
        raise HTTPException(406, str(e))
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
