from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCREEN_WIDTH = 240
SCREEN_HEIGHT = 240
FPS = 30
SLEEP_FPS = 2
SLEEP_IDLE_TIMEOUT_SECONDS = 60.0
AUTO_SAVE_INTERVAL_SECONDS = 60.0
SAVE_INDICATOR_DURATION_SECONDS = 0.9
MENU_FADE_IN_SECONDS = 0.2
WINDOW_TITLE = "Virtual Pet Template"

SAVE_PATH = PROJECT_ROOT / "pet_save.json"
THEME_CONFIG_PATH = PROJECT_ROOT / "menu_themes.json"
FOOD_CONFIG_PATH = PROJECT_ROOT / "food_items.json"
SPLASH_SCREEN_PATH = PROJECT_ROOT / "fullscreenAssets" / "splashscreen_frenworld.png"

DEFAULT_DISPLAY_SCALE = 1
DISPLAY_SCALE_OPTIONS = (1, 2, 3)
DEFAULT_SOUND_VOLUME = 1.0
SOUND_VOLUME_OPTIONS = (0.0, 0.25, 0.5, 0.75, 1.0)
DEFAULT_AUTO_UPDATE_ENABLED = False
DEFAULT_AUTO_RETURN_ENABLED = True
SPLASH_FADE_IN_SECONDS = 0.45
SPLASH_HOLD_SECONDS = 0.35
SPLASH_FADE_OUT_SECONDS = 0.45
SLEEP_WAKE_HOLD_SECONDS = 1.0
DEFAULT_DISPLAY_SATURATION = 1.3
DISPLAY_SATURATION_OPTIONS = (
    ("Normal", 1.0),
    ("Rich", 1.15),
    ("Vivid", 1.3),
    ("Boost", 1.5),
)
DEFAULT_DISPLAY_CONTRAST = 1.3
DISPLAY_CONTRAST_OPTIONS = (
    ("Normal", 1.0),
    ("Rich", 1.15),
    ("Punchy", 1.3),
    ("Arcade", 1.5),
)

HOME_BACKGROUND_PATH = PROJECT_ROOT / "backgrounds" / "house_kitchen_simple.png"
BASE_SPRITE_PATH = PROJECT_ROOT / "creatures" / "bunny" / "base_bunny.png"
FACE_SPRITE_PATH = PROJECT_ROOT / "creatures" / "bunny" / "face_happy_bunny.png"
EXTRA_HAPPY_FACE_PATH = PROJECT_ROOT / "creatures" / "bunny" / "face_extra_happy_bunny.png"
CARROT_FOOD_PATH = PROJECT_ROOT / "food" / "food_carrot.png"
BURGER_FOOD_PATH = PROJECT_ROOT / "food" / "food_burger.png"
RADISH_FOOD_PATH = PROJECT_ROOT / "food" / "food_radish.png"
WATERMELON_FOOD_PATH = PROJECT_ROOT / "food" / "food_watermelon.png"
SOAP_PROP_PATH = PROJECT_ROOT / "props" / "props_soap.png"
BUBBLES_PROP_PATH = PROJECT_ROOT / "props" / "props_bubbles.png"
FLOPPY_PROP_PATH = PROJECT_ROOT / "props" / "props_floppy.png"
MUNCH_FACE_CLOSED_PATH = PROJECT_ROOT / "creatures" / "bunny" / "face_munch_closed_bunny.png"
MUNCH_FACE_OPEN_PATH = PROJECT_ROOT / "creatures" / "bunny" / "face_munch_open_bunny.png"

PET_SPRITE_SIZE = (90, 90)
HOME_PET_SIZE = PET_SPRITE_SIZE
HOME_PET_Y_OFFSET = 55

FOOD_GRID_COLUMNS = 2
FOOD_GRID_ROWS = 2
FOOD_GRID_CELL_SIZE = 64
FOOD_GRID_GAP = 12
FOOD_ICON_SIZE = (32, 32)
SOAP_PROP_SIZE = (32, 32)
BUBBLES_PROP_SIZE = (20, 20)
FLOPPY_PROP_SIZE = (20, 20)

FEED_DROP_DURATION_SECONDS = 0.45
FEED_MUNCH_FRAME_SECONDS = 0.12
FEED_MUNCH_TOGGLE_COUNT = 8
FEED_FOOD_SHAKE_AMPLITUDE = 2
FEED_FOOD_START_Y = 20
FEED_FOOD_TARGET_X_OFFSET = 42
FEED_FOOD_TARGET_Y_OFFSET = 8
ACTION_CELEBRATION_DURATION_SECONDS = 0.75

