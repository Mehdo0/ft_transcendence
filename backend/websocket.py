import uuid
from fastapi import APIRouter, WebSocket
from state import CONNECTIONS, GAMES
from data import Game, GameState, GameType

router = APIRouter()


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("websocket connected")
    try:
        while True:
            data = await websocket.receive_text()
            print("received:", data)
            response = f"Echo from server {data}"
            await websocket.send_text(response)
            print("sent:", response)

    except Exception as e:
        print("websocket closed:", e)


# try:
#     response = await websocket.receive_json()
#     username = response.get("username")
#     CONNECTIONS[username] = websocket
#     try:
#         while True:
#             payload = await websocket.receive_json()
#             if payload.get("type") == "find_player":
#                 await find_player(username)

#     except WebSocketDisconnect:
#         disconnect(username)


async def find_player(username: str):
    queue = MATCHMAKING_QUEUE["TWO_PLAYER_AI"]

    if (len(queue)) >= 1:
        opponent = queue.pop(0)
        await create_game(opponent, username)
    else:
        queue.append(username)
        await CONNECTIONS[username].send_json({"event": "waiting"})


async def create_game(player1: str, player2: str):
    game = Game(
        id=str(uuid.uuid4()),
        game_type=GameType.TWO_PLAYER_AI,
        game_state=GameState.STARTED,
        players=[player1, player2],
    )
    GAMES[game.id] = game

    await CONNECTIONS[player1].send_json(
        {
            "event": "match_found",
            "game_id": game.id,
            "opponent": player2,
        }
    )

    await CONNECTIONS[player2].send_json(
        {
            "event": "match_found",
            "game_id": game.id,
            "opponent": player1,
        }
    )


def disconnect(username: str):
    CONNECTIONS.pop(username, None)
    queue = MATCHMAKING_QUEUE["TWO_PLAYER_AI"]
    if username in queue:
        queue.remove(username)
