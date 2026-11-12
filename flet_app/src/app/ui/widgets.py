import asyncio
import inspect
import logging
from collections.abc import Callable
from typing import Any

import flet as ft

from app.theme import (
    BLACK,
    BORDER_DIM,
    EASE,
    FONT,
    FONT_BOLD,
    GREEN,
    SPRING,
    SURFACE,
    SURFACE_2,
    SURFACE_3,
    TEXT_2,
    TEXT_3,
    WHITE,
)


def txt(
    value: Any,
    size: float = 14,
    color: str = WHITE,
    bold: bool = False,
    upper: bool = False,
    spacing: float | None = None,
    lines: int | None = None,
    align: ft.TextAlign | None = None,
    height: float | None = None,
    **kwargs: Any,
) -> ft.Text:
    value = str(value)
    return ft.Text(
        value.upper() if upper else value,
        size=size,
        color=color,
        font_family=FONT_BOLD if bold else FONT,
        style=ft.TextStyle(letter_spacing=spacing, height=height) if spacing is not None or height else None,
        max_lines=lines,
        overflow=ft.TextOverflow.ELLIPSIS if lines else None,
        text_align=align,
        **kwargs,
    )


def label(value: str, color: str = TEXT_2) -> ft.Text:
    return txt(value, size=11, color=color, bold=True, upper=True, spacing=1.6)


def hard_shadow(color: str, depth: float) -> ft.BoxShadow:
    return ft.BoxShadow(spread_radius=0, blur_radius=0, color=color, offset=ft.Offset(depth, depth))


def border(color: str = WHITE, width: float = 2) -> ft.Border:
    return ft.Border.all(width, color)


async def call(handler: Callable | None, *args: Any):
    if handler is None:
        return
    result = handler(*args)
    if inspect.isawaitable(result):
        await result


def _report(task: asyncio.Task):
    if task.cancelled():
        return
    exc = task.exception()
    if exc:
        logging.getLogger("multispot").error("Background task failed", exc_info=exc)


def spawn(coro) -> asyncio.Task:
    task = asyncio.create_task(coro)
    task.add_done_callback(_report)
    return task


class Pressable(ft.GestureDetector):
    def __init__(
        self,
        face: ft.Container,
        on_press: Callable | None = None,
        shadow: str = WHITE,
        depth: float = 4,
        haptic: Callable | None = None,
        on_long_press: Callable | None = None,
        **kwargs: Any,
    ):
        self.face = face
        self.depth = depth
        self.shadow_color = shadow
        self.on_press = on_press
        self.haptic = haptic
        self.enabled = True
        face.animate = ft.Animation(110, EASE)
        face.shadow = hard_shadow(shadow, depth) if depth else None
        self.holder = ft.Container(
            content=face,
            padding=ft.Padding.only(right=depth, bottom=depth),
            animate=ft.Animation(110, EASE),
            animate_opacity=ft.Animation(200, EASE),
            animate_scale=ft.Animation(140, EASE),
        )
        super().__init__(
            content=self.holder,
            on_tap=self._tap,
            on_tap_down=self._down,
            on_tap_up=self._up,
            on_tap_cancel=self._up,
            on_long_press=on_long_press,
            mouse_cursor=ft.MouseCursor.CLICK,
            **kwargs,
        )

    def _set_pressed(self, pressed: bool):
        d = self.depth
        if d:
            self.holder.padding = ft.Padding.only(left=d, top=d) if pressed else ft.Padding.only(right=d, bottom=d)
            self.face.shadow = hard_shadow(self.shadow_color, 0 if pressed else d)
        else:
            self.holder.scale = 0.96 if pressed else 1
        self.update()

    def recolor_shadow(self, color: str):
        self.shadow_color = color
        if self.depth:
            self.face.shadow = hard_shadow(color, self.depth)

    def _down(self, e):
        if not self.enabled:
            return
        self._set_pressed(True)
        if self.haptic:
            self.haptic()

    def _up(self, e):
        if not self.enabled:
            return
        self._set_pressed(False)

    async def _tap(self, e):
        if not self.enabled:
            return
        await call(self.on_press, e)

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        self.holder.opacity = 1 if enabled else 0.38
        self.mouse_cursor = ft.MouseCursor.CLICK if enabled else ft.MouseCursor.FORBIDDEN


