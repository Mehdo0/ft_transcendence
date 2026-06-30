import pytest
from core.database import add_user, get_user, SessionLocal, engine
from core.exceptions import EmailAlreadyTakenError
from utils.validators import validate_email, InvalidEmailError
from models.models import UserModel
from schemas.data import UserRegister


def _cleanup(session, username: str):
    user = session.get(UserModel, username)
    if user:
        session.delete(user)
        session.commit()


# ── add_user with valid data ────────────────────────────────────

def test_add_user_creates_user_in_db():
    ureg = UserRegister(username="db_test_add", password="pass123", email="testdb@domain.com")
    with SessionLocal() as session:
        _cleanup(session, "db_test_add")

    user = add_user(ureg)
    assert user.username == "db_test_add"
    assert user.email == "testdb@domain.com"
    assert user.elo == 500

    with SessionLocal() as session:
        _cleanup(session, "db_test_add")


# ── get_user returns proper data ────────────────────────────────

def test_get_user_returns_email():
    ureg = UserRegister(username="db_test_get", password="pass123", email="getuser@domain.com")
    with SessionLocal() as session:
        _cleanup(session, "db_test_get")

    add_user(ureg)
    fetched = get_user("db_test_get")
    assert fetched is not None
    assert fetched.email == "getuser@domain.com"
    assert fetched.username == "db_test_get"
    assert fetched.elo == 500

    with SessionLocal() as session:
        _cleanup(session, "db_test_get")


def test_get_nonexistent_user_returns_none():
    result = get_user("no_such_user_db_test_99999")
    assert result is None


# ── email uniqueness at DB level ────────────────────────────────

def test_email_uniqueness_enforced():
    ureg1 = UserRegister(username="db_test_uniq_A", password="pass", email="unique@testdb.com")
    ureg2 = UserRegister(username="db_test_uniq_B", password="pass", email="unique@testdb.com")

    with SessionLocal() as session:
        _cleanup(session, "db_test_uniq_A")
        _cleanup(session, "db_test_uniq_B")

    add_user(ureg1)

    with pytest.raises(EmailAlreadyTakenError) as exc_info:
        add_user(ureg2)
    assert "email" in str(exc_info.value).lower()

    with SessionLocal() as session:
        _cleanup(session, "db_test_uniq_A")
        _cleanup(session, "db_test_uniq_B")


def test_username_uniqueness_enforced_at_db():
    ureg1 = UserRegister(username="db_test_uniq_user", password="pass", email="first@uniqtest.com")
    ureg2 = UserRegister(username="db_test_uniq_user", password="pass", email="second@uniqtest.com")

    with SessionLocal() as session:
        _cleanup(session, "db_test_uniq_user")

    add_user(ureg1)

    with pytest.raises(EmailAlreadyTakenError):
        add_user(ureg2)

    with SessionLocal() as session:
        _cleanup(session, "db_test_uniq_user")
        # also cleanup by email
        u = session.query(UserModel).filter(UserModel.email == "first@uniqtest.com").first()
        if u:
            session.delete(u)
            session.commit()


# ── debug user modo ─────────────────────────────────────────────

def test_modo_user_exists():
    modo = get_user("modo")
    assert modo is not None, "Debug user 'modo' should exist"
    assert modo.username == "modo"
    assert modo.email == "modo@example.com"
    assert modo.elo == 9999


# ── add_user with UserRegister that has invalid email ────────────
def test_userregister_rejects_invalid_email_at_creation():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        UserRegister(username="test", password="pass", email="not-an-email")


# ── validate_email function coverage ────────────────────────────

def test_validate_email_rejects_non_string():
    with pytest.raises(InvalidEmailError):
        validate_email(12345)

    with pytest.raises(InvalidEmailError):
        validate_email(None)


def test_validate_email_allows_valid_emails():
    valid = [
        "user@domain.com",
        "player@game.org",
        "mehdi@42lausanne.ch",
        "a@b.io",
        "modo@example.com",
    ]
    for email in valid:
        validate_email(email)


# ── add_user with edge-case email lengths ───────────────────────

def test_add_user_with_max_local_part():
    local = "a" * 64
    email = f"{local}@domain.com"
    ureg = UserRegister(username="db_test_maxlocal", password="pass", email=email)
    with SessionLocal() as session:
        _cleanup(session, "db_test_maxlocal")

    user = add_user(ureg)
    assert user.email == email

    with SessionLocal() as session:
        _cleanup(session, "db_test_maxlocal")
