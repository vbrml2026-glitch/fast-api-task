from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import (
    get_access_token_expire_minutes,
    get_jwt_algorithm,
    get_jwt_rsa_keys,
    get_jwt_secret,
)

# bcrypt can be finicky depending on the installed `bcrypt` binary package.
# pbkdf2_sha256 is widely supported and good enough for this learning task.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    alg = get_jwt_algorithm()
    expire_minutes = get_access_token_expire_minutes()
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expire_minutes)

    payload = {"sub": subject, "exp": exp}

    if alg == "HS256":
        secret = get_jwt_secret()
        return jwt.encode(payload, secret, algorithm=alg)

    private_pem, _public_pem = get_jwt_rsa_keys()
    if not private_pem:
        raise RuntimeError("JWT_PRIVATE_KEY_PEM is required when JWT_ALGORITHM=RS256")
    return jwt.encode(payload, private_pem, algorithm=alg)


def decode_access_token(token: str) -> str:
    alg = get_jwt_algorithm()

    try:
        if alg == "HS256":
            secret = get_jwt_secret()
            payload = jwt.decode(token, secret, algorithms=[alg])
        else:
            _private_pem, public_pem = get_jwt_rsa_keys()
            if not public_pem:
                raise RuntimeError("JWT_PUBLIC_KEY_PEM is required when JWT_ALGORITHM=RS256")
            payload = jwt.decode(token, public_pem, algorithms=[alg])
    except JWTError as e:
        raise RuntimeError("Invalid or expired JWT") from e

    sub = payload.get("sub")
    if not sub:
        raise RuntimeError("JWT missing subject (sub)")
    return str(sub)

