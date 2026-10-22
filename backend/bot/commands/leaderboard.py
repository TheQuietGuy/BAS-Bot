import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from backend.database.database import get_session
from backend.services import leaderboard_service as lb


class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="Show the current competition leaderboard")
    @app_commands.describe(competition="Name of the competition (defaults to the main leaderboard)")
    async def leaderboard(self, interaction: discord.Interaction, competition: Optional[str] = None):
        with get_session() as session:
            comp = (
                lb.find_competition_by_name(session, competition)
                if competition
                else lb.get_or_create_active_competition(session)
            )
            if comp is None:
                await interaction.response.send_message(
                    f"No competition found called '{competition}'.", ephemeral=True
                )
                return

            ranked = lb.get_leaderboard(session, comp, limit=10)

        if not ranked:
            await interaction.response.send_message(
                f"No scores yet for **{comp.name}**.", ephemeral=True
            )
            return

        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (user, total) in enumerate(ranked):
            prefix = medals[i] if i < 3 else f"{i + 1}."
            lines.append(f"{prefix} **{user.display_name}** — {total} pts")

        embed = discord.Embed(
            title=f"🏆 {comp.name} — Leaderboard",
            description="\n".join(lines),
            colour=discord.Colour.gold(),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="Show a member's competition stats")
    @app_commands.describe(member="Whose profile to show (defaults to you)")
    async def profile(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        with get_session() as session:
            user = lb.get_or_create_user(session, target.id, str(target), target.display_name)
            comp = lb.get_or_create_active_competition(session)
            points = lb.get_user_points(session, user, comp)

        embed = discord.Embed(title=f"{target.display_name}'s Profile", colour=discord.Colour.blue())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name=comp.name, value=f"{points} pts")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="my-points", description="Show your current points")
    async def my_points(self, interaction: discord.Interaction):
        with get_session() as session:
            user = lb.get_or_create_user(
                session, interaction.user.id, str(interaction.user), interaction.user.display_name
            )
            comp = lb.get_or_create_active_competition(session)
            points = lb.get_user_points(session, user, comp)
        await interaction.response.send_message(
            f"You have **{points}** points in **{comp.name}**.", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
