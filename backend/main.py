import random

from fastapi import HTTPException, WebSocket, WebSocketDisconnect

from ai_service import load_word_list, make_ai_guess
from auth import (
    get_username_from_ws_token,
)
from data import ImagePayload
from database import db_cursor, get_user_elo
from state import app, manager
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


# @app.get("/api/word_list/get_word/")
# async def get_random_word():
#     data = load_word_list("list.txt")
#     if data[0] == "Error":
#         raise HTTPException(status_code=500, detail=data[1])

#     word = random.choice(data)
#     return {"word": word}


# @app.websocket("/ws/matchmaking")
# async def websocket_matchmaking(
#     websocket: WebSocket,
# ):
#     token = websocket.cookies.get("access_token")
#     username = get_username_from_ws_token(token)
#     await manager.connect(websocket, username)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await manager.send_personal_message(
#                 {"status": "received", "you_said": data}, username
#             )  # test purpose
#     except WebSocketDisconnect:
#         manager.disconnect(username)


# @app.post("/api/ai_guess/")
# async def ai_guess(
#     payload: ImagePayload,
# ):
#     base64_str = payload.base64_string
#     if "data:image" not in base64_str:
#         raise HTTPException(status_code=406, detail="Bad data sent")
#     results = make_ai_guess(base64_str)
#     if not results or len(results) != 3:
#         raise HTTPException(status_code=500, detail="Bad AI output")
#     return {"guesses": results}


@app.get("/api/get_ranking")
async def get_ranking():
    with db_cursor() as cursor:
        cursor.execute("SELECT username, elo FROM users ORDER BY elo DESC LIMIT 10")
        row = cursor.fetchall()
        result = [
            {"username": player["username"], "elo": player["elo"]} for player in row
        ]
        return result
