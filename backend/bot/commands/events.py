from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from backend.bot.permissions import committee_only
from backend.database.database import get_session
from backend.services import event_service as ev


def _parse_when(when: str) -> Optional[datetime]:
    """Accepts 'YYYY-MM-DD HH:MM' (24h, treated as UTC) since that's
    unambiguous for a small society bot without per-member timezones."""
    try:
        return datetime.strptime(when, "%Y-%m-%d %H:%M")
    except ValueError:
        return None


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    events_group = app_commands.Group(name="events", description="Society events")

    @events_group.command(name="list", description="Show upcoming society events")
    async def list_events(self, interaction: discord.Interaction):
        with get_session() as session:
            upcoming = ev.list_upcoming_events(session)

        if not upcoming:
            await interaction.response.send_message("No upcoming events scheduled.")
            return

        embed = discord.Embed(title="📅 Upcoming Events", colour=discord.Colour.blue())
        for event in upcoming:
            value = f"<t:{int(event.event_time.replace(tzinfo=timezone.utc).timestamp())}:F>"
            if event.location:
                value += f"\n📍 {event.location}"
            if event.description:
                value += f"\n{event.description}"
            embed.add_field(name=event.name, value=value, inline=False)

        await interaction.response.send_message(embed=embed)

    @events_group.command(name="create", description="Add a society event (UTC time)")
    @app_commands.describe(
        name="Event name",
        when="Date and time in UTC, e.g. 2026-10-31 18:00",
        location="Where it's happening",
        description="Extra details",
        reminder_minutes_before="How long before the event to post a reminder (default 60)",
    )
    @committee_only()
    async def create_event(
        self,
        interaction: discord.Interaction,
        name: str,
        when: str,
        location: str = "",
        description: str = "",
        reminder_minutes_before: int = 60,
    ):
        event_time = _parse_when(when)
        if event_time is None:
            await interaction.response.send_message(
                "Couldn't parse that time. Use the format `YYYY-MM-DD HH:MM` in UTC, "
                "e.g. `2026-10-31 18:00`.",
                ephemeral=True,
            )
            return

        with get_session() as session:
            event = ev.create_event(
                session,
                name=name,
                event_time=event_time,
                channel_id=interaction.channel_id,
                created_by_discord_id=interaction.user.id,
                description=description,
                location=location,
                reminder_minutes_before=reminder_minutes_before,
            )

        await interaction.response.send_message(
            f"Added **{event.name}** — a reminder will post in this channel "
            f"{reminder_minutes_before} minutes before it starts."
        )

    @events_group.command(name="delete", description="Remove an event by its ID (see /events list)")
    @app_commands.describe(event_id="The event's ID")
    @committee_only()
    async def delete_event(self, interaction: discord.Interaction, event_id: int):
        with get_session() as session:
            event = ev.get_event(session, event_id)
            if event is None:
                await interaction.response.send_message("No event with that ID.", ephemeral=True)
                return
            name = event.name
            ev.delete_event(session, event)

        await interaction.response.send_message(f"Removed **{name}**.")


async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
