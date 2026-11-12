import asyncio
from datetime import datetime

import flet as ft

from app.api import ApiError
from app.screens.registry import number_of
from app.theme import BLACK, BORDER_DIM, CYAN, EASE, ORANGE, PURPLE, SPRING, SURFACE, SURFACE_2, TEXT_2, WHITE
from app.ui.result import ResultSlot
from app.ui.screen import Screen, header
from app.ui.widgets import BrutalButton, IconSquare, border, empty_state, hard_shadow, label, skeleton_rows, txt

STYLE = {
    "daily_mix": (ft.Icons.WB_TWILIGHT, CYAN),
    "weekly_radar": (ft.Icons.RADAR, ORANGE),
    "monthly_rewind": (ft.Icons.EVENT_REPEAT, PURPLE),
}


def when(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso).strftime("%a %d %b, %H:%M")
    except ValueError:
        return iso


class Switch(ft.Container):
    def __init__(self, on: bool, accent: str, on_toggle):
        self.on = on
        self.accent = accent
        self.knob = ft.Container(width=20, height=20, bgcolor=BLACK if on else WHITE, left=26 if on else 2, top=2, animate_position=ft.Animation(260, SPRING), animate=ft.Animation(200, EASE))
        super().__init__(
            ft.Stack([self.knob], width=48, height=24),
            width=52,
            height=28,
            bgcolor=accent if on else SURFACE_2,
            border=border(WHITE),
            animate=ft.Animation(200, EASE),
            on_click=on_toggle,
        )

    def set(self, on: bool):
        self.on = on
        self.knob.left = 26 if on else 2
        self.knob.bgcolor = BLACK if on else WHITE
        self.bgcolor = self.accent if on else SURFACE_2


