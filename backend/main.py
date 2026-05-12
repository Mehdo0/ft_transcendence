import random

from fastapi import HTTPException, Query, WebSocket, WebSocketDisconnect

from ai_service import load_word_list, make_ai_guess
from auth import (
    get_username_from_ws_token,
)
from data import ImagePayload, UserRegister
from database import add_user, get_user_elo
from state import app, limiter, manager
from websocket import router as websocket_router


# default route
@app.get("/api/")
async def root():
    print("sent hello world!")
    return {"message": "Hello World"}


app.include_router(websocket_router)


# get user stats
@app.get("/api/users/{username}/stats")
async def get_user_stats(username: str):
    # Ask the database file to do the heavy lifting
    elo = get_user_elo(username)
    if elo is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": username, "Elo": elo}


@app.post("/api/users/add_user/")
async def db_add(payload: UserRegister):
    try:
        new_user = add_user(payload.username, payload.password)
        return {"username": new_user.username, "added": "yes"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/word_list/get_word/")
async def get_random_word():
    data = load_word_list("list.txt")
    if data[0] == "Error":
        raise HTTPException(status_code=500, detail=data[1])

    word = random.choice(data)
    return {"word": word}


@app.websocket("/ws/matchmaking")
async def websocket_matchmaking(
    websocket: WebSocket,
    token: str = Query(...),
):  # This forces the URL to include "?token=..."
    username = get_username_from_ws_token(token)
    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(
                {"status": "received", "you_said": data}, username
            )  # test purpose
    except WebSocketDisconnect:
        manager.disconnect(username)


@app.post("/api/ai_guess/")
@limiter.limit("2/second")
async def ai_guess(
    payload: ImagePayload,
):
    base64_str = payload.base64_string
    if "data:image" not in base64_str:
        raise HTTPException(status_code=406, detail="Bad data sent")
    results = make_ai_guess(base64_str)
    if not results or len(results) != 3:
        raise HTTPException(status_code=500, detail="Bad AI output")
    return {"guesses": results}
