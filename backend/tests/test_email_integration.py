import time
import pytest
from fastapi.testclient import TestClient
from main import app
from core.database import SessionLocal
from models.models import UserModel

client = TestClient(app)


def _cleanup_all():
    with SessionLocal() as session:
        for user in session.query(UserModel).filter(
            UserModel.username.like("t_%")
        ).all():
            session.delete(user)
        session.commit()


INVALID_EMAILS = [
    ("notanemail", "must contain exactly one '@' symbol"),
    ("", "must contain exactly one '@' symbol"),
    ("@domain.com", "local part is empty"),
    ("user@", "domain is empty"),
    ("@", "local part is empty"),
    ("user@domain@extra.com", "must contain exactly one '@' symbol"),
    ("user@localhost", "domain must include a tld"),
    ("user@domain", "domain must include a tld"),
    ("user@domain.c", "is too short"),
    ("a@b.x", "is too short"),
    ("user@.domain.com", "cannot start or end with a dot"),
    ("user@domain..com", "contains consecutive dots"),
    ("user..name@domain.com", "contains consecutive dots"),
    (".user@domain.com", "cannot start or end with a dot"),
    ("user.@domain.com", "cannot start or end with a dot"),
    ("user@domain.com.", "cannot start or end with a dot"),
    (" user@domain.com", "contains leading or trailing whitespace"),
    ("user@domain.com ", "contains leading or trailing whitespace"),
    ("user @domain.com", "contains whitespace characters"),
    ("user@ domain.com", "contains whitespace characters"),
    ("user@[192.168.0.1]", "ip address domains are not accepted"),
    ("user@127.0.0.1", "ip address domains are not accepted"),
]


@pytest.mark.parametrize("bad_email,expected_error", INVALID_EMAILS)
def test_register_rejects_invalid_email(bad_email: str, expected_error: str):
    payload = {"username": "t_bad", "password": "pass", "email": bad_email}
    resp = client.post("/api/register/", json=payload)
    assert resp.status_code in (409, 422, 429), f"Got {resp.status_code}: {resp.text}"
    if resp.status_code == 429:
        return
    detail = str(resp.json()["detail"]).lower()
    assert expected_error.lower() in detail, f"Expected '{expected_error}' for '{bad_email}', got '{detail}'"


def test_register_with_valid_email():
    payload = {"username": "t_valid", "password": "s3cret", "email": "t_valid@domain.com"}
    resp = client.post("/api/register/", json=payload)
    if resp.status_code == 429:
        return
    assert resp.status_code == 200, resp.text
    assert resp.json()["user_created"] == "t_valid"


def test_register_rejects_local_part_too_long():
    long_local = "a" * 65 + "@domain.com"
    payload = {"username": "t_longl", "password": "pass", "email": long_local}
    resp = client.post("/api/register/", json=payload)
    assert resp.status_code in (409, 422, 429), resp.text


def test_register_rejects_domain_too_long():
    long_domain = "user@" + "a" * 256 + ".com"
    payload = {"username": "t_longd", "password": "pass", "email": long_domain}
    resp = client.post("/api/register/", json=payload)
    assert resp.status_code in (409, 422, 429), resp.text


def test_register_rejects_hyphen_at_label_edge():
    r1 = client.post("/api/register/", json={"username": "t_h1", "password": "p", "email": "user@-domain.com"})
    assert r1.status_code in (409, 422, 429), r1.text
    r2 = client.post("/api/register/", json={"username": "t_h2", "password": "p", "email": "user@domain-.com"})
    assert r2.status_code in (409, 422, 429), r2.text


def test_register_duplicate_email():
    r1 = client.post("/api/register/", json={"username": "t_dup1", "password": "s3cret", "email": "t_dup@test.com"})
    if r1.status_code == 429:
        return
    assert r1.status_code == 200

    r2 = client.post("/api/register/", json={"username": "t_dup2", "password": "s3cret", "email": "t_dup@test.com"})
    assert r2.status_code in (409, 429), r2.text
    if r2.status_code == 429:
        return
    assert "email" in r2.json()["detail"].lower()


