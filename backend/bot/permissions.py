"""Permission checks. Never trust a username — always check Discord role IDs."""
import discord
from discord import app_commands

from backend import config


def is_committee_member(member: discord.Member) -> bool:
    if not config.COMMITTEE_ROLE_IDS:
        # No committee roles configured yet -- fail safe by denying everyone
        # rather than silently granting admin powers to all members.
        return False
    member_role_ids = {role.id for role in member.roles}
    return bool(member_role_ids & config.COMMITTEE_ROLE_IDS)


def committee_only():
    """Decorator for app_commands that restricts a command to committee members."""

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        if is_committee_member(interaction.user):
            return True
        raise app_commands.CheckFailure(
            "You need a committee role to use this command."
        )

    return app_commands.check(predicate)
