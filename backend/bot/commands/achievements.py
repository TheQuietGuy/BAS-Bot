import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from backend.database.database import get_session
from backend.services import achievement_service as ach
from backend.services import leaderboard_service as lb


class AchievementsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="achievements", description="Show a member's earned badges")
    @app_commands.describe(member="Whose achievements to show (defaults to you)")
    async def achievements(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user

        with get_session() as session:
            user = lb.get_or_create_user(session, target.id, str(target), target.display_name)
            earned = ach.list_user_achievements(session, user)
            all_achievements = ach.list_all_achievements(session)

        earned_keys = {a.key for a in earned}

        embed = discord.Embed(
            title=f"{target.display_name}'s Achievements",
            colour=discord.Colour.gold(),
        )
        for a in all_achievements:
            status = "✅" if a.key in earned_keys else "🔒"
            embed.add_field(name=f"{a.emoji} {a.name} {status}", value=a.description, inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AchievementsCog(bot))
