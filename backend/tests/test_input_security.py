import pytest
from fastapi.testclient import TestClient
from main import app
from core.database import SessionLocal
from models.models import UserModel

client = TestClient(app)


def _cleanup():
    with SessionLocal() as s:
        for u in s.query(UserModel).filter(UserModel.username.like("sec_%")).all():
            s.delete(u)
        s.commit()


def test_sql_injection_username_register():
    payloads = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "admin'--",
        "1' UNION SELECT * FROM users--",
        "'; SELECT * FROM users WHERE ''='",
    ]
    for username in payloads:
        r = client.post("/api/register/", json={
            "username": username, "password": "pass", "email": "sec_sqli@test.com"
        })
        assert r.status_code in (200, 409, 422, 429), (
            f"SQLi username '{username}' caused {r.status_code}: {r.text}"
        )
        _cleanup()


def test_sql_injection_email_register():
    payloads = [
        "'; DROP TABLE users; --@x.com",
        "' OR '1'='1'@x.com",
    ]
    for email in payloads:
        r = client.post("/api/register/", json={
            "username": "sec_sqli_em", "password": "pass", "email": email
        })
        assert r.status_code in (409, 422, 429), (
            f"SQLi email '{email}' caused {r.status_code}: {r.text}"
        )
        _cleanup()


def test_null_byte_injection():
    payloads = [
        ("username", "sec_null\0user"),
        ("email", "null\0@domain.com"),
        ("password", "pass\0word"),
    ]
    for field, value in payloads:
        body = {"username": "sec_null", "password": "pass", "email": "sec_null@test.com"}
        body[field] = value
        r = client.post("/api/register/", json=body)
        assert r.status_code in (200, 409, 422, 429), (
            f"Null byte in {field}: {r.status_code}"
        )
        _cleanup()


def test_oversized_username():
    username = "a" * 1000
    r = client.post("/api/register/", json={
        "username": username, "password": "pass", "email": "sec_big@test.com"
    })
    assert r.status_code in (200, 409, 422, 429), f"Oversized username: {r.status_code}"


def test_oversized_password():
    password = "a" * 5000
    r = client.post("/api/register/", json={
        "username": "sec_bigpw", "password": password, "email": "sec_bigpw@test.com"
    })
    assert r.status_code in (200, 409, 422, 429), f"Oversized password: {r.status_code}"
    _cleanup()


def test_empty_username():
    r = client.post("/api/register/", json={"username": "", "password": "pass", "email": "x@y.com"})
    assert r.status_code in (422, 429), r.text


def test_empty_password():
    r = client.post("/api/register/", json={"username": "sec_empty", "password": "", "email": "x@y.com"})
    assert r.status_code in (422, 429), r.text


def test_special_chars_username():
    valid = ["sec_under_score", "sec-dash", "sec.dot"]
    for username in valid:
        r = client.post("/api/register/", json={
            "username": username, "password": "pass", "email": f"{username}@test.com"
        })
        assert r.status_code in (200, 409, 429), (
            f"Special char username '{username}': {r.status_code}"
        )
        _cleanup()


def test_unicode_username():
    r = client.post("/api/register/", json={
        "username": "séc_ünïcødé", "password": "pass", "email": "sec_uni@test.com"
    })
    assert r.status_code in (200, 409, 429), f"Unicode username: {r.status_code}"
    _cleanup()


def test_xss_in_username():
    xss_payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(1)",
    ]
    for username in xss_payloads:
        r = client.post("/api/register/", json={
            "username": username, "password": "pass", "email": "sec_xss@test.com"
        })
        assert r.status_code in (200, 409, 422, 429), (
            f"XSS username '{username[:20]}': {r.status_code}"
        )
        _cleanup()


def test_path_traversal_username():
    r = client.post("/api/register/", json={
        "username": "../../etc/passwd", "password": "pass", "email": "sec_path@test.com"
    })
    assert r.status_code in (200, 409, 422, 429), r.text
    _cleanup()


def test_users_stats_endpoint_injection():
    payloads = ["../", "'; DROP--", "<script>", "%00"]
    for payload in payloads:
        r = client.get(f"/api/users/{payload}/stats")
        assert r.status_code in (404, 422), f"Path traversal '{payload}': {r.status_code}"


def test_users_stats_nonexistent_user():
    r = client.get("/api/users/nonexistent_user_99999999/stats")
    assert r.status_code == 404, r.text


def test_get_ranking_no_crash():
    r = client.get("/api/get_ranking")
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)


def test_register_very_long_email():
    email = "a" * 500 + "@b.com"
    r = client.post("/api/register/", json={"username": "sec_longem", "password": "p", "email": email})
    assert r.status_code in (409, 422, 429), r.text
