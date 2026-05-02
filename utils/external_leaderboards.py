import logging

import aiohttp

from config import LEADERBOARD_SERVICES

log = logging.getLogger(__name__)


async def award_points_externally(
    user_id: int,
    guild_id: int,
    username: str,
    points: int,
    match_id: str | None = None,
) -> None:
    """Fire-and-forget POST to every enabled external leaderboard service."""
    if not LEADERBOARD_SERVICES:
        return

    payload = {
        "user_id": user_id,
        "guild_id": guild_id,
        "username": username,
        "points": points,
        "game_id": match_id,
    }

    async with aiohttp.ClientSession() as session:
        for name, cfg in LEADERBOARD_SERVICES.items():
            if cfg["guilds"] and str(guild_id) not in cfg["guilds"]:
                continue
            headers = {"Authorization": f"Bearer {cfg['api_key']}"}
            try:
                async with session.post(
                    f"{cfg['url']}/api/v1/points",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    data = await resp.json()
                    log.debug("External leaderboard %s response: %s", name, data)
            except Exception as exc:
                log.warning("Failed to post points to external leaderboard %s: %s", name, exc)
