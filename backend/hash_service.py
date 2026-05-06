from backend.global_var import password_hash


def get_password_hash(password):
    return password_hash.hash(password)
