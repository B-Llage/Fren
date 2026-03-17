from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from virtual_pet.updater import (
    AUTO_UPDATE_ATTEMPTED_ENV,
    load_auto_update_enabled,
    maybe_apply_startup_update,
    try_auto_update,
)


class UpdaterTests(unittest.TestCase):
    def test_load_auto_update_enabled_returns_saved_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "save.json"
            save_path.write_text(json.dumps({"auto_update_enabled": True}), encoding="utf-8")

            self.assertTrue(load_auto_update_enabled(save_path))

    def test_try_auto_update_restores_save_file_after_successful_pull(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            save_path = project_root / "pet_save.json"
            original_contents = b'{"pet":{"name":"Mochi"}}'
            save_path.write_bytes(original_contents)

            completed_process = subprocess.CompletedProcess(args=["git"], returncode=0, stdout="", stderr="")
            with (
                mock.patch("virtual_pet.updater.get_upstream_ref", return_value="origin/main"),
                mock.patch("virtual_pet.updater.get_dirty_paths", return_value=["pet_save.json"]),
                mock.patch("virtual_pet.updater.get_git_output", side_effect=["abc123", "def456"]),
                mock.patch("virtual_pet.updater.run_git_command", return_value=completed_process) as run_git_command,
            ):
                self.assertTrue(try_auto_update(project_root))

            self.assertEqual(save_path.read_bytes(), original_contents)
            self.assertEqual(run_git_command.call_count, 3)

    def test_maybe_apply_startup_update_restarts_after_successful_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            script_path = Path(tmp_dir) / "virtual_pet_template.py"
            script_path.write_text("raise SystemExit(0)\n", encoding="utf-8")

            with (
                mock.patch.dict(os.environ, {}, clear=False),
                mock.patch("virtual_pet.updater.detect_raspberry_pi_model", return_value="Raspberry Pi Zero 2 W Rev 1.0"),
                mock.patch("virtual_pet.updater.load_auto_update_enabled", return_value=True),
                mock.patch("virtual_pet.updater.can_auto_update", return_value=True),
                mock.patch("virtual_pet.updater.try_auto_update", return_value=True),
                mock.patch("virtual_pet.updater.os.execv") as execv_mock,
            ):
                maybe_apply_startup_update(["--platform", "waveshare-hat"], script_path=script_path)
                self.assertEqual(os.environ.get(AUTO_UPDATE_ATTEMPTED_ENV), "1")
                execv_mock.assert_called_once_with(
                    os.sys.executable,
                    [os.sys.executable, str(script_path.resolve()), "--platform", "waveshare-hat"],
                )


if __name__ == "__main__":
    unittest.main()
