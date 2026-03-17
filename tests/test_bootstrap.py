from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest import mock

from tests.pygame_stub import install_pygame_stub


class BootstrapTests(unittest.TestCase):
    def test_main_module_and_wrapper_bootstrap_with_stubbed_pygame(self) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        pygame_stub = install_pygame_stub()

        for module_name in [
            "pygame",
            "virtual_pet.audio",
            "virtual_pet.game",
            "virtual_pet.main",
            "virtual_pet.renderer",
            "virtual_pet_template",
        ]:
            sys.modules.pop(module_name, None)

        with mock.patch.dict(sys.modules, {"pygame": pygame_stub}):
            main_module = importlib.import_module("virtual_pet.main")
            game_module = importlib.import_module("virtual_pet.game")
            models_module = importlib.import_module("virtual_pet.models")
            runtime_module = importlib.import_module("virtual_pet.runtime")
            wrapper_module = importlib.import_module("virtual_pet_template")

            with mock.patch.object(game_module.Game, "show_startup_splash_safe", autospec=True, return_value=None):
                game = game_module.Game()
            
            try:
                self.assertIsNotNone(game.renderer)
                self.assertIsNotNone(game.audio)
                self.assertEqual(game.audio.master_volume, game.settings.sound_volume)
                self.assertIn("Res", game.option_menu)
                self.assertNotIn("Auto Upd", game.option_menu)
                self.assertNotIn("Color", game.option_menu)
                self.assertNotIn("Contrast", game.option_menu)
                played_sounds: list[str] = []
                game.audio.play = played_sounds.append
                game.state.menu_state = models_module.MenuState.MAIN_MENU
                game.state.selected_menu = 0
                game.handle_keyboard_input(pygame_stub.K_a)
                self.assertEqual(game.state.selected_menu, len(game.main_menu) - 1)
                game.state.menu_state = models_module.MenuState.ACTIONS
                game.state.selected_action = game.actions.index("Clean")
                game.confirm_selection()
                self.assertEqual(game.state.menu_state, models_module.MenuState.CLEANING)
                game.confirm_selection()
                self.assertEqual(game.state.menu_state, models_module.MenuState.CELEBRATING)
                game.confirm_selection()
                self.assertEqual(game.state.menu_state, models_module.MenuState.HOME)
                game.complete_eating_animation()
                self.assertEqual(game.state.menu_state, models_module.MenuState.CELEBRATING)
                game.complete_action_celebration()
                self.assertEqual(game.state.menu_state, models_module.MenuState.HOME)
                starting_happiness = game.pet.happiness
                game.state.menu_state = models_module.MenuState.ACTIONS
                game.state.selected_action = game.actions.index("Play")
                game.confirm_selection()
                self.assertEqual(game.state.menu_state, models_module.MenuState.PLAY_MENU)
                game.confirm_selection()
                self.assertEqual(game.state.menu_state, models_module.MenuState.JUMP_ROPE)
                self.assertEqual(game.state.jump_rope_countdown_elapsed, 0.0)
                self.assertIn("countdown_beep", played_sounds)
                game.confirm_selection()
                self.assertFalse(game.state.jump_rope_jump_active)
                countdown_beeps_after_start = played_sounds.count("countdown_beep")
                game.update_jump_rope_game(0.9)
                game.update_jump_rope_game(0.9)
                self.assertEqual(played_sounds.count("countdown_beep"), countdown_beeps_after_start + 2)
                game.update_jump_rope_game(0.9)
                self.assertIn("countdown_start", played_sounds)
                game.confirm_selection()
                self.assertTrue(game.state.jump_rope_jump_active)
                self.assertIn("jump_rope_jump", played_sounds)
                game.state.jump_rope_successes = game_module.JUMP_ROPE_TARGET_SUCCESSES - 1
                game.handle_jump_rope_success()
                self.assertIn("minigame_success", played_sounds)
                self.assertTrue(game.state.jump_rope_clear_pending)
                self.assertTrue(game.state.jump_rope_jump_active)
                self.assertEqual(game.state.menu_state, models_module.MenuState.JUMP_ROPE)
                game.update_jump_rope_game(game_module.JUMP_ROPE_JUMP_DURATION_SECONDS)
                self.assertEqual(game.state.menu_state, models_module.MenuState.CELEBRATING)
                self.assertIn("play_minigame_clear", played_sounds)
                self.assertEqual(game.pet.happiness, min(10, starting_happiness + 2))
                game.complete_action_celebration()
                self.assertEqual(game.state.menu_state, models_module.MenuState.HOME)
                game.apply_sound_volume(1.0)
                game.state.menu_state = models_module.MenuState.OPTIONS
                game.state.selected_option_menu = game.option_menu.index("Volume")
                game.confirm_selection()
                self.assertEqual(game.settings.sound_volume, 0.0)
                self.assertEqual(game.audio.master_volume, 0.0)
            finally:
                game.shutdown(save=False)

            fake_display_backend = mock.Mock()
            with (
                mock.patch.object(game_module, "create_display_backend", return_value=fake_display_backend),
                mock.patch.object(game_module, "can_auto_update", return_value=True),
                mock.patch.object(game_module.Game, "show_startup_splash_safe", autospec=True, return_value=None),
            ):
                hat_game = game_module.Game(
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
                    self.assertNotIn("Res", hat_game.option_menu)
                    self.assertIn("Auto Upd", hat_game.option_menu)
                    self.assertIn("Color", hat_game.option_menu)
                    self.assertIn("Contrast", hat_game.option_menu)
                    hat_game.state.menu_state = models_module.MenuState.OPTIONS
                    hat_game.state.selected_option_menu = hat_game.option_menu.index("Auto Upd")
                    self.assertFalse(hat_game.settings.auto_update_enabled)
                    hat_game.confirm_selection()
                    self.assertTrue(hat_game.settings.auto_update_enabled)
                finally:
                    hat_game.shutdown(save=False)

            splash_window_sizes: list[tuple[int, int]] = []

            def capture_splash(self) -> None:
                splash_window_sizes.append(self.window_size)

            with (
                mock.patch.object(
                    game_module,
                    "load_game_state",
                    return_value=(models_module.Pet(), models_module.AppSettings(display_scale=3)),
                ),
                mock.patch.object(game_module.Game, "show_startup_splash_safe", autospec=True, side_effect=capture_splash),
            ):
                scaled_game = game_module.Game()
                try:
                    self.assertEqual(splash_window_sizes, [(720, 720)])
                finally:
                    scaled_game.shutdown(save=False)

            with (
                mock.patch.object(pygame_stub.transform, "scale", wraps=pygame_stub.transform.scale) as scale_mock,
                mock.patch.object(pygame_stub.transform, "smoothscale", wraps=pygame_stub.transform.smoothscale) as smoothscale_mock,
            ):
                scaled_splash = game_module.Game.build_splash_frame(pygame_stub.Surface((240, 240)), (720, 720), 128)
            self.assertEqual(scaled_splash.get_size(), (720, 720))
            self.assertEqual(scaled_splash.alpha, 128)
            scale_mock.assert_called_once()
            smoothscale_mock.assert_not_called()

            native_splash = game_module.Game.build_splash_frame(pygame_stub.Surface((240, 240)), (240, 240), 200)
            self.assertEqual(native_splash.get_size(), (240, 240))
            self.assertEqual(native_splash.alpha, 200)

            confirm_event = type("Event", (), {"type": pygame_stub.KEYDOWN, "key": pygame_stub.K_RETURN})()
            with mock.patch.object(game_module.Game, "show_startup_splash_safe", autospec=True, return_value=None):
                confirm_game = game_module.Game()
                try:
                    with mock.patch.object(pygame_stub.event, "get", return_value=[confirm_event]):
                        self.assertTrue(confirm_game.poll_splash_confirm())
                finally:
                    confirm_game.shutdown(save=False)

            with mock.patch.object(game_module.Game, "show_startup_splash", autospec=True, side_effect=RuntimeError("boom")):
                splash_safe_game = game_module.Game()
                try:
                    self.assertIsNotNone(splash_safe_game.renderer)
                finally:
                    splash_safe_game.shutdown(save=False)

        self.assertTrue(callable(wrapper_module.main))


if __name__ == "__main__":
    unittest.main()
