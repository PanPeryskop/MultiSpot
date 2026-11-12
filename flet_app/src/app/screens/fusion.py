import asyncio

import flet as ft

from app.api import ApiError
from app.screens._shared import normalize, paste_button, spotify_kind
from app.screens.registry import number_of
from app.theme import BLACK, BORDER_DIM, EASE, GUTTER, SPRING, SURFACE, SURFACE_2, TEXT_2, TEXT_3, WHITE
from app.ui.result import ResultSlot
from app.ui.screen import Screen, header
from app.ui.widgets import BrutalButton, CountPicker, Field, Segmented, border, cover, empty_state, label, skeleton_rows, spawn, txt

MAX_SEEDS = 10


def build(app, feature, **_) -> ft.View:
    accent = feature.accent
    seeds: list[dict] = []
    state = {"filter": "all", "results": None, "search_task": None, "suggestions": None}
    result = ResultSlot()
    tray = ft.Row(spacing=10, scroll=ft.ScrollMode.HIDDEN)
    tray_box = ft.Container(animate_size=ft.Animation(320, EASE), clip_behavior=ft.ClipBehavior.HARD_EDGE)
    feed = ft.Container(skeleton_rows(5), animate_size=ft.Animation(260, EASE))
    adders: dict[str, list[ft.Container]] = {}

    def has(url: str) -> bool:
        return any(s["url"] == url for s in seeds)

    def paint_adders():
        for url, buttons in adders.items():
            on = has(url)
            for b in buttons:
                b.bgcolor = accent if on else SURFACE_2
                b.content.icon = ft.Icons.CHECK if on else ft.Icons.ADD
                b.content.color = BLACK if on else WHITE
                b.rotate = ft.Rotate(0 if on else -0.25)

    def chip(seed: dict) -> ft.Control:
        node = ft.Container(
            ft.Row(
                [
                    cover(seed.get("image"), 34, edge=None, circle=seed["kind"] == "artist"),
                    txt(seed["name"], size=12, bold=True, lines=1, width=110),
                    ft.Icon(ft.Icons.CLOSE, size=16, color=BLACK),
                ],
                spacing=8,
                tight=True,
            ),
            bgcolor=accent,
            padding=ft.Padding.only(left=4, right=10, top=4, bottom=4),
            border=border(BLACK),
            scale=0.4,
            opacity=0,
            animate_scale=ft.Animation(420, SPRING),
            animate_opacity=ft.Animation(200, EASE),
            on_click=lambda e, s=seed: toggle(s),
        )
        return node

    def render_tray():
        if seeds:
            for s in seeds:
                if s.get("_chip") is None:
                    s["_chip"] = chip(s)
            tray.controls = [s["_chip"] for s in seeds]
            tray_box.content = ft.Column([ft.Row([label(f"Seeds {len(seeds)}/{MAX_SEEDS}", accent), ft.Container(expand=True)]), tray], spacing=8)
        else:
            tray_box.content = None
        n = len(seeds)
        fuse.set_text(f"Fuse {n} seed{'s' if n != 1 else ''}" if n else "Add seeds to fuse")
        fuse.set_enabled(n > 0)

    async def pop_in(c: ft.Control):
        await asyncio.sleep(0.03)
        c.scale = 1
        c.opacity = 1
        c.update()

    def toggle(seed: dict):
        existing = next((s for s in seeds if s["url"] == seed["url"]), None)
        if existing:
            seeds.remove(existing)
            app.select()
        else:
            if len(seeds) >= MAX_SEEDS:
                app.toast(f"Max {MAX_SEEDS} seeds", "error")
                return
            seed = {**seed, "_chip": None}
            seeds.append(seed)
            app.tap()
        render_tray()
        paint_adders()
        view.update()
        if not existing:
            spawn(pop_in(seed["_chip"]))

    def adder(item: dict) -> ft.Container:
        b = ft.Container(
            ft.Icon(ft.Icons.ADD, size=18, color=WHITE),
            width=36,
            height=36,
            alignment=ft.Alignment.CENTER,
            border=border(BLACK if has(item["url"]) else BORDER_DIM),
            animate=ft.Animation(200, EASE),
            animate_rotation=ft.Animation(380, SPRING),
            rotate=ft.Rotate(-0.25),
        )
        adders.setdefault(item["url"], []).append(b)
        return b

    def seed_of(item: dict, kind: str) -> dict:
        sub = ", ".join(item.get("artists", [])) if item.get("artists") else kind
        return {"url": item["url"], "name": item["name"], "image": item.get("image"), "kind": kind, "sub": sub}

    def result_row(seed: dict) -> ft.Control:
        return ft.Container(
            ft.Row(
                [
                    cover(seed.get("image"), 46, edge=None, circle=seed["kind"] == "artist"),
                    ft.Column([txt(seed["name"], size=13, bold=True, lines=1), txt(f"{seed['kind']} · {seed['sub']}", size=11, color=TEXT_2, lines=1)], spacing=2, tight=True, expand=True),
                    adder(seed),
                ],
                spacing=12,
            ),
            padding=ft.Padding.symmetric(vertical=6),
            on_click=lambda e, s=seed: toggle(s),
        )

    def card(seed: dict) -> ft.Control:
        a = adder(seed)
        a.width = a.height = 30
        return ft.Container(
            ft.Column(
                [
                    ft.Stack([cover(seed.get("image"), 116, edge=WHITE, circle=seed["kind"] == "artist"), ft.Container(a, right=4, bottom=4)], width=116, height=116),
                    txt(seed["name"], size=12, bold=True, lines=1, width=116),
                    txt(seed["sub"], size=10, color=TEXT_2, lines=1, width=116),
                ],
                spacing=6,
                tight=True,
            ),
            on_click=lambda e, s=seed: toggle(s),
        )

    def carousel(title: str, items: list[dict]) -> ft.Control:
        return ft.Column(
            [label(title), ft.Container(ft.Row([card(s) for s in items], spacing=14, scroll=ft.ScrollMode.HIDDEN), margin=ft.Margin.only(right=-GUTTER))],
            spacing=10,
        )

    def show_suggestions():
        data = state["suggestions"]
        if data is None:
            feed.content = skeleton_rows(4)
            return
        adders.clear()
        blocks = []
        for title, key, kind in (("Recently played", "recent_tracks", "track"), ("Your top tracks", "top_tracks", "track"), ("Your top artists", "top_artists", "artist")):
            items = [seed_of(x, kind) for x in data.get(key, [])]
            if items:
                blocks.append(carousel(title, items))
        playlists = [
            {"url": p["url"], "name": p["name"], "image": p.get("image"), "kind": "playlist", "sub": f"{p.get('tracks_total', 0)} tracks"}
            for p in state.get("playlists") or []
        ]
        if playlists:
            blocks.append(carousel("Your playlists", playlists))
        feed.content = ft.Column(blocks, spacing=24) if blocks else empty_state(ft.Icons.SEARCH, "Search to add seeds", "", accent)

    def show_results():
        data = state["results"] or {}
        adders.clear()
        items: list[dict] = []
        f = state["filter"]
        if f in ("all", "tracks"):
            items += [seed_of(x, "track") for x in data.get("tracks", [])]
        if f in ("all", "artists"):
            items += [seed_of(x, "artist") for x in data.get("artists", [])]
        if f in ("all", "albums"):
            items += [seed_of(x, "album") for x in data.get("albums", [])]
        if f == "all":
            items.sort(key=lambda s: {"artist": 0, "track": 1, "album": 2}[s["kind"]])
        feed.content = ft.Column([filters, *[result_row(s) for s in items]] if items else [filters, empty_state(ft.Icons.SEARCH_OFF, "No matches", "", TEXT_3)], spacing=4)

    async def run_search(query: str):
        await asyncio.sleep(0.35)
        feed.content = skeleton_rows(5)
        feed.update()
        try:
            state["results"] = await app.api.search(query)
        except ApiError as exc:
            app.toast(exc.message, "error")
            return
        show_results()
        paint_adders()
        view.update()

    def on_query(value: str):
        task = state["search_task"]
        if task:
            task.cancel()
        if not value:
            state["results"] = None
            show_suggestions()
            paint_adders()
            view.update()
            return
        state["search_task"] = spawn(run_search(value))

    def on_filter(value):
        state["filter"] = value
        show_results()
        paint_adders()
        view.update()

    async def add_pasted(text: str):
        kind, _ = spotify_kind(text)
        url = normalize(text)
        if not url:
            app.toast("Clipboard has no Spotify link", "error")
            return
        search.value = ""
        toggle({"url": url, "name": f"Pasted {kind}", "image": None, "kind": kind, "sub": "link"})

    search = Field("", "", "Search tracks, artists, albums", accent=accent, prefix_icon=ft.Icons.SEARCH, on_change=on_query)
    search.box.content.controls.append(ft.Container(paste_button(app, search, None, add_pasted), padding=ft.Padding.only(right=6)))
    filters = Segmented([("all", "All"), ("tracks", "Tracks"), ("artists", "Artists"), ("albums", "Albums")], "all", on_filter, accent, app.select, dense=True)

    def open_sheet(e):
        name = Field("Playlist name", "Fusion Mix", accent=accent)
        count = CountPicker("Tracks", 30, 5, 100, accent=accent, haptic=app.select)

        async def go(ev):
            go_btn.set_busy(True)
            try:
                data = await app.api.fusion([s["url"] for s in seeds], name.value or "Fusion Mix", count.value)
            except ApiError as exc:
                go_btn.set_busy(False)
                app.toast(exc.message, "error")
                return
            app.page.pop_dialog()
            result.show(
                app,
                "Fused",
                f"{data.get('track_count', 0)} tracks from {len(seeds)} seeds",
                " + ".join(s["name"] for s in seeds[:4]),
                accent,
                data.get("playlist_url"),
                tracks=data.get("tracks"),
                total=data.get("track_count"),
            )
            await view.list.scroll_to(offset=0, duration=500)

        go_btn = BrutalButton("Fuse now", ft.Icons.HUB, go, accent=accent, haptic=app.thud)
        sheet = ft.BottomSheet(
            ft.Container(
                ft.Column([ft.Row([label("Fusion settings", WHITE), txt(f"{len(seeds)} seeds", size=11, color=accent, bold=True)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), name, count, go_btn], spacing=18, tight=True),
                padding=ft.Padding.only(left=GUTTER, right=GUTTER, top=24, bottom=30),
                border=ft.Border.only(top=ft.BorderSide(2, accent)),
            ),
            bgcolor=SURFACE,
            shape=ft.RoundedRectangleBorder(radius=0),
            scrollable=True,
        )
        app.page.show_dialog(sheet)

    fuse = BrutalButton("Add seeds to fuse", ft.Icons.HUB, open_sheet, accent=accent, haptic=app.thud)
    fuse.set_enabled(False)

    async def ready():
        suggestions, playlists = await asyncio.gather(app.api.fusion_suggestions(), app.api.playlists(0, 20), return_exceptions=True)
        state["suggestions"] = suggestions if isinstance(suggestions, dict) else {}
        state["playlists"] = playlists.get("playlists", []) if isinstance(playlists, dict) else []
        if state["results"] is None:
            show_suggestions()
            paint_adders()
            view.update()

    view = Screen(
        app,
        "/fusion",
        [
            *header(app, feature.title, "Collect up to ten seeds: tracks, artists, albums, playlists or pasted links. Songs that bridge several seeds win.", accent, feature.icon, number_of(feature.key)),
            result,
            search,
            tray_box,
            feed,
        ],
        accent=accent,
        footer=fuse,
        on_ready=ready,
    )
    return view


