from __future__ import annotations

import logging
import math
from datetime import datetime

import pygame

from .config import (
    ACCENT,
    BAD,
    BG,
    BLACK,
    CLEAN_BUBBLE_OFFSETS,
    CLEAN_BUBBLE_FADE_IN_PROGRESS,
    CLEAN_BUBBLE_FADE_OUT_START_PROGRESS,
    CLEAN_BUBBLE_SPAWN_WINDOW,
    CLEAN_DROP_DURATION_SECONDS,
    CLEAN_SCRUB_DURATION_SECONDS,
    CLEAN_SCRUB_OFFSETS,
    CLEAN_SOAP_START_Y,
    CLEAN_SOAP_TARGET_X_OFFSET,
    CLEAN_SOAP_TARGET_Y_OFFSET,
    FEED_DROP_DURATION_SECONDS,
    FEED_FOOD_SHAKE_AMPLITUDE,
    FEED_FOOD_START_Y,
    FEED_FOOD_TARGET_X_OFFSET,
    FEED_FOOD_TARGET_Y_OFFSET,
    FEED_MUNCH_FRAME_SECONDS,
    FEED_MUNCH_TOGGLE_COUNT,
    FOOD_GRID_CELL_SIZE,
    FOOD_GRID_COLUMNS,
    FOOD_GRID_GAP,
    FOOD_GRID_ROWS,
    GOOD,
    HOME_PET_SIZE,
    JUMP_ROPE_ANCHOR_X_OFFSET,
    JUMP_ROPE_ANCHOR_Y_OFFSET,
    JUMP_ROPE_BOTTOM_Y_OFFSET,
    JUMP_ROPE_COUNTDOWN_START,
    JUMP_ROPE_COUNTDOWN_SECONDS,
    JUMP_ROPE_COUNTDOWN_STEP_SECONDS,
    JUMP_ROPE_CONTROL_X_SWAY,
    JUMP_ROPE_CURVE_SEGMENTS,
    JUMP_ROPE_CYCLE_SECONDS,
    JUMP_ROPE_JUMP_DURATION_SECONDS,
    JUMP_ROPE_JUMP_HEIGHT,
    JUMP_ROPE_ROPE_THICKNESS,
    JUMP_ROPE_TARGET_SUCCESSES,
    JUMP_ROPE_TOP_Y_OFFSET,
    MAX_STAT,
    PANEL,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WANDER_BOB_AMPLITUDE,
    WHITE,
)
from .models import AppSettings, FoodItem, Pet, PetMood, RuntimeState, ThemePalette
from .ui_helpers import (
    draw_circle_meter,
    draw_text,
    draw_text_centered,
    format_menu_text,
    paginate_menu_options,
    truncate_text_to_width,
    wrap_text_to_width,
)

logger = logging.getLogger("virtual_pet")


