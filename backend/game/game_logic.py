import asyncio

from fastapi import WebSocketException, status

from core.config import (
    COUNTDOWN_DURATION,
    ROUND_DURATION,
    ROUND_WIN_TARGET,
    SCORE_INCREMENT_PER_SECOND,
)
from core.database import get_user, update_user_elo
from core.setup import manager
from schemas.data import Game, User
from services.services import make_ai_guess
from utils.getters import (
    get_opponents,
    get_random_word,
    get_total_score,
    get_users_unsafe,
)
from utils.utils import calculate_new_elo, cancel_timer, cleanup_game, disconnect


async def end_game(game: Game, winner: User, reason: str | None = None):
    users = get_users_unsafe(game.players)
    losers = users.copy()
    losers.remove(winner)

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

    cancel_timer(game.id)
    cleanup_game(game)


async def handle_round_end(game: Game, winner: User):
    assert len(game.players) > 0

    if len(game.players) == 1:
        await end_game(game, winner)
        return

    game.round_wins[winner.username] += 1

    if game.round_wins[winner.username] >= ROUND_WIN_TARGET:
        await end_game(game, winner)
        return
    else:
        await start_next_round(game)


async def start_next_round(game: Game):
    game.scores = {player: 0 for player in game.players}
    game.ai_scores = {player: 0 for player in game.players}
    game.score_bonuses = {player: 0 for player in game.players}
    game.word = get_random_word()
    loop = asyncio.get_running_loop()
    game.ends_at = loop.time() + COUNTDOWN_DURATION + ROUND_DURATION

    payloads = []
    for username in game.players:
        payloads.append(
            {
                "username": username,
                "payload": {
                    "type": "next_round",
                    "word": game.word,
                    "duration": ROUND_DURATION,
                    "countdown": COUNTDOWN_DURATION,
                    "scores": game.scores,
                    "round_wins": game.round_wins,
                },
            }
        )
    manager._emit("broadcast_to_players", payloads=payloads)
    cancel_timer(game.id)
    manager.game_timers[game.id] = asyncio.create_task(game_timer(game.id))


async def end_game_by_timeout(game_id: str):
    print("ending game ", game_id, " by timeout")
    print("asserting game exists...")

    assert game_id in manager.games
    game = manager.games[game_id]

    print("fetching users...\nusers:")
    users = game.players
    for user in users:
        print("\t", user)
    print("fetching scores...\nscores:")
    scores = game.scores
    for score in scores:
        print("\t", score)
    max_score = max(scores.values())
    winners = [user for user in users if scores[user] == max_score]
    print("winner(s): ", winners)

    assert len(winners) > 0

    if len(winners) > 1:
        payloads = []
        for username in users:
            payloads.append({"username": username, "payload": {"type": "round_tie"}})
        manager._emit("broadcast_to_players", payloads=payloads)
        await start_next_round(game)
        return
    else:
        assert get_user(winners[0]) is not None  # TODO: remove
        await handle_round_end(game, get_user(winners[0]))


async def start_game(payload: dict, user: User):
    code = payload.get("code")
    if not code or code not in manager.lobbies:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Must provide lobby code"
        )

    lobby: dict[str, dict] = manager.lobbies[code]
    if lobby["host"] != user.username:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Only host can start game"
        )
    assert lobby["players"]
    if len(lobby["players"]) < 2:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Cannot start game alone",
        )

    for player in lobby["players"]:
        if manager.player_games.get(player) is not None:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Some Players are already in other games",
            )
        if manager.connections.get(player) is None:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Not all players are connected",
            )

    players = lobby["players"]

    user_objects = []
    for username in players:
        player = get_user(username)
        assert player is not None
        user_objects.append(player)

    await manager.create_game(user_objects, False)


