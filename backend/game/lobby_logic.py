import random
import string
import shortuuid
from fastapi import WebSocket
from schemas.data import User
from state.state import connections, lobbies
from utils.utils import remove_from_matchmaking


async def get_lobby_info(payload: dict, websocket: WebSocket, user: User):
    code = payload.get("code")
    if code in lobbies:
        lobby = lobbies[code]
        await websocket.send_json(
            {
                "type": "lobby_info",
                "players": lobby["players"],
                "host": lobby["host"],
                "me": user.username,
            }
        )
        return

    await websocket.send_json(
        {
            "type": "error",
            "message": "lobby doesn't exist",
        }
    )


async def create_lobby(user: User, websocket: WebSocket):
    remove_from_matchmaking(user.username)

    while True:
        code = shortuuid.ShortUUID().random(length=6).upper()
        if code not in lobbies:
            lobbies[code] = {"host": user.username, "players": [user.username]}
            await websocket.send_json({"type": "lobby_created", "code": code})
            return


async def join_lobby(user: User, code: str, websocket: WebSocket):
    remove_from_matchmaking(user.username)

    if code not in lobbies:
        await websocket.send_json({"type": "error", "message": "lobby not found"})
        return

    lobby = lobbies[code]
    if len(lobby["players"]) >= 4:
        await websocket.send_json({"type": "error", "message": "lobby already full"})
        return

    if user.username in lobby["players"]:
        await websocket.send_json(
            {"type": "error", "message": "player already in lobby"}
        )
        return

    lobby["players"].append(user.username)
    await websocket.send_json({"type": "lobby_joined", "code": code})

    for player in lobby["players"]:
        player_ws = connections.get(player)
        if player != user.username and player_ws:
            await player_ws.send_json(
                {"type": "player_joined", "username": user.username}
            )


async def cleanup_lobby_on_disconnect(user: User):
    for code, lobby in list(lobbies.items()):
        if user.username not in lobby["players"]:
            continue

        if lobby["host"] == user.username:
            closed_lobby = lobbies.pop(code, None)
            if closed_lobby is None:
                continue
            for player in closed_lobby["players"]:
                player_ws = connections.get(player)
                if player_ws:
                    await player_ws.send_json({"type": "lobby_closed"})
            continue

        lobby["players"].remove(user.username)
        for player in lobby["players"]:
            player_ws = connections.get(player)
            if player_ws:
                await player_ws.send_json(
                    {"type": "player_left", "username": user.username}
                )