CLEAN_DROP_DURATION_SECONDS = 0.45
CLEAN_SCRUB_DURATION_SECONDS = 1.5
CLEAN_SCRUB_SOUND_INTERVAL_SECONDS = 0.18
CLEAN_SOAP_START_Y = 18
CLEAN_SOAP_TARGET_X_OFFSET = 22
CLEAN_SOAP_TARGET_Y_OFFSET = -12
CLEAN_SCRUB_OFFSETS = (
    (22, -12),
    (2, -28),
    (-20, -4),
    (16, 18),
    (-14, 24),
    (20, -2),
    (-8, -24),
    (18, 14),
)
CLEAN_BUBBLE_OFFSETS = (
    (-18, -24),
    (8, -26),
    (22, -8),
    (-24, 2),
    (0, 6),
    (18, 14),
    (-14, 20),
    (10, 26),
)
CLEAN_BUBBLE_SPAWN_WINDOW = 0.6
CLEAN_BUBBLE_FADE_IN_PROGRESS = 0.14
CLEAN_BUBBLE_FADE_OUT_START_PROGRESS = 0.78

WANDER_SPEED = 26.0
WANDER_PAUSE_MIN_SECONDS = 1.5
WANDER_PAUSE_MAX_SECONDS = 3.5
WANDER_BOB_AMPLITUDE = 4
WANDER_HOPS_PER_SECOND = 1.25
WANDER_SCREEN_MARGIN = 10

AUDIO_SAMPLE_RATE = 11025
AUDIO_BUFFER_SIZE = 256
AUDIO_SILENCE_LEVEL = 128

DECAY_TIMER_SECONDS = 360.0
HUNGER_DECAY = 1
HYGIENE_DECAY = 1
HAPPINESS_DECAY = 1
HEALTH_DECAY_WHEN_NEGLECTED = 1
HEALTH_RECOVERY_AMOUNT = 1
ACTIONS_PRIMARY_AMOUNT = 2
ACTIONS_SECONDARY_AMOUNT = 1
LEGACY_MAX_STAT = 100
MAX_STAT = 10
MIN_STAT = 0
STAT_FIELDS = ("hunger", "hygiene", "happiness", "health")

MAIN_MENU_OPTIONS = ("Action", "Status", "Option", "Sleep")
OPTION_MENU_OPTIONS = ("Theme", "Menu Mem", "Auto Rtrn", "Volume", "Auto Upd", "Color", "Contrast", "Res", "Reset")
ACTION_OPTIONS = ("Feed", "Play", "Clean", "Heal")
PLAY_MENU_OPTIONS = ("Jump Rope",)
RESET_OPTIONS = ("No", "Yes")

