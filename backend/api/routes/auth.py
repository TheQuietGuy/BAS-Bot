from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from backend import config
from backend.api.auth import CurrentUser, get_current_user
from backend.api.jwt_utils import create_oauth_state, create_session_token, verify_oauth_state
from backend.database.database import get_session
from backend.services import discord_oauth
from backend.services import leaderboard_service as lb

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/login")
async def login():
    """Redirects the browser to Discord's consent screen."""
    if not config.DISCORD_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Discord OAuth2 is not configured on the server.")
    state = create_oauth_state()
    return RedirectResponse(discord_oauth.build_authorize_url(state))


@router.get("/callback")
async def callback(code: str = Query(...), state: str = Query(...)):
    """Discord redirects here after the user approves. Exchanges the code,
    checks committee roles via the bot, issues a session token, and sends
    the browser back to the dashboard with that token attached."""
    if not verify_oauth_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired login attempt. Try again.")

    try:
        access_token = await discord_oauth.exchange_code(code)
        identity = await discord_oauth.fetch_identity(access_token)
    except discord_oauth.OAuthError as e:
        raise HTTPException(status_code=502, detail=str(e))

    discord_id = int(identity["id"])
    username = identity.get("username", "unknown")
    display_name = identity.get("global_name") or username

    role_ids = await discord_oauth.fetch_guild_member_role_ids(identity["id"])
    is_committee = bool(role_ids & config.COMMITTEE_ROLE_IDS)

    # Keep our local user record in sync, same as the bot does.
    with get_session() as session:
        user = lb.get_or_create_user(session, discord_id, username, display_name)
        if user.is_committee != is_committee:
            user.is_committee = is_committee
            session.commit()

    token = create_session_token(discord_id, username, display_name, is_committee)
    return RedirectResponse(f"{config.DASHBOARD_URL}/auth/callback?token={token}")


@router.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)):
    return {
        "discord_id": user.discord_id,
        "username": user.username,
        "display_name": user.display_name,
        "is_committee": user.is_committee,
    }
