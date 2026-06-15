import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from core.database import get_user
from schemas.data import User
from services.services import get_user_from_ws_token
from state.state import (
    connections,
    disconnected_players,
    games,
    matchmaking_queue,
    player_games,
)
from core.setup import router
from game.lobby_logic import create_lobby, join_lobby, get_lobby_info, cleanup_lobby_on_disconnect
from game.game_logic import start_game, surrender_game, ai_guess, create_game, end_game
from utils.getters import get_opponents
from utils.utils import disconnect

@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    try:
        token = websocket.cookies.get("access_token")
        if token is None:
            raise ValueError("no token found")
        user = get_user_from_ws_token(token)
    except Exception:
        return

    await websocket.accept()
    connections[user.username] = websocket

    if user.username in disconnected_players:
        disconnected_players[user.username]["reconnected"] = True
        del disconnected_players[user.username]

    if user.username in player_games:
        await reconnect_user(user, websocket)

    try:
        while True:
            payload = await websocket.receive_json()
            message_type = payload.get("type")
            match message_type:
                case "create_lobby":
                    await create_lobby(user, websocket)
                case "join_lobby":
                    code = payload.get("code", "").upper().strip()
                    if len(code) == 6 or code.isalnum():
                        await join_lobby(user, code, websocket)
                case "get_lobby":
                    await get_lobby_info(payload, websocket, user)
                case "start_game":
                    await start_game(payload, user)
                case "find_player":
                    await find_player(user)
                case "guess":
                    await ai_guess(user, payload, websocket)
                case "surrender":
                    await surrender_game(user)
    except WebSocketDisconnect:
        await disconnect_user(user)





async def disconnect_user(user: User):
    connections.pop(user.username, None)
    if user.username in player_games:
        game_id = player_games[user.username]
        game = games.get(game_id)
        if game:
            for p in game.players:
                if p != user.username and p in connections:
                    await connections[p].send_json({
                        "type": "opponent_disconnected", 
                        "username": user.username
                    })
        asyncio.create_task(handle_disconnect_grace_period(user, game_id))
        return
    await cleanup_lobby_on_disconnect(user)
    disconnect(user)

async def reconnect_user(user: User, websocket: WebSocket):
    game_id = player_games[user.username]
    if game_id not in games:
        raise RuntimeError("player is in player_games but game does not exist")

    current_game = games[game_id]
    opponents = get_opponents(user, game_id)
    loop = asyncio.get_running_loop()
    time_left = (
        max(0, round(current_game.ends_at - loop.time()))
        if current_game.ends_at
        else None
    )

    await websocket.send_json(
        {
            "type": "reconnect_game",
            "game_id": current_game.id,
            "opponent": opponents[0] if opponents else "",
            "players": current_game.players,
            "me": user.username,
            "word": current_game.word,
            "scores": current_game.scores,
            "round_wins": current_game.round_wins,
            "is_ranked": current_game.is_ranked,
            "time_left": time_left,
        }
    )




async def handle_disconnect_grace_period(user: User, game_id: str):
    disconnected_players[user.username] = {"reconnected": False}
    await asyncio.sleep(10)

    if user.username not in disconnected_players:
        return
    if disconnected_players[user.username]["reconnected"]:
        return

    del disconnected_players[user.username]
    connections.pop(user.username, None)

    if game_id in games:
        opponents = get_opponents(user, game_id)
        winner = get_user(opponents[0]) if opponents else None
        if winner:
            await end_game(game_id, winner, "opponent_left")
        return

    disconnect(user)


async def find_player(user: User):
    if user.username in player_games or user.username in matchmaking_queue:
        return

    if len(matchmaking_queue) >= 1:
        opponent_name = matchmaking_queue.pop(0)
        opponent = get_user(opponent_name)
        if opponent is None:
            await connections[user.username].send_json({"type": "waiting"})
            matchmaking_queue.append(user.username)
            return
        await create_game([opponent, user], True)
        return

    matchmaking_queue.append(user.username)
    await connections[user.username].send_json({"type": "waiting"})
