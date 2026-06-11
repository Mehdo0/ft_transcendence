import asyncio
import random
import string
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.database import get_user, update_user_elo
from schemas.data import Game, GameState, GameType, User
from services.ai_service import load_word_list
from services.services import get_user_from_ws_token, make_ai_guess
from state.state import (
    connections,
    disconnected_players,
    game_timers,
    games,
    lobbies,
    matchmaking_queue,
    player_games,
)


router = APIRouter()
ROUND_DURATION = 60
ROUND_WIN_TARGET = 2
SCORE_INCREMENT_PER_SECOND = 0.5


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
                    if await validate_code(code, websocket):
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


async def ai_guess(user: User, payload: dict, websocket: WebSocket) -> bool:
    game_id = player_games.get(user.username)
    if game_id is None or game_id not in games:
        return False

    game = games[game_id]
    strokes = payload.get("strokes", [])
    guess = await make_ai_guess(strokes, game.word)
    game.ai_scores[user.username] = guess.get(game.word) or 0
    score = get_total_score(game, user.username)
    game.scores[user.username] = score

    await websocket.send_json(
        {
            "type": "ai_guess",
            "guess": guess,
            "username": user.username,
            "score": score,
        }
    )
    await broadcast_player_score(game, user.username, score, guess)

    if should_finish_round(game, score):
        await handle_round_end(game_id, user)

    return True


async def broadcast_player_score(
    game: Game,
    username: str,
    score: float,
    guess: dict | None = None,
    include_self: bool = False,
):
    for player in game.players:
        player_ws = connections.get(player)
        if player_ws is None or (player == username and not include_self):
            continue
        payload = {
            "type": "player_guess",
            "username": username,
            "score": score,
        }
        if guess is not None:
            payload["guess"] = guess
        await player_ws.send_json(payload)


def should_finish_round(game: Game, score: float) -> bool:
    return score >= 100


def get_total_score(game: Game, username: str) -> float:
    return min(
        100,
        game.score_bonuses.get(username, 0) + game.ai_scores.get(username, 0),
    )


async def disconnect_user(user: User):
    connections.pop(user.username, None)
    if user.username in player_games:
        game_id = player_games[user.username]
        asyncio.create_task(handle_disconnect_grace_period(user, game_id))
        return
    await cleanup_lobby_on_disconnect(user)
    disconnect(user)


async def surrender_game(user: User) -> bool:
    game_id = player_games.get(user.username)
    if game_id is None or game_id not in games:
        return False
    await finish_game_by_forfeit(game_id, user, "opponent_surrendered")
    return True


async def start_game(payload: dict, user: User):
    code = payload.get("code")
    if code not in lobbies:
        return

    lobby = lobbies[code]
    if lobby["host"] != user.username or len(lobby["players"]) < 1:
        return
    if any(player in player_games for player in lobby["players"]):
        return

    players = get_users([player for player in lobby["players"] if player in connections])
    if not players:
        return

    await create_game(players, False)


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


async def validate_code(code: str, websocket: WebSocket) -> bool:
    if len(code) != 6 or not code.isalnum():
        await websocket.send_json({"type": "error", "message": "invalid code"})
        return False
    return True


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


async def create_lobby(user: User, websocket: WebSocket):
    remove_from_matchmaking(user.username)

    while True:
        characters = string.ascii_uppercase + string.digits
        code = "".join(random.choices(characters, k=6))
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


def get_opponent(user: User, game_id: str) -> User:
    opponents = get_opponents(user, game_id)
    if not opponents:
        raise ValueError("opponent does not exist")
    opponent = get_user(opponents[0])
    if opponent is None:
        raise ValueError("opponent does not exist")
    return opponent


def get_opponents(user: User, game_id: str) -> list[str]:
    return [player for player in games[game_id].players if player != user.username]


def get_users(usernames: list[str]) -> list[User]:
    users = []
    for username in usernames:
        user = get_user(username)
        if user is None:
            raise ValueError("lobby player not found")
        users.append(user)
    return users


