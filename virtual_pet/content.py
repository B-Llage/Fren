from __future__ import annotations

import json
import logging
from pathlib import Path

from .config import (
    FALLBACK_FOOD_ITEMS,
    FALLBACK_MENU_THEME,
    FALLBACK_MENU_THEMES,
    FOOD_CONFIG_PATH,
    FOOD_ICON_SIZE,
    HOME_BACKGROUND_PATH,
    PET_SPRITE_SIZE,
    PROJECT_ROOT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SPLASH_SCREEN_PATH,
    THEME_COLOR_FIELDS,
    THEME_CONFIG_PATH,
)
from .models import FoodItem, ThemePalette

logger = logging.getLogger("virtual_pet")


def resolve_project_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def normalize_theme_color(color_value) -> tuple[int, int, int]:
    if not isinstance(color_value, (list, tuple)) or len(color_value) != 3:
        raise ValueError(f"Invalid color value: {color_value!r}")

    return tuple(int(channel) for channel in color_value)


def normalize_menu_themes(raw_themes: dict) -> dict[str, ThemePalette]:
    normalized: dict[str, ThemePalette] = {}

    for theme_key, theme_values in raw_themes.items():
        if not isinstance(theme_values, dict):
            raise ValueError(f"Theme '{theme_key}' must be an object.")

        normalized[theme_key] = ThemePalette(
            label=str(theme_values["label"]),
            panel=normalize_theme_color(theme_values["panel"]),
            text=normalize_theme_color(theme_values["text"]),
            muted=normalize_theme_color(theme_values["muted"]),
            accent=normalize_theme_color(theme_values["accent"]),
            border=normalize_theme_color(theme_values["border"]),
        )

    if not normalized:
        raise ValueError("No themes were defined.")

    return normalized


def load_menu_themes(path: Path = THEME_CONFIG_PATH) -> tuple[str, dict[str, ThemePalette]]:
    fallback_themes = normalize_menu_themes(FALLBACK_MENU_THEMES)
    if not path.exists():
        logger.warning("Theme config not found at %s; using fallback themes.", path)
        return FALLBACK_MENU_THEME, fallback_themes

    try:
        with path.open("r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)

        if not isinstance(data, dict):
            raise ValueError("Theme config root must be an object.")

        raw_themes = data.get("themes", data)
        if not isinstance(raw_themes, dict):
            raise ValueError("'themes' must be an object.")

        themes = normalize_menu_themes(raw_themes)
        default_theme = str(data.get("default_theme", FALLBACK_MENU_THEME))
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        logger.warning("Failed to load theme config from %s: %s. Using fallback themes.", path, exc)
        return FALLBACK_MENU_THEME, fallback_themes

    if default_theme not in themes:
        logger.warning("Default theme '%s' not found; using '%s' instead.", default_theme, FALLBACK_MENU_THEME)
        default_theme = FALLBACK_MENU_THEME if FALLBACK_MENU_THEME in themes else next(iter(themes))

    return default_theme, themes


def load_pet_sprite(path: Path) -> object | None:
    import pygame

    logger.info("Loading pet sprite from %s", path)
    if not path.exists():
        logger.info("Pet sprite not found; using placeholder drawing.")
        return None

    try:
        sprite = pygame.image.load(str(path)).convert_alpha()
    except pygame.error:
        logger.exception("Failed to load pet sprite from %s", path)
        return None

    if sprite.get_size() != PET_SPRITE_SIZE:
        logger.info("Scaling pet sprite from %s to %s", sprite.get_size(), PET_SPRITE_SIZE)
        sprite = pygame.transform.scale(sprite, PET_SPRITE_SIZE)

    return sprite


def load_background_image(path: Path = HOME_BACKGROUND_PATH) -> object | None:
    import pygame

    logger.info("Loading background image from %s", path)
    if not path.exists():
        logger.info("Background image not found; using solid background.")
        return None

    try:
        image = pygame.image.load(str(path)).convert()
    except pygame.error:
        logger.exception("Failed to load background image from %s", path)
        return None

    target_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
    if image.get_size() != target_size:
        logger.info("Scaling background image from %s to %s", image.get_size(), target_size)
        image = pygame.transform.smoothscale(image, target_size)

    return image


def load_splash_image(path: Path = SPLASH_SCREEN_PATH) -> object | None:
    import pygame

    logger.info("Loading splash image from %s", path)
    if not path.exists():
        logger.info("Splash image not found; skipping splash screen.")
        return None

    try:
        image = pygame.image.load(str(path)).convert_alpha()
    except pygame.error:
        logger.exception("Failed to load splash image from %s", path)
        return None

    return image


def load_food_sprite(path: Path, size: tuple[int, int] = FOOD_ICON_SIZE) -> object | None:
    import pygame

    logger.info("Loading food sprite from %s", path)
    if not path.exists():
        logger.info("Food sprite not found; leaving slot without image.")
        return None

    try:
        sprite = pygame.image.load(str(path)).convert_alpha()
    except pygame.error:
        logger.exception("Failed to load food sprite from %s", path)
        return None

    if sprite.get_size() != size:
        logger.info("Scaling food sprite from %s to %s", sprite.get_size(), size)
        sprite = pygame.transform.smoothscale(sprite, size)

    return sprite


def load_prop_sprite(path: Path, size: tuple[int, int]) -> object | None:
    return load_food_sprite(path, size=size)


def normalize_food_items(raw_foods) -> list[dict[str, Path | str]]:
    if not isinstance(raw_foods, list):
        raise ValueError("Food config must be a list.")

    normalized_foods: list[dict[str, Path | str]] = []
    for food_index, food_item in enumerate(raw_foods):
        if not isinstance(food_item, dict):
            raise ValueError(f"Food entry at index {food_index} must be an object.")

        normalized_foods.append(
            {
                "label": str(food_item["label"]),
                "sprite_path": resolve_project_path(food_item["sprite_path"]),
            }
        )

    if not normalized_foods:
        raise ValueError("No food items were defined.")

    return normalized_foods


def load_food_items(path: Path = FOOD_CONFIG_PATH) -> list[FoodItem]:
    fallback_foods = normalize_food_items(FALLBACK_FOOD_ITEMS)

    if not path.exists():
        logger.warning("Food config not found at %s; using fallback foods.", path)
        normalized_foods = fallback_foods
    else:
        try:
            with path.open("r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)

            raw_foods = data.get("foods", data) if isinstance(data, dict) else data
            normalized_foods = normalize_food_items(raw_foods)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            logger.warning("Failed to load food config from %s: %s. Using fallback foods.", path, exc)
            normalized_foods = fallback_foods

    loaded_foods: list[FoodItem] = []
    for food_item in normalized_foods:
        sprite_path = food_item["sprite_path"]
        loaded_foods.append(
            FoodItem(
                label=food_item["label"],
                sprite_path=sprite_path,
                sprite=load_food_sprite(sprite_path),
            )
        )

    return loaded_foods
