import torchvision.ops.poolers
import uuid
from utils.getters import get_random_word, get_total_score, get_opponents
from utils.utils import send_msg_to_opponents
import asyncio
from core.config import ROUND_DURATION, ROUND_WIN_TARGET, SCORE_INCREMENT_PER_SECOND
from fastapi import WebSocket, WebSocketException, status
from core.database import get_user, update_user_elo
from core.setup import manager
from schemas.data import Game, GameState, User
from services.services import make_ai_guess
from utils.getters import get_users_unsafe
from utils.utils import cancel_timer, calculate_new_elo, cleanup_game


# async def create_game(players: list[User], is_ranked: bool):
#     player_usernames = [player.username for player in players]
#     print("GAME: creating game with players: ", player_usernames)
#     loop = asyncio.get_running_loop()
#     game = Game(
#         id=str(uuid.uuid4()),
#         game_state=GameState.STARTED,
#         players=player_usernames,
#         word=get_random_word(),
#         is_ranked=is_ranked,
#         ends_at=loop.time() + ROUND_DURATION,
#     )
#     print(
#         "game id: ",
#         game.id,
#         ", word: ",
#         game.word,
#         ", ranked: ",
#         game.is_ranked,
#         ", ends_at: ",
#         game.ends_at,
#     )

#     print("creating task for game id ", game.id, "...")

#     manager.games[game.id] = game

#     for player in players:
#         game.scores[player.username] = 0
#         game.ai_scores[player.username] = 0
#         game.score_bonuses[player.username] = 0
#         game.round_wins[player.username] = 0
#         manager.player_manager.games[player.username] = game.id
#         opponents = get_opponents(player, game)
#         print("opponents of player ", player.username, opponents)
#         websocket = manager.manager.connections[player.username]
#         await websocket.send_json(
#             {
#                 "type": "match_found",
#                 "game_id": game.id,
#                 "opponent": opponents,
#                 "players": player_usernames,
#                 "me": player.username,
#                 "word": game.word,
#                 "duration": ROUND_DURATION,
#                 "scores": game.scores,
#                 "round_wins": game.round_wins,
#                 "is_ranked": game.is_ranked,
#             }
#         )

#     manager.game_timers[game.id] = asyncio.create_task(game_timer(game.id))


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
    game.ends_at = loop.time() + ROUND_DURATION

    payloads = []
    for username in game.players:
        payloads.append({
            "username": username,
            "payload": {
                "type": "next_round",
                "word": game.word,
                "duration": ROUND_DURATION,
                "scores": game.scores,
                "round_wins": game.round_wins,
            }
        })
    manager._emit("broadcast_to_players", payloads=payloads)
    cancel_timer(game.id)
    manager.game_timers[game.id] = asyncio.create_task(game_timer(game.id))


async def end_game_by_timeout(game_id: str):
    print("ending game ", game_id, " by timeout")
    print("asserting game exists...")

    assert game_id in manager.games
    game = manager.games[game_id]

    print("fetching users...\nusers:")
    users = manager.games[game_id].players #this could return None
    for user in users:
        print("\t", user)
    print("fetching scores...\nscores:")
    scores = manager.games[game_id].scores
    for score in scores:
        print("\t", score)
    max_score = max(scores.values())
    winners = [user for user in users if scores[user.username] == max_score]
    print("winner(s): ", winners)

    assert len(winners) > 0

    if len(users) == 1:
        print("solo match, user ", users[0], " has won.")
        await send_end_game(users[0].username, "draw", 0, users[0].elo, "timeout") #ws_manager
        cancel_timer(game_id)
        cleanup_game(game)
        return

    if len(winners) > 1:
        for user in users:
            websocket = manager.connections.get(user.username) #link this to ws_manager
            assert websocket is not None
            await websocket.send_json({"type": "round_tie"})
        await start_next_round(game) # game_manager
        return
    else:
        # update scores and start next round
        await handle_round_end(game, winners[0]) # game_manager
        return


async def start_game(payload: dict, user: User): #is this function specific to lobby games ?????
    code = payload.get("code")
    if not code or code not in manager.lobbies:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Must provide lobby code"
        )

    lobby: dict[str, dict] = manager.lobbies[code]
    if lobby[code]["host"] != user.username:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Only host can start game"
        )
    assert lobby[code]["players"]
    if len(lobby["players"]) < 2:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Cannot start game alone",
        )

    for player in lobby[code]["players"]:
        if manager.player_games.get(player) is not None:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Some Players are already in other games",
            )

    players= lobby[code][players]

    for player in players:
        assert player in manager.connections # ws_manager
        assert get_user(player) is not None

    await manager.create_game(players, False)


async def ai_guess(user: User, payload: dict, websocket: WebSocket) -> None:
    game_id = manager.get_game_id(user)
    if game_id is None:
        raise ValueError("You are not part of any games")

    game = manager.games[game_id]
    strokes = payload.get("strokes", [])
    guess = await make_ai_guess(strokes, game.word)
    game.ai_scores[user.username] = guess.get(game.word) or 0
    score = get_total_score(game, user.username)
    game.scores[user.username] = score

    payloads = []
    for user in game.players:
        payloads.append({
            "username": user.username,
            "payload": {
                "type": "ai_guess",
                "guess": guess,
                "scores": score,
            }
        })
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
        assert winner is not None  # if there is another opponent, it should exist TODO: remove
        await end_game(game, winner, "opponent_surrendered") # game_manager
    else:
        payloads = []
        for user in game.players:
            payloads.append({
                "username": user.username,
                "payload": {
                    "type": "opponent_disconnected",
                }
            })
        manager._emit("broadcast_to_players", payloads=payloads)
        manager.player_games.pop(user.username)
        game.players.remove(user.username)


async def increase_scores(game_id: str):
    game = manager.games[game_id]
    for username in game.players:
        game.score_bonuses[username] = (
            game.score_bonuses.get(username, 0) + SCORE_INCREMENT_PER_SECOND
        )
        score = get_total_score(game, username)
        game.scores[username] = score
        await broadcast_player_score( # ws_manager
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
            await handle_round_end(game, winner) # game_manager
            return


async def game_timer(game_id: str):
    for _ in range(ROUND_DURATION):
        await asyncio.sleep(1)
        assert game_id in manager.games  # otherwise, task should be cancelled
        await increase_scores(game_id)

    await end_game_by_timeout(game_id) # game_manager


async def broadcast_player_score(
    game: Game,
    username: str,
    score: float,
    guess: dict | None = None,
    include_self: bool = False,
):
    for player in game.players:
        player_ws = manager.connections.get(player)
        assert player_ws is not None
        if player == username and not include_self:
            continue
        payload = {
            "type": "player_guess",
            "username": username,
            "score": score,
        }
        if guess is not None:
            payload["guess"] = guess
        manager._emit("broadcast_to_players", payload=payload)


async def send_end_game( #ws_manager
    username: str, status: str, elo_diff: int, new_elo: int, reason: str | None = None
):
    websocket = manager.connections.get(username)
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
    manager._emit("broadcast_to_players", payload=payload)
