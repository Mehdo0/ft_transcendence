import random

from backend.ai_service import load_word_list, make_ai_guess
from backend.auth import (
    Depends,
    User,
    get_current_user,
    get_username_from_ws_token,
)
from backend.data import ImagePayload, UserRegister
from backend.database import add_user, get_user_elo
from backend.global_var import app, limiter, manager
from fastapi import HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

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
@app.get("/api/")
async def root():
    print("sent hello world!")
    return {"message": "Hello World"}


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
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/word_list/get_word/")
async def get_random_word(num: int = 1):
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
    request: Request,
    current_user: User = Depends(get_current_user),
):
    base64_str = payload.base64_string
    if "data:image" not in base64_str:
        raise HTTPException(status_code=406, detail="Bad data sent")
    results = make_ai_guess(base64_str)
    if not results or len(results) != 3:
        raise HTTPException(status_code=500, detail="Bad AI output")
    return {"guesses": results}


# ce code est censer etre fonctionnel lorsque le frontend sera operationnel
# app.mount("/", StaticFiles(directory="backend/frontend_dist", html=True), name="frontend")
# @app.exception_handler(404)
# async def not_found_exception_handler(request, exc):
#    return FileResponse("frontend_dist/index.html")