async def send_end_game(
    username: str, status: str, elo_diff: int, new_elo: int, reason: str | None = None
):
    websocket = connections.get(username)
    if websocket is None:
        return

    payload = {
        "type": "end_game",
        "status": status,
        "elo_diff": elo_diff,
        "new_elo": new_elo,
    }
    if reason is not None:
        payload["reason"] = reason
    await websocket.send_json(payload)


async def handle_round_end(game_id: str, winner: User):
    if game_id not in games:
        return

    game = games[game_id]
    if len(game.players) <= 1:
        await end_game(game_id, winner)
        return

    ensure_round_wins(game)
    game.round_wins[winner.username] += 1

    if game.round_wins[winner.username] >= ROUND_WIN_TARGET:
        await end_game(game_id, winner)
        return

    await start_next_round(game_id)


async def start_next_round(game_id: str):
    if game_id not in games:
        return

    game = games[game_id]
    game.scores = {player: 0 for player in game.players}
    game.ai_scores = {player: 0 for player in game.players}
    game.score_bonuses = {player: 0 for player in game.players}
    game.word = get_random_word()
    loop = asyncio.get_running_loop()
    game.ends_at = loop.time() + ROUND_DURATION

    for username in game.players:
        websocket = connections.get(username)
        if websocket:
            await websocket.send_json(
                {
                    "type": "next_round",
                    "word": game.word,
                    "duration": ROUND_DURATION,
                    "scores": game.scores,
                    "round_wins": game.round_wins,
                }
            )

    cancel_timer(game_id)
    game_timers[game_id] = asyncio.create_task(game_timer(game_id))


async def end_game(game_id: str, winner: User):
    if game_id not in games:
        return

    game = games[game_id]
    users = get_users(game.players)
    losers = [user for user in users if user.username != winner.username]

    if game.is_ranked and len(losers) == 1:
        loser = losers[0]
        diff_winner, new_elo_winner = await calculate_new_elo(winner, loser, 1)
        diff_loser, new_elo_loser = await calculate_new_elo(loser, winner, 0)
        update_user_elo(winner, new_elo_winner)
        update_user_elo(loser, new_elo_loser)
        await send_end_game(winner.username, "winner", diff_winner, new_elo_winner)
        await send_end_game(loser.username, "looser", diff_loser, new_elo_loser)
    else:
        for user in users:
            status = "winner" if user.username == winner.username else "looser"
            await send_end_game(user.username, status, 0, user.elo)

    cancel_timer(game_id)
    cleanup_game(game_id, *users)


def cancel_timer(game_id: str):
    task = game_timers.pop(game_id, None)
    if task is not None:
        task.cancel()


async def game_timer(game_id: str):
    for _ in range(ROUND_DURATION):
        await asyncio.sleep(1)
        if game_id not in games:
            return
        await increase_scores(game_id)

    if game_id in games:
        await end_game_by_timeout(game_id)


async def increase_scores(game_id: str):
    game = games[game_id]
    for username in game.players:
        game.score_bonuses[username] = (
            game.score_bonuses.get(username, 0) + SCORE_INCREMENT_PER_SECOND
        )
        score = get_total_score(game, username)
        game.scores[username] = score
        await broadcast_player_score(game, username, score, include_self=True)
        if should_finish_round(game, score):
            winner = get_user(username)
            if winner is None:
                raise ValueError("winner does not exist")
            await handle_round_end(game_id, winner)
            return


async def end_game_by_timeout(game_id: str):
    if game_id not in games:
        return

    game = games[game_id]
    users = get_users(game.players)
    scores = {user.username: game.scores.get(user.username, 0) for user in users}
    max_score = max(scores.values())
    winners = [user for user in users if scores[user.username] == max_score]

    if len(winners) != 1:
        if len(users) <= 1:
            for user in users:
                await send_end_game(user.username, "draw", 0, user.elo, "timeout")
            cancel_timer(game_id)
            cleanup_game(game_id, *users)
            return

        for user in users:
            websocket = connections.get(user.username)
            if websocket:
                await websocket.send_json({"type": "round_tie"})
        await start_next_round(game_id)
        return

    await handle_round_end(game_id, winners[0])


