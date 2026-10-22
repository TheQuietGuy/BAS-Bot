"""Background scheduler for the bot.

Runs once a minute, checking for:
  - scheduled announcements whose time has come -> post + mark posted
  - upcoming events whose reminder window has arrived -> post reminder

Kept as a simple polling loop (discord.ext.tasks) rather than a separate
job queue -- this is a small society bot running on one process, so a
minute of slack is fine and this avoids adding infrastructure.
"""
import logging
from datetime import timezone

import discord
from discord.ext import commands, tasks

from backend.database.database import get_session
from backend.services import announcement_service as ann
from backend.services import event_service as ev

logger = logging.getLogger("bas-bot.scheduler")


class Scheduler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tick.start()

    def cog_unload(self):
        self.tick.cancel()

    @tasks.loop(minutes=1)
    async def tick(self):
        await self._post_due_announcements()
        await self._send_due_reminders()

    @tick.before_loop
    async def before_tick(self):
        await self.bot.wait_until_ready()

    async def _post_due_announcements(self):
        with get_session() as session:
            due = ann.get_due_scheduled(session)
            for announcement in due:
                channel = self.bot.get_channel(announcement.channel_id)
                if channel is None:
                    logger.warning(
                        "Scheduled announcement %s: channel %s not found (skipping, will retry)",
                        announcement.id, announcement.channel_id,
                    )
                    continue
                embed = discord.Embed(
                    title=f"📢 {announcement.title}",
                    description=announcement.message,
                    colour=discord.Colour.purple(),
                )
                embed.set_footer(text="— BAS Committee (scheduled)")
                try:
                    await channel.send(embed=embed)
                    ann.mark_posted(session, announcement)
                    logger.info("Posted scheduled announcement %s", announcement.id)
                except discord.DiscordException:
                    logger.exception("Failed to post scheduled announcement %s", announcement.id)

    async def _send_due_reminders(self):
        with get_session() as session:
            due = ev.get_due_reminders(session)
            for event in due:
                channel = self.bot.get_channel(event.channel_id)
                if channel is None:
                    logger.warning(
                        "Event reminder %s: channel %s not found (skipping, will retry)",
                        event.id, event.channel_id,
                    )
                    continue
                embed = discord.Embed(
                    title=f"⏰ Reminder: {event.name}",
                    description=event.description or "Starting soon!",
                    colour=discord.Colour.blue(),
                )
                if event.location:
                    embed.add_field(name="Location", value=event.location)
                embed.add_field(
                    name="When",
                    value=f"<t:{int(event.event_time.replace(tzinfo=timezone.utc).timestamp())}:R>",
                )
                try:
                    await channel.send(embed=embed)
                    ev.mark_reminder_sent(session, event)
                    logger.info("Sent reminder for event %s", event.id)
                except discord.DiscordException:
                    logger.exception("Failed to send reminder for event %s", event.id)


async def setup(bot: commands.Bot):
    await bot.add_cog(Scheduler(bot))
