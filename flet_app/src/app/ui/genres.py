import asyncio
import random
from collections.abc import Callable

import flet as ft

from app.api import ApiError
from app.theme import BLACK, BORDER_DIM, EASE, SPRING, SURFACE, SURFACE_2
from app.ui.widgets import Field, IconSquare, border, hard_shadow, label, spawn, txt


class GenrePicker(ft.Column):
    def __init__(self, app, accent: str, on_change: Callable[[str | None], None] | None = None):
        self.app = app
        self.accent = accent
        self.handler = on_change
        self.value: str | None = None
        self.options: list[str] = []
        self.task: asyncio.Task | None = None
        self.search = Field("", "", "Any genre, or leave it empty", accent=accent, prefix_icon=ft.Icons.SEARCH, on_change=self._typed)
        self.dice = IconSquare(ft.Icons.CASINO, self._roll, size=40, depth=0, haptic=app.tap, tooltip="Random genre")
        self.search.box.content.controls.append(ft.Container(self.dice, padding=ft.Padding.only(right=6)))
        self.chips = ft.Row(wrap=True, spacing=8, run_spacing=8)
        self.chosen = ft.Container(animate_size=ft.Animation(320, EASE), clip_behavior=ft.ClipBehavior.HARD_EDGE)
        self.cloud = ft.Container(self.chips, animate_size=ft.Animation(360, EASE), clip_behavior=ft.ClipBehavior.HARD_EDGE)
        super().__init__([label("Genre (optional)"), self.chosen, self.search, self.cloud], spacing=10)

    def did_mount(self):
        self.task = spawn(self._load(""))

    async def _typed(self, value: str):
        if self.task:
            self.task.cancel()
        self.task = spawn(self._load(value, delay=0.25))

    async def _load(self, query: str, delay: float = 0.0):
        if delay:
            await asyncio.sleep(delay)
        try:
            data = await self.app.api.genres(query, 18)
        except ApiError:
            return
        self.options = data.get("genres", [])
        self._render_chips()

    def _chip(self, genre: str) -> ft.Container:
        return ft.Container(
            txt(genre, size=11, bold=True, upper=True, spacing=0.8, lines=1),
            padding=ft.Padding.symmetric(horizontal=10, vertical=7),
            bgcolor=SURFACE_2,
            border=border(BORDER_DIM),
            scale=0.6,
            opacity=0,
            animate_scale=ft.Animation(420, SPRING),
            animate_opacity=ft.Animation(220, EASE),
            on_click=lambda e, g=genre: self.pick(g),
        )

    def _render_chips(self):
        self.chips.controls = [self._chip(g) for g in self.options]
        try:
            self.update()
        except Exception:
            return
        spawn(self._pop())

    async def _pop(self):
        for chip in list(self.chips.controls):
            await asyncio.sleep(0.025)
            chip.scale = 1
            chip.opacity = 1
            try:
                chip.update()
            except Exception:
                return

    async def _roll(self, e):
        if self.options:
            self.pick(random.choice(self.options))

    def pick(self, genre: str | None):
        self.value = genre
        self.app.select()
        if genre:
            badge = ft.Container(
                ft.Row(
                    [
                        ft.Container(txt("GENRE", size=9, bold=True, color=BLACK, spacing=1), bgcolor=self.accent, padding=ft.Padding.symmetric(horizontal=6, vertical=3)),
                        txt(genre.upper(), size=14, bold=True, lines=1, expand=True),
                        IconSquare(ft.Icons.CLOSE, lambda e: self.pick(None), size=34, depth=0, haptic=self.app.tap),
                    ],
                    spacing=10,
                ),
                padding=ft.Padding.only(left=10, right=4, top=4, bottom=4),
                bgcolor=SURFACE,
                border=border(self.accent),
                shadow=hard_shadow(self.accent, 4),
                scale=0.8,
                rotate=ft.Rotate(-0.04),
                animate_scale=ft.Animation(520, SPRING),
                animate_rotation=ft.Animation(520, SPRING),
            )
            self.chosen.content = badge
            self.search.visible = False
            self.cloud.content = None
            self.update()
            badge.scale = 1
            badge.rotate = ft.Rotate(0)
            badge.update()
        else:
            self.chosen.content = None
            self.search.visible = True
            self.cloud.content = self.chips
            self.update()
            spawn(self._pop())
        if self.handler:
            self.handler(genre)
