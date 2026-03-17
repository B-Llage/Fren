from __future__ import annotations

import logging
import math
import os
import random

import pygame

from .audio import AudioManager, pre_init_audio
from .config import (
    ACTION_OPTIONS,
    ACTION_CELEBRATION_DURATION_SECONDS,
    BASE_SPRITE_PATH,
    BUBBLES_PROP_PATH,
    BUBBLES_PROP_SIZE,
    CLEAN_DROP_DURATION_SECONDS,
    CLEAN_SCRUB_DURATION_SECONDS,
    CLEAN_SCRUB_SOUND_INTERVAL_SECONDS,
    DECAY_TIMER_SECONDS,
    DEFAULT_DISPLAY_CONTRAST,
    DEFAULT_DISPLAY_SCALE,
    DEFAULT_DISPLAY_SATURATION,
    DEFAULT_SOUND_VOLUME,
    DISPLAY_CONTRAST_OPTIONS,
    DISPLAY_SATURATION_OPTIONS,
    DISPLAY_SCALE_OPTIONS,
    EXTRA_HAPPY_FACE_PATH,
    FACE_SPRITE_PATH,
    FEED_DROP_DURATION_SECONDS,
    FEED_MUNCH_FRAME_SECONDS,
    FEED_MUNCH_TOGGLE_COUNT,
    FOOD_GRID_COLUMNS,
    FOOD_GRID_ROWS,
    FPS,
    HOME_BACKGROUND_PATH,
    HOME_PET_SIZE,
    JUMP_ROPE_COUNTDOWN_START,
    JUMP_ROPE_COUNTDOWN_SECONDS,
    JUMP_ROPE_COUNTDOWN_STEP_SECONDS,
    JUMP_ROPE_CYCLE_SECONDS,
    JUMP_ROPE_JUMP_DURATION_SECONDS,
    JUMP_ROPE_JUMP_HEIGHT,
    JUMP_ROPE_PASS_PHASE,
    JUMP_ROPE_REQUIRED_HEIGHT,
    JUMP_ROPE_TARGET_SUCCESSES,
    MAIN_MENU_OPTIONS,
    MUNCH_FACE_CLOSED_PATH,
    MUNCH_FACE_OPEN_PATH,
    OPTION_MENU_OPTIONS,
    PLAY_MENU_OPTIONS,
    RESET_OPTIONS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SOAP_PROP_PATH,
    SOAP_PROP_SIZE,
    SOUND_VOLUME_OPTIONS,
    SPLASH_FADE_IN_SECONDS,
    SPLASH_FADE_OUT_SECONDS,
    SPLASH_HOLD_SECONDS,
    WANDER_HOPS_PER_SECOND,
    WANDER_PAUSE_MAX_SECONDS,
    WANDER_PAUSE_MIN_SECONDS,
    WANDER_SCREEN_MARGIN,
    WANDER_SPEED,
    WINDOW_TITLE,
)
from .content import load_background_image, load_food_items, load_menu_themes, load_pet_sprite, load_prop_sprite, load_splash_image
from .display import create_display_backend
from .input import (
    INPUT_BACK,
    INPUT_CONFIRM,
    INPUT_DOWN,
    INPUT_LEFT,
    INPUT_NEXT,
    INPUT_PREVIOUS,
    INPUT_RIGHT,
    INPUT_UP,
    create_input_backend,
)
from .models import FoodItem, MenuState, Pet, RuntimeState
from .persistence import load_game_state, save_game_state
from .renderer import GameRenderer
from .runtime import PROFILE_WAVESHARE_HAT, RuntimeConfig, build_runtime_config
from .updater import can_auto_update

logger = logging.getLogger("virtual_pet")


