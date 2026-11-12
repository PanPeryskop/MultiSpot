import asyncio

import flet as ft

from app.theme import BLACK, ELASTIC, FONT_BOLD
from app.ui.widgets import spawn

GLYPH = 0.612


class Marquee(ft.Container):
    def __init__(
        self,
        phrase: str,
        size: float = 13,
        color: str = BLACK,
        bgcolor: str | None = None,
        seconds: float = 16,
        reverse: bool = False,
        height: float = 34,
        rotate: float = 0,
        sway: float = 0,
        intro_delay: float | None = None,
    ):
        self.seconds = seconds
        self.reverse = reverse
        self.angle = rotate
        self.sway = sway
        self.intro_delay = intro_delay
        self.tasks: list[asyncio.Task] = []
        width = len(phrase) * size * GLYPH
        copies = [
            ft.Container(ft.Text(phrase, size=size, color=color, font_family=FONT_BOLD, no_wrap=True), width=width)
            for _ in range(3)
        ]
        self.track = ft.Container(
            ft.Row(copies, spacing=0),
            width=width * 3,
            left=0,
            top=0,
            bottom=0,
            alignment=ft.Alignment.CENTER_LEFT,
            offset=ft.Offset(-1 / 3 if reverse else 0, 0),
        )
        intro = intro_delay is not None
        super().__init__(
            content=ft.Stack([self.track], height=height, clip_behavior=ft.ClipBehavior.HARD_EDGE),
            bgcolor=bgcolor,
            height=height,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            rotate=ft.Rotate(rotate * 6 if intro else rotate),
            offset=ft.Offset(1.2 if reverse else -1.2, 0) if intro else ft.Offset(0, 0),
            animate_rotation=ft.Animation(1400, ELASTIC),
            animate_offset=ft.Animation(1100, ft.AnimationCurve.EASE_OUT_EXPO),
            alignment=ft.Alignment.CENTER_LEFT,
        )

    def did_mount(self):
        self.tasks = [spawn(self._scroll())]
        if self.intro_delay is not None or self.sway:
            self.tasks.append(spawn(self._motion()))

    def will_unmount(self):
        for task in self.tasks:
            task.cancel()

    async def _scroll(self):
        start, end = (-1 / 3, 0.0) if self.reverse else (0.0, -1 / 3)
        while True:
            self.track.animate_offset = None
            self.track.offset = ft.Offset(start, 0)
            self.track.update()
            await asyncio.sleep(0.05)
            self.track.animate_offset = ft.Animation(int(self.seconds * 1000), ft.AnimationCurve.LINEAR)
            self.track.offset = ft.Offset(end, 0)
            self.track.update()
            await asyncio.sleep(self.seconds)

    async def _motion(self):
        if self.intro_delay is not None:
            await asyncio.sleep(self.intro_delay)
            self.offset = ft.Offset(0, 0)
            self.rotate = ft.Rotate(self.angle)
            self.update()
            await asyncio.sleep(1.4)
        if not self.sway:
            return
        self.animate_rotation = ft.Animation(2600, ft.AnimationCurve.EASE_IN_OUT_SINE)
        flip = 1
        while True:
            self.rotate = ft.Rotate(self.angle + self.sway * flip)
            self.update()
            flip = -flip
            await asyncio.sleep(2.6)
