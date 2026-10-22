import logging

import discord
from discord import app_commands
from discord.ext import commands

from backend import config

logger = logging.getLogger("bas-bot")

INITIAL_EXTENSIONS = (
    "backend.bot.commands.general",
    "backend.bot.commands.leaderboard",
    "backend.bot.commands.anime",
    "backend.bot.commands.admin",
    "backend.bot.commands.events",
    "backend.bot.commands.achievements",
    "backend.bot.scheduler",
)


class BASBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # needed to resolve display names / roles reliably
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        for extension in INITIAL_EXTENSIONS:
            await self.load_extension(extension)
            logger.info("Loaded extension %s", extension)

        if config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info("Synced %d commands to guild %s", len(synced), config.GUILD_ID)
        else:
            synced = await self.tree.sync()
            logger.info(
                "Synced %d commands globally (can take up to an hour to appear; "
                "set GUILD_ID in .env for instant syncing during development)",
                len(synced),
            )

    async def on_ready(self):
        logger.info("Logged in as %s (id=%s)", self.user, self.user.id)

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CheckFailure):
            message = str(error) or "You don't have permission to use this command."
        else:
            logger.exception("Unhandled app command error", exc_info=error)
            message = "Something went wrong running that command."

        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


def create_bot() -> BASBot:
    return BASBot()