async def calculate_new_elo(player1: User, player2: User, result: int):
    average = (player1.elo + player2.elo) / 2
    coefficient = 40 - round(average / 50)
    expected = 1 / (1 + 10 ** ((player2.elo - player1.elo) / 400))
    new_elo = round(player1.elo + (coefficient * (result - expected)))
    diff = new_elo - player1.elo
    return diff, new_elo


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
        await finish_game_by_forfeit(game_id, user, "opponent_left")
        return

    disconnect(user)


async def finish_game_by_forfeit(game_id: str, loser: User, reason: str):
    if game_id not in games:
        return

    game = games[game_id]
    users = get_users(game.players)
    winners = [user for user in users if user.username != loser.username]
    cancel_timer(game_id)

    if game.is_ranked and len(winners) == 1:
        winner = winners[0]
        diff_winner, new_elo_winner = await calculate_new_elo(winner, loser, 1)
        diff_loser, new_elo_loser = await calculate_new_elo(loser, winner, 0)
        update_user_elo(winner, new_elo_winner)
        update_user_elo(loser, new_elo_loser)
        await send_end_game(winner.username, "winner", diff_winner, new_elo_winner, reason)
        await send_end_game(loser.username, "looser", diff_loser, new_elo_loser, reason)
    else:
        for user in users:
            status = "looser" if user.username == loser.username else "winner"
            await send_end_game(user.username, status, 0, user.elo, reason)

    cleanup_game(game_id, *users)


def cleanup_game(game_id: str, *users: User):
    games.pop(game_id, None)
    for user in users:
        player_games.pop(user.username, None)
        disconnected_players.pop(user.username, None)


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


async def create_game(players: list[User], is_ranked: bool):
    game = Game(
        id=str(uuid.uuid4()),
        game_type=get_game_type(len(players)),
        game_state=GameState.STARTED,
        players=[player.username for player in players],
        word=get_random_word(),
        is_ranked=is_ranked,
    )
    game.scores = {player.username: 0 for player in players}
    game.ai_scores = {player.username: 0 for player in players}
    game.score_bonuses = {player.username: 0 for player in players}
    game.round_wins = {player.username: 0 for player in players}

    loop = asyncio.get_running_loop()
    game.ends_at = loop.time() + ROUND_DURATION

    games[game.id] = game
    for player in players:
        player_games[player.username] = game.id

    game_timers[game.id] = asyncio.create_task(game_timer(game.id))

    for player in players:
        opponents = [current.username for current in players if current.username != player.username]
        websocket = connections.get(player.username)
        if websocket:
            await websocket.send_json(
                {
                    "type": "match_found",
                    "game_id": game.id,
                    "opponent": opponents[0] if opponents else "",
                    "players": game.players,
                    "me": player.username,
                    "word": game.word,
                    "duration": ROUND_DURATION,
                    "scores": game.scores,
                    "round_wins": game.round_wins,
                    "is_ranked": game.is_ranked,
                }
            )


def get_game_type(player_count: int) -> GameType:
    if player_count <= 1:
        return GameType.SOLO_AI
    if player_count >= 4:
        return GameType.FOUR_PLAYER
    return GameType.TWO_PLAYER_AI


def ensure_round_wins(game: Game):
    for player in game.players:
        game.round_wins[player] = game.round_wins.get(player, 0)


def disconnect(user: User):
    connections.pop(user.username, None)
    player_games.pop(user.username, None)
    remove_from_matchmaking(user.username)


def remove_from_matchmaking(username: str):
    if username in matchmaking_queue:
        matchmaking_queue.remove(username)


def get_random_word():
    data = load_word_list()
    return random.choice(data)
