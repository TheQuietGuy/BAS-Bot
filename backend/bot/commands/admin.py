from datetime import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from backend.bot.permissions import committee_only
from backend.database.database import get_session
from backend.services import achievement_service as ach
from backend.services import announcement_service as ann
from backend.services import leaderboard_service as lb
from backend.services import leaderboard_notify as notify


def _parse_when(when: str) -> Optional[datetime]:
    try:
        return datetime.strptime(when, "%Y-%m-%d %H:%M")
    except ValueError:
        return None


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    admin_group = app_commands.Group(
        name="admin", description="Committee-only management commands"
    )
    points_group = app_commands.Group(
        name="points", description="Award or remove competition points", parent=admin_group
    )
    leaderboard_group = app_commands.Group(
        name="leaderboard", description="Manage the leaderboard", parent=admin_group
    )
    announcement_group = app_commands.Group(
        name="announcement", description="Edit or cancel announcements", parent=admin_group
    )

    # ---- Points ----

    @points_group.command(name="add", description="Award points to a member")
    @app_commands.describe(member="Member to award points to", amount="Points to add", reason="Optional reason")
    @committee_only()
    async def points_add(
        self, interaction: discord.Interaction, member: discord.Member, amount: int, reason: str = ""
    ):
        with get_session() as session:
            user = lb.get_or_create_user(session, member.id, str(member), member.display_name)
            comp = lb.get_or_create_active_competition(session)
            lb.add_points(session, user, comp, amount, reason)
            total = lb.get_user_points(session, user, comp)
            newly_earned = ach.check_participation_achievements(session, user)
            comp_name = comp.name

        message = (
            f"Added **{amount}** points to {member.mention} "
            f"({'reason: ' + reason if reason else 'no reason given'}). "
            f"New total: **{total}**."
        )
        if newly_earned:
            badges = ", ".join(f"{a.emoji} {a.name}" for a in newly_earned)
            message += f"\n🎉 {member.mention} just earned: {badges}"

        await interaction.response.send_message(message)

        achievement_note = (
            f"\n🎉 Also earned: {', '.join(a.name for a in newly_earned)}" if newly_earned else ""
        )
        await notify.notify_leaderboard_update(
            "🏆 Leaderboard update",
            f"**{member.display_name}** +{amount} pts ({comp_name}) — now **{total}** total.{achievement_note}",
        )

    @points_group.command(name="remove", description="Remove points from a member")
    @app_commands.describe(member="Member to remove points from", amount="Points to remove", reason="Optional reason")
    @committee_only()
    async def points_remove(
        self, interaction: discord.Interaction, member: discord.Member, amount: int, reason: str = ""
    ):
        with get_session() as session:
            user = lb.get_or_create_user(session, member.id, str(member), member.display_name)
            comp = lb.get_or_create_active_competition(session)
            lb.add_points(session, user, comp, -abs(amount), reason)
            total = lb.get_user_points(session, user, comp)
            comp_name = comp.name

        await interaction.response.send_message(
            f"Removed **{amount}** points from {member.mention}. New total: **{total}**."
        )

        await notify.notify_leaderboard_update(
            "🏆 Leaderboard update",
            f"**{member.display_name}** -{amount} pts ({comp_name}) — now **{total}** total.",
            colour=0xD6432F,
        )

    # ---- Leaderboard management ----

    @leaderboard_group.command(name="reset", description="Close the current competition and start a fresh one")
    @app_commands.describe(name="Name for the new leaderboard")
    @committee_only()
    async def leaderboard_reset(self, interaction: discord.Interaction, name: str = "General"):
        with get_session() as session:
            old = lb.get_or_create_active_competition(session)
            _, winner = lb.close_competition(session, old)
            new_comp = lb.get_or_create_active_competition(session, name=name)

            newly_earned = ach.check_win_achievements(session, winner) if winner else []
            winner_name = winner.display_name if winner else None

        message = f"Closed **{old.name}** and started a new leaderboard: **{new_comp.name}**."
        if winner_name:
            message += f"\n🏆 Winner of **{old.name}**: {winner_name}"
        if newly_earned:
            badges = ", ".join(f"{a.emoji} {a.name}" for a in newly_earned)
            message += f"\n🎉 {winner_name} just earned: {badges}"

        await interaction.response.send_message(message)

        description = f"**{old.name}** closed"
        description += f" — winner: **{winner_name}** 🏆" if winner_name else " (no scores)"
        description += f".\nNew leaderboard open: **{new_comp.name}**"
        await notify.notify_leaderboard_update("🔁 Leaderboard reset", description, colour=0x4C7EF0)

        await interaction.response.send_message(message)

    # ---- Announcements ----

    @app_commands.command(name="announce", description="Post an announcement now, or schedule it for later")
    @app_commands.describe(
        title="Announcement title",
        message="Announcement body",
        channel="Channel to post in (defaults to this channel)",
        when="Optional: schedule for later instead of posting now. Format: YYYY-MM-DD HH:MM (UTC)",
    )
    @committee_only()
    async def announce(
        self,
        interaction: discord.Interaction,
        title: str,
        message: str,
        channel: Optional[discord.TextChannel] = None,
        when: Optional[str] = None,
    ):
        target_channel = channel or interaction.channel

        if when:
            scheduled_for = _parse_when(when)
            if scheduled_for is None:
                await interaction.response.send_message(
                    "Couldn't parse that time. Use `YYYY-MM-DD HH:MM` in UTC, e.g. `2026-10-31 18:00`.",
                    ephemeral=True,
                )
                return
            with get_session() as session:
                ann.schedule_announcement(
                    session, title, message, interaction.user.id, target_channel.id, scheduled_for
                )
            await interaction.response.send_message(
                f"Scheduled **{title}** for {when} UTC in {target_channel.mention}.", ephemeral=True
            )
            return

        embed = discord.Embed(title=f"📢 {title}", description=message, colour=discord.Colour.purple())
        embed.set_footer(text=f"— BAS Committee ({interaction.user.display_name})")
        await target_channel.send(embed=embed)

        with get_session() as session:
            ann.log_posted_announcement(session, title, message, interaction.user.id, target_channel.id)

        await interaction.response.send_message(
            f"Announcement posted in {target_channel.mention}.", ephemeral=True
        )

    @announcement_group.command(name="edit", description="Edit an announcement's title/message (see the dashboard for IDs)")
    @app_commands.describe(announcement_id="ID of the announcement", title="New title", message="New message")
    @committee_only()
    async def edit_announcement(
        self,
        interaction: discord.Interaction,
        announcement_id: int,
        title: Optional[str] = None,
        message: Optional[str] = None,
    ):
        with get_session() as session:
            row = ann.get_announcement(session, announcement_id)
            if row is None:
                await interaction.response.send_message("No announcement with that ID.", ephemeral=True)
                return
            ann.edit_announcement(session, row, title=title, message=message)

        await interaction.response.send_message(
            f"Updated announcement #{announcement_id}. "
            "Note: this only updates the logged record, not a message already posted to Discord.",
            ephemeral=True,
        )

    @announcement_group.command(name="cancel", description="Cancel a still-scheduled announcement")
    @app_commands.describe(announcement_id="ID of the scheduled announcement")
    @committee_only()
    async def cancel_announcement(self, interaction: discord.Interaction, announcement_id: int):
        with get_session() as session:
            row = ann.get_announcement(session, announcement_id)
            if row is None:
                await interaction.response.send_message("No announcement with that ID.", ephemeral=True)
                return
            if row.status != "scheduled":
                await interaction.response.send_message(
                    "Only scheduled (not-yet-posted) announcements can be cancelled.", ephemeral=True
                )
                return
            ann.cancel_announcement(session, row)

        await interaction.response.send_message(f"Cancelled scheduled announcement #{announcement_id}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
