import shortuuid
from fastapi import WebSocket

from core.setup import manager
from schemas.data import Lobby, User
from utils.utils import remove_from_matchmaking


async def get_lobby_info(payload: dict, websocket: WebSocket, user: User):
    code = payload.get("code")
    if code in manager.lobbies:
        lobby = manager.lobbies[code]
        connected = [p for p in lobby.players if p in manager.connections]
        print("LOBBY: fetching lobby info host: ", lobby.host)
        print("LOBBY: connected players: ", connected)
        print("LOBBY: players in lobby ", code, "are: ", connected)
        await websocket.send_json(
            {
                "type": "lobby_info",
                "exist": True,
                "players": connected,
                "host": lobby.host,
                "me": user.username,
            }
        )
    else:
        await websocket.send_json(
            {
                "type": "lobby_info",
                "exist": False,
            }
        )


async def create_lobby(user: User, websocket: WebSocket):
    print("GAME: creating lobby, host " + user.username)
    remove_from_matchmaking(user.username)

    code = shortuuid.ShortUUID().random(length=6).upper()
    while code in manager.lobbies:
        code = shortuuid.ShortUUID().random(length=6).upper()
    manager.lobbies[code] = Lobby(
        id=code,
        host=user.username,
        players=[user.username],
    )
    print("new lobby: ", Lobby)
    await websocket.send_json({"type": "lobby_created", "code": code})


async def join_lobby(user: User, code: str, websocket: WebSocket):
    remove_from_matchmaking(user.username)
    if len(code) != 6 or not code.isalnum():
        await websocket.send_json({"type": "error", "message": "wrong code"})
        return

    if code not in manager.lobbies:
        await websocket.send_json({"type": "error", "message": "lobby not found"})
        return

    lobby = manager.lobbies[code]
    if len(lobby.players) >= 4:
        await websocket.send_json({"type": "error", "message": "lobby already full"})
        return

    if user.username in lobby.players:
        await websocket.send_json(
            {"type": "error", "message": "player already in lobby"}
        )
        return

    lobby.players.append(user.username)
    await websocket.send_json({"type": "lobby_joined", "code": code})

    for player in lobby.players:
        player_ws = manager.connections.get(player)
        if player != user.username and player_ws:
            await player_ws.send_json(
                {
                    "type": "player_joined",
                    "username": user.username,
                }
            )


async def close_lobby(code: str) -> None:
    lobby = manager.lobbies.pop(code, None)
    if lobby is None:
        return
    for player in lobby.players:
        player_ws = manager.connections.get(player)
        if player_ws:
            await player_ws.send_json({"type": "lobby_closed"})


async def cleanup_lobby_on_disconnect(user: User):
    for code, lobby in list(manager.lobbies.items()):
        if user.username not in lobby.players:
            continue

        if lobby.host == user.username:
            await close_lobby(code)
            return

        lobby.players.remove(user.username)
        for player in lobby.players:
            player_ws = manager.connections.get(player)
            if player_ws:
                await player_ws.send_json(
                    {
                        "type": "player_left",
                        "username": user.username,
                    }
                )
