from __future__ import annotations

import os


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("Missing required environment variable: DATABASE_URL")
    return url


def get_jwt_secret() -> str:
    # For HS256 (default), `JWT_SECRET` is required.
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret:
        raise RuntimeError("Missing required environment variable: JWT_SECRET")
    return secret


def get_jwt_algorithm() -> str:
    # RSA is optional (RS256) as per task; default is HS256 to keep setup simple.
    alg = os.getenv("JWT_ALGORITHM", "HS256").strip().upper()
    if alg not in {"HS256", "RS256"}:
        raise RuntimeError("Unsupported JWT_ALGORITHM; expected HS256 or RS256")
    return alg


def get_jwt_rsa_keys() -> tuple[str | None, str | None]:
    private_pem = os.getenv("JWT_PRIVATE_KEY_PEM", "").strip() or None
    public_pem = os.getenv("JWT_PUBLIC_KEY_PEM", "").strip() or None
    return private_pem, public_pem


def get_access_token_expire_minutes() -> int:
    value = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60").strip()
    try:
        minutes = int(value)
    except ValueError as e:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be an integer") from e
    if minutes <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be > 0")
    return minutes


def get_app_title() -> str:
    return os.getenv("APP_TITLE", "FastAPI Social Task").strip()

