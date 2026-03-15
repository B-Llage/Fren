from __future__ import annotations

import math

import pygame


def draw_text(surface: pygame.Surface, text: str, font: pygame.font.Font, color, x: int, y: int) -> None:
    rendered = font.render(text, True, color)
    surface.blit(rendered, (x, y))


def draw_text_centered(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color,
    center_x: int,
    y: int,
) -> None:
    rendered = font.render(text, True, color)
    x = center_x - (rendered.get_width() // 2)
    surface.blit(rendered, (x, y))


def draw_text_right_aligned(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color,
    right_x: int,
    y: int,
) -> None:
    rendered = font.render(text, True, color)
    x = right_x - rendered.get_width()
    surface.blit(rendered, (x, y))


def format_menu_text(text: str) -> str:
    return text.upper()


def truncate_text_to_width(text: str, font: pygame.font.Font, max_width: int) -> str:
    if font.size(text)[0] <= max_width:
        return text

    ellipsis = "..."
    if font.size(ellipsis)[0] > max_width:
        return ellipsis

    truncated_text = text
    while truncated_text and font.size(truncated_text + ellipsis)[0] > max_width:
        truncated_text = truncated_text[:-1]

    return truncated_text + ellipsis


def wrap_text_to_width(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current_line = words[0]
    for word in words[1:]:
        candidate = f"{current_line} {word}"
        if font.size(candidate)[0] <= max_width:
            current_line = candidate
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def paginate_menu_options(options: list[str], selected_index: int, page_size: int) -> tuple[list[str], int, int, int]:
    if not options:
        return [], 0, 1, 1

    page_size = max(1, page_size)
    selected_index = max(0, min(len(options) - 1, selected_index))
    page_index = selected_index // page_size
    start_index = page_index * page_size
    end_index = min(len(options), start_index + page_size)
    total_pages = math.ceil(len(options) / page_size)
    return options[start_index:end_index], start_index, page_index + 1, total_pages


def draw_circle_meter(
    surface: pygame.Surface,
    x: int,
    y: int,
    value: int,
    total: int,
    active_color,
    inactive_color,
    border_color,
) -> None:
    radius = 5
    gap = 4

    for index in range(total):
        center_x = x + radius + (index * ((radius * 2) + gap))
        center_y = y + radius
        fill_color = active_color if index < value else inactive_color
        pygame.draw.circle(surface, fill_color, (center_x, center_y), radius)
        pygame.draw.circle(surface, border_color, (center_x, center_y), radius, 1)
