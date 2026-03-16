from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from virtual_pet.runtime import PROFILE_DESKTOP, PROFILE_WAVESHARE_HAT, build_runtime_config, detect_raspberry_pi_model


class RuntimeConfigTests(unittest.TestCase):
    def test_auto_detects_desktop_when_no_pi_model_is_present(self) -> None:
        config = build_runtime_config([], detected_model=None)

        self.assertEqual(config.profile, PROFILE_DESKTOP)
        self.assertFalse(config.fullscreen)
        self.assertFalse(config.enable_gpio_input)
        self.assertFalse(config.enable_direct_output)
        self.assertTrue(config.allow_display_scale)

    def test_auto_detects_waveshare_hat_profile_on_raspberry_pi(self) -> None:
        config = build_runtime_config([], detected_model="Raspberry Pi Zero 2 W Rev 1.0")

        self.assertEqual(config.profile, PROFILE_WAVESHARE_HAT)
        self.assertTrue(config.fullscreen)
        self.assertTrue(config.enable_gpio_input)
        self.assertTrue(config.enable_direct_output)
        self.assertFalse(config.allow_display_scale)

    def test_windowed_mode_reenables_display_scale(self) -> None:
        config = build_runtime_config(
            ["--windowed", "--no-direct-output"],
            detected_model="Raspberry Pi Zero 2 W Rev 1.0",
        )

        self.assertEqual(config.profile, PROFILE_WAVESHARE_HAT)
        self.assertFalse(config.fullscreen)
        self.assertTrue(config.enable_gpio_input)
        self.assertFalse(config.enable_direct_output)
        self.assertTrue(config.allow_display_scale)

    def test_detect_raspberry_pi_model_strips_trailing_nulls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "model"
            model_path.write_text("Raspberry Pi Zero 2 W Rev 1.0\x00", encoding="utf-8")

            self.assertEqual(
                detect_raspberry_pi_model(model_path),
                "Raspberry Pi Zero 2 W Rev 1.0",
            )


if __name__ == "__main__":
    unittest.main()
