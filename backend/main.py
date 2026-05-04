import random

from fastapi import HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.ai_service import load_word_list
from backend.auth import get_username_from_ws_token
from backend.database import add_user, fetch_user_stats, reset_database
from backend.global_var import app, manager

# These imports are going to be useful later in the coding process !

# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
# from backend.data import User
# from backend.game import (
#     GameState,
#     GameType,
#     PlayerState,
#     Session,
#     OnlinePlayer,
#     Game,
#     create_game,
# )


# allow SvelteKit dev server
# we might want to switch to using SvelteKit as a proxy to avoid giving direct acces to API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://trsc_front:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# default route
@app.get("/")
async def root():
    return {"message": "Hello World"}


# get user stats
@app.get("/api/users/{user_id}/stats")
async def get_user_stats(user_id: int):
    # Ask the database file to do the heavy lifting
    row = fetch_user_stats(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": row["username"], "wins": row["wins"], "losses": row["losses"]}


@app.get("/api/users/add_user/")
async def db_add(username: str = "drawer"):
    new_user_id = add_user(username)
    row = fetch_user_stats(new_user_id)
    if row is None:
        raise HTTPException(status_code=500, detail="User not added")
    return {"user_id": row["id"], "username": row["username"], "added": "yes"}


@app.get("/destroy")
async def destroy_db():
    reset_database()
    return {"data": "erased"}


@app.get("/api/word_list/get_word/")
async def get_random_word(num: int = 1):
    data = load_word_list("list.txt")
    if data[0] == "Error":
        raise HTTPException(status_code=500, detail=data[1])

    word = random.choice(data)
    return {"word": word}


@app.websocket("/ws/matchmaking")
async def websocket_matchmaking(websocket: WebSocket, token: str = Query(...),): # This forces the URL to include "?token=..."
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


# @app.post("/api/ai_guess/")
# @limiter.limit("2/seconds")
# async def ai_guess(request: Request, current_user: User = Depends(get_current_user)):
#     if "data:image" not in drawing.Base64_drawing:
#         raise HTTPException(status_code=406, detail="Bad data sent")
#     base64_str = drawing.Base64_drawing
#     results = make_ai_guess(base64_str)
#     if not results or len(results) != 3:
#         raise HTTPException(status_code=500, detail="Bad ai output")
#     drawing.ai_results = results
#     return {"ai_guess":drawing.ai_results[drawing.current_word], "game_stop":flag}


# ce code est censer etre fonctionnel lorsque le frontend sera operationnel
# app.mount("/", StaticFiles(directory="backend/frontend_dist", html=True), name="frontend")
# @app.exception_handler(404)
# async def not_found_exception_handler(request, exc):
#    return FileResponse("frontend_dist/index.html")
