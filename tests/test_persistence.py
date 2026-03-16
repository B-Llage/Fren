from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from virtual_pet.models import AppSettings, Pet, ThemePalette
from virtual_pet.persistence import load_game_state, save_game_state


def make_themes() -> tuple[str, dict[str, ThemePalette]]:
    return (
        "ocean_blue",
        {
            "ocean_blue": ThemePalette("Ocean Blue", (1, 1, 1), (2, 2, 2), (3, 3, 3), (4, 4, 4), (5, 5, 5)),
            "diamond_pink": ThemePalette("Diamond Pink", (6, 6, 6), (7, 7, 7), (8, 8, 8), (9, 9, 9), (10, 10, 10)),
        },
    )


class PersistenceTests(unittest.TestCase):
    def test_save_and_load_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "save.json"
            pet = Pet(name="Mochi", hunger=8, hygiene=7, happiness=6, health=5, age_ticks=3)
            settings = AppSettings(
                menu_theme="diamond_pink",
                menu_memory_enabled=False,
                display_scale=3,
                sound_volume=0.5,
                display_saturation=1.3,
            )

            with mock.patch("virtual_pet.persistence.load_menu_themes", return_value=make_themes()):
                save_game_state(pet, settings, path)
                loaded_pet, loaded_settings = load_game_state(path)

        self.assertEqual(loaded_pet.name, "Mochi")
        self.assertEqual(loaded_pet.hunger, 8)
        self.assertEqual(loaded_settings.menu_theme, "diamond_pink")
        self.assertFalse(loaded_settings.menu_memory_enabled)
        self.assertEqual(loaded_settings.display_scale, 3)
        self.assertEqual(loaded_settings.sound_volume, 0.5)
        self.assertEqual(loaded_settings.display_saturation, 1.3)

    def test_legacy_theme_alias_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "save.json"
            path.write_text(
                json.dumps({"pet": {"name": "Mochi"}, "menu_theme": "pink"}),
                encoding="utf-8",
            )

            with mock.patch("virtual_pet.persistence.load_menu_themes", return_value=make_themes()):
                _pet, settings = load_game_state(path)

        self.assertEqual(settings.menu_theme, "diamond_pink")

    def test_legacy_stat_scaling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "save.json"
            path.write_text(
                json.dumps({"name": "Legacy", "hunger": 100, "hygiene": 50, "happiness": 0, "health": 25}),
                encoding="utf-8",
            )

            with mock.patch("virtual_pet.persistence.load_menu_themes", return_value=make_themes()):
                pet, _settings = load_game_state(path)

        self.assertEqual(pet.hunger, 10)
        self.assertEqual(pet.hygiene, 5)
        self.assertEqual(pet.happiness, 0)
        self.assertEqual(pet.health, 2)

    def test_missing_setting_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "save.json"
            path.write_text(json.dumps({"pet": {"name": "Mochi"}}), encoding="utf-8")

            with mock.patch("virtual_pet.persistence.load_menu_themes", return_value=make_themes()):
                _pet, settings = load_game_state(path)

        self.assertEqual(settings.menu_theme, "ocean_blue")
        self.assertTrue(settings.menu_memory_enabled)
        self.assertEqual(settings.display_scale, 1)
        self.assertEqual(settings.sound_volume, 1.0)
        self.assertEqual(settings.display_saturation, 1.0)


if __name__ == "__main__":
    unittest.main()
