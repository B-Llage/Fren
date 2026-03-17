from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from .config import PROJECT_ROOT, SAVE_PATH
from .runtime import detect_raspberry_pi_model

logger = logging.getLogger("virtual_pet")

AUTO_UPDATE_ATTEMPTED_ENV = "FREN_AUTO_UPDATE_ATTEMPTED"
AUTO_UPDATE_ALLOWED_DIRTY_PATHS = (SAVE_PATH.name,)
GIT_COMMAND_TIMEOUT_SECONDS = 12


def can_auto_update(project_root: Path = PROJECT_ROOT) -> bool:
    git_executable = shutil.which("git")
    if git_executable is None:
        return False

    return (project_root / ".git").exists()


def load_auto_update_enabled(save_path: Path = SAVE_PATH) -> bool:
    try:
        with save_path.open("r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except (OSError, ValueError, json.JSONDecodeError):
        return False

    return bool(data.get("auto_update_enabled", False))


def maybe_apply_startup_update(
    argv: Sequence[str] | None = None,
    *,
    project_root: Path = PROJECT_ROOT,
    save_path: Path = SAVE_PATH,
    script_path: Path | None = None,
) -> None:
    if os.environ.get(AUTO_UPDATE_ATTEMPTED_ENV) == "1":
        return

    if detect_raspberry_pi_model() is None:
        return

    if not load_auto_update_enabled(save_path):
        return

    if not can_auto_update(project_root):
        return

    os.environ[AUTO_UPDATE_ATTEMPTED_ENV] = "1"
    if not try_auto_update(project_root):
        return

    restart_script = Path(script_path or sys.argv[0]).resolve()
    restart_args = [sys.executable, str(restart_script), *(list(argv) if argv is not None else sys.argv[1:])]
    try:
        os.execv(sys.executable, restart_args)
    except OSError:
        logger.exception("Auto update succeeded, but restarting the game failed.")


def try_auto_update(project_root: Path = PROJECT_ROOT) -> bool:
    upstream_ref = get_upstream_ref(project_root)
    if not upstream_ref:
        logger.warning("Auto update is enabled, but no upstream branch is configured.")
        return False

    dirty_paths = get_dirty_paths(project_root)
    if dirty_paths is None:
        return False

    disallowed_dirty_paths = [
        relative_path
        for relative_path in dirty_paths
        if relative_path not in AUTO_UPDATE_ALLOWED_DIRTY_PATHS
    ]
    if disallowed_dirty_paths:
        logger.warning(
            "Skipping auto update because the repo has local changes outside the save file: %s",
            ", ".join(disallowed_dirty_paths),
        )
        return False

    local_head = get_git_output(project_root, "rev-parse", "HEAD")
    if not local_head:
        return False

    remote_name = upstream_ref.split("/", 1)[0]
    if not run_git_command(project_root, "fetch", "--quiet", remote_name):
        return False

    upstream_head = get_git_output(project_root, "rev-parse", upstream_ref)
    if not upstream_head or upstream_head == local_head:
        return False

    backups = backup_allowed_dirty_paths(project_root, dirty_paths)
    if backups is None:
        return False

    try:
        if not restore_allowed_paths_to_head(project_root, tuple(backups)):
            return False

        if not run_git_command(project_root, "pull", "--ff-only", "--quiet"):
            return False
    finally:
        restore_backups(project_root, backups)

    return True


def get_upstream_ref(project_root: Path) -> str | None:
    return get_git_output(project_root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")


def get_dirty_paths(project_root: Path) -> list[str] | None:
    result = run_git_command(
        project_root,
        "status",
        "--porcelain",
        "--untracked-files=no",
        capture_output=True,
    )
    if result is None:
        return None

    dirty_paths: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        relative_path = line[3:].strip()
        if " -> " in relative_path:
            relative_path = relative_path.split(" -> ", 1)[1]
        if relative_path:
            dirty_paths.append(relative_path)

    return dirty_paths


def backup_allowed_dirty_paths(project_root: Path, dirty_paths: Sequence[str]) -> dict[str, bytes | None] | None:
    backups: dict[str, bytes | None] = {}
    for relative_path in dirty_paths:
        if relative_path not in AUTO_UPDATE_ALLOWED_DIRTY_PATHS:
            continue

        absolute_path = project_root / relative_path
        try:
            backups[relative_path] = absolute_path.read_bytes() if absolute_path.exists() else None
        except OSError:
            logger.exception("Failed to back up %s before auto update.", absolute_path)
            return None

    return backups


def restore_allowed_paths_to_head(project_root: Path, relative_paths: Sequence[str]) -> bool:
    for relative_path in relative_paths:
        if not run_git_command(project_root, "restore", "--source=HEAD", "--worktree", "--", relative_path):
            return False

    return True


def restore_backups(project_root: Path, backups: dict[str, bytes | None]) -> None:
    for relative_path, original_bytes in backups.items():
        absolute_path = project_root / relative_path
        try:
            if original_bytes is None:
                if absolute_path.exists():
                    absolute_path.unlink()
                continue

            absolute_path.write_bytes(original_bytes)
        except OSError:
            logger.exception("Failed to restore %s after auto update.", absolute_path)


def get_git_output(project_root: Path, *args: str) -> str | None:
    result = run_git_command(project_root, *args, capture_output=True)
    if result is None:
        return None

    return result.stdout.strip() or None


def run_git_command(
    project_root: Path,
    *args: str,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str] | None:
    git_executable = shutil.which("git")
    if git_executable is None:
        return None

    try:
        result = subprocess.run(
            [git_executable, *args],
            cwd=project_root,
            capture_output=capture_output,
            text=True,
            timeout=GIT_COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        logger.exception("Git command failed: git %s", " ".join(args))
        return None

    if result.returncode != 0:
        stderr_output = result.stderr.strip() if capture_output and result.stderr else "unknown error"
        logger.warning("Git command failed: git %s (%s)", " ".join(args), stderr_output)
        return None

    return result
