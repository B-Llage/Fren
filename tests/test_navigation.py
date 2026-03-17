from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest import mock

from tests.pygame_stub import install_pygame_stub


class GridNavigationTests(unittest.TestCase):
    def load_game_modules(self):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        pygame_stub = install_pygame_stub()
        for module_name in [
            "pygame",
            "virtual_pet.audio",
            "virtual_pet.game",
            "virtual_pet.input",
            "virtual_pet.renderer",
        ]:
            sys.modules.pop(module_name, None)

        module_patch = mock.patch.dict(sys.modules, {"pygame": pygame_stub})
        module_patch.start()
        self.addCleanup(module_patch.stop)

        game_module = importlib.import_module("virtual_pet.game")
        input_module = importlib.import_module("virtual_pet.input")
        models_module = importlib.import_module("virtual_pet.models")
        return pygame_stub, game_module, input_module, models_module

    def test_keyboard_arrows_follow_food_grid_direction(self) -> None:
        pygame_stub, game_module, _input_module, models_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.state.menu_state = models_module.MenuState.FOODS
            game.state.selected_food = 0

            game.handle_keyboard_input(pygame_stub.K_RIGHT)
            self.assertEqual(game.state.selected_food, 1)

            game.handle_keyboard_input(pygame_stub.K_DOWN)
            self.assertEqual(game.state.selected_food, 3)

            game.handle_keyboard_input(pygame_stub.K_LEFT)
            self.assertEqual(game.state.selected_food, 2)

            game.handle_keyboard_input(pygame_stub.K_UP)
            self.assertEqual(game.state.selected_food, 0)
        finally:
            game.shutdown(save=False)

    def test_directional_actions_do_not_wrap_food_grid_edges(self) -> None:
        _pygame_stub, game_module, input_module, models_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.state.menu_state = models_module.MenuState.FOODS

            game.state.selected_food = 1
            game.handle_input_action(input_module.INPUT_RIGHT)
            self.assertEqual(game.state.selected_food, 1)

            game.state.selected_food = 0
            game.handle_input_action(input_module.INPUT_UP)
            self.assertEqual(game.state.selected_food, 0)

            game.state.selected_food = 2
            game.handle_input_action(input_module.INPUT_LEFT)
            self.assertEqual(game.state.selected_food, 2)

            game.state.selected_food = 3
            game.handle_input_action(input_module.INPUT_DOWN)
            self.assertEqual(game.state.selected_food, 3)
        finally:
            game.shutdown(save=False)


if __name__ == "__main__":
    unittest.main()
