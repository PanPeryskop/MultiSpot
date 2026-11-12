import asyncio

import flet as ft

from app.api import ApiError
from app.screens.registry import number_of
from app.theme import BLACK, BORDER_DIM, EASE, SPRING, SURFACE, TEXT_2, WHITE
from app.ui.result import ResultSlot
from app.ui.screen import Screen, header
from app.ui.widgets import BrutalButton, CountPicker, Field, border, cover, hard_shadow, label, spawn, txt

SOURCES = [
    ("recent", "Recent", "Last 50 plays", ft.Icons.HISTORY_TOGGLE_OFF),
    ("short_term", "4 weeks", "Heavy rotation", ft.Icons.LOCAL_FIRE_DEPARTMENT),
    ("medium_term", "6 months", "This season", ft.Icons.WB_SUNNY),
    ("long_term", "All time", "Forever faves", ft.Icons.ALL_INCLUSIVE),
]
TITLES = {key: title for key, title, _, _ in SOURCES}


def build(app, feature, **_) -> ft.View:
    accent = feature.accent
    state = {"source": "short_term", "req": 0}
    result = ResultSlot()
    name = Field("Playlist name", "", "Rewind: 4 weeks", accent=accent)
    count = CountPicker("Tracks", 50, 10, 100, accent=accent, haptic=app.select)
    count_slot = ft.Container(count, animate_size=ft.Animation(360, EASE), clip_behavior=ft.ClipBehavior.HARD_EDGE)
    strip = ft.Row(spacing=8, scroll=ft.ScrollMode.HIDDEN)
    strip_box = ft.Container(strip, height=72)
    cards: dict[str, ft.Container] = {}

    def card(key: str, title: str, sub: str, icon: ft.IconData) -> ft.Container:
        node = ft.Container(
            ft.Column(
                [
                    ft.Icon(icon, size=22, color=WHITE),
                    txt(title, size=15, bold=True, upper=True, lines=1),
                    txt(sub, size=10, color=TEXT_2, lines=1),
                ],
                spacing=6,
                tight=True,
            ),
            padding=14,
            expand=True,
            bgcolor=SURFACE,
            border=border(BORDER_DIM),
            animate=ft.Animation(220, EASE),
            animate_scale=ft.Animation(420, SPRING),
            animate_rotation=ft.Animation(420, SPRING),
            scale=1,
            on_click=lambda e, k=key: pick(k),
        )
        cards[key] = node
        return node

    def paint():
        for key, node in cards.items():
            on = key == state["source"]
            node.bgcolor = accent if on else SURFACE
            node.border = border(BLACK if on else BORDER_DIM)
            node.shadow = hard_shadow(WHITE, 4) if on else None
            node.rotate = ft.Rotate(-0.025 if on else 0)
            node.scale = 1.03 if on else 1
            column = node.content
            column.controls[0].color = BLACK if on else WHITE
            column.controls[1].color = BLACK if on else WHITE
            column.controls[2].color = BLACK if on else TEXT_2

    def pick(key: str):
        if key == state["source"]:
            return
        app.select()
        state["source"] = key
        paint()
        name.input.hint_text = f"Rewind: {TITLES[key]}"
        count_slot.content = None if key == "recent" else count
        view.update()
        spawn(load_preview())

    async def load_preview():
        state["req"] += 1
        token = state["req"]
        source = state["source"]
        try:
            if source == "recent":
                data = await app.api.fusion_suggestions()
                tracks = data.get("recent_tracks", [])
            else:
                data = await app.api.top("tracks", source, 12)
                tracks = data.get("tracks", [])
        except ApiError:
            tracks = []
        if token != state["req"]:
            return
        tiles = []
        for t in tracks[:12]:
            tile = ft.Container(cover(t.get("image"), 64, edge=None), offset=ft.Offset(0.6, 0), opacity=0, animate_offset=ft.Animation(420, SPRING), animate_opacity=ft.Animation(260, EASE))
            tiles.append(tile)
        strip.controls = tiles
        try:
            strip.update()
        except Exception:
            return
        for tile in tiles:
            await asyncio.sleep(0.035)
            if token != state["req"]:
                return
            tile.offset = ft.Offset(0, 0)
            tile.opacity = 1
            try:
                tile.update()
            except Exception:
                return

    async def submit(e):
        button.set_busy(True)
        try:
            data = await app.api.rewind(state["source"], name.value or None, count.value)
        except ApiError as exc:
            app.toast(exc.message, "error")
            return
        finally:
            button.set_busy(False)
        result.show(
            app,
            "Snapshot saved",
            f"{data.get('track_count', 0)} tracks",
            f"Your {TITLES[state['source']].lower()} frozen into a playlist.",
            accent,
            data.get("playlist_url"),
            tracks=data.get("tracks"),
            total=data.get("track_count"),
        )

    grid = ft.Column(
        [
            ft.Row([card(*SOURCES[0]), card(*SOURCES[1])], spacing=12),
            ft.Row([card(*SOURCES[2]), card(*SOURCES[3])], spacing=12),
        ],
        spacing=12,
    )
    paint()
    button = BrutalButton("Save snapshot", ft.Icons.SAVE_ALT, submit, accent=accent, haptic=app.thud)

    async def ready():
        await load_preview()

    view = Screen(
        app,
        "/rewind",
        [
            *header(app, feature.title, "Freeze a moment of your listening into a playlist: today, this month, this year or ever.", accent, feature.icon, number_of(feature.key)),
            ft.Column([label("Snapshot"), grid], spacing=10),
            strip_box,
            name,
            count_slot,
            button,
            result,
        ],
        accent=accent,
        on_ready=ready,
    )
    return view
