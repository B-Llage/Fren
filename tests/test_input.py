from __future__ import annotations

import unittest

from virtual_pet.input import INPUT_BACK, INPUT_CONFIRM, INPUT_DOWN, INPUT_LEFT, INPUT_NEXT, INPUT_RIGHT, INPUT_UP, WaveshareHatInput


class FakeButton:
    def __init__(self, pin: int, pull_up: bool = True, bounce_time: float | None = None) -> None:
        self.pin = pin
        self.pull_up = pull_up
        self.bounce_time = bounce_time
        self.is_pressed = False
        self.closed = False

    def close(self) -> None:
        self.closed = True


class WaveshareHatInputTests(unittest.TestCase):
    def build_backend(self, rotation: int = 0) -> tuple[WaveshareHatInput, dict[int, FakeButton]]:
        created_buttons: dict[int, FakeButton] = {}

        def button_factory(pin: int, pull_up: bool = True, bounce_time: float | None = None) -> FakeButton:
            button = FakeButton(pin, pull_up=pull_up, bounce_time=bounce_time)
            created_buttons[pin] = button
            return button

        return WaveshareHatInput(button_factory=button_factory, rotation=rotation), created_buttons

    def test_button_edges_emit_actions_once_per_press(self) -> None:
        backend, buttons = self.build_backend()

        buttons[6].is_pressed = True
        self.assertEqual(backend.poll_actions(), [INPUT_UP])
        self.assertEqual(backend.poll_actions(), [])

        buttons[6].is_pressed = False
        self.assertEqual(backend.poll_actions(), [])

        buttons[13].is_pressed = True
        self.assertEqual(backend.poll_actions(), [INPUT_CONFIRM])

        buttons[13].is_pressed = False
        buttons[16].is_pressed = True
        self.assertEqual(backend.poll_actions(), [INPUT_BACK])

    def test_key1_cycles_forward(self) -> None:
        backend, buttons = self.build_backend()

        buttons[21].is_pressed = True
        self.assertEqual(backend.poll_actions(), [INPUT_NEXT])

    def test_is_confirm_pressed_checks_confirm_buttons(self) -> None:
        backend, buttons = self.build_backend()

        self.assertFalse(backend.is_confirm_pressed())

        buttons[20].is_pressed = True
        self.assertTrue(backend.is_confirm_pressed())

    def test_close_closes_all_buttons(self) -> None:
        backend, buttons = self.build_backend()

        backend.close()

        self.assertTrue(all(button.closed for button in buttons.values()))

    def test_display_rotation_remaps_directional_actions(self) -> None:
        backend, buttons = self.build_backend(rotation=180)

        buttons[6].is_pressed = True
        self.assertEqual(backend.poll_actions(), [INPUT_DOWN])

        buttons[6].is_pressed = False
        backend.poll_actions()
        buttons[5].is_pressed = True
        self.assertEqual(backend.poll_actions(), [INPUT_RIGHT])

        backend, buttons = self.build_backend(rotation=90)
        buttons[26].is_pressed = True
        self.assertEqual(backend.poll_actions(), [INPUT_DOWN])

        backend, buttons = self.build_backend(rotation=270)
        buttons[19].is_pressed = True
        self.assertEqual(backend.poll_actions(), [INPUT_RIGHT])


if __name__ == "__main__":
    unittest.main()
