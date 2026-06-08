import asyncio
import random
import uuid
import string

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from schemas.data import Game, GameState, GameType, ImagePayload
from services.ai_service import load_word_list
from services.services import get_username_from_ws_token, make_ai_guess
from api.api import get_user_elo
from core.database import update_user_elo
from state.state import (
    connections,
    games,
    matchmaking_queue,
    player_games,
    disconnected_players,
    lobbies,
    game_timers
)
from asyncio import sleep


router = APIRouter()


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    try:
        token = websocket.cookies.get("access_token")
        if token is None:
            raise ValueError("no token found")
        username = get_username_from_ws_token(token)
    except Exception:
        return
    await websocket.accept()
    connections[username] = websocket
    #Did they just reconnect during a grace period?
    if username in disconnected_players:
        disconnected_players[username]["reconnected"] = True
        del disconnected_players[username]
        
    #Are they already in an active game? (Send them the state so their UI updates)
    if username in player_games:
        game_id = player_games[username]
        if game_id in games:
            current_game = games[game_id]
            opponent = get_opponent(username, game_id)
            loop = asyncio.get_running_loop()
            time_left = max(0, round(current_game.ends_at - loop.time())) if current_game.ends_at else None
            await websocket.send_json({
                "type": "reconnect_game",
                "game_id": current_game.id,
                "opponent": opponent,
                "word": current_game.word,
                "time_left": time_left
            })
    try:
        while True:
            payload = await websocket.receive_json()
            type = payload.get("type")
            match type:
                case "create_lobby":
                    await create_lobby(username, websocket)
                case "join_lobby":
                    code = payload.get("code", "").upper().strip()
                    if len(code) != 6 or not code.isalnum():
                        await websocket.send_json({"type": "error", "message": "invalid code"})
                        break
                    await join_lobby(username, code, websocket)
                case "get_lobby":
                    code = payload.get("code")
                    if code in lobbies:
                        lobby = lobbies[code]
                        await websocket.send_json({
                            "type": "lobby_info",
                            "players": lobby["players"],
                            "host": lobby["host"],
                            "me": username 
                        })
                case "start_game":
                    code = payload.get("code")
                    if code in lobbies:
                        lobby = lobbies[code]
                        if lobby["host"] == username and len(lobby["players"]) == 2:
                            player1, player2 = lobby["players"][0], lobby["players"][1]
                            await create_game(player1, player2)
                            del lobbies[code]
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
                    await connections[opponent].send_json(
                        {"type": "opponent_guess", "guess": guess}
                    )
                    score = guess.get(games[game_id].word) or 0
                    games[game_id].scores[username] = score
                    if score >= 0.5: #percent to change when AI will be fixed
                        await end_game(websocket, username, opponent)
                case "surrender":
                    game_id = player_games.get(username)
                    if game_id is None or game_id not in games:
                        continue
                    opponent = get_opponent(username, game_id)
                    await finish_game_by_forfeit(game_id, opponent, username, "opponent_surrendered")

    except WebSocketDisconnect:
        # Remove their active socket
        connections.pop(username, None)
        if username in player_games:
            game_id = player_games[username]
            # Start the 5-second countdown timer
            asyncio.create_task(handle_disconnect_grace_period(username, game_id))
        else:
            # If they were just in the lobby or queue, delete them instantly
            disconnect(username)


async def create_lobby(username: str, websocket: WebSocket): #still have to make sure that the code is deleted after 30 min or closed lobby
    while True:
        characters = string.ascii_uppercase + string.digits
        code = ''.join(random.choices(characters, k=6))
        if code not in lobbies:
            lobbies[code] = {"host": username, "players": [username]}
        await websocket.send_json({"type": "lobby_created", "code": code })
        break

async def join_lobby(username: str, code: str, websocket: WebSocket):
        if code not in lobbies:
            await websocket.send_json({"type": "error", "message": "lobby not found" })
            return
        lobby = lobbies[code]
        if len(lobby["players"]) >= 2:
            await websocket.send_json({"type": "error", "message": "lobby already full"})
            return
        if username in lobby["players"]:
            await websocket.send_json({"type": "error", "message": "player already in lobby"})
            return
        lobby["players"].append(username)
        host = lobby["host"] 
        await websocket.send_json({"type": "lobby_joined", "code": code})
        await connections[host].send_json({"type": "player_joined", "username": username})
            



def get_opponent(username: str, game_id: str):
    game = games[game_id]
    for player in game.players:
        if player != username:
            return player


