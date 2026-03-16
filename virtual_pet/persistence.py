from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

from .config import (
    DEFAULT_DISPLAY_CONTRAST,
    DEFAULT_DISPLAY_SCALE,
    DEFAULT_DISPLAY_SATURATION,
    DEFAULT_MENU_MEMORY_ENABLED,
    DEFAULT_SOUND_VOLUME,
    DISPLAY_CONTRAST_OPTIONS,
    DISPLAY_SATURATION_OPTIONS,
    DISPLAY_SCALE_OPTIONS,
    FALLBACK_MENU_THEME,
    LEGACY_MAX_STAT,
    LEGACY_THEME_ALIASES,
    MAX_STAT,
    MIN_STAT,
    SAVE_PATH,
    SOUND_VOLUME_OPTIONS,
    STAT_FIELDS,
)
from .content import load_menu_themes
from .models import AppSettings, Pet

logger = logging.getLogger("virtual_pet")


def normalize_loaded_stat_value(value) -> int:
    numeric_value = int(round(float(value)))
    if numeric_value > MAX_STAT:
        scaled_value = round((numeric_value / LEGACY_MAX_STAT) * MAX_STAT)
        return max(MIN_STAT, min(MAX_STAT, scaled_value))

    return max(MIN_STAT, min(MAX_STAT, numeric_value))


def normalize_loaded_sound_volume(value) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return DEFAULT_SOUND_VOLUME

    if numeric_value > 1.0:
        numeric_value = numeric_value / 100.0

    numeric_value = max(0.0, min(1.0, numeric_value))
    return min(SOUND_VOLUME_OPTIONS, key=lambda option: abs(option - numeric_value))


def normalize_loaded_display_saturation(value) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return DEFAULT_DISPLAY_SATURATION

    supported_values = [option for _label, option in DISPLAY_SATURATION_OPTIONS]
    return min(supported_values, key=lambda option: abs(option - numeric_value))


def normalize_loaded_display_contrast(value) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return DEFAULT_DISPLAY_CONTRAST

    supported_values = [option for _label, option in DISPLAY_CONTRAST_OPTIONS]
    return min(supported_values, key=lambda option: abs(option - numeric_value))


def save_game_state(pet: Pet, settings: AppSettings, path: Path = SAVE_PATH) -> None:
    logger.info("Saving pet data to %s", path)
    payload = {
        "pet": asdict(pet),
        "menu_theme": settings.menu_theme,
        "menu_memory_enabled": settings.menu_memory_enabled,
        "display_scale": settings.display_scale,
        "sound_volume": settings.sound_volume,
        "display_saturation": settings.display_saturation,
        "display_contrast": settings.display_contrast,
    }
    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, indent=2)


def load_game_state(path: Path = SAVE_PATH) -> tuple[Pet, AppSettings]:
    default_theme, available_themes = load_menu_themes()

    logger.info("Loading pet data from %s", path)
    if not path.exists():
        logger.warning("Save file not found. Creating new pet instead.")
        return Pet(), AppSettings(menu_theme=default_theme)

    with path.open("r", encoding="utf-8") as file_handle:
        data = json.load(file_handle)

    if "pet" in data:
        pet_data = data.get("pet", {})
        menu_theme = data.get("menu_theme", default_theme)
        menu_memory_enabled = data.get("menu_memory_enabled", DEFAULT_MENU_MEMORY_ENABLED)
        display_scale = data.get("display_scale", DEFAULT_DISPLAY_SCALE)
        sound_volume = data.get("sound_volume", DEFAULT_SOUND_VOLUME)
        display_saturation = data.get("display_saturation", DEFAULT_DISPLAY_SATURATION)
        display_contrast = data.get("display_contrast", DEFAULT_DISPLAY_CONTRAST)
    else:
        pet_data = data
        menu_theme = default_theme
        menu_memory_enabled = DEFAULT_MENU_MEMORY_ENABLED
        display_scale = DEFAULT_DISPLAY_SCALE
        sound_volume = DEFAULT_SOUND_VOLUME
        display_saturation = DEFAULT_DISPLAY_SATURATION
        display_contrast = DEFAULT_DISPLAY_CONTRAST

    menu_theme = LEGACY_THEME_ALIASES.get(menu_theme, menu_theme)
    if not isinstance(menu_memory_enabled, bool):
        menu_memory_enabled = DEFAULT_MENU_MEMORY_ENABLED
    try:
        display_scale = int(display_scale)
    except (TypeError, ValueError):
        display_scale = DEFAULT_DISPLAY_SCALE
    if display_scale not in DISPLAY_SCALE_OPTIONS:
        display_scale = DEFAULT_DISPLAY_SCALE
    sound_volume = normalize_loaded_sound_volume(sound_volume)
    display_saturation = normalize_loaded_display_saturation(display_saturation)
    display_contrast = normalize_loaded_display_contrast(display_contrast)
    if menu_theme not in available_themes:
        logger.warning("Unknown menu theme '%s'; using default.", menu_theme)
        menu_theme = default_theme if default_theme in available_themes else FALLBACK_MENU_THEME

    pet_defaults = asdict(Pet())
    filtered_pet_data = {key: value for key, value in pet_data.items() if key in pet_defaults}
    for stat_field in STAT_FIELDS:
        if stat_field in filtered_pet_data:
            filtered_pet_data[stat_field] = normalize_loaded_stat_value(filtered_pet_data[stat_field])
    pet_defaults.update(filtered_pet_data)

    pet = Pet(**pet_defaults)
    pet.clamp_stats()
    settings = AppSettings(
        menu_theme=menu_theme,
        menu_memory_enabled=menu_memory_enabled,
        display_scale=display_scale,
        sound_volume=sound_volume,
        display_saturation=display_saturation,
        display_contrast=display_contrast,
    )
    return pet, settings