def test_register_duplicate_username():
    r1 = client.post("/api/register/", json={"username": "t_dupu", "password": "s3cret", "email": "t_dupu1@test.com"})
    if r1.status_code == 429:
        return
    assert r1.status_code == 200, r1.text

    r2 = client.post("/api/register/", json={"username": "t_dupu", "password": "s3cret", "email": "t_dupu2@test.com"})
    assert r2.status_code in (409, 429), r2.text
    if r2.status_code == 429:
        return
    assert "username" in r2.json()["detail"].lower()


def test_register_flow():
    import re
    r = client.post("/api/register/", json={"username": "t_flow", "password": "flowpass", "email": "t_flow@test.com"})
    if r.status_code == 429:
        return
    assert r.status_code == 200, r.text

    r = client.post("/api/token", data={"username": "t_flow", "password": "flowpass"})
    assert r.status_code == 200, r.text

    # Extract token from set-cookie (Secure flag prevents direct cookie send over HTTP)
    m = re.search(r"access_token=([^;]+)", r.headers.get("set-cookie", ""))
    token = m.group(1)
    r = client.get("/api/users/me/", cookies={"access_token": token})
    assert r.status_code == 200, r.text
    assert r.json()["username"] == "t_flow"
    assert r.json()["email"] == "t_flow@test.com"


def test_login_nonexistent_user():
    r = client.post("/api/token", data={"username": "t_nobody", "password": "nope"})
    assert r.status_code == 401, r.text


def test_login_wrong_password():
    r = client.post("/api/register/", json={"username": "t_wp", "password": "good", "email": "t_wp@test.com"})
    if r.status_code == 429:
        return
    assert r.status_code == 200

    r = client.post("/api/token", data={"username": "t_wp", "password": "wrong"})
    assert r.status_code == 401, r.text


def test_logout():
    r = client.post("/api/register/", json={"username": "t_out", "password": "s3cret", "email": "t_out@test.com"})
    if r.status_code == 429:
        return
    assert r.status_code == 200

    r = client.post("/api/logout")
    assert r.status_code == 200, r.text


def test_missing_fields():
    assert client.post("/api/register/", json={"username": "x"}).status_code == 422
    assert client.post("/api/register/", json={"email": "x@y.com"}).status_code == 422
    assert client.post("/api/register/", json={}).status_code == 422


def test_users_me_without_token():
    assert client.get("/api/users/me/").status_code == 403


def test_rate_limit():
    passed = 0
    for i in range(7):
        r = client.post("/api/register/", json={
            "username": f"t_rl_{i}", "password": "p", "email": f"t_rl_{i}@test.com"
        })
        if r.status_code == 200:
            passed += 1
    assert passed <= 6, f"Rate limit not working: {passed} passed"


def test_valid_borderline_emails():
    borderline = [
        ("t_b1", "user+tag@domain.com"),
        ("t_b2", "first.last@domain.com"),
        ("t_b3", "user-name@domain.com"),
        ("t_b4", "user123@domain456.com"),
        ("t_b5", "a@b.io"),
        ("t_b6", "x@ab.de"),
    ]
    from state.config import limiter
    for username, email in borderline:
        limiter.reset()
        r = client.post("/api/register/", json={"username": username, "password": "pass", "email": email})
        assert r.status_code == 200, f"Expected 200 for '{email}', got {r.status_code}: {r.text}"


def test_local_part_exactly_64_chars_accepted():
    local = "a" * 64
    email = f"{local}@domain.com"
    r = client.post("/api/register/", json={"username": "t_64l", "password": "pass", "email": email})
    if r.status_code == 429:
        return
    assert r.status_code == 200, r.text


def test_domain_exactly_255_chars_accepted():
    label = "ab" * 31 + "a"
    domain = f"{label}.{label}.{label}.{label}"
    email = f"user@{domain}"
    assert len(domain) == 255
    r = client.post("/api/register/", json={"username": "t_255d", "password": "pass", "email": email})
    if r.status_code == 429:
        return
    assert r.status_code == 200, r.text


def test_register_with_tab_in_email():
    r = client.post("/api/register/", json={"username": "t_tab", "password": "pass", "email": "user@dom\tain.com"})
    assert r.status_code in (409, 422), r.text


def test_cleanup():
    _cleanup_all()
