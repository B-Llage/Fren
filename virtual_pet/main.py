from __future__ import annotations

import logging
from collections.abc import Sequence

from .game import Game
from .runtime import build_runtime_config


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
    )


def main(argv: Sequence[str] | None = None) -> int:
    configure_logging()
    logger = logging.getLogger("virtual_pet")
    logger.info("Starting virtual pet template...")
    runtime = build_runtime_config(argv)
    logger.info(
        "Runtime profile=%s fullscreen=%s gpio_input=%s direct_output=%s rotation=%s model=%s",
        runtime.profile,
        runtime.fullscreen,
        runtime.enable_gpio_input,
        runtime.enable_direct_output,
        runtime.display_rotation,
        runtime.detected_model or "n/a",
    )

    game: Game | None = None
    try:
        logger.info("Creating game instance...")
        game = Game(runtime=runtime)
        return game.run()
    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
        if game is not None:
            game.shutdown(save=False)
        return 1
