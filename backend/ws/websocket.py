import asyncio
import random
import uuid
import string

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from schemas.data import Game, GameState, GameType, ImagePayload, User
from services.ai_service import load_word_list
from services.services import get_user_from_ws_token, make_ai_guess
from core.database import update_user_elo, get_user
from state.state import (
    connections,
    games,
    matchmaking_queue,
    player_games,
    disconnected_players,
    lobbies,
    game_timers,
)


router = APIRouter()


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
    # Did they just reconnect during a grace period?
    if user.username in disconnected_players:
        disconnected_players[user.username]["reconnected"] = True
        del disconnected_players[user.username]

    # Are they already in an active game? (Send them the state so their UI updates)
    if user.username in player_games:
        game_id = player_games[user.username]
        if game_id in games:
            current_game = games[game_id]
            opponent = get_opponent(user, game_id)
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
                    "opponent": opponent.username,
                    "word": current_game.word,
                    "time_left": time_left,
                }
            )
        else:
            print("player is in player_games but game does not exist")
            assert False
    try:
        while True:
            payload = await websocket.receive_json()
            type = payload.get("type")
            match type:
                case "create_lobby":
                    await create_lobby(user, websocket)
                case "join_lobby":
                    code = payload.get("code", "").upper().strip()
                    if len(code) != 6 or not code.isalnum():
                        await websocket.send_json(
                            {"type": "error", "message": "invalid code"}
                        )
                        break
                    await join_lobby(user, code, websocket)
                case "get_lobby":
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
                case "start_game":
                    code = payload.get("code")
                    if code in lobbies:
                        lobby = lobbies[code]
                        if (
                            lobby["host"] == user.username
                            and len(lobby["players"]) == 2
                        ):
                            player1 = get_user(lobby["players"][0])
                            player2 = get_user(lobby["players"][1])
                            if player1 is None or player2 is None:
                                print("lobby player not found")
                                assert False
                            await create_game(player1, player2)
                            del lobbies[code]
                case "find_player":
                    await find_player(user)
                case "guess":
                    game_id = player_games.get(user.username)
                    if game_id is None or game_id not in games:
                        continue
                    strokes = payload.get("strokes", [])
                    guess = await make_ai_guess(strokes, games[game_id].word)
                    await websocket.send_json({"type": "ai_guess", "guess": guess})
                    opponent = get_opponent(user, game_id)
                    await connections[opponent.username].send_json(
                        {"type": "opponent_guess", "guess": guess}
                    )
                    score = guess.get(games[game_id].word) or 0
                    games[game_id].scores[user.username] = score
                    if score >= 50:  # percent to change when AI will be fixed
                        await end_game(websocket, user, opponent)
                case "surrender":
                    game_id = player_games.get(user.username)
                    if game_id is None or game_id not in games:
                        continue
                    opponent = get_opponent(user, game_id)
                    await finish_game_by_forfeit(
                        game_id, opponent, user, "opponent_surrendered"
                    )

    except WebSocketDisconnect:
        # Remove their active socket
        connections.pop(user.username, None)
        if user.username in player_games:
            game_id = player_games[user.username]
            # Start the 5-second countdown timer
            asyncio.create_task(handle_disconnect_grace_period(user, game_id))
        else:
            # If they were just in the lobby or queue, delete them instantly
            disconnect(user)


async def create_lobby(
    user: User, websocket: WebSocket
):  # still have to make sure that the code is deleted after 30 min or closed lobby
    while True:
        characters = string.ascii_uppercase + string.digits
        code = "".join(random.choices(characters, k=6))
        if code not in lobbies:
            lobbies[code] = {"host": user.username, "players": [user.username]}
        await websocket.send_json({"type": "lobby_created", "code": code})
        break


async def join_lobby(user: User, code: str, websocket: WebSocket):
    if code not in lobbies:
        await websocket.send_json({"type": "error", "message": "lobby not found"})
        return
    lobby = lobbies[code]
    if len(lobby["players"]) >= 2:
        await websocket.send_json({"type": "error", "message": "lobby already full"})
        return
    if user.username in lobby["players"]:
        await websocket.send_json(
            {"type": "error", "message": "player already in lobby"}
        )
        return
    lobby["players"].append(user.username)
    host = lobby["host"]
    await websocket.send_json({"type": "lobby_joined", "code": code})
    await connections[host].send_json(
        {"type": "player_joined", "username": user.username}
    )


def get_opponent(user: User, game_id: str) -> User:
    game = games[game_id]
    for player in game.players:
        if player != user.username:
            opponent = get_user(player)
            if opponent is None:
                assert False  # opponent should exist
            return opponent
    assert False  # opponent should exist


async def end_game(websocket: WebSocket, player: User, opponent: User):
    game_id = player_games.get(player.username)
    diff_winner, new_elo_winner = await calculate_new_elo(player, opponent, 1)
    diff_loser, new_elo_loser = await calculate_new_elo(opponent, player, 0)
    await websocket.send_json(
        {
            "type": "end_game",
            "status": "winner",
            "elo_diff": diff_winner,
            "new_elo": new_elo_winner,
        }
    )
    await connections[opponent.username].send_json(
        {
            "type": "end_game",
            "status": "looser",
            "elo_diff": diff_loser,
            "new_elo": new_elo_loser,
        }
    )
    update_user_elo(player, new_elo_winner)
    update_user_elo(opponent, new_elo_loser)
    if game_id:
        cancel_timer(game_id)
        cleanup_game(game_id, player, opponent)


