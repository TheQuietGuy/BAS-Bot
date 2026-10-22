"""Read-only Discord directory lookups (channels, members) for the
dashboard, so committee members can pick from real names instead of
typing raw IDs.

Uses the bot's own token against Discord's plain REST API -- this needs
no live gateway connection, so the API process can do it exactly like the
bot process can. Every call is best-effort: if it fails (bad token, bot
not in the guild, Discord unreachable), callers get an empty list rather
than a crash, and the dashboard falls back to manual ID entry.
"""
import logging

import aiohttp

from backend import config

logger = logging.getLogger("bas-bot.discord-directory")

DISCORD_API = "https://discord.com/api/v10"
TIMEOUT = aiohttp.ClientTimeout(total=10)

GUILD_TEXT_CHANNEL_TYPE = 0
GUILD_ANNOUNCEMENT_CHANNEL_TYPE = 5


async def fetch_guild_channels() -> list[dict]:
    """Returns [{"id": "...", "name": "..."}] for text-postable channels in
    the configured guild, sorted by position. Empty list on any failure."""
    if not config.GUILD_ID or not config.DISCORD_TOKEN:
        return []

    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as http:
            async with http.get(
                f"{DISCORD_API}/guilds/{config.GUILD_ID}/channels",
                headers={"Authorization": f"Bot {config.DISCORD_TOKEN}"},
            ) as resp:
                if resp.status != 200:
                    logger.warning("Fetching guild channels failed: HTTP %s", resp.status)
                    return []
                channels = await resp.json()
    except Exception:
        logger.exception("Failed to fetch guild channels")
        return []

    text_channels = [
        c for c in channels
        if c.get("type") in (GUILD_TEXT_CHANNEL_TYPE, GUILD_ANNOUNCEMENT_CHANNEL_TYPE)
    ]
    text_channels.sort(key=lambda c: c.get("position", 0))
    return [{"id": c["id"], "name": c["name"]} for c in text_channels]


async def fetch_guild_members(limit: int = 1000) -> list[dict]:
    """Returns [{"discord_id": ..., "username": "...", "display_name": "..."}]
    for non-bot members of the configured guild. Empty list on any failure."""
    if not config.GUILD_ID or not config.DISCORD_TOKEN:
        return []

    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as http:
            async with http.get(
                f"{DISCORD_API}/guilds/{config.GUILD_ID}/members",
                params={"limit": limit},
                headers={"Authorization": f"Bot {config.DISCORD_TOKEN}"},
            ) as resp:
                if resp.status != 200:
                    logger.warning("Fetching guild members failed: HTTP %s", resp.status)
                    return []
                members = await resp.json()
    except Exception:
        logger.exception("Failed to fetch guild members")
        return []

    results = []
    for m in members:
        user = m.get("user") or {}
        if user.get("bot"):
            continue
        results.append({
            "discord_id": int(user["id"]),
            "username": user.get("username", ""),
            "display_name": m.get("nick") or user.get("global_name") or user.get("username", ""),
        })
    return results
