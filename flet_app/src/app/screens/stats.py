import asyncio

import flet as ft

from app.api import ApiError
from app.screens.registry import number_of
from app.theme import BORDER_DIM, EASE, SPRING, SURFACE, TEXT_2, TEXT_3, WHITE
from app.ui.screen import Screen, header
from app.ui.widgets import Segmented, border, compact, cover, empty_state, fill_meters, hard_shadow, meter, skeleton_rows, tag, txt

RANGES = [("short_term", "4 weeks"), ("medium_term", "6 months"), ("long_term", "All time")]
KINDS = [("tracks", "Tracks"), ("artists", "Artists"), ("genres", "Genres")]


def rank_row(app, index: int, image: str | None, title: str, subtitle: str, score: float, accent: str, url: str | None, circle: bool = False) -> ft.Control:
    first = index == 0

    async def open_item(e):
        if url:
            app.tap()
            await app.open_url(url)

    return ft.Container(
        ft.Row(
            [
                txt(f"{index + 1:02d}", size=22 if first else 15, bold=True, color=accent if index < 3 else TEXT_3, width=40),
                cover(image, 64 if first else 48, edge=WHITE if first else None, circle=circle),
                ft.Column(
                    [
                        txt(title, size=15 if first else 13, bold=True, lines=1),
                        txt(subtitle, size=11, color=TEXT_2, lines=1),
                        meter(score, accent if index < 3 else TEXT_3, height=3, duration=900 + index * 40),
                    ],
                    spacing=5,
                    tight=True,
                    expand=True,
                ),
            ],
            spacing=12,
        ),
        padding=ft.Padding.symmetric(vertical=10, horizontal=12) if first else ft.Padding.symmetric(vertical=6, horizontal=0),
        bgcolor=SURFACE if first else None,
        border=border(accent) if first else None,
        shadow=hard_shadow(accent, 5) if first else None,
        on_click=open_item,
    )


def genre_row(index: int, name: str, count: int, top: int, accent: str) -> ft.Control:
    share = count / top if top else 0
    return ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        txt(name.upper(), size=13 if index else 16, bold=True, lines=1, expand=True),
                        txt(f"×{count}", size=12, bold=True, color=accent if index < 3 else TEXT_2),
                    ],
                ),
                meter(share, accent if index < 3 else WHITE, height=14 if index < 3 else 8, duration=1000 + index * 60),
            ],
            spacing=6,
        ),
        padding=ft.Padding.symmetric(vertical=6),
    )


def artist_line(a: dict) -> str:
    parts = []
    if a.get("followers") is not None:
        parts.append(f"{compact(a['followers'])} followers")
    parts.append(", ".join((a.get("genres") or [])[:2]) or "no genre listed")
    return " · ".join(parts)


