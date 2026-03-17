from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest import mock

from tests.pygame_stub import install_pygame_stub


class MenuFadeTests(unittest.TestCase):
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

    def test_menu_fade_starts_when_opening_a_menu(self) -> None:
        game_module, models_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.state.menu_state = models_module.MenuState.MAIN_MENU
            game.draw_ui()
            self.assertEqual(game.get_menu_fade_alpha(), 255)

            game.update(game_module.MENU_FADE_IN_SECONDS / 2)
            self.assertGreater(game.get_menu_fade_alpha(), 0)

            game.update(game_module.MENU_FADE_IN_SECONDS)
            self.assertEqual(game.get_menu_fade_alpha(), 0)
        finally:
            game.shutdown(save=False)

    def test_changing_menu_screens_restarts_fade(self) -> None:
        game_module, models_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.state.menu_state = models_module.MenuState.MAIN_MENU
            game.draw_ui()
            game.update(game_module.MENU_FADE_IN_SECONDS)
            self.assertEqual(game.get_menu_fade_alpha(), 0)

            game.state.menu_state = models_module.MenuState.OPTIONS
            game.draw_ui()
            self.assertEqual(game.get_menu_fade_alpha(), 255)

            game.state.menu_state = models_module.MenuState.HOME
            game.draw_ui()
            self.assertEqual(game.get_menu_fade_alpha(), 0)
        finally:
            game.shutdown(save=False)


if __name__ == "__main__":
    unittest.main()
