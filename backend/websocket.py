import uuid
import random
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, get_username_from_ws_token
from state import CONNECTIONS, GAMES, matchmaking_queue, app, PLAYER_GAMES
from data import Game, GameState, GameType
from ai_service import make_ai_guess, load_word_list


router = APIRouter()

@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    token = websocket.cookies.get("access_token")
    # response = await websocket.receive_json()
    username = get_username_from_ws_token(token)
    CONNECTIONS[username] = websocket
    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") == "find_player":
                await find_player(username)
            elif payload.get("type") == "image":
                game_id = PLAYER_GAMES.get(username)
                if game_id is None or game_id not in GAMES:
                    continue
                guess = make_ai_guess(payload.get("image"), GAMES[game_id].word)
                await websocket.send_json({"type": "ai_guess", "guess": guess})

    except WebSocketDisconnect:
        disconnect(username)


async def find_player(username: str):
    queue = matchmaking_queue["TWO_PLAYER_AI"]

    if (len(queue)) >= 1:
        opponent = queue.pop(0)
        await create_game(opponent, username)
    else:
        queue.append(username)
        await CONNECTIONS[username].send_json({"type": "waiting"})


async def create_game(player1: str, player2: str):
    game = Game(
        id=str(uuid.uuid4()),
        game_type=GameType.TWO_PLAYER_AI,
        game_state=GameState.STARTED,
        players=[player1, player2],
        word=get_random_word()
    )
    GAMES[game.id] = game
    PLAYER_GAMES[player1] = game.id
    PLAYER_GAMES[player2] = game.id

    await CONNECTIONS[player1].send_json(
        {
            "type": "match_found",
            "game_id": game.id,
            "opponent": player2,
            "word": game.word
        }
    )

    await CONNECTIONS[player2].send_json(
        {
            "type": "match_found",
            "game_id": game.id,
            "opponent": player1,    
            "word": game.word
        }
    )


def disconnect(username: str):
    CONNECTIONS.pop(username, None)
    PLAYER_GAMES.pop(username, None)
    queue = matchmaking_queue["TWO_PLAYER_AI"]
    if username in queue:
        queue.remove(username)

def get_random_word():
    data = load_word_list("list.txt")
    word = random.choice(data)
    return word
