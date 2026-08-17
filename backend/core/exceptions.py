# exceptions.py


class UserAlreadyExistsError(Exception):
    pass


class UsernameAlreadyTakenError(Exception):
    pass


class EmailAlreadyTakenError(Exception):
    pass


class WeakPassword(Exception):
    pass


class BadUsername(Exception):
    pass


class ImpossibleEmail(Exception):
    pass