class BrutalButton(Pressable):
    def __init__(
        self,
        text: str,
        icon: ft.IconData | None = None,
        on_click: Callable | None = None,
        variant: str = "primary",
        accent: str = GREEN,
        height: float = 56,
        haptic: Callable | None = None,
        expand: bool | int | None = None,
        **kwargs: Any,
    ):
        if variant == "primary":
            bg, fg, edge, shade, depth = accent, BLACK, BLACK, WHITE, 4
        elif variant == "secondary":
            bg, fg, edge, shade, depth = WHITE, BLACK, WHITE, accent, 4
        elif variant == "danger":
            bg, fg, edge, shade, depth = SURFACE, accent, accent, accent, 4
        else:
            bg, fg, edge, shade, depth = SURFACE, WHITE, BORDER_DIM, WHITE, 0
        self.fg = fg
        self.text = text
        self.icon = icon
        self.busy = False
        self.switcher = ft.AnimatedSwitcher(
            content=self._label(),
            duration=220,
            reverse_duration=120,
            transition=ft.AnimatedSwitcherTransition.SCALE,
            switch_in_curve=SPRING,
        )
        face = ft.Container(
            content=self.switcher,
            bgcolor=bg,
            border=border(edge),
            height=height,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(horizontal=18),
        )
        super().__init__(face, on_press=on_click, shadow=shade, depth=depth, haptic=haptic, expand=expand, **kwargs)

    def _label(self) -> ft.Control:
        parts: list[ft.Control] = []
        if self.icon:
            parts.append(ft.Icon(self.icon, color=self.fg, size=20))
        parts.append(txt(self.text, size=14, color=self.fg, bold=True, upper=True, spacing=1.2, lines=1))
        return ft.Row(parts, spacing=10, alignment=ft.MainAxisAlignment.CENTER, tight=True, key=f"l{self.text}")

    def _spinner(self) -> ft.Control:
        return ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2.5, color=self.fg),
                txt("Working", size=14, color=self.fg, bold=True, upper=True, spacing=1.2),
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
            key="spin",
        )

    def set_text(self, text: str, icon: ft.IconData | None = None):
        self.text = text
        if icon:
            self.icon = icon
        if not self.busy:
            self.switcher.content = self._label()

    def set_busy(self, busy: bool):
        self.busy = busy
        self.enabled = not busy
        self.switcher.content = self._spinner() if busy else self._label()
        self.update()


class IconSquare(Pressable):
    def __init__(
        self,
        icon: ft.IconData,
        on_click: Callable | None = None,
        size: float = 44,
        bg: str = SURFACE_2,
        fg: str = WHITE,
        edge: str = BORDER_DIM,
        shadow: str = WHITE,
        depth: float = 3,
        icon_size: float | None = None,
        haptic: Callable | None = None,
        tooltip: str | None = None,
    ):
        self.icon_control = ft.Icon(icon, color=fg, size=icon_size or size * 0.48)
        face = ft.Container(
            content=self.icon_control,
            width=size,
            height=size,
            bgcolor=bg,
            border=border(edge),
            alignment=ft.Alignment.CENTER,
            tooltip=tooltip,
        )
        super().__init__(face, on_press=on_click, shadow=shadow, depth=depth, haptic=haptic)

    def set_icon(self, icon: ft.IconData):
        self.icon_control.icon = icon