class GameRenderer:
    def __init__(
        self,
        screen: pygame.Surface,
        themes: dict[str, ThemePalette],
        home_background: pygame.Surface | None,
        base_sprite: pygame.Surface | None,
        face_sprite: pygame.Surface | None,
        extra_happy_face_sprite: pygame.Surface | None,
        munch_face_closed_sprite: pygame.Surface | None,
        munch_face_open_sprite: pygame.Surface | None,
        soap_sprite: pygame.Surface | None,
        bubbles_sprite: pygame.Surface | None,
    ) -> None:
        self.screen = screen
        self.themes = themes
        self.home_background = home_background
        self.base_sprite = base_sprite
        self.face_sprite = face_sprite
        self.extra_happy_face_sprite = extra_happy_face_sprite
        self.munch_face_closed_sprite = munch_face_closed_sprite
        self.munch_face_open_sprite = munch_face_open_sprite
        self.soap_sprite = soap_sprite
        self.bubbles_sprite = bubbles_sprite
        self.font = pygame.font.SysFont("arial", 18)
        self.big_font = pygame.font.SysFont("arial", 20, bold=True)
        self.menu_font = pygame.font.SysFont("arial", 22, bold=True)
        self.small_font = pygame.font.SysFont("arial", 12)

    def get_menu_theme_palette(self, settings: AppSettings) -> ThemePalette:
        return self.themes[settings.menu_theme]

    def draw_pet_shadow(self, center_x: int, baseline_y: int, size: tuple[int, int]) -> None:
        shadow_width = max(16, int(round(size[0] * 0.5)))
        shadow_height = max(8, int(round(size[1] * 0.16)))
        shadow_center_y = baseline_y + int(round(size[1] * 0.42))
        shadow_surface = pygame.Surface((shadow_width, shadow_height), pygame.SRCALPHA)
        pygame.draw.ellipse(
            shadow_surface,
            (0, 0, 0, 72),
            shadow_surface.get_rect(),
        )
        shadow_rect = shadow_surface.get_rect(center=(center_x, shadow_center_y))
        self.screen.blit(shadow_surface, shadow_rect)

    def draw_pet(
        self,
        pet: Pet,
        state: RuntimeState,
        center: tuple[int, int],
        size: tuple[int, int],
        face_sprite_override: pygame.Surface | None = None,
        facing_left_override: bool | None = None,
    ) -> None:
        logger.info("Drawing pet...")
        mood = pet.get_mood()
        width, height = size
        facing_left = state.pet_facing_left if facing_left_override is None else facing_left_override
        active_face_sprite = self.face_sprite if face_sprite_override is None else face_sprite_override

        if self.base_sprite is not None or active_face_sprite is not None:
            sprite_rect = pygame.Rect(0, 0, width, height)
            sprite_rect.center = center

            if self.base_sprite is not None:
                base_sprite = self.base_sprite
                if base_sprite.get_size() != size:
                    base_sprite = pygame.transform.scale(base_sprite, size)
                if facing_left:
                    base_sprite = pygame.transform.flip(base_sprite, True, False)
                self.screen.blit(base_sprite, sprite_rect)

            if active_face_sprite is not None:
                face_sprite = active_face_sprite
                if face_sprite.get_size() != size:
                    face_sprite = pygame.transform.scale(face_sprite, size)
                if facing_left:
                    face_sprite = pygame.transform.flip(face_sprite, True, False)
                self.screen.blit(face_sprite, sprite_rect)

            return

        body_rect = pygame.Rect(0, 0, int(width * 0.82), int(height * 0.7))
        body_rect.center = center
        pygame.draw.ellipse(self.screen, ACCENT, body_rect)
        pygame.draw.ellipse(self.screen, WHITE, body_rect, 2)

        eye_y = body_rect.y + int(body_rect.height * 0.4)
        left_eye_x = body_rect.x + int(body_rect.width * 0.35)
        right_eye_x = body_rect.x + int(body_rect.width * 0.65)
        eye_radius = max(2, width // 24)
        pygame.draw.circle(self.screen, BLACK, (left_eye_x, eye_y), eye_radius)
        pygame.draw.circle(self.screen, BLACK, (right_eye_x, eye_y), eye_radius)

        mouth_rect = pygame.Rect(0, 0, int(body_rect.width * 0.28), max(8, height // 10))
        mouth_rect.center = (body_rect.centerx, body_rect.y + int(body_rect.height * 0.68))

        if mood == PetMood.HAPPY:
            pygame.draw.arc(self.screen, BLACK, mouth_rect, 3.14, 6.28, 2)
        elif mood == PetMood.OKAY:
            pygame.draw.line(self.screen, BLACK, (mouth_rect.left, mouth_rect.centery), (mouth_rect.right, mouth_rect.centery), 2)
        elif mood == PetMood.SAD:
            pygame.draw.arc(self.screen, BLACK, mouth_rect, 0, 3.14, 2)
        elif mood == PetMood.SICK:
            left_x_rect = pygame.Rect(left_eye_x - 4, eye_y + 10, 8, 8)
            right_x_rect = pygame.Rect(right_eye_x - 4, eye_y + 10, 8, 8)
            pygame.draw.line(self.screen, BLACK, left_x_rect.topleft, left_x_rect.bottomright, 2)
            pygame.draw.line(self.screen, BLACK, left_x_rect.topright, left_x_rect.bottomleft, 2)
            pygame.draw.line(self.screen, BLACK, right_x_rect.topleft, right_x_rect.bottomright, 2)
            pygame.draw.line(self.screen, BLACK, right_x_rect.topright, right_x_rect.bottomleft, 2)
            pygame.draw.arc(self.screen, BLACK, mouth_rect, 0, 3.14, 2)

    def draw_home_screen(self, pet: Pet, settings: AppSettings, state: RuntimeState) -> None:
        logger.info("Drawing home screen...")
        if self.home_background is not None:
            self.screen.blit(self.home_background, (0, 0))
        else:
            self.screen.fill(BG)

        hop_offset = 0
        if state.pet_wander_duration > 0:
            progress = min(1.0, state.pet_wander_elapsed / state.pet_wander_duration)
            hop_wave = math.sin(progress * state.pet_hop_count * math.pi)
            hop_offset = int(round((hop_wave * hop_wave) * WANDER_BOB_AMPLITUDE))

        pet_center = (int(round(state.pet_wander_x)), state.pet_home_y - hop_offset)
        self.draw_clock(settings)
        self.draw_pet_shadow(pet_center[0], state.pet_home_y, HOME_PET_SIZE)
        self.draw_pet(pet, state, pet_center, HOME_PET_SIZE)

    def draw_eating_screen(
        self,
        pet: Pet,
        settings: AppSettings,
        state: RuntimeState,
        food_options: list[FoodItem],
    ) -> None:
        logger.info("Drawing eating screen...")
        if self.home_background is not None:
            self.screen.blit(self.home_background, (0, 0))
        else:
            self.screen.fill(BG)

        self.draw_clock(settings)

        pet_center = (SCREEN_WIDTH // 2, state.pet_home_y)
        face_override = self.face_sprite
        food_option = None
        if 0 <= state.eating_food_index < len(food_options):
            food_option = food_options[state.eating_food_index]

        if state.eating_elapsed < FEED_DROP_DURATION_SECONDS:
            progress = state.eating_elapsed / FEED_DROP_DURATION_SECONDS
            progress = max(0.0, min(1.0, progress))
            eased_progress = 1.0 - ((1.0 - progress) ** 3)
            food_center_x = pet_center[0] + FEED_FOOD_TARGET_X_OFFSET
            food_center_y = FEED_FOOD_START_Y + ((state.pet_home_y + FEED_FOOD_TARGET_Y_OFFSET - FEED_FOOD_START_Y) * eased_progress)
            food_offset_x = 0
            food_offset_y = 0
            visible_food_height = food_option.sprite.get_height() if food_option is not None and food_option.sprite is not None else 0
        else:
            munch_time = state.eating_elapsed - FEED_DROP_DURATION_SECONDS
            toggle_index = min(FEED_MUNCH_TOGGLE_COUNT - 1, int(munch_time / FEED_MUNCH_FRAME_SECONDS))
            if toggle_index % 2:
                face_override = self.munch_face_open_sprite or self.face_sprite
            else:
                face_override = self.munch_face_closed_sprite or self.face_sprite
            food_center_x = pet_center[0] + FEED_FOOD_TARGET_X_OFFSET
            food_center_y = state.pet_home_y + FEED_FOOD_TARGET_Y_OFFSET
            food_offset_x = int(round(math.sin(munch_time * 30.0) * FEED_FOOD_SHAKE_AMPLITUDE))
            food_offset_y = int(round(math.cos(munch_time * 24.0) * (FEED_FOOD_SHAKE_AMPLITUDE * 0.5)))
            visible_food_height = 0
            if food_option is not None and food_option.sprite is not None:
                bite_count = max(1, (FEED_MUNCH_TOGGLE_COUNT + 1) // 2)
                completed_bites = min(bite_count, (toggle_index // 2) + 1)
                remaining_ratio = max(0.0, 1.0 - (completed_bites / (bite_count + 1)))
                visible_food_height = max(1, int(round(food_option.sprite.get_height() * remaining_ratio)))

        self.draw_pet_shadow(pet_center[0], state.pet_home_y, HOME_PET_SIZE)
        self.draw_pet(pet, state, pet_center, HOME_PET_SIZE, face_sprite_override=face_override, facing_left_override=False)

        if food_option is not None and food_option.sprite is not None and visible_food_height > 0:
            food_rect = food_option.sprite.get_rect(
                center=(
                    int(round(food_center_x + food_offset_x)),
                    int(round(food_center_y + food_offset_y)),
                )
            )
            self.draw_bottom_cropped_sprite(food_option.sprite, food_rect, visible_food_height)

    def draw_cleaning_screen(self, pet: Pet, settings: AppSettings, state: RuntimeState) -> None:
        logger.info("Drawing cleaning screen...")
        if self.home_background is not None:
            self.screen.blit(self.home_background, (0, 0))
        else:
            self.screen.fill(BG)

        self.draw_clock(settings)

        pet_center = (SCREEN_WIDTH // 2, state.pet_home_y)
        self.draw_pet_shadow(pet_center[0], state.pet_home_y, HOME_PET_SIZE)
        self.draw_pet(pet, state, pet_center, HOME_PET_SIZE, facing_left_override=False)

        if state.cleaning_elapsed < CLEAN_DROP_DURATION_SECONDS:
            progress = state.cleaning_elapsed / CLEAN_DROP_DURATION_SECONDS
            progress = max(0.0, min(1.0, progress))
            eased_progress = 1.0 - ((1.0 - progress) ** 3)
            soap_center_x = pet_center[0] + CLEAN_SOAP_TARGET_X_OFFSET
            soap_center_y = CLEAN_SOAP_START_Y + ((pet_center[1] + CLEAN_SOAP_TARGET_Y_OFFSET - CLEAN_SOAP_START_Y) * eased_progress)
        else:
            scrub_time = min(CLEAN_SCRUB_DURATION_SECONDS, state.cleaning_elapsed - CLEAN_DROP_DURATION_SECONDS)
            scrub_progress = scrub_time / CLEAN_SCRUB_DURATION_SECONDS
            segment_count = max(1, len(CLEAN_SCRUB_OFFSETS) - 1)
            segment_duration = CLEAN_SCRUB_DURATION_SECONDS / segment_count
            segment_index = min(segment_count - 1, int(scrub_time / segment_duration))
            segment_progress = (scrub_time - (segment_index * segment_duration)) / segment_duration
            start_offset = CLEAN_SCRUB_OFFSETS[segment_index]
            end_offset = CLEAN_SCRUB_OFFSETS[segment_index + 1]
            soap_center_x = pet_center[0] + start_offset[0] + ((end_offset[0] - start_offset[0]) * segment_progress)
            soap_center_y = pet_center[1] + start_offset[1] + ((end_offset[1] - start_offset[1]) * segment_progress)
            self.draw_cleaning_bubbles(pet_center, scrub_time, scrub_progress)

        if self.soap_sprite is None:
            return

        soap_rect = self.soap_sprite.get_rect(center=(int(round(soap_center_x)), int(round(soap_center_y))))
        self.screen.blit(self.soap_sprite, soap_rect)

    def draw_celebration_screen(self, pet: Pet, settings: AppSettings, state: RuntimeState) -> None:
        logger.info("Drawing celebration screen...")
        if self.home_background is not None:
            self.screen.blit(self.home_background, (0, 0))
        else:
            self.screen.fill(BG)

        self.draw_clock(settings)

        pet_center = (SCREEN_WIDTH // 2, state.pet_home_y)
        face_override = self.extra_happy_face_sprite or self.face_sprite
        self.draw_pet_shadow(pet_center[0], state.pet_home_y, HOME_PET_SIZE)
        self.draw_pet(pet, state, pet_center, HOME_PET_SIZE, face_sprite_override=face_override, facing_left_override=False)

    def draw_jump_rope_screen(self, pet: Pet, settings: AppSettings, state: RuntimeState) -> None:
        logger.info("Drawing jump rope screen...")
        if self.home_background is not None:
            self.screen.blit(self.home_background, (0, 0))
        else:
            self.screen.fill(BG)

        self.draw_clock(settings)
        palette = self.get_menu_theme_palette(settings)
        title_text = format_menu_text("Jump Rope")
        title_surface = self.small_font.render(title_text, True, palette.text)
        title_rect = title_surface.get_rect(topleft=(14, 12))
        title_bg_rect = title_rect.inflate(12, 10)
        pygame.draw.rect(self.screen, palette.panel, title_bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, palette.border, title_bg_rect, 1, border_radius=10)
        self.screen.blit(title_surface, title_rect)

        meter_radius = 7
        meter_gap = 6
        meter_width = (JUMP_ROPE_TARGET_SUCCESSES * (meter_radius * 2)) + ((JUMP_ROPE_TARGET_SUCCESSES - 1) * meter_gap)
        meter_x = (SCREEN_WIDTH - meter_width) // 2
        self.draw_jump_rope_success_meter(meter_x, 48, state.jump_rope_successes, palette)

        jump_offset = 0
        if state.jump_rope_jump_active:
            jump_progress = min(1.0, state.jump_rope_jump_elapsed / JUMP_ROPE_JUMP_DURATION_SECONDS)
            jump_offset = int(round(math.sin(jump_progress * math.pi) * JUMP_ROPE_JUMP_HEIGHT))

        pet_center = (SCREEN_WIDTH // 2, state.pet_home_y - jump_offset)
        left_anchor, right_anchor, rope_points, rope_in_front = self.get_jump_rope_rope(state)

        if not rope_in_front:
            self.draw_jump_rope(palette, left_anchor, right_anchor, rope_points, is_in_front=False)

        self.draw_pet_shadow(pet_center[0], state.pet_home_y, HOME_PET_SIZE)
        self.draw_pet(pet, state, pet_center, HOME_PET_SIZE, facing_left_override=False)

        if rope_in_front:
            self.draw_jump_rope(palette, left_anchor, right_anchor, rope_points, is_in_front=True)

        if state.jump_rope_countdown_elapsed < JUMP_ROPE_COUNTDOWN_SECONDS:
            completed_steps = min(
                JUMP_ROPE_COUNTDOWN_START,
                int((state.jump_rope_countdown_elapsed + 1e-9) / JUMP_ROPE_COUNTDOWN_STEP_SECONDS),
            )
            countdown_value = max(1, JUMP_ROPE_COUNTDOWN_START - completed_steps)
            self.draw_outlined_text_centered(
                str(countdown_value),
                self.menu_font,
                WHITE,
                BLACK,
                SCREEN_WIDTH // 2,
                82,
            )

    def get_jump_rope_rope(
        self,
        state: RuntimeState,
    ) -> tuple[tuple[int, int], tuple[int, int], list[tuple[int, int]], bool]:
        if state.jump_rope_countdown_elapsed < JUMP_ROPE_COUNTDOWN_SECONDS:
            rope_phase = 0.0
        else:
            rope_phase = (state.jump_rope_elapsed / JUMP_ROPE_CYCLE_SECONDS) % 1.0
        rope_wave = math.cos(rope_phase * math.tau)
        pet_base_x = SCREEN_WIDTH // 2
        pet_base_y = state.pet_home_y

        left_anchor = (
            pet_base_x - JUMP_ROPE_ANCHOR_X_OFFSET,
            pet_base_y + JUMP_ROPE_ANCHOR_Y_OFFSET,
        )
        right_anchor = (
            pet_base_x + JUMP_ROPE_ANCHOR_X_OFFSET,
            pet_base_y + JUMP_ROPE_ANCHOR_Y_OFFSET,
        )
        top_control_y = pet_base_y + JUMP_ROPE_TOP_Y_OFFSET
        bottom_control_y = pet_base_y + JUMP_ROPE_BOTTOM_Y_OFFSET
        control_blend = (1.0 - rope_wave) * 0.5
        control_point = (
            int(round(pet_base_x + (math.sin(rope_phase * math.tau) * JUMP_ROPE_CONTROL_X_SWAY))),
            int(round(top_control_y + ((bottom_control_y - top_control_y) * control_blend))),
        )

        rope_points: list[tuple[int, int]] = []
        for segment_index in range(JUMP_ROPE_CURVE_SEGMENTS + 1):
            t = segment_index / JUMP_ROPE_CURVE_SEGMENTS
            inverse_t = 1.0 - t
            point_x = (inverse_t * inverse_t * left_anchor[0]) + (2 * inverse_t * t * control_point[0]) + (t * t * right_anchor[0])
            point_y = (inverse_t * inverse_t * left_anchor[1]) + (2 * inverse_t * t * control_point[1]) + (t * t * right_anchor[1])
            rope_points.append((int(round(point_x)), int(round(point_y))))

        return left_anchor, right_anchor, rope_points, rope_wave < 0.0

    def draw_jump_rope(
        self,
        palette: ThemePalette,
        left_anchor: tuple[int, int],
        right_anchor: tuple[int, int],
        rope_points: list[tuple[int, int]],
        is_in_front: bool,
    ) -> None:
        rope_color = palette.accent
        if not is_in_front:
            rope_color = tuple(max(0, int(channel * 0.7)) for channel in palette.accent)

        rope_outline_thickness = JUMP_ROPE_ROPE_THICKNESS + 2
        for segment_index in range(len(rope_points) - 1):
            pygame.draw.line(
                self.screen,
                BLACK,
                rope_points[segment_index],
                rope_points[segment_index + 1],
                rope_outline_thickness,
            )
            pygame.draw.line(
                self.screen,
                rope_color,
                rope_points[segment_index],
                rope_points[segment_index + 1],
                JUMP_ROPE_ROPE_THICKNESS,
            )

        handle_color = (56, 46, 42)
        pygame.draw.circle(self.screen, handle_color, left_anchor, 4)
        pygame.draw.circle(self.screen, BLACK, left_anchor, 4, 1)
        pygame.draw.circle(self.screen, handle_color, right_anchor, 4)
        pygame.draw.circle(self.screen, BLACK, right_anchor, 4, 1)

    def draw_cleaning_bubbles(self, pet_center: tuple[int, int], scrub_time: float, scrub_progress: float) -> None:
        if self.bubbles_sprite is None:
            return

        for bubble_index, offset in enumerate(CLEAN_BUBBLE_OFFSETS):
            spawn_progress = (bubble_index / max(1, len(CLEAN_BUBBLE_OFFSETS) - 1)) * CLEAN_BUBBLE_SPAWN_WINDOW
            if scrub_progress < spawn_progress:
                continue

            alpha = self.get_cleaning_bubble_alpha(scrub_progress, spawn_progress)
            if alpha <= 0:
                continue

            drift_x = math.sin((scrub_time * 7.0) + bubble_index) * 1.5
            drift_y = math.cos((scrub_time * 5.0) + (bubble_index * 1.7)) * 1.5
            bubble_center = (
                int(round(pet_center[0] + offset[0] + drift_x)),
                int(round(pet_center[1] + offset[1] + drift_y)),
            )
            self.draw_sprite_with_alpha(self.bubbles_sprite, bubble_center, alpha)

    def get_cleaning_bubble_alpha(self, scrub_progress: float, spawn_progress: float) -> int:
        fade_in_progress = (scrub_progress - spawn_progress) / CLEAN_BUBBLE_FADE_IN_PROGRESS
        fade_in_alpha = max(0.0, min(1.0, fade_in_progress))

        if scrub_progress < CLEAN_BUBBLE_FADE_OUT_START_PROGRESS:
            fade_out_alpha = 1.0
        else:
            fade_out_duration = max(0.001, 1.0 - CLEAN_BUBBLE_FADE_OUT_START_PROGRESS)
            fade_out_progress = (scrub_progress - CLEAN_BUBBLE_FADE_OUT_START_PROGRESS) / fade_out_duration
            fade_out_alpha = max(0.0, min(1.0, 1.0 - fade_out_progress))

        return int(round(255 * fade_in_alpha * fade_out_alpha))

    def draw_sprite_with_alpha(
        self,
        sprite: pygame.Surface,
        center: tuple[int, int],
        alpha: int,
    ) -> None:
        draw_surface = sprite.copy() if hasattr(sprite, "copy") else sprite
        if hasattr(draw_surface, "set_alpha"):
            draw_surface.set_alpha(max(0, min(255, alpha)))
        sprite_rect = draw_surface.get_rect(center=center)
        self.screen.blit(draw_surface, sprite_rect)

    def draw_bottom_cropped_sprite(
        self,
        sprite: pygame.Surface,
        full_rect: pygame.Rect,
        visible_height: int,
    ) -> None:
        visible_height = max(0, min(sprite.get_height(), visible_height))
        if visible_height <= 0:
            return

        source_rect = pygame.Rect(0, 0, sprite.get_width(), visible_height)
        self.screen.blit(sprite, full_rect.topleft, source_rect)

    def draw_outlined_text_centered(
        self,
        text: str,
        font: pygame.font.Font,
        fill_color,
        outline_color,
        center_x: int,
        y: int,
    ) -> None:
        for offset_x, offset_y in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            draw_text_centered(self.screen, text, font, outline_color, center_x + offset_x, y + offset_y)
        draw_text_centered(self.screen, text, font, fill_color, center_x, y)

    def draw_outlined_text(
        self,
        text: str,
        font: pygame.font.Font,
        fill_color,
        outline_color,
        x: int,
        y: int,
    ) -> None:
        for offset_x, offset_y in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            draw_text(self.screen, text, font, outline_color, x + offset_x, y + offset_y)
        draw_text(self.screen, text, font, fill_color, x, y)

    def draw_jump_rope_success_meter(
        self,
        x: int,
        y: int,
        value: int,
        palette: ThemePalette,
    ) -> None:
        radius = 7
        gap = 6
        inactive_color = (22, 24, 30)

        for index in range(JUMP_ROPE_TARGET_SUCCESSES):
            center_x = x + radius + (index * ((radius * 2) + gap))
            center_y = y + radius
            fill_color = GOOD if index < value else inactive_color
            pygame.draw.circle(self.screen, fill_color, (center_x, center_y), radius)
            pygame.draw.circle(self.screen, palette.border, (center_x, center_y), radius, 1)

    def draw_bordered_separator(self, y: int) -> None:
        pygame.draw.line(self.screen, BLACK, (18, y), (SCREEN_WIDTH - 18, y), 3)
        pygame.draw.line(self.screen, WHITE, (18, y), (SCREEN_WIDTH - 18, y), 1)

    def draw_fullscreen_menu(self, settings: AppSettings, title: str, options: list[str], selected_index: int) -> None:
        logger.info("Drawing full-screen menu: %s", title)
        self.screen.fill(BG)
        palette = self.get_menu_theme_palette(settings)

        panel_rect = pygame.Rect(6, 6, SCREEN_WIDTH - 12, SCREEN_HEIGHT - 12)
        pygame.draw.rect(self.screen, palette.panel, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, palette.border, panel_rect, 1, border_radius=10)

        draw_text_centered(self.screen, format_menu_text(title), self.big_font, palette.text, SCREEN_WIDTH // 2, 12)
        pygame.draw.line(self.screen, palette.border, (18, 40), (SCREEN_WIDTH - 18, 40), 1)

        row_height = 28
        row_step = 30
        start_y = 52
        row_x = 18
        row_width = SCREEN_WIDTH - 36
        footer_y = SCREEN_HEIGHT - 22
        max_visible_rows = max(1, (footer_y - start_y) // row_step)
        visible_options, start_index, current_page, total_pages = paginate_menu_options(options, selected_index, max_visible_rows)

        for visible_index, option in enumerate(visible_options):
            actual_index = start_index + visible_index
            row_y = start_y + (visible_index * row_step)
            row_rect = pygame.Rect(row_x, row_y, row_width, row_height)
            is_selected = actual_index == selected_index
            label_font = self.menu_font if is_selected else self.font
            label_color = BLACK if is_selected else palette.text
            label_text = truncate_text_to_width(format_menu_text(option), label_font, row_width - 12)
            label_surface = label_font.render(label_text, True, label_color)
            label_x = row_rect.centerx - (label_surface.get_width() // 2)
            label_y = row_rect.centery - (label_surface.get_height() // 2)

            if is_selected:
                pygame.draw.rect(self.screen, palette.accent, row_rect, border_radius=6)

            self.screen.blit(label_surface, (label_x, label_y))

        if total_pages > 1:
            page_text = format_menu_text(f"Page {current_page}/{total_pages}")
            draw_text_centered(self.screen, page_text, self.small_font, palette.muted, SCREEN_WIDTH // 2, footer_y)

    def draw_food_grid_screen(self, settings: AppSettings, food_options: list[FoodItem], selected_food: int) -> None:
        logger.info("Drawing food grid screen...")
        self.screen.fill(BG)
        palette = self.get_menu_theme_palette(settings)

        panel_rect = pygame.Rect(6, 6, SCREEN_WIDTH - 12, SCREEN_HEIGHT - 12)
        pygame.draw.rect(self.screen, palette.panel, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, palette.border, panel_rect, 1, border_radius=10)

        draw_text_centered(self.screen, format_menu_text("Feed"), self.big_font, palette.text, SCREEN_WIDTH // 2, 12)
        pygame.draw.line(self.screen, palette.border, (18, 40), (SCREEN_WIDTH - 18, 40), 1)

        grid_width = (FOOD_GRID_COLUMNS * FOOD_GRID_CELL_SIZE) + ((FOOD_GRID_COLUMNS - 1) * FOOD_GRID_GAP)
        grid_height = (FOOD_GRID_ROWS * FOOD_GRID_CELL_SIZE) + ((FOOD_GRID_ROWS - 1) * FOOD_GRID_GAP)
        start_x = (SCREEN_WIDTH - grid_width) // 2
        start_y = 52

        for cell_index in range(FOOD_GRID_COLUMNS * FOOD_GRID_ROWS):
            row = cell_index // FOOD_GRID_COLUMNS
            col = cell_index % FOOD_GRID_COLUMNS
            cell_x = start_x + col * (FOOD_GRID_CELL_SIZE + FOOD_GRID_GAP)
            cell_y = start_y + row * (FOOD_GRID_CELL_SIZE + FOOD_GRID_GAP)
            cell_rect = pygame.Rect(cell_x, cell_y, FOOD_GRID_CELL_SIZE, FOOD_GRID_CELL_SIZE)
            has_food = cell_index < len(food_options)
            is_selected = has_food and cell_index == selected_food

            if is_selected:
                fill_color = palette.accent
                border_color = palette.border
            else:
                fill_color = BG
                border_color = palette.border

            pygame.draw.rect(self.screen, fill_color, cell_rect, border_radius=8)
            pygame.draw.rect(self.screen, border_color, cell_rect, 1, border_radius=8)

            if not has_food:
                continue

            food_option = food_options[cell_index]
            if food_option.sprite is not None:
                sprite_rect = food_option.sprite.get_rect(center=cell_rect.center)
                self.screen.blit(food_option.sprite, sprite_rect)

        separator_y = start_y + grid_height + 12
        pygame.draw.line(self.screen, palette.border, (18, separator_y), (SCREEN_WIDTH - 18, separator_y), 1)

        if food_options:
            selected_item = food_options[selected_food]
            draw_text_centered(
                self.screen,
                format_menu_text(selected_item.label),
                self.small_font,
                palette.muted,
                SCREEN_WIDTH // 2,
                separator_y + 8,
            )
        else:
            draw_text_centered(
                self.screen,
                format_menu_text("No food"),
                self.small_font,
                palette.muted,
                SCREEN_WIDTH // 2,
                separator_y + 8,
            )

    def draw_status_screen(self, pet: Pet, settings: AppSettings) -> None:
        logger.info("Drawing status screen...")
        self.screen.fill(BG)
        palette = self.get_menu_theme_palette(settings)

        panel_rect = pygame.Rect(6, 6, SCREEN_WIDTH - 12, SCREEN_HEIGHT - 12)
        pygame.draw.rect(self.screen, palette.panel, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, palette.border, panel_rect, 1, border_radius=10)

        draw_text_centered(self.screen, format_menu_text("Status"), self.big_font, palette.text, SCREEN_WIDTH // 2, 12)
        pygame.draw.line(self.screen, palette.border, (18, 40), (SCREEN_WIDTH - 18, 40), 1)

        meter_x = 84
        rows_y = 54
        row_gap = 36
        empty_meter_color = (22, 24, 30)
        stats = [
            ("Tummy", pet.hunger),
            ("Clean", pet.hygiene),
            ("Happy", pet.happiness),
            ("Health", pet.health),
        ]

        for index, (label, value) in enumerate(stats):
            row_y = rows_y + index * row_gap
            draw_text(self.screen, format_menu_text(label), self.small_font, palette.text, 16, row_y + 1)
            draw_circle_meter(
                self.screen,
                meter_x,
                row_y,
                value,
                MAX_STAT,
                palette.accent,
                empty_meter_color,
                palette.border,
            )

    def draw_reset_confirm_screen(self, selected_reset: int, reset_options: list[str]) -> None:
        logger.info("Drawing reset confirmation screen...")
        self.screen.fill(BG)

        panel_rect = pygame.Rect(6, 6, SCREEN_WIDTH - 12, SCREEN_HEIGHT - 12)
        pygame.draw.rect(self.screen, PANEL, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, panel_rect, 1, border_radius=10)

        draw_text_centered(self.screen, format_menu_text("Reset Pet"), self.big_font, WHITE, SCREEN_WIDTH // 2, 12)
        pygame.draw.line(self.screen, WHITE, (18, 40), (SCREEN_WIDTH - 18, 40), 1)
        warning_lines = wrap_text_to_width(
            format_menu_text("This will erase current pet progress."),
            self.font,
            SCREEN_WIDTH - 44,
        )
        warning_start_y = 64
        warning_line_gap = self.font.get_linesize() + 4
        for line_index, line in enumerate(warning_lines):
            draw_text_centered(
                self.screen,
                line,
                self.font,
                BAD,
                SCREEN_WIDTH // 2,
                warning_start_y + (line_index * warning_line_gap),
            )

        button_y = max(154, warning_start_y + (len(warning_lines) * warning_line_gap) + 26)
        button_w = 76
        button_h = 34
        button_gap = 14
        total_w = (button_w * 2) + button_gap
        start_x = (SCREEN_WIDTH - total_w) // 2

        for index, option in enumerate(reset_options):
            button_x = start_x + index * (button_w + button_gap)
            button_rect = pygame.Rect(button_x, button_y, button_w, button_h)
            is_selected = index == selected_reset

            if option == "Yes":
                fill_color = BAD if is_selected else (88, 22, 22)
                text_color = WHITE
                border_color = BAD
            else:
                fill_color = ACCENT if is_selected else PANEL
                text_color = BLACK if is_selected else WHITE
                border_color = WHITE

            pygame.draw.rect(self.screen, fill_color, button_rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, button_rect, 1, border_radius=10)

            label_font = self.menu_font if is_selected else self.font
            label_surface = label_font.render(format_menu_text(option), True, text_color)
            label_rect = label_surface.get_rect(center=button_rect.center)
            self.screen.blit(label_surface, label_rect)

    def draw_clock(self, settings: AppSettings) -> None:
        palette = self.get_menu_theme_palette(settings)
        clock_text = datetime.now().strftime("%I:%M%p")
        clock_surface = self.small_font.render(clock_text, True, palette.text)
        clock_rect = clock_surface.get_rect(topright=(SCREEN_WIDTH - 12, 12))
        clock_bg_rect = clock_rect.inflate(16, 10)
        pygame.draw.rect(self.screen, palette.panel, clock_bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, palette.border, clock_bg_rect, 1, border_radius=10)
        self.screen.blit(clock_surface, clock_rect)
