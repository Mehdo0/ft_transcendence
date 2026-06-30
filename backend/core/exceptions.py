# exceptions.py


class UserAlreadyExistsError(Exception):
    pass


class UsernameAlreadyTakenError(Exception):
    pass


class EmailAlreadyTakenError(Exception):
    pass


class InvalidEmailError(ValueError):
    """Backend logic: email format/domain validation failed."""
    pass
