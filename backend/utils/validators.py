"""
Email validation module.

Provides backend LOGIC validation (domain, TLD, structure)
that complements the frontend regex format check.
"""

import re


class InvalidEmailError(ValueError):
    """Raised when an email fails backend logic validation."""


# Characters allowed in the local part (RFC 5321 simplified: ASCII printable,
# excluding whitespace and a few special chars that are almost never legit
# in user-facing registration)
_LOCAL_PART_RE = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+$")

# Characters allowed in a domain label (RFC 952/1123: letters, digits, hyphens)
_DOMAIN_LABEL_RE = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$")


def validate_email(email: str) -> None:
    """
    Validate an email address with backend logic.

    Checks that go BEYOND the frontend regex:
      - Proper local part / domain structure
      - TLD is at least 2 characters (rejects 'user@domain.c')
      - No IP addresses as domain
      - No consecutive dots or dots at edges
      - No whitespace anywhere
      - RFC 5321 length limits (local 64, domain 255)

    Raises InvalidEmailError if any check fails.
    Returns None on success.
    """
    if not isinstance(email, str):
        raise InvalidEmailError("Email must be a string.")

    # ── Whitespace ───────────────────────────────────────────
    if email != email.strip():
        raise InvalidEmailError("Email contains leading or trailing whitespace.")
    if re.search(r"\s", email):
        raise InvalidEmailError("Email contains whitespace characters.")

    # ── Exactly one @ ────────────────────────────────────────
    if email.count("@") != 1:
        raise InvalidEmailError("Email must contain exactly one '@' symbol.")

    local_part, domain = email.split("@")

    # ── Local part checks ────────────────────────────────────
    if not local_part:
        raise InvalidEmailError("Email local part (before '@') is empty.")
    if len(local_part) > 64:
        raise InvalidEmailError("Email local part exceeds 64 characters (RFC 5321).")
    if local_part.startswith(".") or local_part.endswith("."):
        raise InvalidEmailError("Email local part cannot start or end with a dot.")
    if ".." in local_part:
        raise InvalidEmailError("Email local part contains consecutive dots.")
    if not _LOCAL_PART_RE.match(local_part):
        raise InvalidEmailError(
            "Email local part contains invalid characters."
        )

    # ── Domain checks ────────────────────────────────────────
    if not domain:
        raise InvalidEmailError("Email domain (after '@') is empty.")
    if len(domain) > 255:
        raise InvalidEmailError("Email domain exceeds 255 characters (RFC 5321).")
    if domain.startswith(".") or domain.endswith("."):
        raise InvalidEmailError("Email domain cannot start or end with a dot.")
    if ".." in domain:
        raise InvalidEmailError("Email domain contains consecutive dots.")

    # Reject IP address domains (both bracketed and raw IPv4)
    if domain.startswith("[") and domain.endswith("]"):
        raise InvalidEmailError("IP address domains are not accepted.")
    # Raw IPv4 check: all labels are purely numeric
    labels = domain.split(".")
    if all(label.isdigit() for label in labels):
        raise InvalidEmailError("IP address domains are not accepted.")

    # ── Domain label validation ──────────────────────────────
    # Domain must have at least one dot → at least 2 labels → TLD exists
    if len(labels) < 2:
        raise InvalidEmailError(
            "Email domain must include a TLD (e.g., 'domain.com', not just 'domain')."
        )

    for i, label in enumerate(labels):
        if not label:
            raise InvalidEmailError("Email domain contains an empty label.")
        if len(label) > 63:
            raise InvalidEmailError(
                f"Domain label '{label}' exceeds 63 characters."
            )
        if not _DOMAIN_LABEL_RE.match(label):
            raise InvalidEmailError(
                f"Domain label '{label}' is invalid. "
                "Labels must be alphanumeric, may contain hyphens, "
                "and cannot start or end with a hyphen."
            )

    # ── TLD logic check ──────────────────────────────────────
    tld = labels[-1]
    if len(tld) < 2:
        raise InvalidEmailError(
            f"TLD '{tld}' is too short (minimum 2 characters)."
        )
