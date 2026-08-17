from fastapi import WebSocket, WebSocketDisconnect

from core.setup import router, ws_manager
from schemas.data import User
from services.services import get_user_from_ws_token


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    user = await authenticate_user_trough_ws(websocket)
    await ws_manager.connect(user, websocket)

    try:
         while True:
            payload = await websocket.receive_json()
            try:
                await ws_manager.handle_message(user, payload)
            except Exception as e:
                print("WS: error handling message:", e)
    except WebSocketDisconnect:
        print("user", user.username, "disconnected")
        await ws_manager.disconnect(user)


async def authenticate_user_trough_ws(websocket) -> User:
    try:
        token = websocket.cookies.get("access_token")
        if token is None:
            raise ValueError("no token found")
        print("connecting user through ws token")
        user = get_user_from_ws_token(token)
        print("user " + user.username + " connected.")
    except ValueError:
        print("WS: auth failed")
        await websocket.accept()
        await websocket.send_json(
            {
                "type": "error",
                "message": "authentication failed",
            }
        )
        print("token not found when connecting websocket")
        raise
    except Exception:
        print("WS: auth failed")
        await websocket.accept()
        await websocket.send_json(
            {
                "type": "error",
                "message": "connection failed",
            }
        )
        print("error while fetching user from token")
        raise

    await websocket.accept()
    return user
