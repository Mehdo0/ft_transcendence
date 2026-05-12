import random

from backend.ai_service import load_word_list, make_ai_guess
from backend.auth import (
    Depends,
    User,
    get_current_user,
    get_username_from_ws_token,
)
from backend.data import ImagePayload
from backend.database import get_user_elo
from backend.websocket import router as websocket_router
from backend.global_var import app, limiter, manager
from fastapi import HTTPException, Request, WebSocket, WebSocketDisconnect


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
):
    token = websocket.cookies.get("access_token")
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
