from fastapi import APIRouter

from backend.services import discord_directory

router = APIRouter(prefix="/api/discord", tags=["discord"])


@router.get("/channels")
async def list_channels():
    """Text channels in the society's server, for channel dropdowns.
    Returns an empty list (not an error) if Discord can't be reached, so
    the dashboard can fall back to manual ID entry."""
    return await discord_directory.fetch_guild_channels()


@router.get("/members")
async def list_members():
    """Non-bot members of the society's server, for member pickers.
    Empty list if unavailable -- the dashboard falls back to manual entry."""
    return await discord_directory.fetch_guild_members()
