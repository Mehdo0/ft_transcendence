import asyncio

from fastapi import WebSocketException, status

from core.config import (
    ROUND_DURATION,
    ROUND_COUNTDOWN_DURATION,
    ROUND_REPLAY_FINAL_HOLD_DURATION,
    ROUND_REPLAY_DURATION,
    ROUND_WIN_TARGET,
    SCORE_INCREMENT_PER_SECOND,
)
from core.database import update_user_elo
from core.setup import manager
from game.drawing_replay import (
    create_initial_replay_timeline,
    finalize_replay_timeline,
    record_drawing_change,
    record_score_change,
    sanitize_drawing,
)
from game.lobby_logic import cleanup_lobby_on_disconnect, close_lobby
from schemas.data import Game, GameState, RoundResult, User
from services.services import make_ai_guess
from utils.getters import (
    get_game_user,
    get_game_users,
    get_opponents,
    get_random_word,
    get_total_score,
)
from utils.utils import calculate_new_elo, cancel_timer, cleanup_game


async def end_game(
    game: Game, winner: User, reason: str | None = None, surrender: User | None = None
):
    if manager.games.get(game.id) is not game or game.game_state is GameState.FINISHED:
        return
    game.game_state = GameState.FINISHED

    print(
        "ending game. details:\n",
        game,
        "winner:",
        winner,
        "reason:",
        reason,
        "surrender: ",
        surrender,
    )
    users = get_game_users(game)
    losers = [u for u in users if u.username != winner.username]

    if game.is_ranked and len(losers) == 1:
        print("ranked game, calculating elo")
        loser = losers[0]
        diff_winner, new_elo_winner = await calculate_new_elo(winner, loser, 1)
        diff_loser, new_elo_loser = await calculate_new_elo(loser, winner, 0)
        update_user_elo(winner, new_elo_winner)
        update_user_elo(loser, new_elo_loser)
        await send_end_game(
            winner.username, "winner", diff_winner, new_elo_winner, reason
        )
        await send_end_game(loser.username, "loser", diff_loser, new_elo_loser, reason)
    else:
        if surrender:
            print("user surrenderd ending game")
            for user in users:
                status = "winner" if user.username != surrender.username else "loser"
                await send_end_game(user.username, status, 0, user.elo, reason)
        else:
            print("ending game, winner : ", winner)
            for user in users:
                status = "winner" if user.username == winner.username else "loser"
                await send_end_game(user.username, status, 0, user.elo, reason)

    cancel_timer(game.id)
    cleanup_game(game)


def is_match_complete(game: Game, winner: User | None) -> bool:
    if winner is None:
        return False
    if len(game.players) == 1:
        return True
    return game.round_wins[winner.username] >= ROUND_WIN_TARGET


def create_round_result(game: Game, winner: User | None) -> RoundResult:
    loop = asyncio.get_running_loop()
    timeline_duration = max(0, min(ROUND_DURATION, loop.time() - game.starts_at))
    for username in game.players:
        finalize_replay_timeline(game, username, timeline_duration)
    return RoundResult(
        round_number=game.round_number,
        winner=winner.username if winner else None,
        is_tie=winner is None,
        match_complete=is_match_complete(game, winner),
        duration=ROUND_REPLAY_DURATION,
        final_hold_duration=ROUND_REPLAY_FINAL_HOLD_DURATION,
        timeline_duration=timeline_duration,
        drawings={username: list(strokes) for username, strokes in game.drawings.items()},
        timelines={
            username: list(events)
            for username, events in game.replay_timelines.items()
        },
        scores=dict(game.scores),
        round_wins=dict(game.round_wins),
    )


async def broadcast_round_result(game: Game) -> None:
    if game.round_result is None:
        return
    payload = {"type": "round_result", **game.round_result.model_dump()}
    await manager.emit(
        "broadcast_to_players",
        payloads=[{"username": username, "payload": payload} for username in game.players],
    )


