from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest import mock

from tests.pygame_stub import install_pygame_stub


class AutoReturnTests(unittest.TestCase):
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

    def test_option_menu_exposes_auto_return_toggle(self) -> None:
        game_module, _models_module = self.load_game_modules()

        game = game_module.Game()
        try:
            self.assertIn("Auto Rtrn", game.option_menu)
            self.assertIn("Auto Rtrn: On", game.get_option_menu_labels())
        finally:
            game.shutdown(save=False)

    def test_auto_return_toggle_changes_setting(self) -> None:
        game_module, models_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.state.menu_state = models_module.MenuState.OPTIONS
            game.state.selected_option_menu = game.option_menu.index("Auto Rtrn")

            game.confirm_selection()

            self.assertFalse(game.settings.auto_return_enabled)
            self.assertIn("Auto Rtrn: Off", game.get_option_menu_labels())
        finally:
            game.shutdown(save=False)

    def test_feed_returns_to_food_menu_when_auto_return_enabled(self) -> None:
        game_module, models_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.settings.auto_return_enabled = True
            game.state.menu_state = models_module.MenuState.FOODS
            game.state.selected_food = 0

            game.feed_selected_food()
            self.assertEqual(game.state.menu_state, models_module.MenuState.EATING)

            game.complete_eating_animation()
            self.assertEqual(game.state.menu_state, models_module.MenuState.CELEBRATING)

            game.complete_action_celebration()
            self.assertEqual(game.state.menu_state, models_module.MenuState.FOODS)
        finally:
            game.shutdown(save=False)

    def test_clean_returns_to_actions_when_auto_return_enabled(self) -> None:
        game_module, models_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.settings.auto_return_enabled = True
            game.state.menu_state = models_module.MenuState.ACTIONS
            game.state.selected_action = game.actions.index("Clean")

            game.confirm_selection()
            self.assertEqual(game.state.menu_state, models_module.MenuState.CLEANING)

            game.complete_cleaning_animation()
            self.assertEqual(game.state.menu_state, models_module.MenuState.CELEBRATING)

            game.complete_action_celebration()
            self.assertEqual(game.state.menu_state, models_module.MenuState.ACTIONS)
        finally:
            game.shutdown(save=False)

    def test_jump_rope_returns_to_play_menu_when_auto_return_enabled(self) -> None:
        game_module, models_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.settings.auto_return_enabled = True
            game.state.menu_state = models_module.MenuState.PLAY_MENU
            game.state.selected_play_menu = 0

            game.confirm_selection()
            self.assertEqual(game.state.menu_state, models_module.MenuState.JUMP_ROPE)

            game.complete_jump_rope_game()
            self.assertEqual(game.state.menu_state, models_module.MenuState.CELEBRATING)

            game.complete_action_celebration()
            self.assertEqual(game.state.menu_state, models_module.MenuState.PLAY_MENU)
        finally:
            game.shutdown(save=False)

    def test_heal_returns_home_when_auto_return_disabled(self) -> None:
        game_module, models_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.settings.auto_return_enabled = False
            game.state.menu_state = models_module.MenuState.ACTIONS
            game.state.selected_action = game.actions.index("Heal")

            game.confirm_selection()

            self.assertEqual(game.state.menu_state, models_module.MenuState.HOME)
        finally:
            game.shutdown(save=False)

    def test_heal_returns_to_actions_when_auto_return_enabled(self) -> None:
        game_module, models_module = self.load_game_modules()

        game = game_module.Game()
        try:
            game.settings.auto_return_enabled = True
            game.state.menu_state = models_module.MenuState.ACTIONS
            game.state.selected_action = game.actions.index("Heal")

            game.confirm_selection()

            self.assertEqual(game.state.menu_state, models_module.MenuState.ACTIONS)
        finally:
            game.shutdown(save=False)


if __name__ == "__main__":
    unittest.main()
