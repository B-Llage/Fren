from __future__ import annotations

import types


class FakeRect:
    def __init__(self, x: int = 0, y: int = 0, width: int = 0, height: int = 0) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + (self.width // 2), self.y + (self.height // 2))

    @center.setter
    def center(self, value: tuple[int, int]) -> None:
        self.x = value[0] - (self.width // 2)
        self.y = value[1] - (self.height // 2)

    @property
    def centerx(self) -> int:
        return self.center[0]

    @property
    def centery(self) -> int:
        return self.center[1]

    @property
    def topleft(self) -> tuple[int, int]:
        return (self.x, self.y)

    @property
    def topright(self) -> tuple[int, int]:
        return (self.x + self.width, self.y)

    @property
    def bottomleft(self) -> tuple[int, int]:
        return (self.x, self.y + self.height)

    @property
    def bottomright(self) -> tuple[int, int]:
        return (self.x + self.width, self.y + self.height)

    @property
    def left(self) -> int:
        return self.x

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def top(self) -> int:
        return self.y

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def inflate(self, x_amount: int, y_amount: int) -> "FakeRect":
        return FakeRect(
            self.x - (x_amount // 2),
            self.y - (y_amount // 2),
            self.width + x_amount,
            self.height + y_amount,
        )


class FakeSurface:
    def __init__(self, size: tuple[int, int] = (0, 0), *_args, **_kwargs) -> None:
        self._size = tuple(size)
        self.alpha = 255

    def get_size(self) -> tuple[int, int]:
        return self._size

    def get_width(self) -> int:
        return self._size[0]

    def get_height(self) -> int:
        return self._size[1]

    def blit(self, *_args, **_kwargs) -> None:
        return None

    def fill(self, *_args, **_kwargs) -> None:
        return None

    def convert(self) -> "FakeSurface":
        return self

    def convert_alpha(self) -> "FakeSurface":
        return self

    def copy(self) -> "FakeSurface":
        copied = FakeSurface(self._size)
        copied.alpha = self.alpha
        return copied

    def set_alpha(self, alpha: int | None) -> None:
        self.alpha = 255 if alpha is None else alpha

    def get_rect(self, **kwargs) -> FakeRect:
        rect = FakeRect(0, 0, self._size[0], self._size[1])
        if "center" in kwargs:
            rect.center = kwargs["center"]
        if "topright" in kwargs:
            top_right = kwargs["topright"]
            rect.x = top_right[0] - rect.width
            rect.y = top_right[1]
        return rect


class FakeFont:
    def __init__(self, size: int) -> None:
        self._size = size

    def render(self, text: str, _antialias: bool, _color) -> FakeSurface:
        width = max(1, len(text) * max(4, self._size // 2))
        return FakeSurface((width, self._size + 4))

    def size(self, text: str) -> tuple[int, int]:
        return (max(1, len(text) * max(4, self._size // 2)), self._size + 4)

    def get_linesize(self) -> int:
        return self._size + 4


class FakeSound:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs
        self.volume = 0.0

    def set_volume(self, volume: float) -> None:
        self.volume = volume

    def play(self) -> None:
        return None


class FakeClock:
    def tick(self, _fps: int) -> int:
        return 16


class FakePygameModule(types.SimpleNamespace):
    pass


def install_pygame_stub():
    pygame = FakePygameModule()
    pygame.error = RuntimeError
    pygame.QUIT = 256
    pygame.KEYDOWN = 768
    pygame.K_q = 113
    pygame.K_w = 119
    pygame.K_e = 101
    pygame.SRCALPHA = 65536
    pygame.Surface = FakeSurface
    pygame.Rect = FakeRect

    mixer_state = {"initialized": None}

    def mixer_pre_init(*_args, **_kwargs) -> None:
        return None

    def mixer_init(*_args, **_kwargs) -> None:
        mixer_state["initialized"] = (True,)

    def mixer_get_init():
        return mixer_state["initialized"]

    pygame.mixer = types.SimpleNamespace(
        pre_init=mixer_pre_init,
        init=mixer_init,
        get_init=mixer_get_init,
        Sound=FakeSound,
    )
    pygame.display = types.SimpleNamespace(
        set_caption=lambda *_args, **_kwargs: None,
        set_mode=lambda size, *_args, **_kwargs: FakeSurface(size),
        flip=lambda: None,
    )
    pygame.time = types.SimpleNamespace(Clock=FakeClock)
    pygame.font = types.SimpleNamespace(SysFont=lambda _name, size, bold=False: FakeFont(size))
    pygame.event = types.SimpleNamespace(get=lambda: [])
    pygame.transform = types.SimpleNamespace(
        scale=lambda _surface, size: FakeSurface(size),
        smoothscale=lambda _surface, size: FakeSurface(size),
        flip=lambda surface, _x, _y: surface,
    )
    pygame.image = types.SimpleNamespace(load=lambda _path: FakeSurface((90, 90)))
    pygame.draw = types.SimpleNamespace(
        rect=lambda *_args, **_kwargs: None,
        ellipse=lambda *_args, **_kwargs: None,
        circle=lambda *_args, **_kwargs: None,
        arc=lambda *_args, **_kwargs: None,
        line=lambda *_args, **_kwargs: None,
    )
    pygame.init = lambda: None
    pygame.quit = lambda: None

    return pygame