async def handle_round_end(game: Game, winner: User | None) -> None:
    if not game.round_active:
        return

    game.round_active = False
    cancel_timer(game.id)

    if winner is not None:
        game.round_wins[winner.username] += 1

    game.round_result = create_round_result(game, winner)
    await broadcast_round_result(game)

    task = asyncio.create_task(complete_round_transition(game, winner))
    game.timer = task
    manager.game_timers[game.id] = task


async def complete_round_transition(game: Game, winner: User | None) -> None:
    await asyncio.sleep(ROUND_REPLAY_DURATION)

    if manager.games.get(game.id) is not game:
        return
    if game.round_result.match_complete and winner is not None:
        await end_game(game, winner)
        return

    await start_next_round(game)


async def start_next_round(game: Game):
    cancel_timer(game.id)
    game.scores = {player: 0 for player in game.players}
    game.ai_scores = {player: 0 for player in game.players}
    game.score_bonuses = {player: 0 for player in game.players}
    game.drawings = {player: [] for player in game.players}
    game.replay_timelines = {
        player: create_initial_replay_timeline() for player in game.players
    }
    game.round_number += 1
    game.round_active = True
    game.round_result = None
    game.word = get_random_word()
    loop = asyncio.get_running_loop()
    game.countdown_duration = ROUND_COUNTDOWN_DURATION
    game.starts_at = loop.time() + game.countdown_duration
    game.ends_at = game.starts_at + ROUND_DURATION

    payloads = []
    for username in game.players:
        payloads.append(
            {
                "username": username,
                "payload": {
                    "type": "next_round",
                    "word": game.word,
                    "duration": ROUND_DURATION,
                    "countdown": game.countdown_duration,
                    "scores": game.scores,
                    "round_wins": game.round_wins,
                    "round_number": game.round_number,
                },
            }
        )
    await manager.emit("broadcast_to_players", payloads=payloads)
    manager.game_timers[game.id] = asyncio.create_task(game_timer(game.id))


def get_round_winner(game: Game) -> User | None:
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
    if len(winners) > 1:
        return None
    print("winner: ", winners[0])
    return get_game_user(game, winners[0])


def get_countdown_left(game: Game) -> float:
    loop = asyncio.get_running_loop()
    return max(0, game.starts_at - loop.time())


def get_replay_elapsed(game: Game) -> float:
    loop = asyncio.get_running_loop()
    return max(0, loop.time() - game.starts_at)


def get_game_winner(game: Game, exclude: User | None) -> User | None:
    max_round_win = max(game.round_wins.values())
    winners = [user for user in game.players if game.round_wins[user] == max_round_win]
    if exclude is not None:
        winners = [username for username in winners if username != exclude.username]
    print("winners:", winners)
    if len(winners) != 1:
        print("more than 1 winner -> TIE")
        return None
    return get_game_user(game, winners[0])


async def end_game_by_timeout(game_id: str):
    print("ending game ", game_id, " by timeout")
    game = manager.games.get(game_id)
    if game is None or not game.round_active:
        return

    winner = get_round_winner(game)
    await handle_round_end(game, winner)


async def start_game(payload: dict, user: User):
    code = payload.get("code")
    if not code or code not in manager.lobbies:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Must provide lobby code"
        )

    lobby = manager.lobbies[code]
    if lobby.host != user.username:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Only host can start game"
        )
    if len(lobby.players) < 2:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Cannot start game alone",
        )

    for player in lobby.players:
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

    user_objects = []
    for username in lobby.players:
        player = manager.connected_users.get(username)
        assert player is not None
        user_objects.append(player)

    await manager.create_game(user_objects, False)


