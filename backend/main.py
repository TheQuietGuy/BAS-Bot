import logging

from backend import config
from backend.bot.bot import create_bot
from backend.database.database import get_session, init_db
from backend.services.achievement_service import seed_achievements

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    init_db()
    with get_session() as session:
        seed_achievements(session)
    bot = create_bot()
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
