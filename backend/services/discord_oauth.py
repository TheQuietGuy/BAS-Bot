"""Discord OAuth2 login for the dashboard.

Flow:
  1. Dashboard hits GET /api/auth/login -> redirected to Discord's consent screen.
  2. User approves -> Discord redirects to OAUTH_REDIRECT_URI with a `code`.
  3. Backend exchanges the code for an access token (this module).
  4. Backend calls /users/@me with that token to get the Discord identity.
  5. Backend uses the BOT's own token (not the user's) to look up the
     member's roles in the society's guild -- simpler and more reliable
     than asking the user to also grant the `guilds.members.read` scope.
  6. Backend checks those roles against COMMITTEE_ROLE_IDS and issues its
     own signed session token (see jwt_utils.py).
"""
import aiohttp

from backend import config

DISCORD_API = "https://discord.com/api/v10"


class OAuthError(Exception):
    pass


def build_authorize_url(state: str) -> str:
    from urllib.parse import urlencode

    params = {
        "client_id": config.DISCORD_CLIENT_ID,
        "redirect_uri": config.OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
        "state": state,
        "prompt": "none",
    }
    return f"https://discord.com/oauth2/authorize?{urlencode(params)}"


async def exchange_code(code: str) -> str:
    """Exchanges an OAuth2 authorization code for an access token."""
    data = {
        "client_id": config.DISCORD_CLIENT_ID,
        "client_secret": config.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.OAUTH_REDIRECT_URI,
    }
    async with aiohttp.ClientSession() as http:
        async with http.post(
            f"{DISCORD_API}/oauth2/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            if resp.status != 200:
                raise OAuthError(f"Token exchange failed: {await resp.text()}")
            payload = await resp.json()
    return payload["access_token"]


async def fetch_identity(access_token: str) -> dict:
    """Returns {id, username, global_name, avatar} for the logged-in user."""
    async with aiohttp.ClientSession() as http:
        async with http.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        ) as resp:
            if resp.status != 200:
                raise OAuthError(f"Fetching identity failed: {await resp.text()}")
            return await resp.json()


async def fetch_guild_member_role_ids(discord_user_id: str) -> set[int]:
    """Looks up the member's roles in the configured guild, using the BOT's
    token. Returns an empty set if the bot can't see them (e.g. they've
    left the server) rather than raising, since that just means "not committee"."""
    if not config.GUILD_ID:
        return set()

    async with aiohttp.ClientSession() as http:
        async with http.get(
            f"{DISCORD_API}/guilds/{config.GUILD_ID}/members/{discord_user_id}",
            headers={"Authorization": f"Bot {config.DISCORD_TOKEN}"},
        ) as resp:
            if resp.status != 200:
                return set()
            payload = await resp.json()

    return {int(r) for r in payload.get("roles", [])}
