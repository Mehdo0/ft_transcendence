import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from main import app
from state.config import SECRET_KEY, ALGORITHM
from services.services import create_access_token, get_user_from_ws_token

client = TestClient(app)


def _register(username: str, password: str, email: str):
    resp = client.post(
        "/api/register/",
        json={"username": username, "password": password, "email": email},
    )
    return resp


def _login(username: str, password: str):
    resp = client.post(
        "/api/token",
        data={"username": username, "password": password},
    )
    return resp


def _token(sub="modo", minutes=30):
    return create_access_token(
        data={"sub": sub}, expires_delta=timedelta(minutes=minutes)
    )


# ── JWT creation ────────────────────────────────────────────────


def test_create_access_token_produces_valid_jwt():
    token = _token("testuser")
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "testuser"
    assert "exp" in decoded


def test_create_access_token_with_custom_expiry():
    token = create_access_token(
        data={"sub": "testuser"}, expires_delta=timedelta(seconds=5)
    )
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "testuser"


# ── JWT validation ──────────────────────────────────────────────


def test_valid_token_decodes_correctly():
    token = _token("modo")
    user = get_user_from_ws_token(token)
    assert user.username == "modo"


def test_expired_token_rejected():
    token = create_access_token(
        data={"sub": "modo"}, expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(Exception):
        get_user_from_ws_token(token)


def test_tampered_token_rejected():
    token = _token("modo")
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(Exception):
        get_user_from_ws_token(tampered)


def test_wrong_algorithm_rejected():
    token = jwt.encode({"sub": "modo"}, SECRET_KEY, algorithm="HS512")
    with pytest.raises(Exception):
        get_user_from_ws_token(token)


def test_none_sub_rejected():
    token = jwt.encode({"sub": None, "exp": 9999999999}, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(Exception):
        get_user_from_ws_token(token)


def test_missing_sub_rejected():
    token = jwt.encode({"exp": 9999999999}, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(Exception):
        get_user_from_ws_token(token)


def test_nonexistent_user_rejected():
    token = _token("no_such_user_99999")
    with pytest.raises(Exception):
        get_user_from_ws_token(token)


def test_garbage_token_rejected():
    with pytest.raises(Exception):
        get_user_from_ws_token("not.a.token")


def test_empty_token_rejected():
    with pytest.raises(Exception):
        get_user_from_ws_token("")


def test_none_token_rejected():
    with pytest.raises(Exception):
        get_user_from_ws_token(None)


def test_different_secret_rejected():
    bad_token = jwt.encode({"sub": "modo"}, "wrong-secret-key", algorithm=ALGORITHM)
    with pytest.raises(Exception):
        get_user_from_ws_token(bad_token)


# ── OAuth2 login flow ───────────────────────────────────────────


def test_login_with_valid_credentials():
    resp = _register("t_auth_l1", "correctpass", "t_auth_l1@test.com")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    resp = _login("t_auth_l1", "correctpass")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_login_sets_http_only_cookie():
    resp = _register("t_auth_ck", "correctpass", "t_auth_ck@test.com")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    resp = _login("t_auth_ck", "correctpass")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    assert "set-cookie" in resp.headers
    cookie = resp.headers["set-cookie"].lower()
    assert "access_token=" in cookie
    assert "httponly" in cookie
    assert "samesite=strict" in cookie


def test_login_with_wrong_password():
    resp = _register("t_auth_wp", "correctpass", "t_auth_wp@test.com")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    resp = _login("t_auth_wp", "wrongpassword")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    assert resp.status_code == 401


def test_login_with_nonexistent_user():
    resp = _login("no_such_user_xyz", "whatever")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    assert resp.status_code == 401


def test_login_with_empty_password():
    resp = _register("t_auth_emp", "realpass", "t_auth_emp@test.com")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    resp = _login("t_auth_emp", "")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    assert resp.status_code == 401


def test_login_with_missing_username():
    resp = client.post("/api/token", data={"password": "whatever"})
    assert resp.status_code == 422


def test_login_with_missing_password():
    resp = client.post("/api/token", data={"username": "modo"})
    assert resp.status_code == 422


# ── Authenticated endpoints ─────────────────────────────────────


def test_get_users_me_with_valid_cookie():
    resp = _register("t_auth_me1", "pass123", "t_auth_me1@test.com")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    login_resp = _login("t_auth_me1", "pass123")
    if login_resp.status_code == 429:
        pytest.skip("Rate limited")
    cookie = login_resp.headers.get("set-cookie", "")
    resp = client.get("/api/users/me/", headers={"Cookie": cookie})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "t_auth_me1"


def test_get_users_me_without_cookie():
    resp = client.get("/api/users/me/")
    assert resp.status_code in (401, 403)


def test_get_users_me_with_invalid_cookie():
    resp = client.get(
        "/api/users/me/",
        headers={"Cookie": "access_token=invalid.token.here"},
    )
    assert resp.status_code in (401, 403)


def test_get_users_me_with_expired_token():
    token = create_access_token(
        data={"sub": "modo"}, expires_delta=timedelta(seconds=-1)
    )
    resp = client.get(
        "/api/users/me/",
        headers={"Cookie": f"access_token={token}"},
    )
    assert resp.status_code in (401, 403)


def test_get_users_me_with_tampered_token():
    token = _token("modo")
    tampered = token[:-5] + "AAAAA"
    resp = client.get(
        "/api/users/me/",
        headers={"Cookie": f"access_token={tampered}"},
    )
    assert resp.status_code in (401, 403)


# ── Registration flow ───────────────────────────────────────────


def test_register_creates_user_and_sets_cookie():
    resp = _register("t_auth_r1", "pass123", "t_auth_r1@test.com")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_created"] == "t_auth_r1"
    assert "set-cookie" in resp.headers
    cookie = resp.headers["set-cookie"].lower()
    assert "access_token=" in cookie
    assert "httponly" in cookie


def test_register_sets_secure_cookie():
    resp = _register("t_auth_r2", "pass123", "t_auth_r2@test.com")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    cookie = resp.headers.get("set-cookie", "")
    assert "samesite=strict" in cookie.lower()


def test_register_duplicate_username():
    resp1 = _register("t_auth_dup", "pass123", "t_auth_dup1@test.com")
    if resp1.status_code == 429:
        pytest.skip("Rate limited")
    resp = _register("t_auth_dup", "pass456", "t_auth_dup2@test.com")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    assert resp.status_code == 409


def test_register_duplicate_email():
    resp1 = _register("t_auth_d2a", "pass123", "t_auth_d3@test.com")
    if resp1.status_code == 429:
        pytest.skip("Rate limited")
    resp = _register("t_auth_d2b", "pass456", "t_auth_d3@test.com")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    assert resp.status_code == 409


def test_register_invalid_email():
    resp = _register("t_auth_bm", "pass123", "not-an-email")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    assert resp.status_code == 422


# ── Logout ──────────────────────────────────────────────────────


def test_logout_deletes_cookie():
    resp = client.post("/api/logout")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    cookie = resp.headers.get("set-cookie", "")
    assert "access_token=" in cookie
    assert "max-age=0" in cookie.lower() or "expires=" in cookie.lower()


# ── User stats endpoint (no auth required) ──────────────────────


def test_get_user_stats_existing():
    resp = client.get("/api/users/modo/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "modo"
    assert "Elo" in data


def test_get_user_stats_nonexistent():
    resp = client.get("/api/users/no_such_user_999/stats")
    assert resp.status_code == 404


def test_get_ranking():
    resp = client.get("/api/get_ranking")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ── Token in Authorization header (should fail — cookie only) ───


def test_users_me_rejects_bearer_header():
    token = _token("t_auth_bearer")
    resp = client.get(
        "/api/users/me/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code in (401, 403)
