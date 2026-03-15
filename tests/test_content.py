from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from virtual_pet.config import PROJECT_ROOT
from virtual_pet.content import load_food_items, load_menu_themes


class ContentTests(unittest.TestCase):
    def test_load_menu_themes_reads_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "themes.json"
            path.write_text(
                json.dumps(
                    {
                        "default_theme": "custom_theme",
                        "themes": {
                            "custom_theme": {
                                "label": "Custom Theme",
                                "panel": [1, 2, 3],
                                "text": [4, 5, 6],
                                "muted": [7, 8, 9],
                                "accent": [10, 11, 12],
                                "border": [13, 14, 15],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            default_theme, themes = load_menu_themes(path)

        self.assertEqual(default_theme, "custom_theme")
        self.assertEqual(themes["custom_theme"].label, "Custom Theme")
        self.assertEqual(themes["custom_theme"].accent, (10, 11, 12))

    def test_load_food_items_reads_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "foods.json"
            path.write_text(
                json.dumps(
                    {
                        "foods": [
                            {"label": "Berry", "sprite_path": "food/food_carrot.png"},
                            {"label": "Toast", "sprite_path": "food/food_burger.png"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch("virtual_pet.content.load_food_sprite", return_value=None):
                foods = load_food_items(path)

        self.assertEqual([food.label for food in foods], ["Berry", "Toast"])
        self.assertEqual(foods[0].sprite_path, PROJECT_ROOT / "food" / "food_carrot.png")
        self.assertIsNone(foods[0].sprite)

    def test_load_menu_themes_falls_back_on_bad_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "themes.json"
            path.write_text("{bad json", encoding="utf-8")

            default_theme, themes = load_menu_themes(path)

        self.assertIn(default_theme, themes)
        self.assertGreaterEqual(len(themes), 1)

    def test_load_food_items_resolves_relative_paths_from_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "foods.json"
            path.write_text(
                json.dumps({"foods": [{"label": "Sample", "sprite_path": "food/example.png"}]}),
                encoding="utf-8",
            )

            with mock.patch("virtual_pet.content.load_food_sprite", return_value=None):
                foods = load_food_items(path)

        self.assertEqual(foods[0].sprite_path, PROJECT_ROOT / "food" / "example.png")


if __name__ == "__main__":
    unittest.main()
