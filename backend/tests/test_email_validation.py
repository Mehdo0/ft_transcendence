"""
Tests for backend email validation.

These tests cover the LOGIC validation that complements the frontend regex.
Backend adds: domain logic, format strictness, edge cases the regex misses.
"""

import pytest

# The validator will live here — import it once we create it
# For RED phase, we import after creating the module
from utils.validators import validate_email, InvalidEmailError


# ── VALID EMAILS ──────────────────────────────────────────────

VALID_EMAILS = [
    # Standard
    "user@domain.com",
    "player@game.org",
    "mehdi@42lausanne.ch",
    # Subdomains
    "user@sub.domain.com",
    "admin@mail.example.co.uk",
    # Plus addressing (Gmail-style)
    "user+tag@domain.com",
    "user+spam@example.org",
    # Dots in local part
    "first.last@domain.com",
    "john.doe@company.fr",
    # Hyphens
    "user-name@domain.com",
    "test-user@my-domain.org",
    # Numbers
    "user123@domain456.com",
    "123user@domain.com",
    # Short but valid TLDs (2+ chars)
    "a@b.io",
    "x@ab.de",
    # Common patterns
    "modo@example.com",
]


@pytest.mark.parametrize("email", VALID_EMAILS)
def test_valid_email_should_pass(email: str):
    """Valid emails must be accepted without raising an error."""
    try:
        validate_email(email)
    except InvalidEmailError as e:
        pytest.fail(f"Valid email '{email}' was rejected: {e}")


# ── INVALID FORMAT — no @ ────────────────────────────────────

INVALID_NO_AT = [
    ("notanemail", "no '@' symbol"),
    ("just_a_string", "no '@' symbol"),
    ("domain.com", "no '@' symbol"),
    ("", "empty string"),
    ("   ", "whitespace only"),
]


@pytest.mark.parametrize("email,description", INVALID_NO_AT)
def test_reject_email_without_at(email: str, description: str):
    """Emails without an @ symbol must be rejected."""
    with pytest.raises(InvalidEmailError):
        validate_email(email)


# ── INVALID FORMAT — missing local or domain part ─────────────

INVALID_MISSING_PARTS = [
    ("@domain.com", "missing local part"),
    ("user@", "missing domain part"),
    ("@", "only @ symbol"),
]


@pytest.mark.parametrize("email,description", INVALID_MISSING_PARTS)
def test_reject_email_missing_local_or_domain(email: str, description: str):
    """Emails with empty local part or empty domain must be rejected."""
    with pytest.raises(InvalidEmailError):
        validate_email(email)


# ── INVALID FORMAT — multiple @ ───────────────────────────────

def test_reject_email_with_multiple_at():
    """Emails with multiple @ symbols must be rejected."""
    with pytest.raises(InvalidEmailError):
        validate_email("user@domain@extra.com")


# ── INVALID DOMAIN — no dot in domain (no TLD) ────────────────

INVALID_NO_DOT = [
    ("user@localhost", "no TLD — single label domain"),
    ("user@domain", "no dot at all"),
    ("admin@server", "single word domain"),
]


@pytest.mark.parametrize("email,description", INVALID_NO_DOT)
def test_reject_email_without_domain_dot(email: str, description: str):
    """Backend logic: domain must have at least one dot (proper TLD structure).
    This is a key difference from the frontend regex.
    """
    with pytest.raises(InvalidEmailError):
        validate_email(email)


# ── INVALID TLD — single character ────────────────────────────

INVALID_TLD_SINGLE = [
    ("user@domain.c", "single-char TLD"),
    ("a@b.x", "single-char TLD"),
]


@pytest.mark.parametrize("email,description", INVALID_TLD_SINGLE)
def test_reject_single_char_tld(email: str, description: str):
    """Backend logic: TLD must be at least 2 characters.
    The frontend regex accepts 'x@y.z' — backend must reject it.
    """
    with pytest.raises(InvalidEmailError):
        validate_email(email)


