from state import password_hash


def get_password_hash(password):
    return password_hash.hash(password)