def get_game_info(user: User) -> None:
    game_id = manager.player_games.get(user.username)
    if not game_id:
        manager._emit(
            "broadcast_to_players",
            payloads=[
                {
                    "username": user.username,
                    "payload": {"type": "game_info", "exist": False},
                }
            ],
        )
    game = manager.games.get(game_id)
    assert game is not None
    opponents = get_opponents(user, game)
    manager._emit(
        "broadcast_to_players",
        payloads=[
            {
                "username": user.username,
                "payload": {
                    "type": "game_info",
                    "exist": True,
                    "game_id": game_id,
                    "opponent": opponents,
                    "players": game.players,
                    "me": user.username,
                    "word": game.word,
                    "duration": ROUND_DURATION,
                    "countdown": COUNTDOWN_DURATION,
                    "scores": game.scores,
                    "round_wins": game.round_wins,
                    "is_ranked": game.is_ranked,
                },
            }
        ],
    )


async def ai_guess(user: User, payload: dict) -> None:
    game_id = manager.player_games.get(user.username)
    if game_id is None:
        raise ValueError("You are not part of any games")

    game = manager.games[game_id]
    strokes = payload.get("strokes", [])
    guess = await make_ai_guess(strokes, game.word)
    game.ai_scores[user.username] = guess.get(game.word) or 0
    score = get_total_score(game, user.username)
    game.scores[user.username] = score

    payloads = []
    for username in game.players:
        payloads.append(
            {
                "username": username,
                "payload": {
                    "type": "ai_guess",
                    "guess": guess,
                    "scores": score,
                },
            }
        )
    manager._emit("broadcast_to_players", payloads=payloads)

    if score >= 100:
        await handle_round_end(game, user)


async def surrender_game(user: User) -> None:
    game_id = manager.player_games.get(user.username)
    if game_id is None:
        raise ValueError("game doesnt exist")
    game = manager.games[game_id]
    opponents = get_opponents(user, game)
    if len(opponents) == 1:
        winner = get_user(opponents[0]) if opponents else None
        assert winner is not None
        await end_game(game, winner, "opponent_surrendered")
    else:
        payloads = []
        for player in game.players:
            payloads.append(
                {
                    "username": player,
                    "payload": {
                        "type": "opponent_surrendered",
                    },
                }
            )
        manager._emit("broadcast_to_players", payloads=payloads)
        disconnect(user)


async def increase_scores(game_id: str):
    game = manager.games[game_id]
    for username in game.players:
        game.score_bonuses[username] = (
            game.score_bonuses.get(username, 0) + SCORE_INCREMENT_PER_SECOND
        )
        score = get_total_score(game, username)
        game.scores[username] = score
        await broadcast_player_score(
            game,
            username,
            score,
            None,
            include_self=True,
        )
        if score >= 100:
            winner = get_user(username)
            if winner is None:
                raise ValueError("winner does not exist")
            await handle_round_end(game, winner)
            return


async def game_timer(game_id: str):
    loop = asyncio.get_running_loop()
    await asyncio.sleep(COUNTDOWN_DURATION)

    while True:
        game = manager.games.get(game_id)
        if game is None:
            return
        remaining = game.ends_at - loop.time()
        if remaining <= 0:
            break
        await asyncio.sleep(min(1, remaining))
        if game_id not in manager.games:
            return
        await increase_scores(game_id)

    await end_game_by_timeout(game_id)


async def broadcast_player_score(
    game: Game,
    username: str,
    score: float,
    guess: dict | None = None,
    include_self: bool = False,
):
    payloads = []
    for player in game.players:
        if player == username and not include_self:
            continue
        payload = {
            "type": "player_guess",
            "username": username,
            "score": score,
        }
        if guess is not None:
            payload["guess"] = guess
        payloads.append({"username": player, "payload": payload})
    manager._emit("broadcast_to_players", payloads=payloads)


async def send_end_game(
    username: str, status: str, elo_diff: int, new_elo: int, reason: str | None = None
):
    payload = {
        "type": "end_game",
        "status": status,
        "elo_diff": elo_diff,
        "new_elo": new_elo,
    }
    if reason is not None:
        payload["reason"] = reason
    manager._emit(
        "broadcast_to_players",
        payloads=[
            {
                "username": username,
                "payload": payload,
            }
        ],
    )


async def _start_game_timer(event, data):
    game = data["game"]
    task = asyncio.create_task(game_timer(game.id))
    game.timer = task
    manager.game_timers[game.id] = task


def init_game_events():
    manager.on("game_created", _start_game_timer)
