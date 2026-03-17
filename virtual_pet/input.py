from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("virtual_pet")

INPUT_UP = "up"
INPUT_DOWN = "down"
INPUT_LEFT = "left"
INPUT_RIGHT = "right"
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
    ButtonMapping("joy_up", 6, (INPUT_UP,)),
    ButtonMapping("joy_down", 19, (INPUT_DOWN,)),
    ButtonMapping("joy_left", 5, (INPUT_LEFT,)),
    ButtonMapping("joy_right", 26, (INPUT_RIGHT,)),
    ButtonMapping("joy_press", 13, (INPUT_CONFIRM,)),
    ButtonMapping("key1", 21, (INPUT_NEXT,)),
    ButtonMapping("key2", 20, (INPUT_CONFIRM,)),
    ButtonMapping("key3", 16, (INPUT_BACK,)),
)


class WaveshareHatInput:
    def __init__(self, button_factory=None, rotation: int = 0) -> None:
        if button_factory is None:
            from gpiozero import Button as button_factory

        self._rotation = rotation % 360
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
                actions.extend(self.rotate_actions(mapping.actions))
            self._pressed_states[mapping.name] = is_pressed
        return actions

    def is_confirm_pressed(self) -> bool:
        for mapping, button in self._buttons:
            if INPUT_CONFIRM in mapping.actions and self._is_pressed(button):
                return True

        return False

    def rotate_actions(self, actions: tuple[str, ...]) -> list[str]:
        rotated_actions: list[str] = []
        for action in actions:
            rotated_actions.append(self.rotate_action(action))
        return rotated_actions

    def rotate_action(self, action: str) -> str:
        if self._rotation == 0:
            return action

        if self._rotation == 90:
            return {
                INPUT_UP: INPUT_RIGHT,
                INPUT_RIGHT: INPUT_DOWN,
                INPUT_DOWN: INPUT_LEFT,
                INPUT_LEFT: INPUT_UP,
            }.get(action, action)

        if self._rotation == 180:
            return {
                INPUT_UP: INPUT_DOWN,
                INPUT_RIGHT: INPUT_LEFT,
                INPUT_DOWN: INPUT_UP,
                INPUT_LEFT: INPUT_RIGHT,
            }.get(action, action)

        if self._rotation == 270:
            return {
                INPUT_UP: INPUT_LEFT,
                INPUT_LEFT: INPUT_DOWN,
                INPUT_DOWN: INPUT_RIGHT,
                INPUT_RIGHT: INPUT_UP,
            }.get(action, action)

        return action

    def close(self) -> None:
        for _mapping, button in self._buttons:
            close = getattr(button, "close", None)
            if callable(close):
                close()

    @staticmethod
    def _is_pressed(button: object) -> bool:
        return bool(getattr(button, "is_pressed", False))


def create_input_backend(enable_gpio_input: bool, rotation: int = 0) -> WaveshareHatInput | None:
    if not enable_gpio_input:
        return None

    try:
        return WaveshareHatInput(rotation=rotation)
    except ImportError:
        logger.warning("GPIO input requested, but gpiozero is not installed. Falling back to keyboard input.")
    except Exception:
        logger.exception("GPIO input initialization failed. Falling back to keyboard input.")

    return None
