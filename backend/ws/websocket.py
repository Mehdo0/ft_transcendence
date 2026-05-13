import uuid
import asyncio
from fastapi import APIRouter, WebSocket
from state.state import connections, games
import random
from fastapi import WebSocketDisconnect
from state.state import matchmaking_queue
from fastapi import status
from state.state import (
    player_games,
    disconnected_players,
)
from schemas.data import Game, GameState, GameType
from services.ai_service import load_word_list
from services.services import make_ai_guess, get_username_from_ws_token

router = APIRouter()


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    username = get_username_from_ws_token(token)
    await websocket.accept()
    await websocket.receive_json()
    connections[username] = websocket
    try:
        while True:
            payload = await websocket.receive_json()
            type = payload.get("type")
            match type:
                case "find_player":
                    await find_player(username)
                case "image":
                    game_id = player_games.get(username)
                    if game_id is None or game_id not in games:
                        continue
                    guess = await make_ai_guess(
                        payload.get("image"), games[game_id].word
                    )
                    await websocket.send_json({"type": "ai_guess", "guess": guess})

    except WebSocketDisconnect:
        if game_id is None:
            raise ValueError("game_id not found")
        asyncio.create_task(handle_disconnect_grace_period(username, game_id))


async def handle_disconnect_grace_period(username: str, game_id: str):
    disconnected_players[username] = {"reconnected": False}
    await asyncio.sleep(10)
    if (
        username in disconnected_players
        and not disconnected_players[username]["reconnected"]
    ):
        print(f"Player {username} abandoned the game. Removing them permanently.")
        del disconnected_players[username]


async def find_player(username: str):
    queue = matchmaking_queue["TWO_PLAYER_AI"]

    if (len(queue)) >= 1:
        opponent = queue.pop(0)
        await create_game(opponent, username)
    else:
        queue.append(username)
        await connections[username].send_json({"type": "waiting"})


async def create_game(player1: str, player2: str):
    game = Game(
        id=str(uuid.uuid4()),
        game_type=GameType.TWO_PLAYER_AI,
        game_state=GameState.STARTED,
        players=[player1, player2],
        word=get_random_word(),
    )

    await connections[player1].send_json(
        {
            "type": "match_found",
            "game_id": game.id,
            "opponent": player2,
            "word": game.word,
        }
    )

    await connections[player2].send_json(
        {
            "type": "match_found",
            "game_id": game.id,
            "opponent": player1,
            "word": game.word,
        }
    )


def disconnect(username: str):
    connections.pop(username, None)
    player_games.pop(username, None)
    queue = matchmaking_queue["TWO_PLAYER_AI"]
    if username in queue:
        queue.remove(username)


def get_random_word():
    data = load_word_list()
    word = random.choice(data)
    return word
