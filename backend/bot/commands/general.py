import discord
from discord import app_commands
from discord.ext import commands


class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="List everything the BAS Bot can do")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="BAS Bot — Commands",
            description="Brunel Anime Society bot",
            colour=discord.Colour.purple(),
        )
        embed.add_field(
            name="Everyone",
            value=(
                "`/leaderboard` — show the top members\n"
                "`/profile [member]` — show a member's points\n"
                "`/my-points` — show your own points\n"
                "`/anime search <name>` — look up an anime on MyAnimeList\n"
                "`/anime random` — get a random anime suggestion\n"
                "`/anime top` — top rated anime right now"
            ),
            inline=False,
        )
        embed.add_field(
            name="Committee only",
            value=(
                "`/announce` — post an official announcement\n"
                "`/admin points add` — award points to a member\n"
                "`/admin points remove` — remove points from a member\n"
                "`/admin leaderboard reset` — reset the current leaderboard"
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
