from __future__ import annotations

import logging

import pygame

from .config import SCREEN_HEIGHT, SCREEN_WIDTH

logger = logging.getLogger("virtual_pet")

WAVESHARE_LCD_SPI_PORT = 0
WAVESHARE_LCD_SPI_CS = 0
WAVESHARE_LCD_DC_PIN = 25
WAVESHARE_LCD_RST_PIN = 27
WAVESHARE_LCD_BACKLIGHT_PIN = 24
WAVESHARE_LCD_SPI_SPEED_HZ = 40_000_000


class DirectSpiDisplay:
    def __init__(self, rotation: int = 0) -> None:
        from PIL import Image
        import st7789

        self._image_module = Image
        self._display = st7789.ST7789(
            port=WAVESHARE_LCD_SPI_PORT,
            cs=WAVESHARE_LCD_SPI_CS,
            dc=WAVESHARE_LCD_DC_PIN,
            backlight=WAVESHARE_LCD_BACKLIGHT_PIN,
            rst=WAVESHARE_LCD_RST_PIN,
            width=SCREEN_WIDTH,
            height=SCREEN_HEIGHT,
            rotation=rotation,
            spi_speed_hz=WAVESHARE_LCD_SPI_SPEED_HZ,
        )
        logger.info("Initialized direct SPI output for the Waveshare ST7789 display.")

    def present(self, surface: pygame.Surface) -> None:
        rgb_bytes = pygame.image.tostring(surface, "RGB")
        frame = self._image_module.frombytes("RGB", surface.get_size(), rgb_bytes)
        self._display.display(frame)


def create_display_backend(enable_direct_output: bool, rotation: int = 0) -> DirectSpiDisplay | None:
    if not enable_direct_output:
        return None

    try:
        return DirectSpiDisplay(rotation=rotation)
    except ImportError:
        logger.warning(
            "Direct SPI output requested, but one or more packages are missing. "
            "Install pillow and st7789 on the Pi to drive the HAT directly."
        )
    except Exception:
        logger.exception("Direct SPI display initialization failed. Falling back to the normal pygame display path.")

    return None