def cancel_timer(game_id: str):
    task = game_timers.pop(game_id, None)
    if task is not None:
        task.cancel()


async def game_timer(game_id: str):
    await asyncio.sleep(60)
    if game_id in games:
        await end_game_by_timeout(game_id)


async def end_game_by_timeout(game_id: str):
    if game_id not in games:
        return
    game = games[game_id]
    name1, name2 = game.players[0], game.players[1]
    score1 = game.scores.get(name1, 0)
    score2 = game.scores.get(name2, 0)

    user1, user2 = get_user(name1), get_user(name2)
    if user1 is None or user2 is None:
        assert False  # both players should exist

    if score1 == score2:
        # Draw: no Elo change
        for name in (name1, name2):
            if name in connections:
                await connections[name].send_json(
                    {
                        "type": "end_game",
                        "status": "draw",
                        "elo_diff": 0,
                        "reason": "timeout",
                    }
                )
        cancel_timer(game_id)
        cleanup_game(game_id, user1, user2)
        return

    winner, loser = (user1, user2) if score1 > score2 else (user2, user1)
    diff_w, new_elo_w = await calculate_new_elo(winner, loser, 1)
    diff_l, new_elo_l = await calculate_new_elo(loser, winner, 0)
    update_user_elo(winner, new_elo_w)
    update_user_elo(loser, new_elo_l)
    if winner.username in connections:
        await connections[winner.username].send_json(
            {
                "type": "end_game",
                "status": "winner",
                "elo_diff": diff_w,
                "new_elo": new_elo_w,
                "reason": "timeout",
            }
        )
    if loser.username in connections:
        await connections[loser.username].send_json(
            {
                "type": "end_game",
                "status": "looser",
                "elo_diff": diff_l,
                "new_elo": new_elo_l,
                "reason": "timeout",
            }
        )
    cancel_timer(game_id)
    cleanup_game(game_id, winner, loser)


async def calculate_new_elo(player1: User, player2: User, result: int):
    moyenne = (player1.elo + player1.elo) / 2
    K = 40 - round(moyenne / 50)
    E = 1 / (1 + 10 ** ((player2.elo - player1.elo) / 400))
    new_elo = round(player1.elo + (K * (result - E)))
    diff = new_elo - player1.elo
    return diff, new_elo


async def handle_disconnect_grace_period(user: User, game_id: str):
    disconnected_players[user.username] = {"reconnected": False}
    await asyncio.sleep(10)
    if (
        user.username in disconnected_players
        and not disconnected_players[user.username]["reconnected"]
    ):
        print(f"Player {user.username} abandoned the game. Removing them permanently.")
        del disconnected_players[user.username]
        disconnect(user)
        if game_id in games:
            opponent = get_opponent(user, game_id)
            await finish_game_by_forfeit(game_id, opponent, user, "opponent_left")
        else:
            disconnect(user)


async def finish_game_by_forfeit(game_id: str, winner: User, loser: User, reason: str):
    if game_id not in games:
        return  # already finished / cleaned up
    cancel_timer(game_id)
    diff_w, new_elo_w = await calculate_new_elo(winner, loser, 1)
    _, new_elo_l = await calculate_new_elo(loser, winner, 0)
    update_user_elo(winner, new_elo_w)
    update_user_elo(loser, new_elo_l)
    # Notify the winner if they are still connected
    if winner.username in connections:
        await connections[winner.username].send_json(
            {
                "type": "end_game",
                "status": "winner",
                "elo_diff": diff_w,
                "new_elo": new_elo_w,
                "reason": reason,
            }
        )
    cleanup_game(game_id, winner, loser)


def cleanup_game(game_id: str, *users: User):
    games.pop(game_id, None)
    for u in users:
        player_games.pop(u.username, None)
        disconnected_players.pop(u.username, None)


async def find_player(user: User):
    queue = matchmaking_queue["TWO_PLAYER_AI"]

    if (len(queue)) >= 1:
        opponent = get_user(queue.pop(0))
        if opponent is None:
            print("opponent not found")
            assert False
        await create_game(opponent, user)
    else:
        queue.append(user.username)
        await connections[user.username].send_json({"type": "waiting"})


async def create_game(player1: User, player2: User):
    game = Game(
        id=str(uuid.uuid4()),
        game_type=GameType.TWO_PLAYER_AI,
        game_state=GameState.STARTED,
        players=[player1.username, player2.username],
        word=get_random_word(),
    )

    loop = asyncio.get_running_loop()
    game.ends_at = loop.time() + 60

    games[game.id] = game
    player_games[player1.username] = game.id
    player_games[player2.username] = game.id

    game_timers[game.id] = asyncio.create_task(game_timer(game.id))

    await connections[player1.username].send_json(
        {
            "type": "match_found",
            "game_id": game.id,
            "opponent": player2.username,
            "word": game.word,
            "duration": 60,
        }
    )

    await connections[player2.username].send_json(
        {
            "type": "match_found",
            "game_id": game.id,
            "opponent": player1.username,
            "word": game.word,
            "duration": 60,
        }
    )


def disconnect(user: User):
    connections.pop(user.username, None)
    player_games.pop(user.username, None)
    queue = matchmaking_queue["TWO_PLAYER_AI"]
    if user.username in queue:
        queue.remove(user.username)


def get_random_word():
    data = load_word_list()
    word = random.choice(data)
    return word
