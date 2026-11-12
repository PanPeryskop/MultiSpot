import asyncio
import math

import flet as ft

from app.theme import EASE, EASE_SOFT, ELASTIC, SPRING


def prime(control: ft.Control, dy: float = 0.18, dx: float = 0.0, scale: float | None = None):
    control.opacity = 0
    control.offset = ft.Offset(dx, dy)
    control.animate_opacity = ft.Animation(520, EASE)
    control.animate_offset = ft.Animation(720, EASE_SOFT)
    if scale is not None:
        control.scale = scale
        control.animate_scale = ft.Animation(720, SPRING)


def settle(control: ft.Control):
    control.opacity = 1
    control.offset = ft.Offset(0, 0)
    if control.animate_scale and control.scale not in (None, 1):
        control.scale = 1


async def cascade(controls: list[ft.Control], start: float = 0.08, step: float = 0.055):
    await asyncio.sleep(start)
    for control in controls:
        settle(control)
        try:
            control.update()
        except Exception:
            return
        await asyncio.sleep(step)


def curtain(color: str) -> ft.Container:
    return ft.Container(
        bgcolor=color,
        left=0,
        right=0,
        top=0,
        bottom=0,
        offset=ft.Offset(0, 0),
        animate_offset=ft.Animation(680, ft.AnimationCurve.EASE_IN_OUT_CUBIC_EMPHASIZED),
        ignore_interactions=True,
    )


async def lift(control: ft.Container, delay: float = 0.04):
    await asyncio.sleep(delay)
    control.offset = ft.Offset(0, -1.02)
    control.update()


def prime_stamp(control: ft.Control):
    control.opacity = 0
    control.scale = 1.35
    control.rotate = ft.Rotate(-0.09)
    control.animate_opacity = ft.Animation(180, EASE)
    control.animate_scale = ft.Animation(650, ELASTIC)
    control.animate_rotation = ft.Animation(650, ELASTIC)


def stamp(control: ft.Control):
    control.opacity = 1
    control.scale = 1
    control.rotate = ft.Rotate(0.012)


def turn(control: ft.Control, quarter_turns: float):
    current = control.rotate.angle if isinstance(control.rotate, ft.Rotate) else 0
    control.rotate = ft.Rotate(current + quarter_turns * math.pi / 2)
