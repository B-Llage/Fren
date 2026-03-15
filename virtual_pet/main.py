from __future__ import annotations

import logging

from .game import Game


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
    )


def main() -> int:
    configure_logging()
    logger = logging.getLogger("virtual_pet")
    logger.info("Starting virtual pet template...")

    game: Game | None = None
    try:
        logger.info("Creating game instance...")
        game = Game()
        return game.run()
    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
        if game is not None:
            game.shutdown(save=False)
        return 1
