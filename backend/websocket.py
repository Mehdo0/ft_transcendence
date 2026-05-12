from fastapi import WebSocket, WebSocketDisconnect
from backend.global_var import app, MATCHMAKING_QUEUE
from backend.data import ClientWebsocketMessageType

ALLOWED_ORIGINS = {
    "https://localhost",
}


@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            type: ClientWebsocketMessageType = data.get("type")
            _ = type
            websocket.send_json("hi from server")

            # match type:
            #     case "drawing":
            #         make_ai_guess()
            #     case "quit":
            #         player_quit_game()
            #     case _:
            #         await websocket.send_json({"event": "error", "msg": "unknown type"})
    except WebSocketDisconnect:
        raise WebSocketDisconnect

        # manager.disconnect(websocket)

        # if type == "find_player":
        #     MATCHMAKING_QUEUE["TWO_PLAYER_AI"].append(data.get("username"))
