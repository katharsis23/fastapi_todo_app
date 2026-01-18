import bcrypt


def hash_password(initial_password: str):
    return bcrypt.hash(initial_password)


def verify_password(secret: str, verified_password: str):
    return bcrypt.verify(secret=secret, hash=verified_password)