def build(app, feature, **_) -> ft.View:
    accent = feature.accent
    state = {"range": "medium_term", "kind": "tracks"}
    cache: dict[tuple[str, str], dict] = {}
    body = ft.Container(skeleton_rows(8), animate_size=ft.Animation(300, EASE))
    summary = ft.Container(animate_opacity=ft.Animation(400, EASE), opacity=0)
    req = {"n": 0}

    async def fetch(force: bool = False) -> dict | None:
        key = (state["kind"], state["range"])
        if key in cache and not force:
            return cache[key]
        try:
            data = await app.api.top(state["kind"], state["range"], 50 if state["kind"] != "tracks" else 50)
        except ApiError as exc:
            app.toast(exc.message, "error")
            return None
        cache[key] = data
        return data

    def build_list(data: dict) -> list[ft.Control]:
        kind = state["kind"]
        if kind == "tracks":
            items = data.get("tracks", [])
            return [rank_row(app, i, t.get("image"), t["name"], ", ".join(t.get("artists", [])), (t.get("popularity") or 0) / 100, accent, t.get("url")) for i, t in enumerate(items)]
        if kind == "artists":
            items = data.get("artists", [])
            return [
                rank_row(app, i, a.get("image"), a["name"], artist_line(a), (a.get("popularity") or 0) / 100, accent, a.get("url"), circle=True)
                for i, a in enumerate(items)
            ]
        items = data.get("genres", [])
        top = items[0]["count"] if items else 0
        return [genre_row(i, g["name"], g["count"], top, accent) for i, g in enumerate(items)]

    def build_summary(data: dict) -> ft.Control | None:
        kind = state["kind"]
        if kind == "tracks" and data.get("tracks"):
            t = data["tracks"]
            avg = sum(x.get("popularity") or 0 for x in t) / len(t)
            explicit = sum(1 for x in t if x.get("explicit"))
            artists = len({a for x in t for a in x.get("artists", [])})
            return stat_strip([("avg pop", f"{avg:.0f}"), ("artists", str(artists)), ("explicit", f"{explicit * 100 // len(t)}%")])
        if kind == "artists" and data.get("artists"):
            a = data["artists"]
            followers = sum(x.get("followers") or 0 for x in a)
            obscure = sum(1 for x in a if (x.get("popularity") or 0) < 50)
            return stat_strip([("reach", compact(followers)), ("niche", str(obscure)), ("top", a[0]["name"].split(" ")[0][:8])])
        if kind == "genres" and data.get("genres"):
            g = data["genres"]
            tagged = data.get("artists_tagged")
            coverage = f"{tagged}/{data.get('artists_total')}" if tagged is not None else f"{g[0]['count']}"
            return stat_strip([("genres", str(len(g))), ("#1", g[0]["name"].split(" ")[0][:9]), ("tagged", coverage)])
        return None

    def stat_strip(items: list[tuple[str, str]]) -> ft.Control:
        return ft.Row(
            [
                ft.Container(
                    ft.Column([txt(v, size=20, bold=True, color=accent, lines=1), txt(k, size=10, color=TEXT_2, upper=True, bold=True, spacing=1)], spacing=2, tight=True),
                    expand=True,
                    padding=12,
                    border=border(BORDER_DIM),
                    bgcolor=SURFACE,
                )
                for k, v in items
            ],
            spacing=10,
        )

    async def render(force: bool = False):
        req["n"] += 1
        token = req["n"]
        if (state["kind"], state["range"]) not in cache or force:
            body.content = skeleton_rows(8)
            summary.opacity = 0
            view.update()
        data = await fetch(force)
        if token != req["n"]:
            return
        if data is None:
            body.content = empty_state(ft.Icons.WIFI_OFF, "Couldn't load", "Pull down to retry.", accent)
            view.update()
            return
        controls = build_list(data)
        if not controls:
            if state["kind"] == "genres":
                body.content = empty_state(ft.Icons.LABEL_OFF, "No genres listed", "Spotify stopped tagging most artists with genres.", accent)
            else:
                body.content = empty_state(ft.Icons.MUSIC_OFF, "Not enough listening yet", "Spotify needs more history for this range.", accent)
            view.update()
            return
        column = ft.Column(controls, spacing=8)
        for i, c in enumerate(controls[:12]):
            c.opacity = 0
            c.offset = ft.Offset(0, 0.4)
            c.animate_opacity = ft.Animation(260 + i * 45, EASE)
            c.animate_offset = ft.Animation(420 + i * 45, SPRING)
        body.content = column
        summary.content = build_summary(data)
        view.update()
        await asyncio.sleep(0.03)
        for c in controls[:12]:
            c.opacity = 1
            c.offset = ft.Offset(0, 0)
        fill_meters(column)
        summary.opacity = 1
        view.update()

    async def on_range(value):
        state["range"] = value
        await render()

    async def on_kind(value):
        state["kind"] = value
        await render()

    async def refresh(e):
        app.thud()
        await render(force=True)

    async def ready():
        await render()

    view = Screen(
        app,
        "/stats",
        [
            *header(app, feature.title, "Your listening, ranked. Tap anything to open it in Spotify.", accent, feature.icon, number_of(feature.key)),
            Segmented(RANGES, state["range"], on_range, accent, app.select, dense=True),
            Segmented(KINDS, state["kind"], on_kind, WHITE, app.select, dense=True),
            summary,
            body,
            ft.Row([tag("Pull to refresh", TEXT_3)], alignment=ft.MainAxisAlignment.CENTER),
        ],
        accent=accent,
        on_refresh=refresh,
        on_ready=ready,
    )
    return view


