from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from .config import (
    ACTIONS_PRIMARY_AMOUNT,
    ACTIONS_SECONDARY_AMOUNT,
    DEFAULT_DISPLAY_CONTRAST,
    DEFAULT_DISPLAY_SCALE,
    DEFAULT_DISPLAY_SATURATION,
    DEFAULT_MENU_MEMORY_ENABLED,
    DEFAULT_SOUND_VOLUME,
    FALLBACK_MENU_THEME,
    HEALTH_DECAY_WHEN_NEGLECTED,
    HEALTH_RECOVERY_AMOUNT,
    HOME_PET_Y_OFFSET,
    HUNGER_DECAY,
    HYGIENE_DECAY,
    HAPPINESS_DECAY,
    MAX_STAT,
    MIN_STAT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

logger = logging.getLogger("virtual_pet")

Color = tuple[int, int, int]


class PetMood(Enum):
    HAPPY = auto()
    OKAY = auto()
    SAD = auto()
    SICK = auto()


class MenuState(Enum):
    HOME = auto()
    MAIN_MENU = auto()
    ACTIONS = auto()
    PLAY_MENU = auto()
    OPTIONS = auto()
    RESOLUTION = auto()
    FOODS = auto()
    EATING = auto()
    CLEANING = auto()
    JUMP_ROPE = auto()
    CELEBRATING = auto()
    STATUS = auto()
    THEMES = auto()
    RESET_CONFIRM = auto()


@dataclass
class ThemePalette:
    label: str
    panel: Color
    text: Color
    muted: Color
    accent: Color
    border: Color


@dataclass
class FoodItem:
    label: str
    sprite_path: Path
    sprite: object | None = None


@dataclass
class AppSettings:
    menu_theme: str = FALLBACK_MENU_THEME
    menu_memory_enabled: bool = DEFAULT_MENU_MEMORY_ENABLED
    display_scale: int = DEFAULT_DISPLAY_SCALE
    sound_volume: float = DEFAULT_SOUND_VOLUME
    display_saturation: float = DEFAULT_DISPLAY_SATURATION
    display_contrast: float = DEFAULT_DISPLAY_CONTRAST


@dataclass
class RuntimeState:
    menu_state: MenuState = MenuState.HOME
    selected_menu: int = 0
    selected_action: int = 0
    selected_play_menu: int = 0
    selected_option_menu: int = 0
    selected_food: int = 0
    selected_theme: int = 0
    selected_resolution: int = 0
    selected_reset: int = 0
    eating_food_index: int = 0
    eating_elapsed: float = 0.0
    last_eating_toggle_index: int = -1
    cleaning_elapsed: float = 0.0
    last_cleaning_scrub_index: int = -1
    celebration_elapsed: float = 0.0
    jump_rope_elapsed: float = 0.0
    jump_rope_countdown_elapsed: float = 0.0
    jump_rope_successes: int = 0
    jump_rope_jump_elapsed: float = 0.0
    jump_rope_jump_active: bool = False
    jump_rope_clear_pending: bool = False
    jump_rope_last_evaluated_cycle: int = -1
    jump_rope_last_countdown_number: int = -1
    pet_home_y: int = (SCREEN_HEIGHT // 2) + HOME_PET_Y_OFFSET
    pet_wander_x: float = float(SCREEN_WIDTH // 2)
    pet_wander_start_x: float = float(SCREEN_WIDTH // 2)
    pet_wander_target_x: float = float(SCREEN_WIDTH // 2)
    pet_wander_duration: float = 0.0
    pet_wander_elapsed: float = 0.0
    pet_hop_count: int = 1
    pet_wander_pause: float = 0.0
    pet_facing_left: bool = False
    running: bool = True
    decay_accumulator: float = 0.0


@dataclass
class Pet:
    name: str = "Mochi"
    age_ticks: int = 0
    hunger: int = 10
    hygiene: int = 10
    happiness: int = 10
    health: int = 10

    def clamp_stats(self) -> None:
        logger.info("Clamping pet stats...")
        self.hunger = max(MIN_STAT, min(MAX_STAT, self.hunger))
        self.hygiene = max(MIN_STAT, min(MAX_STAT, self.hygiene))
        self.happiness = max(MIN_STAT, min(MAX_STAT, self.happiness))
        self.health = max(MIN_STAT, min(MAX_STAT, self.health))

    def get_mood(self) -> PetMood:
        logger.debug("Evaluating pet mood...")
        avg = (self.hunger + self.hygiene + self.happiness + self.health) / 4

        if self.health <= 2:
            return PetMood.SICK
        if avg >= 8:
            return PetMood.HAPPY
        if avg >= 5:
            return PetMood.OKAY
        return PetMood.SAD

    def update_decay(self) -> None:
        logger.info("Applying decay tick to pet...")
        self.age_ticks += 1
        self.hunger -= HUNGER_DECAY
        self.hygiene -= HYGIENE_DECAY
        self.happiness -= HAPPINESS_DECAY

        neglected_stats = sum(1 for value in [self.hunger, self.hygiene, self.happiness] if value <= 2)
        if neglected_stats >= 2:
            logger.warning("Pet is neglected; decreasing health.")
            self.health -= HEALTH_DECAY_WHEN_NEGLECTED
        else:
            self.health += HEALTH_RECOVERY_AMOUNT

        self.clamp_stats()

    def feed(self) -> None:
        logger.info("Action: feed")
        self.hunger += ACTIONS_PRIMARY_AMOUNT
        self.happiness += ACTIONS_SECONDARY_AMOUNT
        self.clamp_stats()

    def play(self) -> None:
        logger.info("Action: play")
        self.happiness += ACTIONS_PRIMARY_AMOUNT
        self.clamp_stats()

    def clean(self) -> None:
        logger.info("Action: clean")
        self.hygiene += ACTIONS_PRIMARY_AMOUNT
        self.health += ACTIONS_SECONDARY_AMOUNT
        self.clamp_stats()

    def heal(self) -> None:
        logger.info("Action: heal")
        self.health += ACTIONS_PRIMARY_AMOUNT
        self.clamp_stats()
