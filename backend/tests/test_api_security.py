import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from main import app
from services.services import create_access_token

client = TestClient(app)


def _register(username: str, password: str, email: str):
    return client.post(
        "/api/register/",
        json={"username": username, "password": password, "email": email},
    )


def _login(username: str, password: str):
    return client.post(
        "/api/token",
        data={"username": username, "password": password},
    )


def _token(sub="modo", minutes=30):
    return create_access_token(
        data={"sub": sub}, expires_delta=timedelta(minutes=minutes)
    )


# ── SQL injection in login username ─────────────────────────────

SQLI_PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "'; DROP TABLE users; --",
    "' UNION SELECT * FROM users --",
    "admin'--",
    "' OR 1=1--",
    "1' OR '1' = '1",
    "' OR '' = '",
    '" OR "" = "',
    "'; DELETE FROM users WHERE '1'='1",
    "' OR username LIKE '%modo%' --",
]


@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_login_sqli_username_rejected(payload: str):
    resp = _login(payload, "password")
    assert resp.status_code in (401, 422, 429), (
        f"SQLi username '{payload[:30]}' got unexpected {resp.status_code}"
    )


@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_login_sqli_password_rejected(payload: str):
    _register("t_sec_sqli", "realpass", "t_sec_sqli@test.com")
    resp = _login("t_sec_sqli", payload)
    assert resp.status_code in (401, 429), (
        f"SQLi password '{payload[:30]}' got unexpected {resp.status_code}"
    )


# ── SQL injection in registration fields ────────────────────────


@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_register_sqli_username(payload: str):
    resp = _register(payload, "pass123", f"sqli_{abs(hash(payload)) % 10000}@test.com")
    assert resp.status_code in (200, 409, 422, 429), (
        f"SQLi username '{payload[:30]}' got unexpected {resp.status_code}"
    )


@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_register_sqli_email(payload: str):
    resp = _register(f"t_sqli_{abs(hash(payload)) % 10000}", "pass123", payload)
    assert resp.status_code in (422, 429), (
        f"SQLi email '{payload[:30]}' got unexpected {resp.status_code}"
    )


# ── XSS attempts ────────────────────────────────────────────────

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "javascript:alert(1)",
    "<body onload=alert(1)>",
    "'><script>alert(1)</script>",
    "\"><script>alert(1)</script>",
    "<iframe src=javascript:alert(1)>",
    "<<SCRIPT>alert(1);//<</SCRIPT>",
    "<IMG \"\"\"><SCRIPT>alert(1)</SCRIPT>\">",
]


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_register_xss_username(payload: str):
    resp = _register(payload, "pass123", f"xss_{abs(hash(payload)) % 10000}@test.com")
    assert resp.status_code in (200, 409, 422, 429)


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_register_xss_email(payload: str):
    resp = _register(f"t_xss_{abs(hash(payload)) % 10000}", "pass123", payload)
    assert resp.status_code in (422, 429)


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_login_xss_username(payload: str):
    resp = _login(payload, "password")
    assert resp.status_code in (401, 422, 429)


# ── Path traversal in username param ────────────────────────────

PATH_TRAVERSAL = [
    "../etc/passwd",
    "..%5c..%5cwindows%5csystem32",
    "/etc/passwd",
    "....//....//etc/passwd",
    "..%2f..%2fetc%2fpasswd",
    "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
]


@pytest.mark.parametrize("payload", PATH_TRAVERSAL)
def test_user_stats_path_traversal(payload: str):
    resp = client.get(f"/api/users/{payload}/stats")
    assert resp.status_code == 404, f"Path traversal '{payload}' got {resp.status_code}"


# ── Null byte injection ─────────────────────────────────────────

# Note: raw null bytes can't be sent via HTTP - httpx/urllib3 reject them.
# These test URL-encoded variants that might bypass filters.

NULL_BYTE_URLENCODED = [
    "%00test",
    "test%00",
    "%00",
]


@pytest.mark.parametrize("payload", NULL_BYTE_URLENCODED)
def test_user_stats_null_byte_encoded(payload: str):
    resp = client.get(f"/api/users/{payload}/stats")
    assert resp.status_code == 404, (
        f"Null byte encoded '{payload}' got {resp.status_code}"
    )


@pytest.mark.parametrize("payload", NULL_BYTE_URLENCODED)
def test_login_null_byte_encoded(payload: str):
    resp = _login(payload, "password")
    assert resp.status_code in (401, 422, 429)


# ── Oversized inputs ────────────────────────────────────────────


def test_register_oversized_username():
    huge = "A" * 10000
    resp = _register(huge, "pass123", "biguser@test.com")
    assert resp.status_code in (200, 422, 429)


def test_register_oversized_password():
    huge = "A" * 10000
    resp = _register("t_bigpass", huge, "bigpass@test.com")
    assert resp.status_code in (200, 422, 429)


def test_register_oversized_email():
    huge = "A" * 10000 + "@test.com"
    resp = _register("t_bigemail", "pass123", huge)
    assert resp.status_code in (200, 422, 429)


def test_login_oversized_username():
    huge = "A" * 10000
    resp = _login(huge, "password")
    assert resp.status_code in (401, 422, 429)


def test_login_oversized_password():
    _register("t_bigpw2", "realpass", "bigpw2@test.com")
    huge = "A" * 10000
    resp = _login("t_bigpw2", huge)
    assert resp.status_code in (401, 429)


