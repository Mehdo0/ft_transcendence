import re

from core.exceptions import InvalidEmailError


_LOCAL_PART_RE = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+$")
_DOMAIN_LABEL_RE = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$")


def validate_email(email: str) -> None:
    if not isinstance(email, str):
        raise InvalidEmailError("Email must be a string.")

    if email != email.strip():
        raise InvalidEmailError("Email contains leading or trailing whitespace.")
    if re.search(r"\s", email):
        raise InvalidEmailError("Email contains whitespace characters.")

    if email.count("@") != 1:
        raise InvalidEmailError("Email must contain exactly one '@' symbol.")

    local_part, domain = email.split("@")

    if not local_part:
        raise InvalidEmailError("Email local part is empty.")
    if len(local_part) > 64:
        raise InvalidEmailError("Email local part exceeds 64 characters.")
    if local_part.startswith(".") or local_part.endswith("."):
        raise InvalidEmailError("Email local part cannot start or end with a dot.")
    if ".." in local_part:
        raise InvalidEmailError("Email local part contains consecutive dots.")
    if not _LOCAL_PART_RE.match(local_part):
        raise InvalidEmailError("Email local part contains invalid characters.")

    if not domain:
        raise InvalidEmailError("Email domain is empty.")
    if len(domain) > 255:
        raise InvalidEmailError("Email domain exceeds 255 characters.")
    if domain.startswith(".") or domain.endswith("."):
        raise InvalidEmailError("Email domain cannot start or end with a dot.")
    if ".." in domain:
        raise InvalidEmailError("Email domain contains consecutive dots.")

    if domain.startswith("[") and domain.endswith("]"):
        raise InvalidEmailError("IP address domains are not accepted.")

    labels = domain.split(".")
    if all(label.isdigit() for label in labels):
        raise InvalidEmailError("IP address domains are not accepted.")

    if len(labels) < 2:
        raise InvalidEmailError("Email domain must include a TLD.")

    for label in labels:
        if not label:
            raise InvalidEmailError("Email domain contains an empty label.")
        if len(label) > 63:
            raise InvalidEmailError(f"Domain label '{label}' exceeds 63 characters.")
        if not _DOMAIN_LABEL_RE.match(label):
            raise InvalidEmailError(f"Domain label '{label}' is invalid.")

    tld = labels[-1]
    if len(tld) < 2:
        raise InvalidEmailError(f"TLD '{tld}' is too short.")
