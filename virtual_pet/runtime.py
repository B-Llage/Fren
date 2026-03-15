from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

RASPBERRY_PI_MODEL_PATH = Path("/proc/device-tree/model")
PROFILE_AUTO = "auto"
PROFILE_DESKTOP = "desktop"
PROFILE_WAVESHARE_HAT = "waveshare-hat"
PROFILE_CHOICES = (PROFILE_AUTO, PROFILE_DESKTOP, PROFILE_WAVESHARE_HAT)
_AUTO_DETECT = object()


@dataclass(frozen=True)
class RuntimeConfig:
    profile: str = PROFILE_DESKTOP
    fullscreen: bool = False
    hide_mouse: bool = False
    enable_gpio_input: bool = False
    allow_display_scale: bool = True
    detected_model: str | None = None


def detect_raspberry_pi_model(model_path: Path = RASPBERRY_PI_MODEL_PATH) -> str | None:
    try:
        model_text = model_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None

    model_text = model_text.replace("\x00", "").strip()
    if "Raspberry Pi" not in model_text:
        return None

    return model_text


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the virtual pet game.")
    parser.add_argument(
        "--platform",
        choices=PROFILE_CHOICES,
        default=PROFILE_AUTO,
        help="Launch profile. Defaults to auto-detect.",
    )
    parser.add_argument(
        "--fullscreen",
        action="store_true",
        help="Force fullscreen mode.",
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Force windowed mode.",
    )
    parser.add_argument(
        "--gpio-input",
        action="store_true",
        help="Enable GPIO button input.",
    )
    parser.add_argument(
        "--no-gpio-input",
        action="store_true",
        help="Disable GPIO button input.",
    )
    return parser


def build_runtime_config(
    argv: Sequence[str] | None = None,
    *,
    detected_model: str | None | object = _AUTO_DETECT,
) -> RuntimeConfig:
    parser = create_argument_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.fullscreen and args.windowed:
        parser.error("Choose either --fullscreen or --windowed, not both.")

    if args.gpio_input and args.no_gpio_input:
        parser.error("Choose either --gpio-input or --no-gpio-input, not both.")

    resolved_model = detect_raspberry_pi_model() if detected_model is _AUTO_DETECT else detected_model

    profile = args.platform
    if profile == PROFILE_AUTO:
        profile = PROFILE_WAVESHARE_HAT if resolved_model else PROFILE_DESKTOP

    if args.fullscreen:
        fullscreen = True
    elif args.windowed:
        fullscreen = False
    else:
        fullscreen = profile == PROFILE_WAVESHARE_HAT

    if args.gpio_input:
        enable_gpio_input = True
    elif args.no_gpio_input:
        enable_gpio_input = False
    else:
        enable_gpio_input = profile == PROFILE_WAVESHARE_HAT

    return RuntimeConfig(
        profile=profile,
        fullscreen=fullscreen,
        hide_mouse=fullscreen,
        enable_gpio_input=enable_gpio_input,
        allow_display_scale=not fullscreen,
        detected_model=resolved_model if isinstance(resolved_model, str) else None,
    )
