import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from schemas.data import Game, GameState, User
import state.state as state
from utils.utils import (
    calculate_new_elo,
    cleanup_game,
    disconnect,
    remove_from_matchmaking,
    cancel_timer,
    send_msg_to_opponents,
    send_msg_to_players,
)
from utils.getters import get_total_score, get_opponents, get_users_unsafe, get_random_word


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


# ── calculate_new_elo ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_elo_equal_players_win():
    p1 = make_user("a", elo=500)
    p2 = make_user("b", elo=500)
    diff, new_elo = await calculate_new_elo(p1, p2, 1)
    assert diff == 15
    assert new_elo == 515


@pytest.mark.asyncio
async def test_elo_equal_players_loss():
    p1 = make_user("a", elo=500)
    p2 = make_user("b", elo=500)
    diff, new_elo = await calculate_new_elo(p1, p2, 0)
    assert diff == -15
    assert new_elo == 485


@pytest.mark.asyncio
async def test_elo_underdog_wins():
    p1 = make_user("low", elo=300)
    p2 = make_user("high", elo=700)
    diff, new_elo = await calculate_new_elo(p1, p2, 1)
    assert diff > 20
    assert new_elo > 300


@pytest.mark.asyncio
async def test_elo_favorite_wins_small_gain():
    p1 = make_user("high", elo=700)
    p2 = make_user("low", elo=300)
    diff, new_elo = await calculate_new_elo(p1, p2, 1)
    assert 0 < diff < 20
    assert 700 < new_elo < 720


@pytest.mark.asyncio
async def test_elo_favorite_loses_big_loss():
    p1 = make_user("high", elo=700)
    p2 = make_user("low", elo=300)
    diff, new_elo = await calculate_new_elo(p1, p2, 0)
    assert diff < -20
    assert new_elo < 700


@pytest.mark.asyncio
async def test_elo_extreme_elo_difference():
    p1 = make_user("pro", elo=2000)
    p2 = make_user("newb", elo=100)
    diff_win, new_elo_win = await calculate_new_elo(p1, p2, 1)
    diff_loss, new_elo_loss = await calculate_new_elo(p1, p2, 0)
    assert 0 <= diff_win <= 3
    assert diff_loss <= -15


@pytest.mark.asyncio
async def test_elo_coefficient_at_boundaries():
    p1 = make_user("a", elo=0)
    p2 = make_user("b", elo=0)
    diff, new_elo = await calculate_new_elo(p1, p2, 1)
    average = (0 + 0) / 2
    coeff = 40 - round(average / 50)
    assert coeff == 40
    assert diff == 20


@pytest.mark.asyncio
async def test_elo_symmetry():
    p1 = make_user("a", elo=600)
    p2 = make_user("b", elo=400)
    diff_a, new_a = await calculate_new_elo(p1, p2, 1)
    diff_b, new_b = await calculate_new_elo(p2, p1, 0)
    assert diff_a + diff_b == 0
    assert (new_a - 600) + (new_b - 400) == 0


@pytest.mark.asyncio
async def test_elo_result_is_draw():
    p1 = make_user("a", elo=500)
    p2 = make_user("b", elo=500)
    diff, new_elo = await calculate_new_elo(p1, p2, 0.5)
    assert diff == 0
    assert new_elo == 500


@pytest.mark.asyncio
async def test_elo_zero_elo_players():
    p1 = make_user("a", elo=0)
    p2 = make_user("b", elo=1000)
    diff, new_elo = await calculate_new_elo(p1, p2, 1)
    assert diff > 0
    assert new_elo > 0


@pytest.mark.asyncio
async def test_elo_new_elo_never_negative():
    p1 = make_user("a", elo=0)
    p2 = make_user("b", elo=3000)
    diff, new_elo = await calculate_new_elo(p1, p2, 0)
    assert new_elo >= 0


# ── get_total_score ───────────────────────────────────────────────


def test_get_total_score_zero():
    game = make_game()
    assert get_total_score(game, "p1") == 0


def test_get_total_score_with_ai():
    game = make_game()
    game.ai_scores["p1"] = 45.0
    assert get_total_score(game, "p1") == 45.0


def test_get_total_score_with_bonus():
    game = make_game()
    game.score_bonuses["p1"] = 10.0
    assert get_total_score(game, "p1") == 10.0


def test_get_total_score_combined():
    game = make_game()
    game.ai_scores["p1"] = 30.0
    game.score_bonuses["p1"] = 25.0
    assert get_total_score(game, "p1") == 55.0


def test_get_total_score_capped_at_100():
    game = make_game()
    game.ai_scores["p1"] = 60.0
    game.score_bonuses["p1"] = 50.0
    assert get_total_score(game, "p1") == 100.0


