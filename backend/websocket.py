from fastapi import WebSocket, WebSocketDisconnect
from backend.global_var import app, MATCHMAKING_QUEUE


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            type = data.get("type")

            if type == "find_player":
                MATCHMAKING_QUEUE["TWO_PLAYER_AI"].append(data.get("username"))

            else:
                await websocket.send_json({"event": "error", "msg": "unknown type"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        