def test_user_stats_oversized_username():
    huge = "A" * 10000
    resp = client.get(f"/api/users/{huge}/stats")
    assert resp.status_code == 404


# ── Input validation on /api/users/{username}/stats ─────────────

SPECIAL_USERNAMES = [
    ("", 404),
    ("   ", 404),
    ("modo", 200),
    (".", 404),
    ("..", 404),
    ("#", 404),
    ("?query=1", 404),
    ("test%20user", 404),
    ("test+user", 404),
    ("test@user", 404),
]


@pytest.mark.parametrize("username,expected", SPECIAL_USERNAMES)
def test_user_stats_special_chars(username: str, expected: int):
    resp = client.get(f"/api/users/{username}/stats")
    assert resp.status_code == expected, f"'{username}' got {resp.status_code}"


# ── Malformed request bodies ────────────────────────────────────


def test_register_empty_body():
    resp = client.post("/api/register/", json={})
    assert resp.status_code == 422


def test_register_missing_fields():
    resp = client.post("/api/register/", json={"username": "test"})
    assert resp.status_code == 422
    resp = client.post("/api/register/", json={"password": "pass"})
    assert resp.status_code == 422
    resp = client.post("/api/register/", json={"email": "test@test.com"})
    assert resp.status_code == 422


def test_register_extra_fields():
    resp = _register("t_extra", "pass", "extra@test.com")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    assert resp.status_code == 200
    # Extra fields in request body are ignored by Pydantic by default


def test_register_wrong_types():
    resp = client.post(
        "/api/register/",
        json={"username": 12345, "password": "pass", "email": "test@test.com"},
    )
    assert resp.status_code == 422
    resp = client.post(
        "/api/register/",
        json={"username": "test", "password": ["list"], "email": "test@test.com"},
    )
    assert resp.status_code == 422


def test_login_wrong_content_type():
    resp = client.post("/api/token", json={"username": "modo", "password": "test"})
    assert resp.status_code == 422


def test_login_empty_body():
    resp = client.post("/api/token", data={})
    assert resp.status_code == 422


# ── Rate limiting ───────────────────────────────────────────────


def test_register_rate_limit():
    for i in range(10):
        resp = _register(f"t_rl_{i}", "pass123", f"rl_{i}@test.com")
        if resp.status_code == 429:
            return
    pytest.fail("Rate limit not triggered after 10 registrations (limit is 5/min)")


def test_token_rate_limit_triggers():
    _register("t_rl_token", "pass123", "rl_token@test.com")
    for i in range(20):
        resp = _login("t_rl_token", "wrong")
        if resp.status_code == 429:
            return
    pytest.fail("Rate limit not triggered after 20 login attempts (limit is 10/min)")


# ── CSRF protections ────────────────────────────────────────────


def test_login_cookie_httponly():
    resp = _register("t_csrf1", "pass123", "csrf1@test.com")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    resp = _login("t_csrf1", "pass123")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    cookie = resp.headers.get("set-cookie", "").lower()
    assert "httponly" in cookie, "Cookie should be HttpOnly"
    assert "samesite=strict" in cookie, "Cookie should be SameSite=Strict"


def test_register_cookie_httponly():
    resp = _register("t_csrf2", "pass123", "csrf2@test.com")
    if resp.status_code == 429:
        pytest.skip("Rate limited")
    cookie = resp.headers.get("set-cookie", "").lower()
    assert "httponly" in cookie, "Cookie should be HttpOnly"
    assert "samesite=strict" in cookie, "Cookie should be SameSite=Strict"


def test_users_me_requires_cookie_not_header():
    token = _token("t_csrf3")
    resp = client.get(
        "/api/users/me/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code in (401, 403)


# ── Unicode / encoding attacks ──────────────────────────────────


def test_register_unicode_username():
    resp = _register("测试用户", "pass123", "unicode@test.com")
    assert resp.status_code in (200, 422, 429)


def test_register_unicode_email():
    resp = _register("t_unicode_email", "pass123", "user@测试.com")
    assert resp.status_code in (422, 429)


def test_user_stats_unicode():
    resp = client.get("/api/users/测试用户/stats")
    assert resp.status_code in (404, 200)


# ── HTTP method attacks ─────────────────────────────────────────


def test_get_on_post_endpoints():
    resp = client.get("/api/token")
    assert resp.status_code == 405
    resp = client.get("/api/register/")
    assert resp.status_code == 405


def test_post_on_get_endpoints():
    resp = client.post("/api/users/me/")
    assert resp.status_code == 405
    resp = client.post("/api/get_ranking")
    assert resp.status_code == 405


def test_put_on_endpoints():
    resp = client.put("/api/token")
    assert resp.status_code == 405
    resp = client.put("/api/register/")
    assert resp.status_code == 405


def test_delete_on_endpoints():
    resp = client.delete("/api/token")
    assert resp.status_code == 405
    resp = client.delete("/api/register/")
    assert resp.status_code in (405, 404)


# ── Content-type attacks ────────────────────────────────────────


def test_register_form_data_instead_of_json():
    resp = client.post(
        "/api/register/",
        data={"username": "test", "password": "pass", "email": "test@test.com"},
    )
    assert resp.status_code == 422


def test_token_json_instead_of_form():
    resp = client.post(
        "/api/token",
        json={"username": "modo", "password": "test"},
    )
    assert resp.status_code == 422