async def end_game(websocket: WebSocket, username: str, opponent: str):
    game_id = player_games.get(username)
    diff_winner, new_elo_winner = await calculate_new_elo(username, opponent, 1)
    diff_loser, new_elo_loser = await calculate_new_elo(opponent, username, 0)
    await websocket.send_json({"type": "end_game", "status": "winner", "elo_diff": diff_winner, "new_elo": new_elo_winner})
    await connections[opponent].send_json({"type": "end_game", "status": "looser", "elo_diff": diff_loser, "new_elo": new_elo_loser})
    update_user_elo(username, new_elo_winner)
    update_user_elo(opponent, new_elo_loser)
    if game_id:
        cancel_timer(game_id)
        cleanup_game(game_id, username, opponent)


def cancel_timer(game_id: str):
    task = game_timers.pop(game_id, None)
    if task is not None:
        task.cancel()


async def game_timer(game_id: str):
    await sleep(60)
    if game_id in games:
        await end_game_by_timeout(game_id)


async def end_game_by_timeout(game_id: str):
    if game_id not in games:
        return
    game = games[game_id]
    player1, player2 = game.players[0], game.players[1]
    score1 = game.scores.get(player1, 0)
    score2 = game.scores.get(player2, 0)

    if score1 == score2:
        # Draw: no Elo change
        for player in (player1, player2):
            if player in connections:
                await connections[player].send_json({
                    "type": "end_game",
                    "status": "draw",
                    "elo_diff": 0,
                    "reason": "timeout",
                })
        cancel_timer(game_id)
        cleanup_game(game_id, player1, player2)
        return

    winner, loser = (player1, player2) if score1 > score2 else (player2, player1)
    diff_w, new_elo_w = await calculate_new_elo(winner, loser, 1)
    diff_l, new_elo_l = await calculate_new_elo(loser, winner, 0)
    update_user_elo(winner, new_elo_w)
    update_user_elo(loser, new_elo_l)
    if winner in connections:
        await connections[winner].send_json({
            "type": "end_game", "status": "winner",
            "elo_diff": diff_w, "new_elo": new_elo_w, "reason": "timeout",
        })
    if loser in connections:
        await connections[loser].send_json({
            "type": "end_game", "status": "looser",
            "elo_diff": diff_l, "new_elo": new_elo_l, "reason": "timeout",
        })
    cancel_timer(game_id)
    cleanup_game(game_id, winner, loser)


async def calculate_new_elo(username1: str, username2: str, result: int):
    elo1 = await get_user_elo(username1)
    elo2 = await get_user_elo(username2)
    moyenne = (elo1 + elo2) / 2
    K = 40 - round(moyenne / 50)
    E = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
    new_elo = round(elo1 + (K * (result - E)))
    diff = new_elo - elo1
    return diff, new_elo

async def handle_disconnect_grace_period(username: str, game_id: str):
    disconnected_players[username] = {"reconnected": False}
    await asyncio.sleep(10)
    if (
        username in disconnected_players
        and not disconnected_players[username]["reconnected"]
    ):
        print(f"Player {username} abandoned the game. Removing them permanently.")
        del disconnected_players[username]
        if game_id in games:
            opponent = get_opponent(username, game_id)
            await finish_game_by_forfeit(game_id, opponent, username, "opponent_left")
        else:
            disconnect(username)


async def finish_game_by_forfeit(game_id: str, winner: str, loser: str, reason: str):
    if game_id not in games:
        return  # already finished / cleaned up
    cancel_timer(game_id)
    diff_w, new_elo_w = await calculate_new_elo(winner, loser, 1)
    diff_l, new_elo_l = await calculate_new_elo(loser, winner, 0)
    update_user_elo(winner, new_elo_w)
    update_user_elo(loser, new_elo_l)
    # Notify the winner if they are still connected
    if winner in connections:
        await connections[winner].send_json({
            "type": "end_game",
            "status": "winner",
            "elo_diff": diff_w,
            "new_elo": new_elo_w,
            "reason": reason,
        })
    cleanup_game(game_id, winner, loser)


def cleanup_game(game_id: str, *usernames: str):
    games.pop(game_id, None)
    for u in usernames:
        player_games.pop(u, None)
        disconnected_players.pop(u, None)


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

    loop = asyncio.get_running_loop()
    game.ends_at = loop.time() + 60

    games[game.id] = game
    player_games[player1] = game.id
    player_games[player2] = game.id

    game_timers[game.id] = asyncio.create_task(game_timer(game.id))

    await connections[player1].send_json(
        {
            "type": "match_found",
            "game_id": game.id,
            "opponent": player2,
            "word": game.word,
            "duration": 60,
        }
    )

    await connections[player2].send_json(
        {
            "type": "match_found",
            "game_id": game.id,
            "opponent": player1,
            "word": game.word,
            "duration": 60,
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
