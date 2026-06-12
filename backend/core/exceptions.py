# exceptions.py


class UserAlreadyExistsError(Exception):
    pass


class UsernameAlreadyTakenError(Exception):
    pass


class EmailAlreadyTakenError(Exception):
    pass