JUMP_ROPE_TARGET_SUCCESSES = 4
JUMP_ROPE_CYCLE_SECONDS = 1.25
JUMP_ROPE_COUNTDOWN_START = 3
JUMP_ROPE_COUNTDOWN_STEP_SECONDS = 0.9
JUMP_ROPE_COUNTDOWN_SECONDS = JUMP_ROPE_COUNTDOWN_START * JUMP_ROPE_COUNTDOWN_STEP_SECONDS
JUMP_ROPE_PASS_PHASE = 0.55
JUMP_ROPE_JUMP_DURATION_SECONDS = 0.42
JUMP_ROPE_JUMP_HEIGHT = 28
JUMP_ROPE_REQUIRED_HEIGHT = 16
JUMP_ROPE_ANCHOR_X_OFFSET = 60
JUMP_ROPE_ANCHOR_Y_OFFSET = -2
JUMP_ROPE_TOP_TARGET_Y_OFFSET = -((HOME_PET_SIZE[1] // 2) + 5)
JUMP_ROPE_BOTTOM_TARGET_Y_OFFSET = HOME_PET_SIZE[1] // 2
JUMP_ROPE_TOP_Y_OFFSET = (2 * JUMP_ROPE_TOP_TARGET_Y_OFFSET) - JUMP_ROPE_ANCHOR_Y_OFFSET
JUMP_ROPE_BOTTOM_Y_OFFSET = (2 * JUMP_ROPE_BOTTOM_TARGET_Y_OFFSET) - JUMP_ROPE_ANCHOR_Y_OFFSET
JUMP_ROPE_CONTROL_X_SWAY = 8
JUMP_ROPE_CURVE_SEGMENTS = 10
JUMP_ROPE_ROPE_THICKNESS = 3

BG = (24, 26, 32)
PANEL = (38, 42, 52)
TEXT = (240, 240, 240)
MUTED = (170, 170, 170)
ACCENT = (120, 200, 255)
GOOD = (110, 220, 130)
WARN = (255, 200, 90)
BAD = (255, 110, 110)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

FALLBACK_MENU_THEME = "ocean_blue"
DEFAULT_MENU_MEMORY_ENABLED = True
LEGACY_THEME_ALIASES = {
    "pink": "diamond_pink",
    "light_blue": "ocean_blue",
}
THEME_COLOR_FIELDS = ("panel", "text", "muted", "accent", "border")

FALLBACK_MENU_THEMES = {
    "diamond_pink": {
        "label": "Diamond Pink",
        "panel": (86, 40, 72),
        "text": (255, 244, 250),
        "muted": (241, 196, 221),
        "accent": (255, 186, 222),
        "border": (255, 228, 240),
    },
    "ocean_blue": {
        "label": "Ocean Blue",
        "panel": (24, 54, 88),
        "text": (240, 248, 255),
        "muted": (170, 206, 232),
        "accent": (94, 188, 255),
        "border": (209, 231, 250),
    },
    "forest_green": {
        "label": "Forest Green",
        "panel": (26, 56, 40),
        "text": (239, 248, 240),
        "muted": (176, 210, 184),
        "accent": (116, 193, 131),
        "border": (213, 236, 219),
    },
    "aurora_purple": {
        "label": "Aurora Purple",
        "panel": (53, 39, 81),
        "text": (246, 241, 255),
        "muted": (198, 183, 226),
        "accent": (170, 129, 255),
        "border": (231, 223, 255),
    },
    "sunflower_yellow": {
        "label": "Sunflower Yellow",
        "panel": (92, 72, 18),
        "text": (255, 250, 226),
        "muted": (237, 223, 160),
        "accent": (255, 214, 74),
        "border": (255, 238, 174),
    },
    "royal_crimson": {
        "label": "Royal Crimson",
        "panel": (86, 22, 34),
        "text": (255, 241, 244),
        "muted": (232, 181, 191),
        "accent": (217, 68, 96),
        "border": (247, 210, 218),
    },
    "citrus_orange": {
        "label": "Citrus Orange",
        "panel": (98, 48, 16),
        "text": (255, 245, 233),
        "muted": (239, 193, 145),
        "accent": (255, 145, 54),
        "border": (255, 223, 190),
    },
    "mint_green": {
        "label": "Mint Green",
        "panel": (24, 72, 62),
        "text": (240, 255, 250),
        "muted": (175, 224, 210),
        "accent": (108, 224, 181),
        "border": (208, 245, 233),
    },
    "cherry_lagoon": {
        "label": "Cherry Lagoon",
        "panel": (28, 48, 86),
        "text": (248, 250, 255),
        "muted": (182, 203, 233),
        "accent": (230, 82, 110),
        "border": (255, 200, 212),
    },
    "solar_reef": {
        "label": "Solar Reef",
        "panel": (18, 64, 74),
        "text": (246, 255, 251),
        "muted": (165, 219, 214),
        "accent": (255, 130, 88),
        "border": (255, 223, 170),
    },
    "sapphire_gold": {
        "label": "Sapphire Gold",
        "panel": (25, 44, 96),
        "text": (247, 250, 255),
        "muted": (176, 198, 237),
        "accent": (247, 194, 76),
        "border": (255, 231, 171),
    },
    "berry_cyan": {
        "label": "Berry Cyan",
        "panel": (72, 27, 73),
        "text": (255, 244, 255),
        "muted": (214, 177, 224),
        "accent": (89, 221, 255),
        "border": (170, 238, 255),
    },
    "ember_teal": {
        "label": "Ember Teal",
        "panel": (72, 39, 26),
        "text": (255, 246, 239),
        "muted": (229, 189, 167),
        "accent": (79, 212, 196),
        "border": (164, 241, 230),
    },
    "dusk_lime": {
        "label": "Dusk Lime",
        "panel": (51, 40, 79),
        "text": (250, 247, 255),
        "muted": (204, 191, 229),
        "accent": (178, 232, 88),
        "border": (219, 249, 179),
    },
}

FALLBACK_FOOD_ITEMS = [
    {"label": "Carrot", "sprite_path": CARROT_FOOD_PATH},
    {"label": "Burger", "sprite_path": BURGER_FOOD_PATH},
    {"label": "Radish", "sprite_path": RADISH_FOOD_PATH},
    {"label": "Watermelon", "sprite_path": WATERMELON_FOOD_PATH},
]

SOUND_EFFECT_SPECS = {
    "menu_cycle": {
        "notes": [(1046, 30, 0.18), (1318, 24, 0.16)],
        "duty_cycle": 0.35,
        "gap_ms": 4,
        "volume": 0.4,
    },
    "menu_confirm": {
        "notes": [(784, 28, 0.2), (988, 28, 0.22), (1318, 38, 0.24)],
        "duty_cycle": 0.4,
        "gap_ms": 4,
        "volume": 0.4,
    },
    "menu_back": {
        "notes": [(988, 24, 0.18), (740, 42, 0.2)],
        "duty_cycle": 0.35,
        "gap_ms": 4,
        "volume": 0.4,
    },
    "setting_change": {
        "notes": [(1174, 22, 0.16), (1568, 22, 0.18), (1318, 30, 0.2)],
        "duty_cycle": 0.3,
        "gap_ms": 4,
        "volume": 0.38,
    },
    "feed_start": {
        "notes": [(392, 30, 0.22), (523, 44, 0.24)],
        "duty_cycle": 0.5,
        "gap_ms": 5,
        "volume": 0.42,
    },
    "eat_munch": {
        "notes": [(196, 16, 0.26), (147, 12, 0.18)],
        "duty_cycle": 0.25,
        "gap_ms": 0,
        "volume": 0.34,
    },
    "eat_finish": {
        "notes": [(523, 26, 0.2), (659, 30, 0.22), (784, 52, 0.24)],
        "duty_cycle": 0.45,
        "gap_ms": 5,
        "volume": 0.42,
    },
    "play_action": {
        "notes": [(659, 24, 0.2), (784, 24, 0.22), (988, 44, 0.24)],
        "duty_cycle": 0.4,
        "gap_ms": 4,
        "volume": 0.4,
    },
    "countdown_beep": {
        "notes": [(1174, 30, 0.18)],
        "duty_cycle": 0.35,
        "gap_ms": 0,
        "volume": 0.32,
    },
    "countdown_start": {
        "notes": [(988, 20, 0.18), (1318, 24, 0.2), (1760, 42, 0.22)],
        "duty_cycle": 0.35,
        "gap_ms": 4,
        "volume": 0.34,
    },
    "jump_rope_jump": {
        "notes": [(784, 18, 0.18), (1046, 28, 0.2)],
        "duty_cycle": 0.32,
        "gap_ms": 2,
        "volume": 0.32,
    },
    "minigame_success": {
        "notes": [(988, 22, 0.18), (1318, 28, 0.2), (1568, 34, 0.22)],
        "duty_cycle": 0.36,
        "gap_ms": 4,
        "volume": 0.34,
    },
    "play_minigame_clear": {
        "notes": [(659, 40, 0.18), (880, 40, 0.2), (1174, 46, 0.22), (1568, 72, 0.24)],
        "duty_cycle": 0.38,
        "gap_ms": 5,
        "volume": 0.42,
    },
    "clean_action": {
        "notes": [(523, 18, 0.16), (784, 18, 0.18), (1174, 34, 0.2)],
        "duty_cycle": 0.3,
        "gap_ms": 4,
        "volume": 0.38,
    },
    "clean_scrub": {
        "notes": [(220, 10, 0.18), (294, 12, 0.16), (247, 16, 0.15)],
        "duty_cycle": 0.22,
        "gap_ms": 0,
        "volume": 0.3,
    },
    "clean_finish": {
        "notes": [(659, 24, 0.18), (880, 28, 0.2), (1174, 44, 0.22)],
        "duty_cycle": 0.35,
        "gap_ms": 4,
        "volume": 0.38,
    },
    "action_celebrate": {
        "notes": [(784, 24, 0.18), (988, 24, 0.2), (1318, 48, 0.22)],
        "duty_cycle": 0.4,
        "gap_ms": 4,
        "volume": 0.42,
    },
    "heal_action": {
        "notes": [(440, 26, 0.18), (554, 28, 0.2), (740, 46, 0.22)],
        "duty_cycle": 0.45,
        "gap_ms": 5,
        "volume": 0.4,
    },
    "reset_confirm": {
        "notes": [(220, 44, 0.22), (165, 60, 0.24)],
        "duty_cycle": 0.5,
        "gap_ms": 6,
        "volume": 0.42,
    },
}
