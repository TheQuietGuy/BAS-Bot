"""Central place for reading configuration from environment variables."""
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _parse_ids(raw: str) -> set[int]:
    ids = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if chunk.isdigit():
            ids.add(int(chunk))
    return ids


DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
GUILD_ID: Optional[int] = int(os.getenv("GUILD_ID")) if os.getenv("GUILD_ID", "").isdigit() else None
COMMITTEE_ROLE_IDS: set[int] = _parse_ids(os.getenv("COMMITTEE_ROLE_IDS", ""))
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "database/bas.db")

# Shared secret the React dashboard sends as "Authorization: Bearer <key>"
# for committee-only API endpoints. DEPRECATED in favour of Discord OAuth2
# login (see DISCORD_CLIENT_ID etc. below) -- kept only so a dashboard
# built against the old flow doesn't break overnight. Leave unset once
# OAuth2 login is wired up.
DASHBOARD_API_KEY: str = os.getenv("DASHBOARD_API_KEY", "")

# --- Discord OAuth2 login for the dashboard ---
# Same Discord application as the bot. Add a redirect URI in the
# Discord Developer Portal (OAuth2 tab) matching OAUTH_REDIRECT_URI exactly.
DISCORD_CLIENT_ID: str = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET: str = os.getenv("DISCORD_CLIENT_SECRET", "")
OAUTH_REDIRECT_URI: str = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/callback")
# Where to send the browser back to after login, with the session token attached.
DASHBOARD_URL: str = os.getenv("DASHBOARD_URL", "http://localhost:5173")
# Signs the dashboard's session tokens. Generate with:
#   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET: str = os.getenv("JWT_SECRET", "")
JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "12"))

# --- Leaderboard update notifications ---
# A Discord webhook URL for one channel (Channel Settings -> Integrations ->
# Webhooks -> New Webhook -> Copy Webhook URL). Whenever points change --
# via a slash command OR the dashboard/API -- a short update posts here.
# A webhook (not the bot's own connection) is used deliberately: it's the
# one mechanism both the bot process and the API process (which has no
# live Discord connection) can use identically. Leave blank to disable.
LEADERBOARD_UPDATES_WEBHOOK_URL: str = os.getenv("LEADERBOARD_UPDATES_WEBHOOK_URL", "")

if not DISCORD_TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in."
    )
