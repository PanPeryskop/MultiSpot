import asyncio

import flet as ft

from app.api import ApiError
from app.screens.registry import number_of
from app.theme import BORDER_DIM, EASE, SPRING, SURFACE, TEXT_2, TEXT_3, WHITE
from app.ui.result import ResultSlot
from app.ui.screen import Screen, header
from app.ui.widgets import BrutalButton, Segmented, border, cover, empty_state, hard_shadow, skeleton_rows, spawn, tag, txt

WINDOWS = [(7, "7 days"), (14, "14 days"), (30, "30 days")]


def build(app, feature, **_) -> ft.View:
    accent = feature.accent
    state = {"days": 14, "req": 0, "count": 0}
    result = ResultSlot()
    summary = txt("", size=11, color=TEXT_2, upper=True, spacing=1, bold=True)
    feed = ft.Container(skeleton_rows(5, 84), animate_size=ft.Animation(320, EASE))
    sweep = ft.Container(
        ft.Icon(ft.Icons.RADAR, size=44, color=accent),
        rotate=ft.Rotate(0),
        animate_rotation=ft.Animation(1200, ft.AnimationCurve.LINEAR),
    )

    async def spin(token: int):
        angle = 0.0
        while state["req"] == token and isinstance(feed.content, ft.Column) and feed.content.data == "scan":
            angle += 6.2832
            sweep.rotate = ft.Rotate(angle)
            try:
                sweep.update()
            except Exception:
                return
            await asyncio.sleep(1.2)

    def card(r: dict) -> ft.Control:
        link = r.get("url")

        async def open_release(e):
            if link:
                app.tap()
                await app.open_url(link)

        node = ft.Container(
            ft.Row(
                [
                    ft.Container(cover(r.get("image"), 76, edge=None), shadow=hard_shadow(accent if r.get("album_type") == "album" else WHITE, 4)),
                    ft.Column(
                        [
                            ft.Row([tag(r.get("album_type") or "release", accent, r.get("album_type") == "album"), txt(r.get("release_date", ""), size=10, color=TEXT_3, bold=True)], spacing=8),
                            txt(r.get("name", ""), size=14, bold=True, lines=2, height=1.15),
                            txt(", ".join(r.get("artists") or []), size=11, color=TEXT_2, lines=1),
                        ],
                        spacing=5,
                        tight=True,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.NORTH_EAST, size=18, color=TEXT_3),
                ],
                spacing=14,
            ),
            padding=10,
            bgcolor=SURFACE,
            border=border(BORDER_DIM),
            ink=True,
            on_click=open_release,
            opacity=0,
            offset=ft.Offset(0.15, 0),
            animate_opacity=ft.Animation(280, EASE),
            animate_offset=ft.Animation(460, SPRING),
        )
        return node

    async def load():
        state["req"] += 1
        token = state["req"]
        scanning = ft.Column(
            [ft.Row([sweep], alignment=ft.MainAxisAlignment.CENTER), txt("Scanning your artists…", size=12, color=TEXT_2, align=ft.TextAlign.CENTER)],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
            data="scan",
            height=160,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        feed.content = scanning
        summary.value = ""
        save.set_enabled(False)
        view.update()
        spawn(spin(token))
        try:
            data = await app.api.release_radar(state["days"])
        except ApiError as exc:
            if token == state["req"]:
                feed.content = empty_state(ft.Icons.WIFI_OFF, "Couldn't scan", exc.message, accent)
                view.update()
            return
        if token != state["req"]:
            return
        releases = data.get("releases", [])
        state["count"] = len(releases)
        if not releases:
            feed.content = empty_state(ft.Icons.NOTIFICATIONS_OFF, "Quiet week", f"Nothing new from your {data.get('artists_checked', 0)} artists.", accent)
            view.update()
            return
        summary.value = f"{len(releases)} releases · {data.get('artists_checked', 0)} artists checked"
        cards = [card(r) for r in releases]
        feed.content = ft.Column(cards, spacing=10)
        save.set_enabled(True)
        view.update()
        for c in cards[:14]:
            await asyncio.sleep(0.04)
            if token != state["req"]:
                return
            c.opacity = 1
            c.offset = ft.Offset(0, 0)
            c.update()
        for c in cards[14:]:
            c.opacity = 1
            c.offset = ft.Offset(0, 0)
        view.update()

    async def on_days(value):
        state["days"] = value
        await load()

    async def submit(e):
        save.set_busy(True)
        try:
            data = await app.api.save_release_radar(state["days"])
        except ApiError as exc:
            app.toast(exc.message, "error")
            return
        finally:
            save.set_busy(False)
        result.show(app, "Radar saved", f"{data.get('track_count', 0)} new tracks", f"Everything from the last {state['days']} days in one playlist.", accent, data.get("playlist_url"), tracks=data.get("tracks"), total=data.get("track_count"))
        await view.list.scroll_to(offset=0, duration=500)

    save = BrutalButton("Save as playlist", ft.Icons.PLAYLIST_ADD, submit, accent=accent, haptic=app.thud)
    save.set_enabled(False)

    async def ready():
        await load()

    view = Screen(
        app,
        "/release-radar",
        [
            *header(app, feature.title, "Fresh drops from the artists you follow and play the most. Want it every Friday? Turn on Autopilot.", accent, feature.icon, number_of(feature.key)),
            Segmented(WINDOWS, state["days"], on_days, accent, app.select, dense=True),
            result,
            summary,
            feed,
        ],
        accent=accent,
        footer=save,
        on_ready=ready,
    )
    return view