class Field(ft.Column):
    def __init__(
        self,
        title: str,
        value: str = "",
        hint: str = "",
        accent: str = GREEN,
        on_change: Callable | None = None,
        on_submit: Callable | None = None,
        trailing: ft.Control | None = None,
        keyboard: ft.KeyboardType = ft.KeyboardType.TEXT,
        prefix_icon: ft.IconData | None = None,
        autofocus: bool = False,
    ):
        self.accent = accent
        self.on_value = on_change
        self.input = ft.TextField(
            value=value,
            hint_text=hint,
            border=ft.InputBorder.NONE,
            text_style=ft.TextStyle(font_family=FONT, size=15, color=WHITE),
            hint_style=ft.TextStyle(font_family=FONT, size=14, color=TEXT_3),
            cursor_color=accent,
            selection_color=ft.Colors.with_opacity(0.35, accent),
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=16),
            keyboard_type=keyboard,
            on_change=self._changed,
            on_submit=on_submit,
            on_focus=lambda e: self._focus(True),
            on_blur=lambda e: self._focus(False),
            prefix_icon=ft.Icon(prefix_icon, color=TEXT_2, size=20) if prefix_icon else None,
            autofocus=autofocus,
            expand=True,
            dense=True,
        )
        row = [self.input]
        if trailing:
            row.append(ft.Container(trailing, padding=ft.Padding.only(right=6)))
        self.box = ft.Container(
            content=ft.Row(row, spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=SURFACE,
            border=border(WHITE),
            shadow=hard_shadow(WHITE, 0),
            animate=ft.Animation(160, EASE),
        )
        controls: list[ft.Control] = [label(title)] if title else []
        controls.append(self.box)
        super().__init__(controls, spacing=8)

    @property
    def value(self) -> str:
        return (self.input.value or "").strip()

    @value.setter
    def value(self, v: str):
        self.input.value = v

    def _focus(self, focused: bool):
        self.box.border = border(self.accent if focused else WHITE)
        self.box.shadow = hard_shadow(self.accent, 4 if focused else 0)
        self.box.update()

    async def _changed(self, e):
        await call(self.on_value, self.value)


class Segmented(ft.Container):
    def __init__(
        self,
        options: list[tuple[Any, str]],
        value: Any,
        on_change: Callable | None = None,
        accent: str = GREEN,
        haptic: Callable | None = None,
        dense: bool = False,
    ):
        self.options = options
        self.value = value
        self.accent = accent
        self.handler = on_change
        self.haptic = haptic
        self.cells: dict[Any, tuple[ft.Container, ft.Text]] = {}
        row: list[ft.Control] = []
        for i, (key, text) in enumerate(options):
            t = txt(text, size=11 if dense else 12, bold=True, upper=True, spacing=1, lines=1, align=ft.TextAlign.CENTER)
            cell = ft.Container(
                content=t,
                expand=True,
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding.symmetric(vertical=12 if dense else 14, horizontal=4),
                border=ft.Border.only(left=ft.BorderSide(2, WHITE)) if i else None,
                animate=ft.Animation(200, EASE),
                on_click=self._click,
                data=key,
            )
            self.cells[key] = (cell, t)
            row.append(cell)
        super().__init__(
            content=ft.Row(row, spacing=0),
            border=border(WHITE),
            bgcolor=SURFACE,
            shadow=hard_shadow(WHITE, 3),
        )
        self._paint()

    def _paint(self):
        for key, (cell, t) in self.cells.items():
            on = key == self.value
            cell.bgcolor = self.accent if on else SURFACE
            t.color = BLACK if on else TEXT_2

    async def _click(self, e):
        await self._pick(e.control.data)

    async def _pick(self, key: Any):
        if key == self.value:
            return
        self.value = key
        if self.haptic:
            self.haptic()
        self._paint()
        self.update()
        await call(self.handler, key)


class CountPicker(ft.Column):
    def __init__(
        self,
        title: str,
        value: int,
        lo: int,
        hi: int,
        unit: str = "tracks",
        accent: str = GREEN,
        haptic: Callable | None = None,
        on_change: Callable | None = None,
    ):
        self.value = value
        self.lo = lo
        self.hi = hi
        self.haptic = haptic
        self.handler = on_change
        self.number = txt(value, size=46, bold=True, color=accent, height=1.0)
        self.number.animate_scale = ft.Animation(160, SPRING)
        self.slider = ft.Slider(
            value=value,
            min=lo,
            max=hi,
            divisions=hi - lo,
            active_color=accent,
            inactive_color=SURFACE_3,
            thumb_color=WHITE,
            overlay_color=ft.Colors.with_opacity(0.15, accent),
            on_change=self._slide,
            padding=ft.Padding.symmetric(horizontal=0, vertical=8),
        )
        minus = IconSquare(ft.Icons.REMOVE, lambda e: self._step(-1), size=40, depth=2)
        plus = IconSquare(ft.Icons.ADD, lambda e: self._step(1), size=40, depth=2, bg=accent, fg=BLACK, edge=BLACK)
        self.plus = plus
        head = ft.Row(
            [
                ft.Row(
                    [self.number, ft.Container(txt(unit, size=12, color=TEXT_2, upper=True, bold=True, spacing=1), padding=ft.Padding.only(bottom=8))],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    tight=True,
                ),
                ft.Row([minus, plus], spacing=10, tight=True),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        range_row = ft.Row(
            [txt(lo, size=10, color=TEXT_3), txt(hi, size=10, color=TEXT_3)],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        body = ft.Container(
            ft.Column([head, self.slider, range_row], spacing=4),
            padding=ft.Padding.only(left=16, right=16, top=14, bottom=10),
            border=border(BORDER_DIM),
            bgcolor=SURFACE,
        )
        super().__init__([label(title), body], spacing=8)

    def recolor(self, accent: str):
        self.number.color = accent
        self.slider.active_color = accent
        self.slider.overlay_color = ft.Colors.with_opacity(0.15, accent)
        self.plus.face.bgcolor = accent

    def _apply(self, v: int, from_slider: bool):
        v = max(self.lo, min(self.hi, v))
        if v == self.value:
            return
        self.value = v
        self.number.value = str(v)
        if not from_slider:
            self.slider.value = v
        self.number.scale = 1.12
        if self.haptic:
            self.haptic()
        self.update()
        self.number.scale = 1
        self.number.update()
        if self.handler:
            self.handler(v)

    def _slide(self, e):
        self._apply(int(round(e.control.value)), True)

    def _step(self, delta: int):
        self._apply(self.value + delta, False)


def tag(text: str, color: str = GREEN, filled: bool = False) -> ft.Container:
    return ft.Container(
        txt(text, size=10, bold=True, upper=True, spacing=1.2, color=BLACK if filled else color),
        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        border=ft.Border.all(1.5, color),
        bgcolor=color if filled else None,
    )


def cover(src: str | None, size: float, edge: str | None = WHITE, icon: ft.IconData = ft.Icons.MUSIC_NOTE, circle: bool = False) -> ft.Container:
    content: ft.Control
    if src:
        content = ft.Image(
            src=src,
            width=size,
            height=size,
            fit=ft.BoxFit.COVER,
            fade_in_animation=ft.Animation(260, EASE),
            error_content=ft.Icon(icon, color=TEXT_3, size=size * 0.4),
        )
    else:
        content = ft.Icon(icon, color=TEXT_3, size=size * 0.4)
    return ft.Container(
        content=content,
        width=size,
        height=size,
        bgcolor=SURFACE_3,
        border=border(edge, 2) if edge else None,
        alignment=ft.Alignment.CENTER,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        shape=ft.BoxShape.CIRCLE if circle else None,
    )


def skeleton_rows(count: int = 6, height: float = 64) -> ft.Control:
    rows = [
        ft.Row(
            [
                ft.Container(width=height - 12, height=height - 12, bgcolor=SURFACE_2),
                ft.Column(
                    [
                        ft.Container(height=12, width=180, bgcolor=SURFACE_2),
                        ft.Container(height=10, width=110, bgcolor=SURFACE_2),
                    ],
                    spacing=8,
                    expand=True,
                ),
            ],
            spacing=14,
            height=height,
        )
        for _ in range(count)
    ]
    return ft.Shimmer(
        content=ft.Column(rows, spacing=6),
        base_color=SURFACE_2,
        highlight_color=SURFACE_3,
        period=1300,
    )


def empty_state(icon: ft.IconData, title: str, body: str = "", accent: str = TEXT_2) -> ft.Control:
    return ft.Container(
        ft.Column(
            [
                ft.Container(
                    ft.Icon(icon, size=30, color=accent),
                    width=64,
                    height=64,
                    border=border(accent),
                    alignment=ft.Alignment.CENTER,
                ),
                txt(title, size=14, bold=True, upper=True, spacing=1, align=ft.TextAlign.CENTER),
                txt(body, size=12, color=TEXT_2, align=ft.TextAlign.CENTER) if body else ft.Container(),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        padding=ft.Padding.symmetric(vertical=36, horizontal=20),
        alignment=ft.Alignment.CENTER,
    )


def meter(value: float, accent: str = GREEN, height: float = 6, duration: int = 900) -> ft.Container:
    bar = ft.Container(
        bgcolor=accent,
        height=height,
        scale=ft.Scale(scale_y=1, scale_x=0.001, alignment=ft.Alignment.CENTER_LEFT),
        animate_scale=ft.Animation(duration, EASE),
        data=max(0.0, min(1.0, value)),
    )
    return ft.Container(bar, bgcolor=SURFACE_3, height=height)


def fill_meters(root: ft.Control):
    stack = [root]
    while stack:
        node = stack.pop()
        content = getattr(node, "content", None)
        if isinstance(node, ft.Container) and isinstance(content, ft.Container) and content.animate_scale and isinstance(content.data, float):
            content.scale = ft.Scale(scale_y=1, scale_x=max(0.001, content.data), alignment=ft.Alignment.CENTER_LEFT)
        for attr in ("controls", "content"):
            child = getattr(node, attr, None)
            if isinstance(child, list):
                stack.extend(child)
            elif isinstance(child, ft.Control):
                stack.append(child)


def compact(n: int | float) -> str:
    n = float(n or 0)
    for div, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            v = n / div
            return f"{v:.1f}".rstrip("0").rstrip(".") + suffix
    return str(int(n))


def mmss(ms: int | float) -> str:
    s = int((ms or 0) // 1000)
    return f"{s // 60}:{s % 60:02d}"
