import re


class InvalidEmailError(ValueError):
    pass


_LOCAL_PART_RE = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+$")
_DOMAIN_LABEL_RE = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$")


def validate_email(email: str) -> None:
    if not isinstance(email, str):
        raise InvalidEmailError("Email must be a string.")
    if email != email.strip() or re.search(r"\s", email):
        raise InvalidEmailError("Email contains whitespace.")
    if email.count("@") != 1:
        raise InvalidEmailError("Email must contain exactly one '@' symbol.")
    local_part, domain = email.split("@")
    if not local_part or len(local_part) > 64:
        raise InvalidEmailError("Invalid local part.")
    if local_part.startswith(".") or local_part.endswith(".") or ".." in local_part:
        raise InvalidEmailError("Invalid dots in local part.")
    if not _LOCAL_PART_RE.match(local_part):
        raise InvalidEmailError("Invalid characters in local part.")
    if not domain or len(domain) > 255:
        raise InvalidEmailError("Invalid domain.")
    if domain.startswith(".") or domain.endswith(".") or ".." in domain:
        raise InvalidEmailError("Invalid dots in domain.")
    if (domain.startswith("[") and domain.endswith("]")) or all(l.isdigit() for l in domain.split(".")):
        raise InvalidEmailError("IP addresses not accepted.")
    labels = domain.split(".")
    if len(labels) < 2:
        raise InvalidEmailError("Domain must include a TLD.")
    for label in labels:
        if not label or len(label) > 63 or not _DOMAIN_LABEL_RE.match(label):
            raise InvalidEmailError(f"Invalid domain label '{label}'.")
    if len(labels[-1]) < 2:
        raise InvalidEmailError("TLD too short.")