async def get_game_info(user: User) -> None:
    game_id = manager.player_games.get(user.username)
    game = manager.games.get(game_id)
    if not game:
        await manager.emit(
            "broadcast_to_players",
            payloads=[
                {
                    "username": user.username,
                    "payload": {"type": "game_info", "exist": False},
                }
            ],
        )
        return
    game = manager.games.get(game_id)
    assert game is not None
    opponents = get_opponents(user, game)
    loop = asyncio.get_running_loop()
    time_left = max(0, game.ends_at - loop.time()) if game.ends_at else None
    await manager.emit(
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
                    "time_left": time_left,
                    "countdown": game.countdown_duration,
                    "countdown_left": get_countdown_left(game),
                    "duration": ROUND_DURATION,
                    "scores": game.scores,
                    "round_wins": game.round_wins,
                    "round_number": game.round_number,
                    "round_result": (
                        game.round_result.model_dump() if game.round_result else None
                    ),
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
    if not game.round_active:
        return
    if get_countdown_left(game) > 0:
        return

    strokes = payload.get("strokes", [])
    drawing = sanitize_drawing(strokes)
    record_drawing_change(game, user.username, drawing, get_replay_elapsed(game))
    guess = await make_ai_guess(strokes, game.word)
    game.ai_scores[user.username] = guess.get(game.word) or 0
    score = get_total_score(game, user.username)
    game.scores[user.username] = score
    record_score_change(game, user.username, get_replay_elapsed(game))

    payloads = []
    for username in game.players:
        payloads.append(
            {
                "username": username,
                "payload": {
                    "type": "ai_guess",
                    "username": user.username,
                    "guess": guess,
                    "scores": score,
                },
            }
        )
    await manager.emit("broadcast_to_players", payloads=payloads)

    if score >= 100:
        await handle_round_end(game, user)


async def surrender_game(user: User, leave_lobby: bool = False) -> None:
    print("user", user.username, "is surrendering")
    game_id = manager.player_games.get(user.username)
    if game_id is None:
        print("INFO: game has already ended, cannot surrender")
        return
    game = manager.games[game_id]
    opponents = get_opponents(user, game)
    print("notifying opponents (", opponents, ")")
    payloads = []
    for opponent in opponents:
        payloads.append(
            {
                "username": opponent,
                "payload": {
                    "type": "opponent_surrendered",
                },
            }
        )
    await manager.emit("broadcast_to_players", payloads=payloads)
    winner = get_game_winner(game, user)
    if winner is None and len(opponents) == 1:
        winner = get_game_user(game, opponents[0])
    if winner is None:
        print("tie, ending game")
        await end_game(game, user, user.username + " surrendered", user)
    else:
        print("winner is", winner.username)
        await end_game(game, winner, user.username + " surrendered")
    print("closing the lobby...")
    if leave_lobby:
        await cleanup_lobby_on_disconnect(user)
    else:
        for code, lobby in list(manager.lobbies.items()):
            if user.username in lobby.players and lobby.host == user.username:
                await close_lobby(code)
                break


async def increase_scores(game_id: str):
    game = manager.games.get(game_id)
    if game is None or not game.round_active:
        return
    for username in game.players:
        game.score_bonuses[username] = (
            game.score_bonuses.get(username, 0) + SCORE_INCREMENT_PER_SECOND
        )
        score = get_total_score(game, username)
        game.scores[username] = score
        record_score_change(game, username, get_replay_elapsed(game))
        await broadcast_player_score(
            game,
            username,
            score,
            None,
            include_self=True,
        )
        if score >= 100:
            winner = get_game_user(game, username)
            if winner is None:
                raise ValueError("winner does not exist")
            await handle_round_end(game, winner)
            return


async def game_timer(game_id: str):
    game = manager.games.get(game_id)
    if game is None:
        return
    await asyncio.sleep(max(0, game.starts_at - asyncio.get_running_loop().time()))

    while True:
        loop = asyncio.get_running_loop()
        game = manager.games.get(game_id)
        if game is None or not game.round_active:
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
    await manager.emit("broadcast_to_players", payloads=payloads)


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
    await manager.emit(
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
