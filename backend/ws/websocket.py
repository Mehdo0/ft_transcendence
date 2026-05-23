import random
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from schemas.data import Game, GameState, GameType, ImagePayload
from services.ai_service import load_word_list
from services.services import get_username_from_ws_token, make_ai_guess
from state.state import (
    connections,
    games,
    matchmaking_queue,
    player_games,
    disconnected_players,
)


router = APIRouter()


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    try:
        token = websocket.cookies.get("access_token")
        username = get_username_from_ws_token(token)
    except Exception:
        return
    await websocket.accept()
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
                    image_payload = ImagePayload(base64_string=payload.get("image"))
                    guess = await make_ai_guess(image_payload, games[game_id].word)
                    await websocket.send_json({"type": "ai_guess", "guess": guess})
                    opponent = get_opponent(username, game_id)
                    await connections[opponent].send_json({"type": "opponent_guess", "guess": guess})
                    score = guess.get(games[game_id].word)
                    if score >= 1:
                        await end_game(websocket, opponent)
            

    except WebSocketDisconnect:
        if game_id is None:
            raise ValueError("game_id not found")
        # asyncio.create_task(handle_disconnect_grace_period(username, game_id))

def get_opponent(username: str, game_id: str):
    game = games[game_id]
    for player in game.players:
        if player != username:
            return player

async def end_game(websocket: WebSocket, opponent: str):
    await websocket.send_json({"type": "end_game", "status": "winner"})
    await connections[opponent].send_json({"type": "end_game", "status": "looser"})

    


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

    games[game.id] = game
    player_games[player1] = game.id
    player_games[player2] = game.id

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
