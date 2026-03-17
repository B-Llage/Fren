from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest import mock

from tests.pygame_stub import install_pygame_stub


class SleepModeTests(unittest.TestCase):
    def load_game_modules(self):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        pygame_stub = install_pygame_stub()
        for module_name in [
            "pygame",
            "virtual_pet.audio",
            "virtual_pet.game",
            "virtual_pet.renderer",
            "virtual_pet.runtime",
        ]:
            sys.modules.pop(module_name, None)

        module_patch = mock.patch.dict(sys.modules, {"pygame": pygame_stub})
        module_patch.start()
        self.addCleanup(module_patch.stop)

        game_module = importlib.import_module("virtual_pet.game")
        models_module = importlib.import_module("virtual_pet.models")
        runtime_module = importlib.import_module("virtual_pet.runtime")
        splash_patch = mock.patch.object(game_module.Game, "show_startup_splash_safe", autospec=True, return_value=None)
        splash_patch.start()
        self.addCleanup(splash_patch.stop)
        return pygame_stub, game_module, models_module, runtime_module

    def test_main_menu_sleep_option_enters_sleep_mode(self) -> None:
        _pygame_stub, game_module, models_module, _runtime_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.state.menu_state = models_module.MenuState.MAIN_MENU
            game.state.selected_menu = game.main_menu.index("Sleep")

            game.confirm_selection()

            self.assertEqual(game.state.menu_state, models_module.MenuState.SLEEP)
        finally:
            game.shutdown(save=False)

    def test_sleep_mode_only_updates_decay_until_wake(self) -> None:
        _pygame_stub, game_module, models_module, _runtime_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.enter_sleep_mode()
            starting_age = game.pet.age_ticks
            game.state.decay_accumulator = game_module.DECAY_TIMER_SECONDS - 0.25

            with (
                mock.patch.object(game, "refresh_battery_status") as battery_refresh,
                mock.patch.object(game, "show_startup_splash_safe") as splash_mock,
            ):
                game.update(0.5)

            battery_refresh.assert_not_called()
            splash_mock.assert_not_called()
            self.assertEqual(game.pet.age_ticks, starting_age + 1)
            self.assertEqual(game.state.menu_state, models_module.MenuState.SLEEP)
        finally:
            game.shutdown(save=False)

    def test_sleep_mode_wakes_after_confirm_hold(self) -> None:
        _pygame_stub, game_module, models_module, _runtime_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.enter_sleep_mode()

            with (
                mock.patch.object(game, "show_startup_splash_safe") as splash_mock,
                mock.patch.object(game, "refresh_battery_status") as battery_refresh,
            ):
                game.keyboard_confirm_active = True
                game.update(game_module.SLEEP_WAKE_HOLD_SECONDS)

            splash_mock.assert_called_once_with()
            battery_refresh.assert_called_once_with()
            self.assertEqual(game.state.menu_state, models_module.MenuState.HOME)
            self.assertEqual(game.state.sleep_wake_hold_elapsed, 0.0)
        finally:
            game.shutdown(save=False)

    def test_hat_sleep_toggles_display_power_state(self) -> None:
        _pygame_stub, game_module, models_module, runtime_module = self.load_game_modules()

        fake_display_backend = mock.Mock()
        with mock.patch.object(game_module, "create_display_backend", return_value=fake_display_backend):
            game = game_module.Game(
                runtime=runtime_module.RuntimeConfig(
                    profile=runtime_module.PROFILE_WAVESHARE_HAT,
                    fullscreen=True,
                    hide_mouse=True,
                    enable_gpio_input=False,
                    enable_direct_output=True,
                    allow_display_scale=False,
                )
            )

        try:
            fake_display_backend.reset_mock()
            game.enter_sleep_mode()
            fake_display_backend.set_sleeping.assert_called_once_with(True)
            self.assertEqual(game.state.menu_state, models_module.MenuState.SLEEP)

            fake_display_backend.reset_mock()
            with (
                mock.patch.object(game, "show_startup_splash_safe") as splash_mock,
                mock.patch.object(game, "refresh_battery_status") as battery_refresh,
            ):
                game.keyboard_confirm_active = True
                game.update(game_module.SLEEP_WAKE_HOLD_SECONDS)

            fake_display_backend.set_sleeping.assert_called_once_with(False)
            splash_mock.assert_called_once_with()
            battery_refresh.assert_called_once_with()
            self.assertEqual(game.state.menu_state, models_module.MenuState.HOME)
        finally:
            game.shutdown(save=False)

    def test_pi_inactivity_enters_sleep_mode_after_sixty_seconds(self) -> None:
        _pygame_stub, game_module, models_module, runtime_module = self.load_game_modules()

        game = game_module.Game(
            runtime=runtime_module.RuntimeConfig(
                profile=runtime_module.PROFILE_WAVESHARE_HAT,
                fullscreen=True,
                hide_mouse=True,
                enable_gpio_input=False,
                enable_direct_output=False,
                allow_display_scale=False,
                detected_model="Raspberry Pi Zero 2 W Rev 1.0",
            )
        )
        try:
            game.update(game_module.SLEEP_IDLE_TIMEOUT_SECONDS)

            self.assertEqual(game.state.menu_state, models_module.MenuState.SLEEP)
            self.assertEqual(game.sleep_idle_elapsed, 0.0)
        finally:
            game.shutdown(save=False)

    def test_input_resets_pi_inactivity_timer(self) -> None:
        _pygame_stub, game_module, models_module, runtime_module = self.load_game_modules()

        game = game_module.Game(
            runtime=runtime_module.RuntimeConfig(
                profile=runtime_module.PROFILE_WAVESHARE_HAT,
                fullscreen=True,
                hide_mouse=True,
                enable_gpio_input=False,
                enable_direct_output=False,
                allow_display_scale=False,
                detected_model="Raspberry Pi Zero 2 W Rev 1.0",
            )
        )
        try:
            game.sleep_idle_elapsed = game_module.SLEEP_IDLE_TIMEOUT_SECONDS - 1.0

            game.handle_input_action(game_module.INPUT_NEXT)
            game.update(2.0)

            self.assertNotEqual(game.state.menu_state, models_module.MenuState.SLEEP)
            self.assertLess(game.sleep_idle_elapsed, game_module.SLEEP_IDLE_TIMEOUT_SECONDS)
        finally:
            game.shutdown(save=False)

    def test_desktop_does_not_auto_sleep_from_inactivity(self) -> None:
        _pygame_stub, game_module, models_module, _runtime_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.update(game_module.SLEEP_IDLE_TIMEOUT_SECONDS + 5.0)

            self.assertEqual(game.state.menu_state, models_module.MenuState.HOME)
        finally:
            game.shutdown(save=False)


if __name__ == "__main__":
    unittest.main()
