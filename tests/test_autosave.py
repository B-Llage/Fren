from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest import mock

from tests.pygame_stub import install_pygame_stub


class AutoSaveTests(unittest.TestCase):
    def load_game_modules(self):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        pygame_stub = install_pygame_stub()
        for module_name in [
            "pygame",
            "virtual_pet.audio",
            "virtual_pet.game",
            "virtual_pet.renderer",
        ]:
            sys.modules.pop(module_name, None)

        module_patch = mock.patch.dict(sys.modules, {"pygame": pygame_stub})
        module_patch.start()
        self.addCleanup(module_patch.stop)

        game_module = importlib.import_module("virtual_pet.game")
        models_module = importlib.import_module("virtual_pet.models")
        splash_patch = mock.patch.object(game_module.Game, "show_startup_splash_safe", autospec=True, return_value=None)
        splash_patch.start()
        self.addCleanup(splash_patch.stop)
        return game_module, models_module

    def test_update_auto_saves_after_one_minute(self) -> None:
        game_module, _models_module = self.load_game_modules()

        with mock.patch.object(game_module, "save_game_state") as save_mock:
            game = game_module.Game()
            try:
                game.update(game_module.AUTO_SAVE_INTERVAL_SECONDS)

                save_mock.assert_called_once_with(game.pet, game.settings)
                self.assertEqual(game.auto_save_elapsed, 0.0)
                self.assertEqual(game.save_indicator_elapsed, game_module.SAVE_INDICATOR_DURATION_SECONDS)
            finally:
                game.shutdown(save=False)

    def test_leaving_options_menu_saves_and_returns_to_main_menu(self) -> None:
        game_module, models_module = self.load_game_modules()

        with mock.patch.object(game_module, "save_game_state") as save_mock:
            game = game_module.Game()
            try:
                game.state.menu_state = models_module.MenuState.OPTIONS

                game.go_back()

                save_mock.assert_called_once_with(game.pet, game.settings)
                self.assertEqual(game.state.menu_state, models_module.MenuState.MAIN_MENU)
                self.assertEqual(game.save_indicator_elapsed, game_module.SAVE_INDICATOR_DURATION_SECONDS)
            finally:
                game.shutdown(save=False)

    def test_draw_ui_shows_save_indicator_when_recent_save_occurred(self) -> None:
        game_module, models_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.state.menu_state = models_module.MenuState.HOME
            game.save_indicator_elapsed = game_module.SAVE_INDICATOR_DURATION_SECONDS

            with mock.patch.object(game.renderer, "draw_save_indicator") as draw_indicator_mock:
                game.draw_ui()

            draw_indicator_mock.assert_called_once()
        finally:
            game.shutdown(save=False)


if __name__ == "__main__":
    unittest.main()
