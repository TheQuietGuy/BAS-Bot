"""Wrapper around the free Jikan API (unofficial MyAnimeList API).

Docs: https://docs.api.jikan.moe/
No API key needed. Results are cached in the local AnimeCache table so
repeat lookups (e.g. /anime Frieren twice) don't keep hitting the API.

Jikan rate-limits fairly aggressively (3 req/sec, 60/min) and occasionally
hiccups, so every request here has a timeout, one retry on a 429, and
every failure mode (bad status, network error, unexpected response shape)
turns into a clear AnimeNotFoundError instead of an unhandled 500.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import aiohttp
from sqlalchemy import select

from backend.database.database import get_session
from backend.database.models import AnimeCache

logger = logging.getLogger("bas-bot.anime")

JIKAN_BASE = "https://api.jikan.moe/v4"
CACHE_TTL = timedelta(hours=12)
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)
HEADERS = {"User-Agent": "BAS-Bot/1.0 (Brunel Anime Society Discord bot)"}


class AnimeNotFoundError(Exception):
    pass


def _cache_to_dict(entry: AnimeCache) -> dict:
    return {
        "mal_id": entry.mal_id,
        "title": entry.title,
        "description": entry.description,
        "score": entry.score,
        "episodes": entry.episodes,
        "status": entry.status,
        "genres": [g for g in entry.genres.split(",") if g],
        "image_url": entry.image_url,
        "mal_url": entry.mal_url,
    }


def _api_result_to_dict(data: dict) -> dict:
    return {
        "mal_id": data["mal_id"],
        "title": data.get("title") or data.get("title_english") or "Unknown",
        "description": (data.get("synopsis") or "")[:1000],
        "score": data.get("score"),
        "episodes": data.get("episodes"),
        "status": data.get("status") or "",
        "genres": [g["name"] for g in data.get("genres", [])],
        "image_url": (data.get("images", {}).get("jpg", {}) or {}).get("image_url", ""),
        "mal_url": data.get("url", ""),
    }


def _save_to_cache(info: dict) -> None:
    with get_session() as session:
        existing = session.scalar(select(AnimeCache).where(AnimeCache.mal_id == info["mal_id"]))
        genres_str = ",".join(info["genres"])
        if existing:
            existing.title = info["title"]
            existing.description = info["description"]
            existing.score = info["score"]
            existing.episodes = info["episodes"]
            existing.status = info["status"]
            existing.genres = genres_str
            existing.image_url = info["image_url"]
            existing.mal_url = info["mal_url"]
            existing.last_updated = datetime.now(timezone.utc)
        else:
            session.add(AnimeCache(
                mal_id=info["mal_id"],
                title=info["title"],
                description=info["description"],
                score=info["score"],
                episodes=info["episodes"],
                status=info["status"],
                genres=genres_str,
                image_url=info["image_url"],
                mal_url=info["mal_url"],
            ))
        session.commit()


async def _get_json(path: str, params: Optional[dict] = None) -> dict:
    """GET a Jikan endpoint with a timeout, one retry on 429, and every
    failure (bad status, network error, malformed JSON) turned into
    AnimeNotFoundError with a message that actually says what went wrong."""
    url = f"{JIKAN_BASE}{path}"

    for attempt in range(2):
        try:
            async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT, headers=HEADERS) as http:
                async with http.get(url, params=params) as resp:
                    if resp.status == 429 and attempt == 0:
                        logger.info("Jikan rate-limited us on %s, retrying once", path)
                        await asyncio.sleep(2)
                        continue
                    if resp.status != 200:
                        body = await resp.text()
                        raise AnimeNotFoundError(
                            f"MyAnimeList lookup failed (HTTP {resp.status}). {body[:200]}"
                        )
                    try:
                        return await resp.json()
                    except (aiohttp.ContentTypeError, ValueError) as e:
                        raise AnimeNotFoundError(
                            f"MyAnimeList returned something unexpected: {e}"
                        )
        except AnimeNotFoundError:
            raise
        except asyncio.TimeoutError:
            raise AnimeNotFoundError(
                "MyAnimeList didn't respond in time. Try again in a moment."
            )
        except aiohttp.ClientConnectorError as e:
            raise AnimeNotFoundError(
                f"Couldn't reach MyAnimeList — check your internet connection. ({e})"
            )
        except aiohttp.ClientError as e:
            raise AnimeNotFoundError(f"MyAnimeList request failed: {e}")

    # Only reached if we retried once on 429 and it happened again.
    raise AnimeNotFoundError("MyAnimeList is rate-limiting us right now. Try again shortly.")


async def search_anime(query: str) -> dict:
    """Search MyAnimeList (via Jikan) for the best-matching anime and return its info.

    Raises AnimeNotFoundError if nothing matches, or the request fails.
    """
    payload = await _get_json(
        "/anime", params={"q": query, "limit": 1, "order_by": "popularity", "sort": "asc"}
    )

    results = payload.get("data") or []
    if not results:
        raise AnimeNotFoundError(f"No anime found matching '{query}'")

    try:
        info = _api_result_to_dict(results[0])
    except (KeyError, TypeError) as e:
        raise AnimeNotFoundError(f"MyAnimeList returned an unexpected result shape: {e}")

    _save_to_cache(info)
    return info


async def random_anime() -> dict:
    payload = await _get_json("/random/anime")

    data = payload.get("data")
    if not data:
        raise AnimeNotFoundError("MyAnimeList didn't return a random anime -- try again.")

    try:
        info = _api_result_to_dict(data)
    except (KeyError, TypeError) as e:
        raise AnimeNotFoundError(f"MyAnimeList returned an unexpected result shape: {e}")

    _save_to_cache(info)
    return info


async def top_anime(limit: int = 5) -> list[dict]:
    payload = await _get_json("/top/anime", params={"limit": limit})

    raw_results = payload.get("data") or []
    results = []
    for item in raw_results:
        try:
            results.append(_api_result_to_dict(item))
        except (KeyError, TypeError):
            continue  # skip one malformed entry rather than failing the whole list

    for info in results:
        _save_to_cache(info)
    return results