def build(app, feature, **_) -> ft.View:
    accent = feature.accent
    result = ResultSlot()
    state: dict = {"data": None}
    active = ft.Column(spacing=16)
    catalog = ft.Column(spacing=12)
    body = ft.Container(skeleton_rows(3, 110), animate_size=ft.Animation(320, EASE))

    def pilot_card(item: dict) -> ft.Control:
        icon, color = STYLE.get(item["kind"], (ft.Icons.SMART_TOY, accent))
        status = txt("", size=11, color=TEXT_2, lines=2)
        schedule = txt("", size=11, bold=True, color=color, upper=True, spacing=0.8)

        def paint():
            schedule.value = f"{item.get('schedule', '')} · next {when(item.get('next_run'))}" if item["enabled"] else "Paused"
            status.value = f"Last run {when(item.get('last_run'))}" + (f" · {item['last_status']}" if item.get("last_status") else "")
            node.opacity = 1 if item["enabled"] else 0.55
            node.shadow = hard_shadow(color, 6) if item["enabled"] else None

        async def toggle(e):
            app.select()
            switch.set(not item["enabled"])
            switch.update()
            try:
                fresh = await app.api.toggle_autopilot(item["id"], not item["enabled"])
            except ApiError as exc:
                switch.set(item["enabled"])
                switch.update()
                app.toast(exc.message, "error")
                return
            item.update(fresh)
            paint()
            node.update()

        async def run_now(e):
            run_btn.set_busy(True)
            try:
                fresh = await app.api.run_autopilot(item["id"])
            except ApiError as exc:
                app.toast(exc.message, "error")
                return
            finally:
                run_btn.set_busy(False)
            item.update(fresh)
            paint()
            node.update()
            app.toast(fresh.get("last_status") or "Done", "success")

        async def open_playlist(e):
            if item.get("playlist_url"):
                app.tap()
                await app.open_url(item["playlist_url"])

        async def remove(e):
            app.thud()
            node.scale = 0.9
            node.opacity = 0
            node.update()
            try:
                await app.api.delete_autopilot(item["id"])
            except ApiError as exc:
                node.scale = 1
                node.opacity = 1
                node.update()
                app.toast(exc.message, "error")
                return
            await asyncio.sleep(0.25)
            await reload()
            app.toast("Autopilot removed, playlist kept", "info")

        switch = Switch(item["enabled"], color, toggle)
        run_btn = BrutalButton("Run now", ft.Icons.PLAY_ARROW, run_now, variant="ghost", haptic=app.tap, height=42)
        node = ft.Container(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(ft.Icon(icon, color=BLACK, size=24), width=48, height=48, bgcolor=color, border=border(BLACK), alignment=ft.Alignment.CENTER, rotate=ft.Rotate(-0.05)),
                            ft.Column([txt((item.get("settings") or {}).get("name") or item.get("label", ""), size=16, bold=True, lines=1), schedule], spacing=3, tight=True, expand=True),
                            switch,
                        ],
                        spacing=12,
                    ),
                    status,
                    ft.Row(
                        [
                            ft.Container(run_btn, expand=True),
                            IconSquare(ft.Icons.OPEN_IN_NEW, open_playlist, size=42, depth=2, haptic=app.tap),
                            IconSquare(ft.Icons.DELETE_OUTLINE, remove, size=42, depth=2),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor=SURFACE,
            border=border(color),
            animate=ft.Animation(220, EASE),
            animate_opacity=ft.Animation(220, EASE),
            animate_scale=ft.Animation(240, EASE),
            scale=1,
        )
        paint()
        return node

    def offer_card(kind: dict) -> ft.Control:
        icon, color = STYLE.get(kind["kind"], (ft.Icons.SMART_TOY, accent))

        async def create(e):
            button.set_busy(True)
            try:
                item = await app.api.create_autopilot(kind["kind"])
            except ApiError as exc:
                app.toast(exc.message, "error")
                button.set_busy(False)
                return
            result.show(app, "Autopilot on", item.get("label", ""), item.get("last_status") or "First playlist is ready.", color, item.get("playlist_url"), tracks=item.get("tracks"), total=item.get("last_count"))
            await reload()

        button = BrutalButton("Turn on", ft.Icons.BOLT, create, accent=color, haptic=app.thud, height=44)
        return ft.Container(
            ft.Column(
                [
                    ft.Row([ft.Icon(icon, color=color, size=22), txt(kind["label"], size=15, bold=True, upper=True, lines=1, expand=True)], spacing=10),
                    txt(kind["description"], size=12, color=TEXT_2, height=1.4),
                    txt(kind["schedule"], size=10, color=color, bold=True, upper=True, spacing=1),
                    button,
                ],
                spacing=10,
            ),
            padding=16,
            border=border(BORDER_DIM),
            bgcolor=SURFACE,
        )

    async def reload():
        try:
            data = await app.api.autopilots()
        except ApiError as exc:
            body.content = empty_state(ft.Icons.WIFI_OFF, "Couldn't load", exc.message, accent)
            view.update()
            return
        state["data"] = data
        items = data.get("automations", [])
        taken = {a["kind"] for a in items}
        cards = [pilot_card(a) for a in items]
        offers = [offer_card(k) for k in data.get("kinds", []) if k["kind"] not in taken]
        active.controls = cards
        catalog.controls = offers
        blocks: list[ft.Control] = []
        if cards:
            blocks += [label("Running", accent), active]
        if offers:
            blocks += [label("Add an autopilot"), catalog]
        body.content = ft.Column(blocks, spacing=14)
        for c in cards + offers:
            c.opacity = 0
            c.offset = ft.Offset(0, 0.25)
            c.animate_offset = ft.Animation(420, SPRING)
        view.update()
        for c in cards + offers:
            await asyncio.sleep(0.05)
            c.opacity = 1 if c not in cards or (c.shadow is not None) else 0.55
            c.offset = ft.Offset(0, 0)
            c.update()

    async def ready():
        await reload()

    view = Screen(
        app,
        "/autopilot",
        [
            *header(app, feature.title, "Playlists that keep themselves fresh. MultiSpot refreshes them on schedule, even when your phone is off.", accent, feature.icon, number_of(feature.key)),
            result,
            body,
        ],
        accent=accent,
        on_ready=ready,
    )
    return view
