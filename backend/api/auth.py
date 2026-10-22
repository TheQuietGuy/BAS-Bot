"""Auth dependencies for the API.

Primary path: a Discord-OAuth2-issued session JWT (see routes/auth.py and
jwt_utils.py), carrying an `is_committee` claim already checked against
Discord roles at login time.

Legacy path: DASHBOARD_API_KEY, a shared secret, kept only so an older
dashboard build doesn't break overnight. New code should log in with
Discord instead -- see README for migration notes.
"""
from fastapi import Header, HTTPException, status
from typing import Optional

from backend import config
from backend.api.jwt_utils import TokenError, decode_session_token


class CurrentUser:
    def __init__(self, discord_id: int, username: str, display_name: str, is_committee: bool):
        self.discord_id = discord_id
        self.username = username
        self.display_name = display_name
        self.is_committee = is_committee


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization: Bearer <token> header.",
        )
    return authorization.removeprefix("Bearer ").strip()


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> CurrentUser:
    """Resolves the logged-in dashboard user from a session JWT."""
    token = _extract_bearer_token(authorization)

    try:
        payload = decode_session_token(token)
    except TokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return CurrentUser(
        discord_id=int(payload["sub"]),
        username=payload["username"],
        display_name=payload["display_name"],
        is_committee=payload["is_committee"],
    )


async def require_committee(authorization: Optional[str] = Header(default=None)) -> CurrentUser:
    token = _extract_bearer_token(authorization)

    # Legacy shared-secret path, kept for backward compatibility only.
    if config.DASHBOARD_API_KEY and token == config.DASHBOARD_API_KEY:
        return CurrentUser(
            discord_id=0,
            username="legacy-api-key",
            display_name="Committee (legacy key)",
            is_committee=True,
        )

    try:
        payload = decode_session_token(token)
    except TokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    if not payload.get("is_committee"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You need a committee role in the Discord server to do this.",
        )

    return CurrentUser(
        discord_id=int(payload["sub"]),
        username=payload["username"],
        display_name=payload["display_name"],
        is_committee=True,
    )
