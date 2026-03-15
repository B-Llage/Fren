from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_TARGET = ROOT / "virtual_pet_template.py"
WATCH_GLOB = "*.py"
POLL_INTERVAL_SECONDS = 0.5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the pygame app and restart it when Python files change.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=str(DEFAULT_TARGET),
        help="Python entry point to run. Defaults to virtual_pet_template.py.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=POLL_INTERVAL_SECONDS,
        help="Polling interval in seconds. Defaults to 0.5.",
    )
    return parser.parse_args()


def snapshot_python_files(root: Path) -> dict[Path, int]:
    files: dict[Path, int] = {}
    for path in root.rglob(WATCH_GLOB):
        if "__pycache__" in path.parts:
            continue

        try:
            files[path] = path.stat().st_mtime_ns
        except FileNotFoundError:
            continue

    return files


def find_changes(previous: dict[Path, int], current: dict[Path, int]) -> list[Path]:
    changed: list[Path] = []

    for path, mtime in current.items():
        if previous.get(path) != mtime:
            changed.append(path)

    for path in previous:
        if path not in current:
            changed.append(path)

    return sorted(changed)


def start_child(target: Path) -> subprocess.Popen[bytes]:
    print(f"[dev] starting {target.name}")
    return subprocess.Popen(
        [sys.executable, str(target)],
        cwd=str(ROOT),
    )


def stop_child(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return

    print("[dev] stopping app")
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        print("[dev] app did not exit in time; killing it")
        process.kill()
        process.wait()


def main() -> int:
    args = parse_args()
    target = Path(args.target).resolve()

    if not target.exists():
        print(f"[dev] target does not exist: {target}", file=sys.stderr)
        return 1

    known_files = snapshot_python_files(ROOT)
    child = start_child(target)
    waiting_for_fix = False

    try:
        while True:
            time.sleep(args.interval)

            current_files = snapshot_python_files(ROOT)
            changed_files = find_changes(known_files, current_files)
            known_files = current_files

            if changed_files:
                changed_display = ", ".join(
                    str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
                    for path in changed_files[:5]
                )
                if len(changed_files) > 5:
                    changed_display += ", ..."

                print(f"[dev] detected changes: {changed_display}")
                stop_child(child)
                child = start_child(target)
                waiting_for_fix = False
                continue

            if child is None:
                continue

            exit_code = child.poll()
            if exit_code is None:
                continue

            if exit_code == 0 and not waiting_for_fix:
                print("[dev] app exited cleanly")
                return 0

            if not waiting_for_fix:
                print(f"[dev] app exited with code {exit_code}; waiting for file changes")
                waiting_for_fix = True
                child = None

    except KeyboardInterrupt:
        print("\n[dev] stopping watcher")
        return 0
    finally:
        stop_child(child)


if __name__ == "__main__":
    raise SystemExit(main())
