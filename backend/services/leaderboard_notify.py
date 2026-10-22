"""Posts leaderboard change notifications to a Discord channel via webhook.

A webhook is used instead of the bot's own Discord connection so BOTH the
bot process AND the API process (which has no live Discord gateway
connection) can post updates the exact same way -- a leaderboard change
made from the dashboard shows up in the channel just as one made with a
slash command does.

Setup: in the target Discord channel, Settings -> Integrations ->
Webhooks -> New Webhook -> Copy Webhook URL -> put it in .env as
LEADERBOARD_UPDATES_WEBHOOK_URL. Leave it blank to disable notifications
entirely.
"""
import logging

import aiohttp

from backend import config

logger = logging.getLogger("bas-bot.leaderboard-notify")

TIMEOUT = aiohttp.ClientTimeout(total=10)


async def notify_leaderboard_update(title: str, description: str, colour: int = 0x7C6FE0) -> None:
    """Fire-and-forget: posts an embed to the configured webhook.

    No-ops silently if no webhook is configured, and NEVER raises -- a
    failed notification should never break the leaderboard change itself.
    """
    if not config.LEADERBOARD_UPDATES_WEBHOOK_URL:
        return

    payload = {"embeds": [{"title": title, "description": description, "color": colour}]}

    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as http:
            async with http.post(config.LEADERBOARD_UPDATES_WEBHOOK_URL, json=payload) as resp:
                if resp.status >= 300:
                    logger.warning(
                        "Leaderboard update webhook returned %s: %s",
                        resp.status, await resp.text(),
                    )
    except Exception:
        logger.exception("Failed to post leaderboard update webhook")
