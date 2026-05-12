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
)
from fastapi import HTTPException, APIRouter, Depends
from data import UserRegister, ImagePayload, Token, User

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


@router.post("/api/users/add_user/")
async def API_add_user(payload: UserRegister):
    try:
        new_user = await add_user(payload.username, payload.password)
        return {"username": new_user.username, "added": "yes"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/ai_guess/")
async def API_ai_guess(payload: ImagePayload):
    try:
        results = await make_ai_guess(payload)
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
        return await get_access_token(form_data)
    except Exception as e:
        raise HTTPException(400, e)


@router.get("/users/me/")
async def API_get_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user


@router.post("/api/register/")
async def API_register(username: str, password: str):
    try:
        await register_user(username, password)
    except ValueError as e:
        raise HTTPException(400, e)
