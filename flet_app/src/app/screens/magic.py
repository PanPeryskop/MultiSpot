import asyncio

import flet as ft

from app.api import ApiError
from app.screens.registry import number_of
from app.theme import BLACK, SURFACE, TEXT_2
from app.ui.result import ResultSlot
from app.ui.screen import Screen, header
from app.ui.widgets import BrutalButton, CountPicker, Field, border, spawn, txt


def build(app, feature, **_) -> ft.View:
    accent = feature.accent
    result = ResultSlot()
    name = Field("Playlist name", "Magic Mix", accent=accent)
    count = CountPicker("Mix length", 25, 5, 100, accent=accent, haptic=app.select)
    orbs = [
        ft.Container(
            width=size,
            height=size,
            shape=ft.BoxShape.CIRCLE,
            border=ft.Border.all(2, accent),
            bgcolor=accent if i == 2 else None,
            animate_scale=ft.Animation(900, ft.AnimationCurve.EASE_IN_OUT_SINE),
            animate_rotation=ft.Animation(1200, ft.AnimationCurve.EASE_IN_OUT_CUBIC),
            scale=1,
        )
        for i, size in enumerate((150, 104, 58))
    ]
    stage = ft.Container(
        ft.Stack([ft.Container(o, alignment=ft.Alignment.CENTER, left=0, right=0, top=0, bottom=0) for o in orbs] + [
            ft.Container(ft.Icon(ft.Icons.AUTO_AWESOME, color=BLACK, size=28), alignment=ft.Alignment.CENTER, left=0, right=0, top=0, bottom=0)
        ]),
        height=190,
        bgcolor=SURFACE,
        border=border(),
    )
    state = {"busy": False}

    async def pulse():
        k = 0
        while state["busy"]:
            for i, orb in enumerate(orbs):
                orb.scale = 1.18 if (k + i) % 2 == 0 else 0.86
            stage.update()
            k += 1
            await asyncio.sleep(0.45)
        for orb in orbs:
            orb.scale = 1
        stage.update()

    async def submit(e):
        button.set_busy(True)
        state["busy"] = True
        spawn(pulse())
        try:
            data = await app.api.magic(name.value or "Magic Mix", count.value)
        except ApiError as exc:
            app.toast(exc.message, "error")
            return
        finally:
            state["busy"] = False
            button.set_busy(False)
        seeds = data.get("seeds") or []
        result.show(
            app,
            "Conjured",
            f"{data.get('track_count', 0)} fresh tracks",
            f"Seeded from {', '.join(seeds[:5])}." if seeds else "Built from your taste.",
            accent,
            data.get("playlist_url"),
            tracks=data.get("tracks"),
            total=data.get("track_count"),
        )

    button = BrutalButton("Cast the mix", ft.Icons.AUTO_AWESOME, submit, accent=accent, haptic=app.thud)
    return Screen(
        app,
        "/magic",
        [
            *header(app, feature.title, "One tap. We pick some of your favourites, find what their fans play next to them and skip what you already have on repeat.", accent, feature.icon, number_of(feature.key)),
            stage,
            name,
            count,
            txt("Every cast picks different seeds from your last months.", size=11, color=TEXT_2),
            button,
            result,
        ],
        accent=accent,
    )
