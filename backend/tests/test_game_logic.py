import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["torchvision"] = MagicMock()
sys.modules["torchvision.ops"] = MagicMock()
sys.modules["torchvision.ops.poolers"] = MagicMock()

import pytest
import asyncio

from schemas.data import Game, GameState, User
import state.state as state
from game import game_logic


@pytest.fixture(autouse=True)
def reset_state():
    state.connections.clear()
    state.games.clear()
    state.player_games.clear()
    state.lobbies.clear()
    state.matchmaking_queue.clear()
    state.disconnected_players.clear()
    state.game_timers.clear()


def make_user(name="test_player", email="test@test.com", elo=500):
    return User(username=name, email=email, elo=elo)


def make_game(game_id="g1", players=None, word="cat", is_ranked=False, ends_at=100.0):
    if players is None:
        players = ["p1", "p2"]
    game = Game(
        id=game_id,
        game_state=GameState.STARTED,
        players=players,
        word=word,
        ends_at=ends_at,
        is_ranked=is_ranked,
    )
    for p in players:
        game.scores[p] = 0
        game.ai_scores[p] = 0
        game.score_bonuses[p] = 0
        game.round_wins[p] = 0
    return game


# ── create_game ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_game_basic():
    p1 = make_user("p1")
    p2 = make_user("p2")
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    state.connections["p1"] = ws1
    state.connections["p2"] = ws2

    with patch("game.game_logic.get_random_word", return_value="cat"):
        with patch("game.game_logic.asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.time.return_value = 1000.0
            await game_logic.create_game([p1, p2], False)

    assert len(state.games) == 1
    game = list(state.games.values())[0]
    assert game.word == "cat"
    assert game.is_ranked is False
    assert game.scores["p1"] == 0
    assert game.scores["p2"] == 0
    assert state.player_games["p1"] == game.id
    assert state.player_games["p2"] == game.id
    ws1.send_json.assert_called_once()
    ws2.send_json.assert_called_once()
    call_args = ws1.send_json.call_args[0][0]
    assert call_args["type"] == "match_found"
    assert call_args["word"] == "cat"


@pytest.mark.asyncio
async def test_create_game_ranked():
    p1 = make_user("p1")
    p2 = make_user("p2")
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    state.connections["p1"] = ws1
    state.connections["p2"] = ws2

    with patch("game.game_logic.get_random_word", return_value="dog"):
        with patch("game.game_logic.asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.time.return_value = 1000.0
            await game_logic.create_game([p1, p2], True)

    game = list(state.games.values())[0]
    assert game.is_ranked is True
    call_args = ws1.send_json.call_args[0][0]
    assert call_args["is_ranked"] is True


@pytest.mark.asyncio
async def test_create_game_sets_opponents():
    p1 = make_user("p1")
    p2 = make_user("p2")
    p3 = make_user("p3")
    for name in ["p1", "p2", "p3"]:
        state.connections[name] = AsyncMock()

    with patch("game.game_logic.get_random_word", return_value="cat"):
        with patch("game.game_logic.asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.time.return_value = 1000.0
            await game_logic.create_game([p1, p2, p3], False)

    call_args = state.connections["p1"].send_json.call_args[0][0]
    assert call_args["me"] == "p1"
    assert sorted(call_args["opponent"]) == sorted(["p2", "p3"])


@pytest.mark.asyncio
async def test_create_game_solo():
    p1 = make_user("p1")
    state.connections["p1"] = AsyncMock()

    with patch("game.game_logic.get_random_word", return_value="cat"):
        with patch("game.game_logic.asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.time.return_value = 1000.0
            await game_logic.create_game([p1], False)

    call_args = state.connections["p1"].send_json.call_args[0][0]
    assert call_args["opponent"] == []


# ── handle_round_end ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_round_end_first_win_continues():
    p1 = make_user("p1")
    p2 = make_user("p2")
    game = make_game(players=["p1", "p2"])
    state.games[game.id] = game
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()

    with patch("game.game_logic.get_random_word", return_value="dog"):
        with patch("game.game_logic.asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.time.return_value = 500.0
            with patch("game.game_logic.cancel_timer"):
                await game_logic.handle_round_end(game, p1)

    assert game.round_wins["p1"] == 1
    assert game.scores["p1"] == 0
    assert game.scores["p2"] == 0


@pytest.mark.asyncio
async def test_handle_round_end_wins_best_of():
    p1 = make_user("p1")
    p2 = make_user("p2")
    game = make_game(players=["p1", "p2"])
    game.round_wins["p1"] = 1
    state.games[game.id] = game
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()

    with patch("game.game_logic.get_users_unsafe") as mock_get_users:
        mock_get_users.return_value = [p1, p2]
        with patch("game.game_logic.cancel_timer"):
            with patch("game.game_logic.cleanup_game"):
                with patch("game.game_logic.calculate_new_elo") as mock_elo:
                    mock_elo.return_value = (20, 520)
                    with patch("game.game_logic.update_user_elo"):
                        with patch("game.game_logic.send_end_game", new_callable=AsyncMock):
                            await game_logic.handle_round_end(game, p1)

    assert game.round_wins["p1"] == 2


@pytest.mark.asyncio
async def test_handle_round_end_solo_player():
    p1 = make_user("p1")
    game = make_game(players=["p1"])
    state.games[game.id] = game
    state.connections["p1"] = AsyncMock()

    with patch("game.game_logic.get_users_unsafe") as mock_get_users:
        mock_get_users.return_value = [p1]
        with patch("game.game_logic.cancel_timer"):
            with patch("game.game_logic.cleanup_game"):
                with patch("game.game_logic.send_end_game", new_callable=AsyncMock):
                    await game_logic.handle_round_end(game, p1)


# ── end_game ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_end_game_ranked():
    p1 = make_user("p1", elo=500)
    p2 = make_user("p2", elo=500)
    game = make_game(players=["p1", "p2"], is_ranked=True)
    state.games[game.id] = game
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()

    with patch("game.game_logic.get_users_unsafe", return_value=[p1, p2]):
        with patch("game.game_logic.calculate_new_elo") as mock_elo:
            mock_elo.side_effect = [(20, 520), (-20, 480)]
            with patch("game.game_logic.update_user_elo"):
                with patch("game.game_logic.cancel_timer"):
                    with patch("game.game_logic.cleanup_game"):
                        with patch("game.game_logic.send_end_game", new_callable=AsyncMock) as mock_send:
                            await game_logic.end_game(game, p1)

    assert mock_send.call_count == 2
    winner_call = mock_send.call_args_list[0]
    assert winner_call[0][1] == "winner"
    assert winner_call[0][2] == 20
    assert winner_call[0][3] == 520


@pytest.mark.asyncio
async def test_end_game_unranked():
    p1 = make_user("p1", elo=500)
    p2 = make_user("p2", elo=500)
    game = make_game(players=["p1", "p2"], is_ranked=False)
    state.games[game.id] = game
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()

    with patch("game.game_logic.get_users_unsafe", return_value=[p1, p2]):
        with patch("game.game_logic.cancel_timer"):
            with patch("game.game_logic.cleanup_game"):
                with patch("game.game_logic.send_end_game", new_callable=AsyncMock) as mock_send:
                    await game_logic.end_game(game, p1)

    assert mock_send.call_count == 2
    # Winner notification first (p1 is first in users list)
    winner_call = mock_send.call_args_list[0]
    assert winner_call[0][1] == "winner"
    assert winner_call[0][2] == 0
    # Loser notification second
    loser_call = mock_send.call_args_list[1]
    assert loser_call[0][1] == "looser"
    assert loser_call[0][2] == 0


@pytest.mark.asyncio
async def test_end_game_with_reason():
    p1 = make_user("p1", elo=500)
    p2 = make_user("p2", elo=500)
    game = make_game(players=["p1", "p2"], is_ranked=False)
    state.games[game.id] = game
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()

    with patch("game.game_logic.get_users_unsafe", return_value=[p1, p2]):
        with patch("game.game_logic.cancel_timer"):
            with patch("game.game_logic.cleanup_game"):
                with patch("game.game_logic.send_end_game", new_callable=AsyncMock) as mock_send:
                    await game_logic.end_game(game, p1, "opponent_surrendered")

    loser_call = mock_send.call_args_list[0]
    assert loser_call[0][4] == "opponent_surrendered"


# ── end_game_by_timeout ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_end_game_by_timeout_clear_winner():
    p1 = make_user("p1")
    p2 = make_user("p2")
    game = make_game(players=["p1", "p2"])
    game.scores["p1"] = 50.0
    game.scores["p2"] = 30.0
    state.games[game.id] = game
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()

    with patch("game.game_logic.get_users_unsafe", return_value=[p1, p2]):
        with patch("game.game_logic.cancel_timer"):
            with patch("game.game_logic.cleanup_game"):
                with patch("game.game_logic.send_end_game", new_callable=AsyncMock):
                    with patch("game.game_logic.calculate_new_elo", return_value=(20, 520)):
                        with patch("game.game_logic.update_user_elo"):
                            await game_logic.end_game_by_timeout(game.id)


@pytest.mark.asyncio
async def test_end_game_by_timeout_tie():
    p1 = make_user("p1")
    p2 = make_user("p2")
    game = make_game(players=["p1", "p2"])
    game.scores["p1"] = 40.0
    game.scores["p2"] = 40.0
    state.games[game.id] = game
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()

    with patch("game.game_logic.get_users_unsafe", return_value=[p1, p2]):
        with patch("game.game_logic.get_random_word", return_value="bird"):
            with patch("game.game_logic.asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value.time.return_value = 500.0
                with patch("game.game_logic.cancel_timer"):
                    await game_logic.end_game_by_timeout(game.id)

    p1_calls = state.connections["p1"].send_json.call_args_list
    assert p1_calls[0][0][0] == {"type": "round_tie"}
    assert p1_calls[1][0][0]["type"] == "next_round"


@pytest.mark.asyncio
async def test_end_game_by_timeout_solo():
    p1 = make_user("p1", elo=500)
    game = make_game(players=["p1"])
    game.scores["p1"] = 10.0
    state.games[game.id] = game
    state.connections["p1"] = AsyncMock()

    with patch("game.game_logic.get_users_unsafe", return_value=[p1]):
        with patch("game.game_logic.cancel_timer"):
            with patch("game.game_logic.cleanup_game"):
                with patch("game.game_logic.send_end_game", new_callable=AsyncMock) as mock_send:
                    await game_logic.end_game_by_timeout(game.id)

    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert call_args[0][1] == "draw"
    assert call_args[0][4] == "timeout"


# ── start_next_round ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_next_round_resets_scores():
    p1 = make_user("p1")
    p2 = make_user("p2")
    game = make_game(players=["p1", "p2"])
    game.scores["p1"] = 80.0
    game.scores["p2"] = 60.0
    game.ai_scores["p1"] = 40.0
    game.score_bonuses["p1"] = 40.0
    game.round_wins["p1"] = 1
    state.games[game.id] = game
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()

    with patch("game.game_logic.get_random_word", return_value="fish"):
        with patch("game.game_logic.asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.time.return_value = 500.0
            with patch("game.game_logic.cancel_timer"):
                await game_logic.start_next_round(game)

    assert game.scores["p1"] == 0
    assert game.scores["p2"] == 0
    assert game.ai_scores["p1"] == 0
    assert game.score_bonuses["p1"] == 0
    assert game.word == "fish"
    assert game.round_wins["p1"] == 1

    state.connections["p1"].send_json.assert_called_once()
    call_args = state.connections["p1"].send_json.call_args[0][0]
    assert call_args["type"] == "next_round"
    assert call_args["word"] == "fish"


# ── ai_guess ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ai_guess_updates_score():
    user = make_user("p1")
    ws = AsyncMock()
    game = make_game(players=["p1", "p2"])
    state.games[game.id] = game
    state.player_games["p1"] = game.id
    state.connections["p1"] = ws
    state.connections["p2"] = AsyncMock()

    with patch("game.game_logic.make_ai_guess") as mock_ai:
        mock_ai.return_value = {"cat": 75.0}
        with patch("game.game_logic.broadcast_player_score", new_callable=AsyncMock):
            await game_logic.ai_guess(user, {"strokes": []}, ws)

    assert game.ai_scores["p1"] == 75.0
    assert game.scores["p1"] == 75.0
    assert ws.send_json.call_count >= 1
    call_args = ws.send_json.call_args_list[0][0][0]
    assert call_args["type"] == "ai_guess"
    assert call_args["score"] == 75.0


@pytest.mark.asyncio
async def test_ai_guess_not_in_game():
    user = make_user("p1")
    ws = AsyncMock()
    with pytest.raises(ValueError, match="not part of any games"):
        await game_logic.ai_guess(user, {"strokes": []}, ws)


@pytest.mark.asyncio
async def test_ai_guess_score_capped_at_100():
    user = make_user("p1")
    ws = AsyncMock()
    game = make_game(players=["p1", "p2"])
    game.score_bonuses["p1"] = 30.0
    state.games[game.id] = game
    state.player_games["p1"] = game.id
    state.connections["p1"] = ws
    state.connections["p2"] = AsyncMock()
    state.game_timers[game.id] = MagicMock()

    with patch("game.game_logic.make_ai_guess") as mock_ai:
        mock_ai.return_value = {"cat": 80.0}
        with patch("game.game_logic.broadcast_player_score", new_callable=AsyncMock):
            with patch("game.game_logic.asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value.time.return_value = 500.0
                with patch("game.game_logic.get_random_word", return_value="dog"):
                    await game_logic.ai_guess(user, {"strokes": []}, ws)

    assert game.round_wins["p1"] == 1


@pytest.mark.asyncio
async def test_ai_guess_triggers_round_end_at_100():
    user = make_user("p1")
    ws = AsyncMock()
    p2 = make_user("p2")
    game = make_game(players=["p1", "p2"])
    state.games[game.id] = game
    state.player_games["p1"] = game.id
    state.connections["p1"] = ws
    state.connections["p2"] = AsyncMock()

    with patch("game.game_logic.make_ai_guess") as mock_ai:
        mock_ai.return_value = {"cat": 100.0}
        with patch("game.game_logic.get_random_word", return_value="dog"):
            with patch("game.game_logic.asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value.time.return_value = 500.0
                with patch("game.game_logic.cancel_timer"):
                    await game_logic.ai_guess(user, {"strokes": []}, ws)

    assert game.round_wins["p1"] == 1


# ── surrender_game ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_surrender_game():
    user = make_user("p1")
    winner = make_user("p2")
    game = make_game(players=["p1", "p2"])
    state.games[game.id] = game
    state.player_games["p1"] = game.id

    with patch("game.game_logic.get_user", return_value=winner):
        with patch("game.game_logic.get_users_unsafe", return_value=[user, winner]):
            with patch("game.game_logic.cancel_timer"):
                with patch("game.game_logic.cleanup_game"):
                    with patch("game.game_logic.send_end_game", new_callable=AsyncMock):
                        with patch("game.game_logic.calculate_new_elo", return_value=(0, 500)):
                            with patch("game.game_logic.update_user_elo"):
                                await game_logic.surrender_game(user)


@pytest.mark.asyncio
async def test_surrender_game_not_in_game():
    user = make_user("p1")
    with pytest.raises(ValueError, match="game doesnt exist"):
        await game_logic.surrender_game(user)


@pytest.mark.asyncio
async def test_surrender_game_solo_notifies_opponents():
    user = make_user("p1")
    game = make_game(players=["p1"])
    state.games[game.id] = game
    state.player_games["p1"] = game.id

    with patch("game.game_logic.send_msg_to_opponents", new_callable=AsyncMock) as mock_send:
        await game_logic.surrender_game(user)

    mock_send.assert_called_once()
    call_args = mock_send.call_args[0][2]
    assert call_args["type"] == "opponent_disconnected"


# ── broadcast_player_score ───────────────────────────────────────


@pytest.mark.asyncio
async def test_broadcast_player_score_excludes_self():
    game = make_game(players=["p1", "p2", "p3"])
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    ws3 = AsyncMock()
    state.connections["p1"] = ws1
    state.connections["p2"] = ws2
    state.connections["p3"] = ws3

    await game_logic.broadcast_player_score(game, "p1", 50.0)

    ws1.send_json.assert_not_called()
    ws2.send_json.assert_called_once()
    ws3.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_broadcast_player_score_include_self():
    game = make_game(players=["p1", "p2"])
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    state.connections["p1"] = ws1
    state.connections["p2"] = ws2

    await game_logic.broadcast_player_score(game, "p1", 75.0, include_self=True)

    ws1.send_json.assert_called_once()
    ws2.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_broadcast_player_score_with_guess():
    game = make_game(players=["p1", "p2"])
    ws2 = AsyncMock()
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = ws2

    guess = {"cat": 80.0, "dog": 2.0}
    await game_logic.broadcast_player_score(game, "p1", 80.0, guess=guess)

    call_args = ws2.send_json.call_args[0][0]
    assert call_args["guess"] == guess


# ── send_end_game ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_end_game():
    ws = AsyncMock()
    state.connections["p1"] = ws

    await game_logic.send_end_game("p1", "winner", 20, 520)

    ws.send_json.assert_called_once()
    call_args = ws.send_json.call_args[0][0]
    assert call_args["type"] == "end_game"
    assert call_args["status"] == "winner"
    assert call_args["elo_diff"] == 20
    assert call_args["new_elo"] == 520


@pytest.mark.asyncio
async def test_send_end_game_disconnected():
    await game_logic.send_end_game("no_one", "looser", -20, 480)


@pytest.mark.asyncio
async def test_send_end_game_with_reason():
    ws = AsyncMock()
    state.connections["p1"] = ws

    await game_logic.send_end_game("p1", "looser", -20, 480, "timeout")

    call_args = ws.send_json.call_args[0][0]
    assert call_args["reason"] == "timeout"


# ── increase_scores ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_increase_scores_increments_bonuses():
    p1 = make_user("p1")
    p2 = make_user("p2")
    game = make_game(players=["p1", "p2"])
    state.games[game.id] = game
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()

    with patch("game.game_logic.broadcast_player_score", new_callable=AsyncMock):
        await game_logic.increase_scores(game.id)

    assert game.score_bonuses["p1"] == 0.5
    assert game.score_bonuses["p2"] == 0.5
    assert game.scores["p1"] == 0.5
    assert game.scores["p2"] == 0.5


@pytest.mark.asyncio
async def test_increase_scores_triggers_round_end_at_100():
    p1 = make_user("p1")
    p2 = make_user("p2")
    game = make_game(players=["p1", "p2"])
    game.score_bonuses["p1"] = 99.5
    state.games[game.id] = game
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()
    state.player_games["p1"] = game.id

    with patch("game.game_logic.broadcast_player_score", new_callable=AsyncMock):
        with patch("game.game_logic.get_user", return_value=p1):
            with patch("game.game_logic.get_random_word", return_value="dog"):
                with patch("game.game_logic.asyncio.get_running_loop") as mock_loop:
                    mock_loop.return_value.time.return_value = 500.0
                    with patch("game.game_logic.cancel_timer"):
                        await game_logic.increase_scores(game.id)

    assert game.round_wins["p1"] == 1


# ── game_timer ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_game_timer_calls_increase_scores():
    game = make_game(game_id="gt1", players=["p1", "p2"])
    state.games["gt1"] = game
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()

    call_count = [0]

    async def fake_increase(gid):
        call_count[0] += 1
        if call_count[0] >= 2:
            raise asyncio.CancelledError()

    with patch("game.game_logic.increase_scores", side_effect=fake_increase):
        with patch("game.game_logic.ROUND_DURATION", 60):
            try:
                await game_logic.game_timer("gt1")
            except asyncio.CancelledError:
                pass

    assert call_count[0] >= 1


@pytest.mark.asyncio
async def test_game_timer_ends_by_timeout():
    game = make_game(game_id="gt2", players=["p1", "p2"])
    state.games["gt2"] = game
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()

    call_count = [0]

    async def fake_increase(gid):
        call_count[0] += 1

    async def fake_timeout(gid):
        call_count[0] = -1

    with patch("game.game_logic.increase_scores", side_effect=fake_increase):
        with patch("game.game_logic.end_game_by_timeout", side_effect=fake_timeout):
            with patch("game.game_logic.ROUND_DURATION", 1):
                await game_logic.game_timer("gt2")

    assert call_count[0] == -1


# ── start_game ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_game_missing_code():
    from fastapi import WebSocketException
    user = make_user("p1")
    with pytest.raises(WebSocketException):
        await game_logic.start_game({}, user)


@pytest.mark.asyncio
async def test_start_game_not_host():
    from fastapi import WebSocketException
    user = make_user("p2")
    state.lobbies["ABC123"] = {"host": "p1", "players": ["p1", "p2"]}
    with pytest.raises(WebSocketException, match="Only host"):
        await game_logic.start_game({"code": "ABC123"}, user)


@pytest.mark.asyncio
async def test_start_game_not_enough_players():
    from fastapi import WebSocketException
    user = make_user("p1")
    state.lobbies["ABC123"] = {"host": "p1", "players": ["p1"]}
    with pytest.raises(WebSocketException, match="Cannot start game alone"):
        await game_logic.start_game({"code": "ABC123"}, user)


@pytest.mark.asyncio
async def test_start_game_player_already_in_game():
    from fastapi import WebSocketException
    user = make_user("p1")
    state.lobbies["ABC123"] = {"host": "p1", "players": ["p1", "p2"]}
    state.player_games["p2"] = "existing_game"
    with pytest.raises(WebSocketException, match="already in other games"):
        await game_logic.start_game({"code": "ABC123"}, user)


@pytest.mark.asyncio
async def test_start_game_success():
    p1 = make_user("p1")
    p2 = make_user("p2")
    state.lobbies["ABC123"] = {"host": "p1", "players": ["p1", "p2"]}
    state.connections["p1"] = AsyncMock()
    state.connections["p2"] = AsyncMock()

    with patch("game.game_logic.create_game", new_callable=AsyncMock) as mock_create:
        with patch("game.game_logic.get_user") as mock_get:
            mock_get.side_effect = lambda name: make_user(name)
            await game_logic.start_game({"code": "ABC123"}, p1)

    mock_create.assert_called_once()
    players = mock_create.call_args[0][0]
    assert len(players) == 2
    assert players[0].username == "p1"
    assert not mock_create.call_args[0][1]
