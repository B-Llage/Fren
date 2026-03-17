from __future__ import annotations

import sys
from pathlib import Path

from virtual_pet.updater import maybe_apply_startup_update


def main(argv: list[str] | None = None) -> int:
    resolved_argv = list(sys.argv[1:] if argv is None else argv)
    maybe_apply_startup_update(resolved_argv, script_path=Path(__file__).resolve())

    from virtual_pet.main import main as app_main

    return app_main(resolved_argv)

if __name__ == "__main__":
    raise SystemExit(main())
