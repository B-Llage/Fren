from __future__ import annotations

import logging
import time

import pygame

from .config import SCREEN_HEIGHT, SCREEN_WIDTH

logger = logging.getLogger("virtual_pet")

WAVESHARE_LCD_SPI_PORT = 0
WAVESHARE_LCD_SPI_CS = 0
WAVESHARE_LCD_DC_PIN = 25
WAVESHARE_LCD_RST_PIN = 27
WAVESHARE_LCD_BACKLIGHT_PIN = 24
WAVESHARE_LCD_SPI_SPEED_HZ = 40_000_000
WAVESHARE_LCD_INIT_DELAY_SECONDS = 0.12
WAVESHARE_LCD_TARGET_FPS = 15


class DirectSpiDisplay:
    def __init__(self, rotation: int = 0) -> None:
        import numpy
        import spidev
        from gpiozero import OutputDevice

        self._numpy = numpy
        self._rotation_steps = (rotation // 90) % 4
        self._clear_frame = bytes(SCREEN_WIDTH * SCREEN_HEIGHT * 2)
        self._frame_interval_seconds = 1.0 / WAVESHARE_LCD_TARGET_FPS
        self._last_present_at = 0.0
        self._saturation = 1.0
        self._saturation_scale = 256

        self._spi = spidev.SpiDev()
        self._spi.open(WAVESHARE_LCD_SPI_PORT, WAVESHARE_LCD_SPI_CS)
        self._spi.max_speed_hz = WAVESHARE_LCD_SPI_SPEED_HZ
        self._spi.mode = 0

        self._dc = OutputDevice(WAVESHARE_LCD_DC_PIN, active_high=True, initial_value=False)
        self._rst = OutputDevice(WAVESHARE_LCD_RST_PIN, active_high=True, initial_value=True)
        self._backlight = OutputDevice(WAVESHARE_LCD_BACKLIGHT_PIN, active_high=True, initial_value=True)

        self.reset()
        self.initialize()
        self.clear()
        logger.info("Initialized direct SPI output for the Waveshare ST7789 display.")

    def set_saturation(self, saturation: float) -> None:
        self._saturation = max(0.5, min(1.6, float(saturation)))
        self._saturation_scale = int(round(self._saturation * 256.0))

    def reset(self) -> None:
        self._rst.on()
        time.sleep(0.01)
        self._rst.off()
        time.sleep(0.01)
        self._rst.on()
        time.sleep(0.01)

    def initialize(self) -> None:
        self.write_command(0x36)
        self.write_data((0x70,))

        self.write_command(0x3A)
        self.write_data((0x05,))

        self.write_command(0xB2)
        self.write_data((0x0C, 0x0C, 0x00, 0x33, 0x33))

        self.write_command(0xB7)
        self.write_data((0x35,))

        self.write_command(0xBB)
        self.write_data((0x19,))

        self.write_command(0xC0)
        self.write_data((0x2C,))

        self.write_command(0xC2)
        self.write_data((0x01,))

        self.write_command(0xC3)
        self.write_data((0x12,))

        self.write_command(0xC4)
        self.write_data((0x20,))

        self.write_command(0xC6)
        self.write_data((0x0F,))

        self.write_command(0xD0)
        self.write_data((0xA4, 0xA1))

        self.write_command(0xE0)
        self.write_data((0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23))

        self.write_command(0xE1)
        self.write_data((0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23))

        self.write_command(0x21)
        self.write_command(0x11)
        time.sleep(WAVESHARE_LCD_INIT_DELAY_SECONDS)
        self.write_command(0x29)
        time.sleep(0.05)

    def clear(self) -> None:
        self.set_window(0, 0, SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1)
        self.write_frame(self._clear_frame)

    def present(self, surface: pygame.Surface) -> None:
        now = time.monotonic()
        if self._last_present_at and (now - self._last_present_at) < self._frame_interval_seconds:
            return

        self._last_present_at = now
        rgb_bytes = pygame.image.tostring(surface, "RGB")
        frame = self._numpy.frombuffer(rgb_bytes, dtype=self._numpy.uint8).reshape((SCREEN_HEIGHT, SCREEN_WIDTH, 3))
        if self._rotation_steps:
            frame = self._numpy.rot90(frame, k=self._rotation_steps)
        if self._saturation_scale != 256:
            frame = self.apply_saturation(frame)

        pixel_data = (
            ((frame[..., 0].astype(self._numpy.uint16) & 0xF8) << 8)
            | ((frame[..., 1].astype(self._numpy.uint16) & 0xFC) << 3)
            | (frame[..., 2].astype(self._numpy.uint16) >> 3)
        )
        payload = pixel_data.astype(">u2", copy=False).tobytes()
        self.set_window(0, 0, SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1)
        self.write_frame(payload)

    def apply_saturation(self, frame: object) -> object:
        frame_i32 = frame.astype(self._numpy.int32, copy=False)
        luma = (
            (54 * frame_i32[..., 0])
            + (183 * frame_i32[..., 1])
            + (19 * frame_i32[..., 2])
        ) >> 8
        saturated = luma[..., None] + (((frame_i32 - luma[..., None]) * self._saturation_scale) >> 8)
        return self._numpy.clip(saturated, 0, 255).astype(self._numpy.uint8)

    def set_window(self, x_start: int, y_start: int, x_end: int, y_end: int) -> None:
        self.write_command(0x2A)
        self.write_data(
            (
                (x_start >> 8) & 0xFF,
                x_start & 0xFF,
                (x_end >> 8) & 0xFF,
                x_end & 0xFF,
            )
        )
        self.write_command(0x2B)
        self.write_data(
            (
                (y_start >> 8) & 0xFF,
                y_start & 0xFF,
                (y_end >> 8) & 0xFF,
                y_end & 0xFF,
            )
        )
        self.write_command(0x2C)

    def write_command(self, command: int) -> None:
        self._dc.off()
        self._write((command & 0xFF,))

    def write_data(self, data: bytes | tuple[int, ...] | list[int]) -> None:
        self._dc.on()
        self._write(data)

    def write_frame(self, frame_bytes: bytes) -> None:
        self._dc.on()
        self._write(frame_bytes)

    def _write(self, payload: bytes | tuple[int, ...] | list[int]) -> None:
        writebytes2 = getattr(self._spi, "writebytes2", None)
        if callable(writebytes2):
            writebytes2(payload)
            return

        self._spi.xfer3(list(payload))

    def close(self) -> None:
        for device in (self._backlight, self._rst, self._dc):
            close = getattr(device, "close", None)
            if callable(close):
                close()
        close_spi = getattr(self._spi, "close", None)
        if callable(close_spi):
            close_spi()


def create_display_backend(enable_direct_output: bool, rotation: int = 0) -> DirectSpiDisplay | None:
    if not enable_direct_output:
        return None

    try:
        return DirectSpiDisplay(rotation=rotation)
    except ImportError:
        logger.warning(
            "Direct SPI output requested, but one or more packages are missing. "
            "Install python3-spidev, python3-numpy, and gpiozero on the Pi."
        )
    except Exception:
        logger.exception("Direct SPI display initialization failed. Falling back to the normal pygame display path.")

    return None
