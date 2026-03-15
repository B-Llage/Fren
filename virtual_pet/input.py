from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("virtual_pet")

INPUT_PREVIOUS = "previous"
INPUT_NEXT = "next"
INPUT_CONFIRM = "confirm"
INPUT_BACK = "back"


@dataclass(frozen=True)
class ButtonMapping:
    name: str
    pin: int
    actions: tuple[str, ...]


WAVESHARE_HAT_BUTTONS = (
    ButtonMapping("joy_up", 6, (INPUT_PREVIOUS,)),
    ButtonMapping("joy_down", 19, (INPUT_NEXT,)),
    ButtonMapping("joy_left", 5, (INPUT_PREVIOUS,)),
    ButtonMapping("joy_right", 26, (INPUT_NEXT,)),
    ButtonMapping("joy_press", 13, (INPUT_CONFIRM,)),
    ButtonMapping("key1", 21, (INPUT_PREVIOUS,)),
    ButtonMapping("key2", 20, (INPUT_CONFIRM,)),
    ButtonMapping("key3", 16, (INPUT_BACK,)),
)


class WaveshareHatInput:
    def __init__(self, button_factory=None) -> None:
        if button_factory is None:
            from gpiozero import Button as button_factory

        self._buttons: list[tuple[ButtonMapping, object]] = []
        self._pressed_states: dict[str, bool] = {}
        for mapping in WAVESHARE_HAT_BUTTONS:
            button = button_factory(mapping.pin, pull_up=True, bounce_time=0.05)
            self._buttons.append((mapping, button))
            self._pressed_states[mapping.name] = self._is_pressed(button)

        logger.info("Initialized Waveshare HAT input on %s GPIO inputs.", len(self._buttons))

    def poll_actions(self) -> list[str]:
        actions: list[str] = []
        for mapping, button in self._buttons:
            is_pressed = self._is_pressed(button)
            was_pressed = self._pressed_states[mapping.name]
            if is_pressed and not was_pressed:
                actions.extend(mapping.actions)
            self._pressed_states[mapping.name] = is_pressed
        return actions

    def close(self) -> None:
        for _mapping, button in self._buttons:
            close = getattr(button, "close", None)
            if callable(close):
                close()

    @staticmethod
    def _is_pressed(button: object) -> bool:
        return bool(getattr(button, "is_pressed", False))


def create_input_backend(enable_gpio_input: bool) -> WaveshareHatInput | None:
    if not enable_gpio_input:
        return None

    try:
        return WaveshareHatInput()
    except ImportError:
        logger.warning("GPIO input requested, but gpiozero is not installed. Falling back to keyboard input.")
    except Exception:
        logger.exception("GPIO input initialization failed. Falling back to keyboard input.")

    return None