# ── INVALID — dot placement ───────────────────────────────────

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
    """Backend logic: reject emails with dots in illegal positions
    that the frontend regex would accept.
    """
    with pytest.raises(InvalidEmailError):
        validate_email(email)


# ── INVALID — hyphens in wrong places ─────────────────────────

INVALID_HYPHEN_PLACEMENT = [
    ("user@-domain.com", "hyphen at start of domain label"),
    ("user@domain-.com", "hyphen at end of domain label"),
]


@pytest.mark.parametrize("email,description", INVALID_HYPHEN_PLACEMENT)
def test_reject_hyphen_at_label_edge(email: str, description: str):
    """Domain labels cannot start or end with a hyphen (RFC 952/1123)."""
    with pytest.raises(InvalidEmailError):
        validate_email(email)


# ── INVALID — whitespace ──────────────────────────────────────

INVALID_WHITESPACE = [
    (" user@domain.com", "leading space"),
    ("user@domain.com ", "trailing space"),
    ("user @domain.com", "space in local part"),
    ("user@ domain.com", "space in domain"),
    ("user@dom ain.com", "space mid-domain"),
]


@pytest.mark.parametrize("email,description", INVALID_WHITESPACE)
def test_reject_email_with_whitespace(email: str, description: str):
    """Any whitespace anywhere in an email is invalid."""
    with pytest.raises(InvalidEmailError):
        validate_email(email)


# ── INVALID — IP address as domain ────────────────────────────

def test_reject_ip_address_domain():
    """Backend logic: IP addresses in brackets or raw are not valid email domains
    for a user-facing registration system (even if technically RFC-allowed)."""
    with pytest.raises(InvalidEmailError):
        validate_email("user@[192.168.0.1]")
    with pytest.raises(InvalidEmailError):
        validate_email("user@127.0.0.1")


# ── INVALID — local part too long ─────────────────────────────

def test_reject_local_part_too_long():
    """RFC 5321: local part max 64 characters."""
    long_local = "a" * 65 + "@domain.com"
    with pytest.raises(InvalidEmailError):
        validate_email(long_local)


# ── INVALID — domain too long ─────────────────────────────────

def test_reject_domain_too_long():
    """RFC 5321: domain max 255 characters."""
    long_domain = "user@" + "a" * 256 + ".com"
    with pytest.raises(InvalidEmailError):
        validate_email(long_domain)


# ── INTEGRATION: Pydantic model validation ────────────────────

def test_userregister_schema_validates_email():
    """The UserRegister Pydantic model must validate email via our validator."""
    from schemas.data import UserRegister

    # Valid: should not raise
    user = UserRegister(username="test", password="pass", email="valid@domain.com")
    assert user.email == "valid@domain.com"

    # Invalid: should raise ValidationError
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        UserRegister(username="test", password="pass", email="not-an-email")


# ── BOUNDARY: exactly at limits ───────────────────────────────

def test_local_part_exactly_64_chars_ok():
    """Local part of exactly 64 chars (the RFC limit) should be valid."""
    local = "a" * 64
    email = f"{local}@domain.com"
    try:
        validate_email(email)
    except InvalidEmailError:
        pytest.fail("64-char local part should be valid")


def test_domain_exactly_255_chars_ok():
    """Domain of exactly 255 chars should be valid."""
    # A valid domain label is max 63 chars. We build: label63.label63.label63.label63
    label = "a" * 63
    domain = ".".join([label, label, label, label[:60]])  # ~249 chars — hmm let's be precise
    # Actually let's just build a valid 255-char domain
    label = "a" * 63  # 63 chars
    # 4 labels of 63 chars = 252 chars plus 3 dots = 255 chars total
    domain = f"{label}.{label}.{label}.{label[:60]}"  # 63+1+63+1+63+1+60 = 252
    # Need exactly 255: 63+1+63+1+63+1+63 = 255
    domain = f"{label}.{label}.{label}.{label}"
    email = f"user@{domain}"
    assert len(domain) == 255, f"Test setup: domain should be 255 chars, got {len(domain)}"
    try:
        validate_email(email)
    except InvalidEmailError:
        pytest.fail("255-char domain should be valid")
