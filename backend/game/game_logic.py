from typing import Coroutine
import uuid
from utils.getters import get_random_word, get_total_score, get_opponents
import asyncio
from core.setup import ROUND_DURATION, ROUND_WIN_TARGET, SCORE_INCREMENT_PER_SECOND
from fastapi import WebSocket
from core.database import get_user, update_user_elo
from schemas.data import Game, GameState, User
from services.services import make_ai_guess
from state.state import (
    connections,
    game_timers,
    games,
    lobbies,
    player_games,
)
from utils.getters import get_users
from utils.utils import cancel_timer, calculate_new_elo, cleanup_game, ensure_round_wins


async def create_game(players: list[User], is_ranked: bool):
    loop = asyncio.get_running_loop()
    game = Game(
        id=str(uuid.uuid4()),
        game_state=GameState.STARTED,
        players=[player.username for player in players],
        word=get_random_word(),
        is_ranked=is_ranked,
        ends_at=loop.time() + ROUND_DURATION,
    )
    games[game.id] = game
    game_timers[game.id] = asyncio.create_task(game_timer(game.id))

    for player in players:
        game.scores[player.username] = 0
        game.ai_scores[player.username] = 0
        game.score_bonuses[player.username] = 0
        game.round_wins[player.username] = 0
        player_games[player.username] = game.id
        opponents = get_opponents(player, game.id)
        websocket = connections[player.username]
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


async def end_game(game_id: str, winner: User, reason: str | None = None):
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
            await send_end_game(user.username, status, 0, user.elo, reason)

    cancel_timer(game_id)
    cleanup_game(game_id, *users)


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


async def start_game(payload: dict, user: User):
    code = payload.get("code")
    if code not in lobbies:
        return

    lobby = lobbies[code]
    if lobby["host"] != user.username or len(lobby["players"]) < 1:
        return
    if any(player in player_games for player in lobby["players"]):
        return

    players = get_users(
        [player for player in lobby["players"] if player in connections]
    )
    if not players:
        return

    await create_game(players, False)


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

    if score >= 100:
        await handle_round_end(game_id, user)

    return True


async def surrender_game(user: User) -> bool:
    game_id = player_games.get(user.username)
    if game_id is None or game_id not in games:
        return False
    opponents = get_opponents(user, game_id)
    winner = get_user(opponents[0]) if opponents else None
    if winner is None:
        return False
    await end_game(game_id, winner, "opponent_surrendered")
    return True


async def increase_scores(
    game_id: str,
):  # TODO: use the user object instead of the username
    game = games[game_id]
    for username in game.players:
        game.score_bonuses[username] = (
            game.score_bonuses.get(username, 0) + SCORE_INCREMENT_PER_SECOND
        )
        score = get_total_score(game, username)
        game.scores[username] = score
        await broadcast_player_score(game, username, score, include_self=True)
        if score >= 100:
            winner = get_user(username)
            if winner is None:
                raise ValueError("winner does not exist")
            await handle_round_end(game_id, winner)
            return


async def game_timer(game_id: str):
    for _ in range(ROUND_DURATION):
        await asyncio.sleep(1)
        if game_id not in games:
            return
        await increase_scores(game_id)

    if game_id in games:
        await end_game_by_timeout(game_id)


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