def test_get_total_score_exactly_100():
    game = make_game()
    game.ai_scores["p1"] = 0.0
    game.score_bonuses["p1"] = 100.0
    assert get_total_score(game, "p1") == 100.0


def test_get_total_score_missing_player_defaults_zero():
    game = make_game(players=["p1"])
    assert get_total_score(game, "p1") == 0


# ── get_opponents ─────────────────────────────────────────────────


def test_get_opponents_two_players():
    user = make_user("p1")
    game = make_game(players=["p1", "p2"])
    state.games[game.id] = game
    opponents = get_opponents(user, game)
    assert opponents == ["p2"]


def test_get_opponents_four_players():
    user = make_user("p2")
    game = make_game(players=["p1", "p2", "p3", "p4"])
    state.games[game.id] = game
    opponents = get_opponents(user, game)
    assert "p2" not in opponents
    assert len(opponents) == 3


def test_get_opponents_solo():
    user = make_user("p1")
    game = make_game(players=["p1"])
    state.games[game.id] = game
    opponents = get_opponents(user, game)
    assert opponents == []


# ── cleanup_game ──────────────────────────────────────────────────


def test_cleanup_game_removes_from_state():
    game = make_game(game_id="g_cleanup", players=["p1", "p2"])
    state.games["g_cleanup"] = game
    state.player_games["p1"] = "g_cleanup"
    state.player_games["p2"] = "g_cleanup"
    state.disconnected_players.append("p1")
    state.disconnected_players.append("p2")

    cleanup_game(game)

    assert "g_cleanup" not in state.games
    assert "p1" not in state.player_games
    assert "p2" not in state.player_games
    assert "p1" not in state.disconnected_players
    assert "p2" not in state.disconnected_players


# ── disconnect ────────────────────────────────────────────────────


def test_disconnect_removes_from_state():
    user = make_user("p1")
    state.connections["p1"] = MagicMock()
    state.player_games["p1"] = "g1"
    state.matchmaking_queue.append("p1")

    disconnect(user)

    assert "p1" not in state.connections
    assert "p1" not in state.player_games
    assert "p1" not in state.matchmaking_queue


def test_disconnect_not_in_state_no_error():
    user = make_user("absent")
    disconnect(user)


# ── remove_from_matchmaking ───────────────────────────────────────


def test_remove_from_matchmaking_present():
    state.matchmaking_queue.append("p1")
    remove_from_matchmaking("p1")
    assert "p1" not in state.matchmaking_queue


def test_remove_from_matchmaking_absent():
    remove_from_matchmaking("no_one")
    assert "no_one" not in state.matchmaking_queue


# ── cancel_timer ──────────────────────────────────────────────────


def test_cancel_timer_cancels_task():
    mock_task = MagicMock()
    state.game_timers["g1"] = mock_task
    cancel_timer("g1")
    mock_task.cancel.assert_called_once()
    assert "g1" not in state.game_timers


def test_cancel_timer_nonexistent_raises():
    with pytest.raises(AttributeError):
        cancel_timer("no_such_timer")


# ── send_msg_to_opponents ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_msg_to_opponents():
    user = make_user("p1")
    game = make_game(players=["p1", "p2", "p3"])
    ws2 = AsyncMock()
    ws3 = AsyncMock()
    state.connections["p2"] = ws2
    state.connections["p3"] = ws3

    msg = {"type": "test", "data": "hello"}
    await send_msg_to_opponents(game, user, msg)

    ws2.send_json.assert_called_once_with(msg)
    ws3.send_json.assert_called_once_with(msg)


# ── send_msg_to_players ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_msg_to_players():
    game = make_game(players=["p1", "p2"])
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    state.connections["p1"] = ws1
    state.connections["p2"] = ws2

    msg = {"type": "broadcast"}
    await send_msg_to_players(game, msg)

    ws1.send_json.assert_called_once_with(msg)
    ws2.send_json.assert_called_once_with(msg)


# ── get_random_word ───────────────────────────────────────────────


def test_get_random_word_returns_string():
    word = get_random_word()
    assert isinstance(word, str)
    assert len(word) > 0


def test_get_random_word_from_list():
    from services.ai_service import load_word_list
    word_list = load_word_list()
    word = get_random_word()
    assert word in word_list


# ── get_users_unsafe ──────────────────────────────────────────────


def test_get_users_unsafe_single():
    with patch("utils.getters.get_user") as mock_get:
        mock_get.return_value = make_user("p1")
        users = get_users_unsafe(["p1"])
        assert len(users) == 1
        assert users[0].username == "p1"


def test_get_users_unsafe_multiple():
    with patch("utils.getters.get_user") as mock_get:
        mock_get.side_effect = lambda name: make_user(name)
        users = get_users_unsafe(["p1", "p2", "p3"])
        assert len(users) == 3


def test_get_users_unsafe_empty_asserts():
    with pytest.raises(AssertionError):
        get_users_unsafe([])
