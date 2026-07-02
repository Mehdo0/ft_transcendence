import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, status
from core.database import get_user
from schemas.data import User, Game
from services.services import get_user_from_ws_token
from state.state import (
    connections,
    disconnected_players,
    games,
    matchmaking_queue,
    player_games,
)
from core.setup import router, manager
from game.lobby_logic import (
    create_lobby,
    join_lobby,
    get_lobby_info,
    cleanup_lobby_on_disconnect,
)
from game.game_logic import start_game, surrender_game, ai_guess, create_game, end_game
from utils.getters import get_opponents
from utils.utils import disconnect, send_msg_to_opponents


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    user = await authenticate_user_trough_ws(websocket)
    manager.connections[user.username] = websocket

    if user.username in manager.disconnected_players:
        manager.disconnected_players.remove(user.username)  # user reconnected

    if user.username in manager.player_games:
        await reconnect_user(user, websocket)

    try:
        while True:
            payload = await websocket.receive_json()
            message_type = payload.get("type")
            print("WS: received msg, type: ", message_type)
            if message_type != "guess":
                print("WS: user " + user.username + ", msg " + json.dumps(payload))
            else:
                print("WS: user " + user.username + " guessed")
            match message_type:
                case "create_lobby":
                    await create_lobby(user, websocket)
                case "join_lobby":
                    code = payload.get("code", "").upper().strip()
                    await join_lobby(user, code, websocket)
                case "get_lobby":
                    await get_lobby_info(payload, websocket, user)
                case "start_game":
                    await start_game(payload, user)
                case "find_player":
                    await manager.find_player(user)
                case "guess":
                    await ai_guess(user, payload, websocket)
                case "surrender":
                    await surrender_game(user)
    except WebSocketDisconnect:
        await disconnect_user(user)


async def authenticate_user_trough_ws(websocket) -> User:
    try:
        token = websocket.cookies.get("access_token")
        if token is None:
            raise ValueError("no token found")
        print("connecting user through ws token")
        user = get_user_from_ws_token(token)
        print("user ", user.username, " connected.")
    except ValueError as e:
        await websocket.accept()
        await websocket.send_json(
            {
                "type": "error",
                "message": "authentication failed",
            }
        )
        print("token not found when connecting websocket")
        raise e
    except Exception as e:
        await websocket.accept()
        await websocket.send_json(
            {
                "type": "error",
                "message": "connection failed",
            }
        )
        assert token is not None
        print("error while fetching user from token: " + token)
        raise e

    if user.username in connections:
        await websocket.accept()
        await websocket.send_json(
            {
                "type": "error",
                "message": "already connected — close your other tab first",
            }
        )
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Only one connection allowed",
        )
    await websocket.accept()
    return user


async def disconnect_user(user: User):
    assert user.username in connections
    connections.pop(user.username, None)
    if user.username in manager.player_games:  # user is part of a game
        game_id = manager.player_games[user.username]
        game = manager.games[game_id]  # game should exist if player is a part of it
        await send_msg_to_opponents(
            game,
            user,
            {
                "type": "opponent_disconnected",
                "user": user.username,
            },
        )
        asyncio.create_task(handle_disconnect_grace_period(user, game))
        return
    await cleanup_lobby_on_disconnect(user)
    disconnect(user)


async def reconnect_user(user: User, websocket: WebSocket):
    game_id = manager.player_games[user.username]
    if game_id not in games:
        raise RuntimeError("player is in player_games but game does not exist")

    game = manager.games[game_id]
    opponents = get_opponents(user, game)
    loop = asyncio.get_running_loop()
    time_left = max(0, round(game.ends_at - loop.time())) if game.ends_at else None

    await websocket.send_json(
        {
            "type": "reconnect_game",
            "game_id": game.id,
            "opponent": opponents[0] if opponents else "",
            "players": game.players,
            "me": user.username,
            "word": game.word,
            "scores": game.scores,
            "round_wins": game.round_wins,
            "is_ranked": game.is_ranked,
            "time_left": time_left,
        }
    )


async def handle_disconnect_grace_period(user: User, game: Game):
    manager.disconnected_players.append(user.username)
    await asyncio.sleep(10)

    if user.username not in manager.disconnected_players:  # user reconnected since
        return

    opponents = get_opponents(user, game)
    manager.disconnected_players.remove(user.username)  # remove player from game definitely
    disconnect(user)

    if len(opponents) == 1:
        winner = get_user(opponents[0])
        assert winner is not None
        await end_game(game, winner, "opponent_left")
    await send_msg_to_opponents(
        game,
        user,
        {
            "type": "opponent_left",
            "user": user.username,
        },
    )
    return


# async def find_player(user: User):
#     if user.username in manager.player_games:  # player should not be in active game
#         raise ValueError("player is already in a game")
#     if user.username in manager.matchmaking_queue:  # player should not be in queue
#         raise ValueError("player is already in matchmaking")

#     print("GAME: player '" + user.username + "' is looking for a game...")

#     if len(manager.matchmaking_queue) >= 1:  # another player is already waiting
#         print("\tfound another player to match ", user.username, " against!")
#         opponent_name = manager.matchmaking_queue.pop(0)
#         print("\t" + user.username + " vs " + opponent_name)
#         assert get_user(opponent_name) is not None
#         opponent = get_user(opponent_name)
#         assert opponent is not None
#         await create_game([opponent, user], True)
#         return
#     else:
#         print("\tno player waiting, adding ", user.username, "to queue")
#         manager.matchmaking_queue.append(user.username)
#         await manager.onnections[user.username].send_json({"type": "waiting"})


# async def send_error_raise()
