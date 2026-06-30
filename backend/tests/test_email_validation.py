import pytest

from utils.validators import validate_email, InvalidEmailError


VALID_EMAILS = [
    "user@domain.com",
    "player@game.org",
    "mehdi@42lausanne.ch",
    "user@sub.domain.com",
    "admin@mail.example.co.uk",
    "user+tag@domain.com",
    "user+spam@example.org",
    "first.last@domain.com",
    "john.doe@company.fr",
    "user-name@domain.com",
    "test-user@my-domain.org",
    "user123@domain456.com",
    "123user@domain.com",
    "a@b.io",
    "x@ab.de",
    "modo@example.com",
]


@pytest.mark.parametrize("email", VALID_EMAILS)
def test_valid_email_should_pass(email: str):
    try:
        validate_email(email)
    except InvalidEmailError as e:
        pytest.fail(f"Valid email '{email}' was rejected: {e}")


INVALID_NO_AT = [
    ("notanemail", "no '@' symbol"),
    ("just_a_string", "no '@' symbol"),
    ("domain.com", "no '@' symbol"),
    ("", "empty string"),
    ("   ", "whitespace only"),
]


@pytest.mark.parametrize("email,description", INVALID_NO_AT)
def test_reject_email_without_at(email: str, description: str):
    with pytest.raises(InvalidEmailError):
        validate_email(email)


INVALID_MISSING_PARTS = [
    ("@domain.com", "missing local part"),
    ("user@", "missing domain part"),
    ("@", "only @ symbol"),
]


@pytest.mark.parametrize("email,description", INVALID_MISSING_PARTS)
def test_reject_email_missing_local_or_domain(email: str, description: str):
    with pytest.raises(InvalidEmailError):
        validate_email(email)


def test_reject_email_with_multiple_at():
    with pytest.raises(InvalidEmailError):
        validate_email("user@domain@extra.com")


INVALID_NO_DOT = [
    ("user@localhost", "no TLD"),
    ("user@domain", "no dot at all"),
    ("admin@server", "single word domain"),
]


@pytest.mark.parametrize("email,description", INVALID_NO_DOT)
def test_reject_email_without_domain_dot(email: str, description: str):
    with pytest.raises(InvalidEmailError):
        validate_email(email)


INVALID_TLD_SINGLE = [
    ("user@domain.c", "single-char TLD"),
    ("a@b.x", "single-char TLD"),
]


@pytest.mark.parametrize("email,description", INVALID_TLD_SINGLE)
def test_reject_single_char_tld(email: str, description: str):
    with pytest.raises(InvalidEmailError):
        validate_email(email)


INVALID_DOT_PLACEMENT = [
    ("user@.domain.com", "dot immediately after @"),
    ("user@domain..com", "consecutive dots in domain"),
    ("user..name@domain.com", "consecutive dots in local part"),
    (".user@domain.com", "dot at start of local part"),
    ("user.@domain.com", "dot at end of local part"),
    ("user@domain.com.", "dot at end of domain"),
]


@pytest.mark.parametrize("email,description", INVALID_DOT_PLACEMENT)
def test_reject_bad_dot_placement(email: str, description: str):
    with pytest.raises(InvalidEmailError):
        validate_email(email)


INVALID_HYPHEN_PLACEMENT = [
    ("user@-domain.com", "hyphen at start of domain label"),
    ("user@domain-.com", "hyphen at end of domain label"),
]


@pytest.mark.parametrize("email,description", INVALID_HYPHEN_PLACEMENT)
def test_reject_hyphen_at_label_edge(email: str, description: str):
    with pytest.raises(InvalidEmailError):
        validate_email(email)


INVALID_WHITESPACE = [
    (" user@domain.com", "leading space"),
    ("user@domain.com ", "trailing space"),
    ("user @domain.com", "space in local part"),
    ("user@ domain.com", "space in domain"),
    ("user@dom ain.com", "space mid-domain"),
]


@pytest.mark.parametrize("email,description", INVALID_WHITESPACE)
def test_reject_email_with_whitespace(email: str, description: str):
    with pytest.raises(InvalidEmailError):
        validate_email(email)


def test_reject_ip_address_domain():
    with pytest.raises(InvalidEmailError):
        validate_email("user@[192.168.0.1]")
    with pytest.raises(InvalidEmailError):
        validate_email("user@127.0.0.1")


def test_reject_local_part_too_long():
    long_local = "a" * 65 + "@domain.com"
    with pytest.raises(InvalidEmailError):
        validate_email(long_local)


def test_reject_domain_too_long():
    long_domain = "user@" + "a" * 256 + ".com"
    with pytest.raises(InvalidEmailError):
        validate_email(long_domain)


def test_userregister_schema_validates_email():
    from schemas.data import UserRegister
    from pydantic import ValidationError

    user = UserRegister(username="test", password="pass", email="valid@domain.com")
    assert user.email == "valid@domain.com"

    with pytest.raises(ValidationError):
        UserRegister(username="test", password="pass", email="not-an-email")


def test_local_part_exactly_64_chars_ok():
    local = "a" * 64
    email = f"{local}@domain.com"
    try:
        validate_email(email)
    except InvalidEmailError:
        pytest.fail("64-char local part should be valid")


def test_domain_exactly_255_chars_ok():
    label = "a" * 63
    domain = f"{label}.{label}.{label}.{label}"
    email = f"user@{domain}"
    assert len(domain) == 255
    try:
        validate_email(email)
    except InvalidEmailError:
        pytest.fail("255-char domain should be valid")
