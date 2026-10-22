"""Signs and verifies the dashboard's session tokens.

These are the API's own tokens (not Discord's) -- issued once after a
successful Discord OAuth2 login, so the dashboard doesn't need to re-check
Discord roles on every request.
"""
from datetime import datetime, timedelta, timezone

import jwt

from backend import config

ALGORITHM = "HS256"


class TokenError(Exception):
    pass


def create_session_token(discord_id: int, username: str, display_name: str, is_committee: bool) -> str:
    if not config.JWT_SECRET:
        raise TokenError("JWT_SECRET is not configured on the server.")

    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(discord_id),
        "username": username,
        "display_name": display_name,
        "is_committee": is_committee,
        "iat": now,
        "exp": now + timedelta(hours=config.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=ALGORITHM)


def decode_session_token(token: str) -> dict:
    if not config.JWT_SECRET:
        raise TokenError("JWT_SECRET is not configured on the server.")
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise TokenError("Session expired -- please log in again.")
    except jwt.InvalidTokenError:
        raise TokenError("Invalid session token.")


def create_oauth_state() -> str:
    """Short-lived, signed CSRF token for the OAuth2 `state` parameter --
    proves the callback belongs to a login we actually initiated, without
    needing server-side session storage."""
    if not config.JWT_SECRET:
        raise TokenError("JWT_SECRET is not configured on the server.")
    now = datetime.now(timezone.utc)
    payload = {"typ": "oauth_state", "iat": now, "exp": now + timedelta(minutes=5)}
    return jwt.encode(payload, config.JWT_SECRET, algorithm=ALGORITHM)


def verify_oauth_state(state: str) -> bool:
    try:
        payload = jwt.decode(state, config.JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return False
    return payload.get("typ") == "oauth_state"