class Game:
    def __init__(self, runtime: RuntimeConfig | None = None) -> None:
        self.runtime = runtime or build_runtime_config(())
        self.display_output = create_display_backend(
            self.runtime.enable_direct_output,
            rotation=self.runtime.display_rotation,
        )
        if self.runtime.enable_direct_output and self.display_output is not None:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        logger.info("Initializing pygame...")
        pre_init_audio()
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)

        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.window = self.screen
        self.window_size = self.screen.get_size()
        self.clock = pygame.time.Clock()
        self._is_shutdown = False
        self.state = RuntimeState()
        logger.info("Loading pet state...")
        self.pet, self.settings = load_game_state()
        self.hardware_input = create_input_backend(
            self.runtime.enable_gpio_input,
            rotation=self.runtime.display_rotation,
        )
        mouse = getattr(pygame, "mouse", None)
        if mouse is not None and hasattr(mouse, "set_visible"):
            mouse.set_visible(not self.runtime.hide_mouse)
        self.refresh_window(self.settings.display_scale)
        self.show_startup_splash()

        logger.info("Loading content...")
        self.default_menu_theme, self.themes = load_menu_themes()
        self.home_background = load_background_image(HOME_BACKGROUND_PATH)
        self.base_sprite = load_pet_sprite(BASE_SPRITE_PATH)
        self.face_sprite = load_pet_sprite(FACE_SPRITE_PATH)
        self.extra_happy_face_sprite = load_pet_sprite(EXTRA_HAPPY_FACE_PATH)
        self.munch_face_closed_sprite = load_pet_sprite(MUNCH_FACE_CLOSED_PATH)
        self.munch_face_open_sprite = load_pet_sprite(MUNCH_FACE_OPEN_PATH)
        self.soap_sprite = load_prop_sprite(SOAP_PROP_PATH, SOAP_PROP_SIZE)
        self.bubbles_sprite = load_prop_sprite(BUBBLES_PROP_PATH, BUBBLES_PROP_SIZE)
        self.food_options: list[FoodItem] = load_food_items()
        self.audio = AudioManager()
        if self.settings.menu_theme not in self.themes:
            self.settings.menu_theme = self.default_menu_theme

        self.main_menu = list(MAIN_MENU_OPTIONS)
        self.auto_update_supported = self.runtime.profile == PROFILE_WAVESHARE_HAT and can_auto_update()
        self.option_menu = [option for option in OPTION_MENU_OPTIONS if self.is_option_enabled(option)]
        self.actions = list(ACTION_OPTIONS)
        self.play_menu = list(PLAY_MENU_OPTIONS)
        self.theme_options = list(self.themes.keys())
        self.resolution_options = list(DISPLAY_SCALE_OPTIONS)
        self.sound_volume_options = list(SOUND_VOLUME_OPTIONS)
        self.display_contrast_options = [value for _label, value in DISPLAY_CONTRAST_OPTIONS]
        self.display_saturation_options = [value for _label, value in DISPLAY_SATURATION_OPTIONS]
        self.reset_options = list(RESET_OPTIONS)
        self.state.selected_theme = self.theme_options.index(self.settings.menu_theme)
        self.state.selected_resolution = self.resolution_options.index(self.settings.display_scale)
        self.state.selected_option_menu = self.clamp_selection(self.state.selected_option_menu, self.option_menu)
        self.apply_sound_volume(self.settings.sound_volume)
        self.apply_display_saturation(self.settings.display_saturation)
        self.apply_display_contrast(self.settings.display_contrast)
        self.state.pet_wander_x = float(SCREEN_WIDTH // 2)
        self.state.pet_wander_start_x = self.state.pet_wander_x
        self.state.pet_wander_target_x = self.state.pet_wander_x
        self.state.pet_wander_pause = random.uniform(WANDER_PAUSE_MIN_SECONDS, WANDER_PAUSE_MAX_SECONDS)

        self.renderer = GameRenderer(
            screen=self.screen,
            themes=self.themes,
            home_background=self.home_background,
            base_sprite=self.base_sprite,
            face_sprite=self.face_sprite,
            extra_happy_face_sprite=self.extra_happy_face_sprite,
            munch_face_closed_sprite=self.munch_face_closed_sprite,
            munch_face_open_sprite=self.munch_face_open_sprite,
            soap_sprite=self.soap_sprite,
            bubbles_sprite=self.bubbles_sprite,
        )
        self.apply_display_scale(self.settings.display_scale)

    def play_sound(self, sound_name: str) -> None:
        self.audio.play(sound_name)

    @staticmethod
    def clamp_selection(selected_index: int, options: list[object]) -> int:
        if not options:
            return 0

        return max(0, min(selected_index, len(options) - 1))

    @staticmethod
    def cycle_index(selected_index: int, options: list[object], step: int) -> int:
        if not options:
            return 0

        return (selected_index + step) % len(options)

    def is_option_enabled(self, option_name: str) -> bool:
        if option_name == "Auto Upd":
            return self.auto_update_supported
        if option_name == "Color":
            return self.display_output is not None
        if option_name == "Contrast":
            return self.display_output is not None
        if option_name == "Res":
            return self.runtime.allow_display_scale

        return True

    def refresh_window(self, display_scale: int | None = None) -> None:
        window_flags = getattr(pygame, "FULLSCREEN", 0) if self.runtime.fullscreen else 0
        scale = DEFAULT_DISPLAY_SCALE if display_scale is None else display_scale
        if display_scale is None and hasattr(self, "settings"):
            scale = self.settings.display_scale

        requested_size = (SCREEN_WIDTH * scale, SCREEN_HEIGHT * scale)
        if self.display_output is not None:
            requested_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
            window_flags = 0
        elif self.runtime.fullscreen:
            requested_size = (0, 0)

        self.window = pygame.display.set_mode(requested_size, window_flags)
        actual_size = self.window.get_size()
        if actual_size == (0, 0):
            actual_size = (SCREEN_WIDTH, SCREEN_HEIGHT) if self.runtime.fullscreen else requested_size
        self.window_size = actual_size

    def present_frame(self) -> None:
        if self.display_output is not None:
            self.display_output.present(self.screen)

        if self.window_size == self.screen.get_size():
            self.window.blit(self.screen, (0, 0))
        else:
            scaled_surface = pygame.transform.scale(self.screen, self.window_size)
            self.window.blit(scaled_surface, (0, 0))

        pygame.display.flip()

    @staticmethod
    def build_splash_frame(
        splash_image: pygame.Surface,
        target_size: tuple[int, int],
        alpha: int,
    ) -> pygame.Surface:
        if splash_image.get_size() != target_size:
            splash_frame = pygame.transform.scale(splash_image, target_size)
        else:
            splash_frame = splash_image.copy() if hasattr(splash_image, "copy") else splash_image

        if hasattr(splash_frame, "set_alpha"):
            splash_frame.set_alpha(alpha)

        return splash_frame

    def show_startup_splash(self) -> None:
        splash_image = load_splash_image()
        if splash_image is None:
            return

        total_duration = SPLASH_FADE_IN_SECONDS + SPLASH_HOLD_SECONDS + SPLASH_FADE_OUT_SECONDS
        elapsed = 0.0

        while elapsed < total_duration and self.state.running:
            dt = self.clock.tick(FPS) / 1000.0
            elapsed += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.state.running = False
                    break

            if not self.state.running:
                break

            if elapsed < SPLASH_FADE_IN_SECONDS:
                alpha_progress = elapsed / SPLASH_FADE_IN_SECONDS
            elif elapsed < SPLASH_FADE_IN_SECONDS + SPLASH_HOLD_SECONDS:
                alpha_progress = 1.0
            else:
                fade_out_elapsed = elapsed - SPLASH_FADE_IN_SECONDS - SPLASH_HOLD_SECONDS
                alpha_progress = 1.0 - (fade_out_elapsed / SPLASH_FADE_OUT_SECONDS)

            splash_alpha = max(0, min(255, int(round(alpha_progress * 255))))
            self.screen.fill((0, 0, 0))
            screen_frame = self.build_splash_frame(splash_image, self.screen.get_size(), splash_alpha)
            self.screen.blit(screen_frame, (0, 0))

            if self.display_output is not None:
                self.display_output.present(self.screen)

            if self.window_size == self.screen.get_size():
                self.window.blit(self.screen, (0, 0))
            else:
                self.window.fill((0, 0, 0))
                window_frame = self.build_splash_frame(splash_image, self.window_size, splash_alpha)
                self.window.blit(window_frame, (0, 0))

            pygame.display.flip()

        self.screen.fill((0, 0, 0))
        self.present_frame()

    def apply_display_scale(self, display_scale: int) -> None:
        if display_scale not in DISPLAY_SCALE_OPTIONS:
            display_scale = DEFAULT_DISPLAY_SCALE

        self.settings.display_scale = display_scale
        self.refresh_window()
        logger.info(
            "Applied display mode fullscreen=%s direct_output=%s scale=%sx (%sx%s).",
            self.runtime.fullscreen,
            self.display_output is not None,
            self.settings.display_scale,
            *self.window_size,
        )

    def apply_sound_volume(self, sound_volume: float) -> None:
        if sound_volume not in self.sound_volume_options:
            sound_volume = min(self.sound_volume_options, key=lambda option: abs(option - sound_volume))

        self.settings.sound_volume = sound_volume
        self.audio.set_master_volume(self.settings.sound_volume)
        logger.info("Applied sound volume %s%%.", int(round(self.settings.sound_volume * 100)))

    def get_display_saturation_label(self) -> str:
        for label, value in DISPLAY_SATURATION_OPTIONS:
            if value == self.settings.display_saturation:
                return label

        return "Normal"

    def get_display_contrast_label(self) -> str:
        for label, value in DISPLAY_CONTRAST_OPTIONS:
            if value == self.settings.display_contrast:
                return label

        return "Rich"

    def apply_display_saturation(self, display_saturation: float) -> None:
        if display_saturation not in self.display_saturation_options:
            display_saturation = min(
                self.display_saturation_options,
                key=lambda option: abs(option - display_saturation),
            )

        self.settings.display_saturation = display_saturation
        if self.display_output is not None:
            self.display_output.set_saturation(self.settings.display_saturation)
        logger.info(
            "Applied display saturation %s (%.2fx).",
            self.get_display_saturation_label(),
            self.settings.display_saturation,
        )

    def cycle_display_saturation(self) -> None:
        try:
            current_index = self.display_saturation_options.index(self.settings.display_saturation)
        except ValueError:
            current_index = self.display_saturation_options.index(DEFAULT_DISPLAY_SATURATION)

        next_index = (current_index + 1) % len(self.display_saturation_options)
        self.apply_display_saturation(self.display_saturation_options[next_index])

    def apply_display_contrast(self, display_contrast: float) -> None:
        if display_contrast not in self.display_contrast_options:
            display_contrast = min(
                self.display_contrast_options,
                key=lambda option: abs(option - display_contrast),
            )

        self.settings.display_contrast = display_contrast
        if self.display_output is not None:
            self.display_output.set_contrast(self.settings.display_contrast)
        logger.info(
            "Applied display contrast %s (%.2fx).",
            self.get_display_contrast_label(),
            self.settings.display_contrast,
        )

    def cycle_display_contrast(self) -> None:
        try:
            current_index = self.display_contrast_options.index(self.settings.display_contrast)
        except ValueError:
            current_index = self.display_contrast_options.index(DEFAULT_DISPLAY_CONTRAST)

        next_index = (current_index + 1) % len(self.display_contrast_options)
        self.apply_display_contrast(self.display_contrast_options[next_index])

    def cycle_sound_volume(self) -> None:
        try:
            current_index = self.sound_volume_options.index(self.settings.sound_volume)
        except ValueError:
            current_index = self.sound_volume_options.index(DEFAULT_SOUND_VOLUME)

        next_index = (current_index + 1) % len(self.sound_volume_options)
        self.apply_sound_volume(self.sound_volume_options[next_index])

    def open_main_menu(self) -> None:
        if not self.settings.menu_memory_enabled:
            self.state.selected_menu = 0
        self.state.menu_state = MenuState.MAIN_MENU

    def open_actions_menu(self) -> None:
        if not self.settings.menu_memory_enabled:
            self.state.selected_action = 0
        self.state.menu_state = MenuState.ACTIONS

    def open_play_menu(self) -> None:
        if not self.settings.menu_memory_enabled:
            self.state.selected_play_menu = 0
        self.state.menu_state = MenuState.PLAY_MENU

    def open_option_menu(self) -> None:
        if not self.settings.menu_memory_enabled:
            self.state.selected_option_menu = 0
        else:
            self.state.selected_option_menu = self.clamp_selection(self.state.selected_option_menu, self.option_menu)
        self.state.menu_state = MenuState.OPTIONS

    def open_food_menu(self) -> None:
        if not self.settings.menu_memory_enabled:
            self.state.selected_food = 0
        self.state.menu_state = MenuState.FOODS

    def open_theme_menu(self) -> None:
        if not self.settings.menu_memory_enabled:
            self.state.selected_theme = self.theme_options.index(self.settings.menu_theme)
        self.state.menu_state = MenuState.THEMES

    def open_resolution_menu(self) -> None:
        if not self.runtime.allow_display_scale:
            logger.info("Display scale menu is disabled for the current runtime.")
            self.open_option_menu()
            return

        if not self.settings.menu_memory_enabled:
            self.state.selected_resolution = self.resolution_options.index(self.settings.display_scale)
        self.state.menu_state = MenuState.RESOLUTION

    def open_reset_confirm(self) -> None:
        if not self.settings.menu_memory_enabled:
            self.state.selected_reset = 0
        self.state.menu_state = MenuState.RESET_CONFIRM

    def get_option_menu_labels(self) -> list[str]:
        labels: list[str] = []
        menu_mem_state = "On" if self.settings.menu_memory_enabled else "Off"
        volume_percent = int(round(self.settings.sound_volume * 100))
        auto_update_state = "On" if self.settings.auto_update_enabled else "Off"

        for option in self.option_menu:
            if option == "Theme":
                labels.append("Theme")
            elif option == "Menu Mem":
                labels.append(f"Menu Mem: {menu_mem_state}")
            elif option == "Volume":
                labels.append(f"Vol: {volume_percent}%")
            elif option == "Auto Upd":
                labels.append(f"Upd: {auto_update_state}")
            elif option == "Color":
                labels.append(f"Color: {self.get_display_saturation_label()}")
            elif option == "Contrast":
                labels.append(f"Contrast: {self.get_display_contrast_label()}")
            elif option == "Res":
                labels.append(f"Res: {self.settings.display_scale}x")
            elif option == "Reset":
                labels.append("Reset")

        return labels

    def reset_pet(self) -> None:
        logger.info("Resetting pet to default state.")
        self.pet = Pet()

    def reset_jump_rope_state(self) -> None:
        self.state.jump_rope_elapsed = 0.0
        self.state.jump_rope_countdown_elapsed = 0.0
        self.state.jump_rope_successes = 0
        self.state.jump_rope_jump_elapsed = 0.0
        self.state.jump_rope_jump_active = False
        self.state.jump_rope_clear_pending = False
        self.state.jump_rope_last_evaluated_cycle = -1
        self.state.jump_rope_last_countdown_number = -1

    def get_jump_rope_countdown_value(self) -> int:
        if self.state.jump_rope_countdown_elapsed >= JUMP_ROPE_COUNTDOWN_SECONDS:
            return 0

        completed_steps = min(
            JUMP_ROPE_COUNTDOWN_START,
            int((self.state.jump_rope_countdown_elapsed + 1e-9) / JUMP_ROPE_COUNTDOWN_STEP_SECONDS),
        )
        return max(1, JUMP_ROPE_COUNTDOWN_START - completed_steps)

    def get_jump_rope_jump_height(self) -> int:
        if not self.state.jump_rope_jump_active:
            return 0

        progress = min(1.0, self.state.jump_rope_jump_elapsed / JUMP_ROPE_JUMP_DURATION_SECONDS)
        return int(round(math.sin(progress * math.pi) * JUMP_ROPE_JUMP_HEIGHT))

    def handle_action(self) -> None:
        action = self.actions[self.state.selected_action]
        logger.info("Performing selected action: %s", action)

        if action == "Feed":
            self.play_sound("menu_confirm")
            self.open_food_menu()
        elif action == "Play":
            self.play_sound("menu_confirm")
            self.open_play_menu()
        elif action == "Clean":
            self.play_sound("clean_action")
            self.start_cleaning_animation()
        elif action == "Heal":
            self.pet.heal()
            self.play_sound("heal_action")
            self.state.menu_state = MenuState.HOME

    def start_jump_rope_game(self) -> None:
        logger.info("Starting jump rope minigame.")
        self.reset_jump_rope_state()
        self.state.pet_wander_x = float(SCREEN_WIDTH // 2)
        self.state.pet_wander_start_x = self.state.pet_wander_x
        self.state.pet_wander_target_x = self.state.pet_wander_x
        self.state.pet_wander_duration = 0.0
        self.state.pet_wander_elapsed = 0.0
        self.state.pet_facing_left = False
        self.state.menu_state = MenuState.JUMP_ROPE
        self.state.jump_rope_last_countdown_number = self.get_jump_rope_countdown_value()
        self.play_sound("countdown_beep")

    def complete_jump_rope_game(self) -> None:
        logger.info("Jump rope minigame cleared.")
        self.reset_jump_rope_state()
        self.complete_play_minigame()

    def complete_play_minigame(self) -> None:
        logger.info("Completing play minigame reward flow.")
        self.pet.play()
        self.start_action_celebration(sound_name="play_minigame_clear")

    def handle_jump_rope_jump(self) -> None:
        if self.state.jump_rope_countdown_elapsed < JUMP_ROPE_COUNTDOWN_SECONDS:
            logger.info("Jump rope countdown is still active; ignoring confirm input.")
            return

        if self.state.jump_rope_clear_pending:
            logger.info("Jump rope clear is pending; ignoring confirm input.")
            return

        if self.state.jump_rope_jump_active:
            logger.info("Jump rope jump already active; ignoring confirm input.")
            return

        logger.info("Starting jump rope jump.")
        self.state.jump_rope_jump_active = True
        self.state.jump_rope_jump_elapsed = 0.0
        self.play_sound("jump_rope_jump")

    def handle_jump_rope_success(self) -> None:
        self.state.jump_rope_successes += 1
        logger.info(
            "Jump rope success %s/%s.",
            self.state.jump_rope_successes,
            JUMP_ROPE_TARGET_SUCCESSES,
        )
        self.play_sound("minigame_success")
        if self.state.jump_rope_successes >= JUMP_ROPE_TARGET_SUCCESSES:
            self.state.jump_rope_clear_pending = True

    def feed_selected_food(self) -> None:
        if not self.food_options:
            logger.info("No food options available.")
            return

        selected_food = self.food_options[self.state.selected_food]
        logger.info("Feeding selected food: %s", selected_food.label)
        self.state.eating_food_index = self.state.selected_food
        self.state.eating_elapsed = 0.0
        self.state.last_eating_toggle_index = -1
        self.state.pet_wander_x = float(SCREEN_WIDTH // 2)
        self.state.pet_wander_start_x = self.state.pet_wander_x
        self.state.pet_wander_target_x = self.state.pet_wander_x
        self.state.pet_wander_duration = 0.0
        self.state.pet_wander_elapsed = 0.0
        self.state.pet_wander_pause = random.uniform(WANDER_PAUSE_MIN_SECONDS, WANDER_PAUSE_MAX_SECONDS)
        self.state.pet_facing_left = False
        self.state.menu_state = MenuState.EATING
        self.play_sound("feed_start")

    def start_cleaning_animation(self) -> None:
        logger.info("Starting cleaning animation.")
        self.state.cleaning_elapsed = 0.0
        self.state.last_cleaning_scrub_index = -1
        self.state.pet_wander_x = float(SCREEN_WIDTH // 2)
        self.state.pet_wander_start_x = self.state.pet_wander_x
        self.state.pet_wander_target_x = self.state.pet_wander_x
        self.state.pet_wander_duration = 0.0
        self.state.pet_wander_elapsed = 0.0
        self.state.pet_wander_pause = random.uniform(WANDER_PAUSE_MIN_SECONDS, WANDER_PAUSE_MAX_SECONDS)
        self.state.pet_facing_left = False
        self.state.menu_state = MenuState.CLEANING

    def complete_eating_animation(self) -> None:
        logger.info("Completing eating animation.")
        self.pet.feed()
        self.state.eating_elapsed = 0.0
        self.state.last_eating_toggle_index = -1
        self.start_action_celebration()

    def complete_cleaning_animation(self) -> None:
        logger.info("Completing cleaning animation.")
        self.pet.clean()
        self.state.cleaning_elapsed = 0.0
        self.state.last_cleaning_scrub_index = -1
        self.start_action_celebration()

    def start_action_celebration(self, sound_name: str = "action_celebrate") -> None:
        logger.info("Starting post-action celebration.")
        self.state.celebration_elapsed = 0.0
        self.state.pet_wander_x = float(SCREEN_WIDTH // 2)
        self.state.pet_wander_start_x = self.state.pet_wander_x
        self.state.pet_wander_target_x = self.state.pet_wander_x
        self.state.pet_wander_duration = 0.0
        self.state.pet_wander_elapsed = 0.0
        self.state.pet_facing_left = False
        self.state.menu_state = MenuState.CELEBRATING
        self.play_sound(sound_name)

    def complete_action_celebration(self) -> None:
        logger.info("Completing post-action celebration.")
        self.state.celebration_elapsed = 0.0
        self.state.pet_wander_pause = random.uniform(WANDER_PAUSE_MIN_SECONDS, WANDER_PAUSE_MAX_SECONDS)
        self.state.menu_state = MenuState.HOME

    def cycle_selection(self, step: int = 1) -> None:
        if self.state.menu_state == MenuState.HOME:
            logger.info("Opening main menu.")
            self.open_main_menu()
            self.play_sound("menu_cycle")
            return

        if self.state.menu_state == MenuState.ACTIONS:
            self.state.selected_action = self.cycle_index(self.state.selected_action, self.actions, step)
            logger.info("Selected action index changed to %s", self.state.selected_action)
            self.play_sound("menu_cycle")
            return

        if self.state.menu_state == MenuState.PLAY_MENU:
            self.state.selected_play_menu = self.cycle_index(self.state.selected_play_menu, self.play_menu, step)
            logger.info("Selected play menu index changed to %s", self.state.selected_play_menu)
            self.play_sound("menu_cycle")
            return

        if self.state.menu_state == MenuState.OPTIONS:
            self.state.selected_option_menu = self.cycle_index(self.state.selected_option_menu, self.option_menu, step)
            logger.info("Selected option menu index changed to %s", self.state.selected_option_menu)
            self.play_sound("menu_cycle")
            return

        if self.state.menu_state == MenuState.RESOLUTION:
            self.state.selected_resolution = self.cycle_index(self.state.selected_resolution, self.resolution_options, step)
            logger.info("Selected resolution index changed to %s", self.state.selected_resolution)
            self.play_sound("menu_cycle")
            return

        if self.state.menu_state == MenuState.FOODS:
            if self.food_options:
                self.state.selected_food = self.cycle_index(self.state.selected_food, self.food_options, step)
                logger.info("Selected food index changed to %s", self.state.selected_food)
                self.play_sound("menu_cycle")
            return

        if self.state.menu_state == MenuState.EATING:
            logger.info("Eating animation is active; ignoring selection cycle.")
            return

        if self.state.menu_state == MenuState.CLEANING:
            logger.info("Cleaning animation is active; ignoring selection cycle.")
            return

        if self.state.menu_state == MenuState.JUMP_ROPE:
            logger.info("Jump rope minigame is active; ignoring selection cycle.")
            return

        if self.state.menu_state == MenuState.CELEBRATING:
            logger.info("Celebration animation is active; ignoring selection cycle.")
            return

        if self.state.menu_state == MenuState.THEMES:
            self.state.selected_theme = self.cycle_index(self.state.selected_theme, self.theme_options, step)
            logger.info("Selected theme index changed to %s", self.state.selected_theme)
            self.play_sound("menu_cycle")
            return

        if self.state.menu_state == MenuState.RESET_CONFIRM:
            self.state.selected_reset = self.cycle_index(self.state.selected_reset, self.reset_options, step)
            logger.info("Selected reset confirmation index changed to %s", self.state.selected_reset)
            self.play_sound("menu_cycle")
            return

        if self.state.menu_state == MenuState.STATUS:
            logger.info("Status view has no selectable items.")
            return

        self.state.selected_menu = self.cycle_index(self.state.selected_menu, self.main_menu, step)
        logger.info("Selected main menu index changed to %s", self.state.selected_menu)
        self.play_sound("menu_cycle")

    def move_food_grid_selection(self, horizontal_step: int, vertical_step: int) -> bool:
        if not self.food_options:
            return False

        current_index = self.clamp_selection(self.state.selected_food, self.food_options)
        current_row = current_index // FOOD_GRID_COLUMNS
        current_column = current_index % FOOD_GRID_COLUMNS
        target_row = current_row + vertical_step
        target_column = current_column + horizontal_step

        if target_column < 0 or target_column >= FOOD_GRID_COLUMNS:
            return False
        if target_row < 0 or target_row >= FOOD_GRID_ROWS:
            return False

        target_index = (target_row * FOOD_GRID_COLUMNS) + target_column
        if target_index >= len(self.food_options):
            return False

        if target_index == current_index:
            return False

        self.state.selected_food = target_index
        logger.info("Selected food index changed to %s", self.state.selected_food)
        self.play_sound("menu_cycle")
        return True

    def handle_directional_selection(self, action: str) -> bool:
        if self.state.menu_state != MenuState.FOODS:
            return False

        if action == INPUT_LEFT:
            self.move_food_grid_selection(-1, 0)
            return True
        if action == INPUT_RIGHT:
            self.move_food_grid_selection(1, 0)
            return True
        if action == INPUT_UP:
            self.move_food_grid_selection(0, -1)
            return True
        if action == INPUT_DOWN:
            self.move_food_grid_selection(0, 1)
            return True

        return False

    def confirm_selection(self) -> None:
        if self.state.menu_state == MenuState.HOME:
            logger.info("Confirm pressed on home screen; no action taken.")
            return

        if self.state.menu_state == MenuState.ACTIONS:
            self.handle_action()
            return

        if self.state.menu_state == MenuState.PLAY_MENU:
            selected_game = self.play_menu[self.state.selected_play_menu]
            logger.info("Confirming play menu choice: %s", selected_game)
            if selected_game == "Jump Rope":
                self.start_jump_rope_game()
            return

        if self.state.menu_state == MenuState.OPTIONS:
            selected_option = self.option_menu[self.state.selected_option_menu]
            logger.info("Confirming option menu choice: %s", selected_option)

            if selected_option == "Theme":
                self.play_sound("menu_confirm")
                self.open_theme_menu()
            elif selected_option == "Menu Mem":
                self.settings.menu_memory_enabled = not self.settings.menu_memory_enabled
                logger.info("Menu memory toggled to %s", self.settings.menu_memory_enabled)
                self.play_sound("setting_change")
            elif selected_option == "Volume":
                self.cycle_sound_volume()
                self.play_sound("setting_change")
            elif selected_option == "Auto Upd":
                self.settings.auto_update_enabled = not self.settings.auto_update_enabled
                logger.info("Auto update toggled to %s", self.settings.auto_update_enabled)
                self.play_sound("setting_change")
            elif selected_option == "Color":
                self.cycle_display_saturation()
                self.play_sound("setting_change")
            elif selected_option == "Contrast":
                self.cycle_display_contrast()
                self.play_sound("setting_change")
            elif selected_option == "Res":
                self.play_sound("menu_confirm")
                self.open_resolution_menu()
            elif selected_option == "Reset":
                self.play_sound("menu_confirm")
                self.open_reset_confirm()
            return

        if self.state.menu_state == MenuState.RESOLUTION:
            selected_scale = self.resolution_options[self.state.selected_resolution]
            logger.info("Changing display scale to %sx", selected_scale)
            self.apply_display_scale(selected_scale)
            self.play_sound("setting_change")
            self.open_option_menu()
            return

        if self.state.menu_state == MenuState.FOODS:
            self.feed_selected_food()
            return

        if self.state.menu_state == MenuState.EATING:
            logger.info("Confirm pressed during eating animation; skipping to completion.")
            self.complete_eating_animation()
            return

        if self.state.menu_state == MenuState.CLEANING:
            logger.info("Confirm pressed during cleaning animation; skipping to completion.")
            self.complete_cleaning_animation()
            return

        if self.state.menu_state == MenuState.JUMP_ROPE:
            self.handle_jump_rope_jump()
            return

        if self.state.menu_state == MenuState.CELEBRATING:
            logger.info("Confirm pressed during celebration animation; skipping to home.")
            self.complete_action_celebration()
            return

        if self.state.menu_state == MenuState.THEMES:
            self.settings.menu_theme = self.theme_options[self.state.selected_theme]
            logger.info("Menu theme changed to %s", self.settings.menu_theme)
            self.play_sound("setting_change")
            self.open_option_menu()
            return

        if self.state.menu_state == MenuState.RESET_CONFIRM:
            if self.reset_options[self.state.selected_reset] == "Yes":
                self.reset_pet()
                self.play_sound("reset_confirm")
                self.state.menu_state = MenuState.HOME
            else:
                self.play_sound("menu_back")
                self.open_option_menu()
            return

        if self.state.menu_state == MenuState.STATUS:
            logger.info("Status view has no confirm action.")
            return

        selected_option = self.main_menu[self.state.selected_menu]
        logger.info("Confirming main menu option: %s", selected_option)

        if selected_option == "Action":
            self.play_sound("menu_confirm")
            self.open_actions_menu()
        elif selected_option == "Status":
            self.play_sound("menu_confirm")
            self.state.menu_state = MenuState.STATUS
        elif selected_option == "Option":
            self.play_sound("menu_confirm")
            self.open_option_menu()

    def go_back(self) -> None:
        if self.state.menu_state == MenuState.HOME:
            logger.info("Back pressed on home screen; ignoring input.")
            return

        if self.state.menu_state == MenuState.MAIN_MENU:
            logger.info("Closing main menu and returning to home screen.")
            self.play_sound("menu_back")
            self.state.menu_state = MenuState.HOME
            return

        if self.state.menu_state == MenuState.PLAY_MENU:
            logger.info("Leaving play menu and returning to actions.")
            self.play_sound("menu_back")
            self.open_actions_menu()
            return

        if self.state.menu_state == MenuState.FOODS:
            logger.info("Leaving food menu and returning to actions.")
            self.play_sound("menu_back")
            self.open_actions_menu()
            return

        if self.state.menu_state == MenuState.EATING:
            logger.info("Eating animation is active; ignoring back input.")
            return

        if self.state.menu_state == MenuState.CLEANING:
            logger.info("Cleaning animation is active; ignoring back input.")
            return

        if self.state.menu_state == MenuState.JUMP_ROPE:
            logger.info("Leaving jump rope minigame and returning to play menu.")
            self.reset_jump_rope_state()
            self.play_sound("menu_back")
            self.open_play_menu()
            return

        if self.state.menu_state == MenuState.CELEBRATING:
            logger.info("Celebration animation is active; ignoring back input.")
            return

        if self.state.menu_state in (MenuState.ACTIONS, MenuState.STATUS, MenuState.OPTIONS):
            logger.info("Leaving submenu and returning to main menu.")
            self.play_sound("menu_back")
            self.open_main_menu()
            return

        if self.state.menu_state in (MenuState.THEMES, MenuState.RESOLUTION, MenuState.RESET_CONFIRM):
            logger.info("Leaving option submenu and returning to options.")
            self.play_sound("menu_back")
            self.open_option_menu()

    def get_wander_bounds(self) -> tuple[float, float]:
        half_width = HOME_PET_SIZE[0] / 2
        min_x = half_width + WANDER_SCREEN_MARGIN
        max_x = SCREEN_WIDTH - half_width - WANDER_SCREEN_MARGIN
        return min_x, max_x

    def start_wander_move(self) -> None:
        min_x, max_x = self.get_wander_bounds()
        if max_x <= min_x:
            self.state.pet_wander_start_x = SCREEN_WIDTH / 2
            self.state.pet_wander_x = self.state.pet_wander_start_x
            self.state.pet_wander_target_x = SCREEN_WIDTH / 2
            self.state.pet_wander_duration = 0.0
            self.state.pet_wander_elapsed = 0.0
            return

        target_x = self.state.pet_wander_x
        for _ in range(5):
            target_x = random.uniform(min_x, max_x)
            if abs(target_x - self.state.pet_wander_x) >= 8.0:
                break

        distance = abs(target_x - self.state.pet_wander_x)
        if distance <= 1.0:
            self.state.pet_wander_pause = random.uniform(WANDER_PAUSE_MIN_SECONDS, WANDER_PAUSE_MAX_SECONDS)
            return

        self.state.pet_wander_start_x = self.state.pet_wander_x
        self.state.pet_wander_target_x = target_x
        self.state.pet_wander_duration = distance / WANDER_SPEED
        self.state.pet_wander_elapsed = 0.0
        self.state.pet_hop_count = max(1, round(self.state.pet_wander_duration * WANDER_HOPS_PER_SECOND))
        self.state.pet_facing_left = self.state.pet_wander_target_x < self.state.pet_wander_start_x
        logger.info(
            "New wander move: start=%.2f target=%.2f duration=%.2f hops=%s",
            self.state.pet_wander_start_x,
            self.state.pet_wander_target_x,
            self.state.pet_wander_duration,
            self.state.pet_hop_count,
        )

    def update_pet_wander(self, dt: float) -> None:
        if self.state.menu_state != MenuState.HOME:
            return

        if self.state.pet_wander_duration <= 0:
            self.state.pet_wander_pause -= dt
            if self.state.pet_wander_pause <= 0:
                self.start_wander_move()
            return

        self.state.pet_wander_elapsed = min(self.state.pet_wander_duration, self.state.pet_wander_elapsed + dt)
        progress = self.state.pet_wander_elapsed / self.state.pet_wander_duration
        self.state.pet_wander_x = self.state.pet_wander_start_x + (
            (self.state.pet_wander_target_x - self.state.pet_wander_start_x) * progress
        )

        min_x, max_x = self.get_wander_bounds()
        self.state.pet_wander_x = max(min_x, min(max_x, self.state.pet_wander_x))

        if progress >= 1.0:
            self.state.pet_wander_x = self.state.pet_wander_target_x
            self.state.pet_wander_duration = 0.0
            self.state.pet_wander_elapsed = 0.0
            self.state.pet_wander_pause = random.uniform(WANDER_PAUSE_MIN_SECONDS, WANDER_PAUSE_MAX_SECONDS)

    def update_eating_animation(self, dt: float) -> None:
        if self.state.menu_state != MenuState.EATING:
            return

        self.state.eating_elapsed += dt
        if self.state.eating_elapsed >= FEED_DROP_DURATION_SECONDS:
            munch_time = self.state.eating_elapsed - FEED_DROP_DURATION_SECONDS
            toggle_index = min(FEED_MUNCH_TOGGLE_COUNT - 1, int(munch_time / FEED_MUNCH_FRAME_SECONDS))
            if toggle_index != self.state.last_eating_toggle_index:
                self.state.last_eating_toggle_index = toggle_index
                if toggle_index % 2 == 0:
                    self.play_sound("eat_munch")

        total_duration = FEED_DROP_DURATION_SECONDS + (FEED_MUNCH_TOGGLE_COUNT * FEED_MUNCH_FRAME_SECONDS)
        if self.state.eating_elapsed >= total_duration:
            self.complete_eating_animation()

    def update_cleaning_animation(self, dt: float) -> None:
        if self.state.menu_state != MenuState.CLEANING:
            return

        self.state.cleaning_elapsed += dt
        if self.state.cleaning_elapsed >= CLEAN_DROP_DURATION_SECONDS:
            scrub_time = self.state.cleaning_elapsed - CLEAN_DROP_DURATION_SECONDS
            scrub_index = int(scrub_time / CLEAN_SCRUB_SOUND_INTERVAL_SECONDS)
            if scrub_index != self.state.last_cleaning_scrub_index:
                self.state.last_cleaning_scrub_index = scrub_index
                self.play_sound("clean_scrub")

        total_duration = CLEAN_DROP_DURATION_SECONDS + CLEAN_SCRUB_DURATION_SECONDS
        if self.state.cleaning_elapsed >= total_duration:
            self.complete_cleaning_animation()

    def update_jump_rope_game(self, dt: float) -> None:
        if self.state.menu_state != MenuState.JUMP_ROPE:
            return

        if self.state.jump_rope_countdown_elapsed < JUMP_ROPE_COUNTDOWN_SECONDS:
            previous_countdown_value = self.get_jump_rope_countdown_value()
            self.state.jump_rope_countdown_elapsed = min(
                JUMP_ROPE_COUNTDOWN_SECONDS,
                self.state.jump_rope_countdown_elapsed + dt,
            )
            countdown_value = self.get_jump_rope_countdown_value()
            if (
                countdown_value > 0
                and countdown_value != self.state.jump_rope_last_countdown_number
            ):
                self.state.jump_rope_last_countdown_number = countdown_value
                self.play_sound("countdown_beep")
            elif countdown_value == 0 and previous_countdown_value > 0:
                self.state.jump_rope_last_countdown_number = 0
                self.play_sound("countdown_start")
            return

        self.state.jump_rope_elapsed += dt

        if self.state.jump_rope_jump_active:
            self.state.jump_rope_jump_elapsed += dt
            if self.state.jump_rope_jump_elapsed >= JUMP_ROPE_JUMP_DURATION_SECONDS:
                self.state.jump_rope_jump_elapsed = 0.0
                self.state.jump_rope_jump_active = False
                if self.state.jump_rope_clear_pending:
                    self.complete_jump_rope_game()
                    return

        cycle_index = int(self.state.jump_rope_elapsed / JUMP_ROPE_CYCLE_SECONDS)
        cycle_progress = (self.state.jump_rope_elapsed % JUMP_ROPE_CYCLE_SECONDS) / JUMP_ROPE_CYCLE_SECONDS
        if cycle_progress < JUMP_ROPE_PASS_PHASE or self.state.jump_rope_last_evaluated_cycle == cycle_index:
            return

        self.state.jump_rope_last_evaluated_cycle = cycle_index
        if self.get_jump_rope_jump_height() >= JUMP_ROPE_REQUIRED_HEIGHT:
            self.handle_jump_rope_success()

    def update_action_celebration(self, dt: float) -> None:
        if self.state.menu_state != MenuState.CELEBRATING:
            return

        self.state.celebration_elapsed += dt
        if self.state.celebration_elapsed >= ACTION_CELEBRATION_DURATION_SECONDS:
            self.complete_action_celebration()

    def update(self, dt: float) -> None:
        logger.debug("Updating game state with dt=%.4f", dt)
        previous_menu_state = self.state.menu_state
        self.update_eating_animation(dt)
        self.update_cleaning_animation(dt)
        self.update_jump_rope_game(dt)
        if not (self.state.menu_state == MenuState.CELEBRATING and previous_menu_state != MenuState.CELEBRATING):
            self.update_action_celebration(dt)
        self.update_pet_wander(dt)
        self.state.decay_accumulator += dt
        if self.state.decay_accumulator >= DECAY_TIMER_SECONDS:
            logger.info("Decay timer reached; updating pet stats.")
            self.pet.update_decay()
            self.state.decay_accumulator = 0.0

    def draw_ui(self) -> None:
        logger.debug("Drawing UI...")
        if self.state.menu_state == MenuState.HOME:
            self.renderer.draw_home_screen(self.pet, self.settings, self.state)
            return

        if self.state.menu_state == MenuState.MAIN_MENU:
            self.renderer.draw_fullscreen_menu(self.settings, "Menu", self.main_menu, self.state.selected_menu)
            return

        if self.state.menu_state == MenuState.ACTIONS:
            self.renderer.draw_fullscreen_menu(self.settings, "Action", self.actions, self.state.selected_action)
            return

        if self.state.menu_state == MenuState.PLAY_MENU:
            self.renderer.draw_fullscreen_menu(self.settings, "Play", self.play_menu, self.state.selected_play_menu)
            return

        if self.state.menu_state == MenuState.OPTIONS:
            self.renderer.draw_fullscreen_menu(self.settings, "Option", self.get_option_menu_labels(), self.state.selected_option_menu)
            return

        if self.state.menu_state == MenuState.RESOLUTION:
            resolution_labels = [f"{scale}X" for scale in self.resolution_options]
            self.renderer.draw_fullscreen_menu(self.settings, "Res", resolution_labels, self.state.selected_resolution)
            return

        if self.state.menu_state == MenuState.FOODS:
            self.renderer.draw_food_grid_screen(self.settings, self.food_options, self.state.selected_food)
            return

        if self.state.menu_state == MenuState.EATING:
            self.renderer.draw_eating_screen(self.pet, self.settings, self.state, self.food_options)
            return

        if self.state.menu_state == MenuState.CLEANING:
            self.renderer.draw_cleaning_screen(self.pet, self.settings, self.state)
            return

        if self.state.menu_state == MenuState.JUMP_ROPE:
            self.renderer.draw_jump_rope_screen(self.pet, self.settings, self.state)
            return

        if self.state.menu_state == MenuState.CELEBRATING:
            self.renderer.draw_celebration_screen(self.pet, self.settings, self.state)
            return

        if self.state.menu_state == MenuState.STATUS:
            self.renderer.draw_status_screen(self.pet, self.settings)
            return

        if self.state.menu_state == MenuState.THEMES:
            theme_labels = [self.themes[theme_key].label for theme_key in self.theme_options]
            self.renderer.draw_fullscreen_menu(self.settings, "Theme", theme_labels, self.state.selected_theme)
            return

        if self.state.menu_state == MenuState.RESET_CONFIRM:
            self.renderer.draw_reset_confirm_screen(self.state.selected_reset, self.reset_options)

    def handle_events(self) -> None:
        logger.debug("Polling events...")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("Quit event received.")
                self.state.running = False
            elif event.type == pygame.KEYDOWN:
                logger.debug("Key pressed: %s", event.key)
                self.handle_keyboard_input(event.key)

        if self.hardware_input is not None:
            for action in self.hardware_input.poll_actions():
                self.handle_input_action(action)

    def handle_keyboard_input(self, key: int) -> None:
        if self.key_matches(key, "K_q", "K_TAB"):
            self.handle_input_action(INPUT_NEXT)
        elif self.key_matches(key, "K_a"):
            self.handle_input_action(INPUT_PREVIOUS)
        elif self.key_matches(key, "K_DOWN"):
            self.handle_input_action(INPUT_DOWN)
        elif self.key_matches(key, "K_RIGHT"):
            self.handle_input_action(INPUT_RIGHT)
        elif self.key_matches(key, "K_UP"):
            self.handle_input_action(INPUT_UP)
        elif self.key_matches(key, "K_LEFT"):
            self.handle_input_action(INPUT_LEFT)
        elif self.key_matches(key, "K_w", "K_RETURN", "K_SPACE"):
            self.handle_input_action(INPUT_CONFIRM)
        elif self.key_matches(key, "K_e", "K_ESCAPE", "K_BACKSPACE"):
            self.handle_input_action(INPUT_BACK)

    def handle_input_action(self, action: str) -> None:
        if action == INPUT_NEXT:
            self.cycle_selection(1)
        elif action == INPUT_PREVIOUS:
            self.cycle_selection(-1)
        elif action in (INPUT_DOWN, INPUT_RIGHT, INPUT_UP, INPUT_LEFT):
            if self.handle_directional_selection(action):
                return
            if action in (INPUT_DOWN, INPUT_RIGHT):
                self.cycle_selection(1)
            else:
                self.cycle_selection(-1)
        elif action == INPUT_CONFIRM:
            self.confirm_selection()
        elif action == INPUT_BACK:
            self.go_back()

    @staticmethod
    def key_matches(key: int, *key_names: str) -> bool:
        for key_name in key_names:
            if key == getattr(pygame, key_name, None):
                return True

        return False

    def shutdown(self, save: bool = True) -> None:
        if self._is_shutdown:
            return

        self._is_shutdown = True
        if save:
            logger.info("Saving state before quit...")
            save_game_state(self.pet, self.settings)
        if self.display_output is not None:
            self.display_output.close()
        if self.hardware_input is not None:
            self.hardware_input.close()
        pygame.quit()
        logger.info("Shutdown complete.")

    def run(self) -> int:
        logger.info("Entering main loop...")
        try:
            while self.state.running:
                dt = self.clock.tick(FPS) / 1000.0
                self.handle_events()
                self.update(dt)
                self.draw_ui()
                self.present_frame()
        finally:
            logger.info("Exiting main loop.")
            self.shutdown(save=True)

        return 0
