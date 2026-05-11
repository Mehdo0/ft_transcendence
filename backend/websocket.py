from fastapi import WebSocket, WebSocketDisconnect
from backend.global_var import app


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while (true):
            data = await.websocket

