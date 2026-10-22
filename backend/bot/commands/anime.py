import discord
from discord import app_commands
from discord.ext import commands

from backend.services import anime_service


def _anime_embed(info: dict) -> discord.Embed:
    embed = discord.Embed(
        title=info["title"],
        url=info["mal_url"] or None,
        description=(info["description"][:400] + "…") if len(info["description"]) > 400 else info["description"],
        colour=discord.Colour.purple(),
    )
    if info["genres"]:
        embed.add_field(name="Genres", value=" • ".join(info["genres"]), inline=False)
    if info["episodes"]:
        embed.add_field(name="Episodes", value=str(info["episodes"]))
    if info["status"]:
        embed.add_field(name="Status", value=info["status"])
    if info["score"]:
        embed.add_field(name="MAL Score", value=f"⭐ {info['score']}")
    if info["image_url"]:
        embed.set_thumbnail(url=info["image_url"])
    embed.set_footer(text="Data from MyAnimeList via Jikan API")
    return embed


class AnimeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    anime_group = app_commands.Group(name="anime", description="Look up anime information")

    @anime_group.command(name="search", description="Search MyAnimeList for an anime")
    @app_commands.describe(name="Title to search for")
    async def search(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        try:
            info = await anime_service.search_anime(name)
        except anime_service.AnimeNotFoundError as e:
            await interaction.followup.send(str(e))
            return
        await interaction.followup.send(embed=_anime_embed(info))

    @anime_group.command(name="random", description="Get a random anime suggestion")
    async def random(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            info = await anime_service.random_anime()
        except anime_service.AnimeNotFoundError as e:
            await interaction.followup.send(str(e))
            return
        await interaction.followup.send(embed=_anime_embed(info))

    @anime_group.command(name="top", description="Show the current top-rated anime")
    async def top(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            results = await anime_service.top_anime(limit=5)
        except anime_service.AnimeNotFoundError as e:
            await interaction.followup.send(str(e))
            return

        lines = [
            f"**{i + 1}. {info['title']}** — ⭐ {info['score'] or 'N/A'}"
            for i, info in enumerate(results)
        ]
        embed = discord.Embed(
            title="Top Anime (MyAnimeList)",
            description="\n".join(lines),
            colour=discord.Colour.purple(),
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AnimeCog(bot))
