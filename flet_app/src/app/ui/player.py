import asyncio
import math
import time
from collections.abc import Callable

import flet as ft

from app.api import ApiError
from app.theme import BLACK, BORDER_DIM, EASE, EASE_SOFT, GREEN, SPRING, SURFACE, SURFACE_2, TEXT_2, TEXT_3, WHITE
from app.ui.widgets import IconSquare, border, cover, hard_shadow, label, mmss, spawn, txt

POLL_SECONDS = 5


class PlayerStore:
    def __init__(self, app):
        self.app = app
        self.track: dict | None = None
        self.is_playing = False
        self.loaded = False
        self.synced_at = 0.0
        self.base_progress = 0
        self.listeners: set[Callable[[str], None]] = set()
        self.task: asyncio.Task | None = None
        self.paused = False

    @property
    def progress_ms(self) -> int:
        if not self.track:
            return 0
        elapsed = (time.monotonic() - self.synced_at) * 1000 if self.is_playing else 0
        return int(min(self.track.get("duration_ms", 0), self.base_progress + elapsed))

    @property
    def fraction(self) -> float:
        if not self.track or not self.track.get("duration_ms"):
            return 0
        return self.progress_ms / self.track["duration_ms"]

    @property
    def track_url(self) -> str | None:
        return f"https://open.spotify.com/track/{self.track['id']}" if self.track and self.track.get("id") else None

    def subscribe(self, listener: Callable[[str], None]):
        self.listeners.add(listener)

    def unsubscribe(self, listener: Callable[[str], None]):
        self.listeners.discard(listener)

    def emit(self, reason: str):
        for listener in list(self.listeners):
            try:
                listener(reason)
            except Exception:
                self.listeners.discard(listener)

    def start(self):
        self.paused = False
        if not self.task or self.task.done():
            self.task = spawn(self._loop())

    def stop(self):
        if self.task:
            self.task.cancel()
        self.task = None
        self.track = None
        self.loaded = False

    def suspend(self, suspended: bool):
        self.paused = suspended
        if not suspended:
            spawn(self.refresh())

    async def _loop(self):
        ticks = 0
        while True:
            if not self.paused:
                if ticks % POLL_SECONDS == 0:
                    await self.refresh()
                elif self.is_playing:
                    if self.track and self.progress_ms >= self.track.get("duration_ms", 0):
                        await self.refresh()
                    else:
                        self.emit("tick")
            ticks += 1
            await asyncio.sleep(1)

    async def refresh(self):
        try:
            data = await self.app.api.now_playing()
        except ApiError as exc:
            if exc.unauthorized:
                self.stop()
            return
        previous = self.track["id"] if self.track else None
        self.loaded = True
        if data.get("playing"):
            self.track = data["track"]
            self.is_playing = bool(data.get("is_playing"))
            self.base_progress = self.track.get("progress_ms", 0)
        else:
            self.track = None
            self.is_playing = False
            self.base_progress = 0
        self.synced_at = time.monotonic()
        current = self.track["id"] if self.track else None
        self.emit("track" if current != previous else "state")

    async def toggle(self, *_):
        if not self.track:
            return
        self.app.thud()
        self.base_progress = self.progress_ms
        self.synced_at = time.monotonic()
        self.is_playing = not self.is_playing
        self.emit("state")
        try:
            await self.app.api.playback("play" if self.is_playing else "pause")
        except ApiError as exc:
            self.is_playing = not self.is_playing
            self.emit("state")
            self.app.toast(_playback_error(exc), "error")
        await asyncio.sleep(0.7)
        await self.refresh()

    async def jump(self, direction: int):
        if not self.track:
            return
        self.app.thud()
        self.emit("next" if direction > 0 else "prev")
        try:
            await self.app.api.playback("skip" if direction > 0 else "previous")
        except ApiError as exc:
            self.app.toast(_playback_error(exc), "error")
        await asyncio.sleep(0.6)
        await self.refresh()


def _playback_error(exc: ApiError) -> str:
    if exc.status >= 500 or exc.status == 404:
        return "No active Spotify device (Premium needed)"
    return exc.message


class ProgressLine(ft.Container):
    def __init__(self, height: float = 3, color: str = GREEN, track: str = SURFACE_2):
        self.done = ft.Container(bgcolor=color, height=height, expand=0)
        self.rest = ft.Container(height=height, expand=1000)
        super().__init__(content=ft.Row([self.done, self.rest], spacing=0), bgcolor=track, height=height)

    def show(self, fraction: float, smooth: bool = True):
        filled = int(max(0.0, min(1.0, fraction)) * 1000)
        self.done.expand = filled
        self.done.visible = filled > 0
        self.rest.expand = 1000 - filled
        self.rest.visible = filled < 1000


class MiniPlayer(ft.GestureDetector):
    def __init__(self, app):
        self.app = app
        self.store = app.player
        self.progress = ProgressLine()
        self.dot = ft.Container(width=7, height=7, bgcolor=GREEN, shape=ft.BoxShape.CIRCLE, animate_opacity=ft.Animation(900, EASE))
        self.title = txt("", size=13, bold=True, lines=1)
        self.subtitle = txt("", size=11, color=TEXT_2, lines=1)
        self.art_slot = ft.Container(width=48, height=48)
        self.info = ft.Container(
            ft.Column([ft.Row([self.dot, ft.Container(self.title, expand=True)], spacing=8), self.subtitle], spacing=2, tight=True),
            expand=True,
            animate_offset=ft.Animation(260, EASE),
            animate_opacity=ft.Animation(200, EASE),
        )
        self.play = IconSquare(ft.Icons.PLAY_ARROW, self.store.toggle, size=42, bg=GREEN, fg=BLACK, edge=BLACK, depth=2)
        self.skip = IconSquare(ft.Icons.SKIP_NEXT, lambda e: self.store.jump(1), size=42, depth=2)
        self.filled = ft.Row(
            [self.art_slot, self.info, self.play, self.skip],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.empty = ft.Row(
            [
                ft.Container(ft.Icon(ft.Icons.MUSIC_OFF, color=TEXT_3, size=20), width=48, height=48, border=border(BORDER_DIM), alignment=ft.Alignment.CENTER),
                ft.Column(
                    [txt("Nothing playing", size=13, bold=True, upper=True, spacing=1), txt("Start Spotify on any device", size=11, color=TEXT_2)],
                    spacing=2,
                    tight=True,
                    expand=True,
                ),
                ft.Icon(ft.Icons.REFRESH, color=TEXT_2, size=18),
            ],
            spacing=12,
        )
        self.body = ft.Container(
            ft.Column([ft.Container(self.filled, padding=ft.Padding.all(10)), self.progress], spacing=0),
            bgcolor=SURFACE,
            border=border(WHITE),
            shadow=hard_shadow(GREEN, 5),
        )
        self.shell = ft.Container(
            self.body,
            offset=ft.Offset(0, 1.6),
            opacity=0,
            animate_offset=ft.Animation(700, SPRING),
            animate_opacity=ft.Animation(300, EASE),
            padding=ft.Padding.only(right=5, bottom=5),
        )
        super().__init__(
            content=self.shell,
            on_tap=self._open,
            on_horizontal_drag_end=self._swipe,
            mouse_cursor=ft.MouseCursor.CLICK,
        )
        self.track_id: str | None = "__init__"

    def did_mount(self):
        self.store.subscribe(self._on_store)
        self._render("track", initial=True)

    def will_unmount(self):
        self.store.unsubscribe(self._on_store)

    def _on_store(self, reason: str):
        self._render(reason)

    def _render(self, reason: str, initial: bool = False):
        store = self.store
        if reason in ("next", "prev"):
            self.info.offset = ft.Offset(-0.25 if reason == "next" else 0.25, 0)
            self.info.opacity = 0
            self.update()
            return
        if not store.loaded:
            return
        self.shell.offset = ft.Offset(0, 0)
        self.shell.opacity = 1
        track = store.track
        if reason == "track" or initial or self.info.opacity == 0:
            tid = track["id"] if track else None
            if tid != self.track_id or initial:
                self.track_id = tid
                self.body.content.controls[0].content = self.filled if track else self.empty
                if track:
                    self.title.value = track["name"]
                    self.subtitle.value = ", ".join(track.get("artists", []))
                    self.art_slot.content = ft.Hero(tag="np-art", content=cover(track.get("image"), 48))
            self.info.offset = ft.Offset(0, 0)
            self.info.opacity = 1
        self.play.set_icon(ft.Icons.PAUSE if store.is_playing else ft.Icons.PLAY_ARROW)
        self.dot.opacity = (0.25 if self.dot.opacity == 1 else 1) if store.is_playing else 0.25
        self.progress.show(store.fraction, smooth=reason == "tick")
        try:
            self.update()
        except Exception:
            pass

    async def _open(self, e):
        if not self.store.loaded:
            return
        if not self.store.track:
            self.app.tap()
            await self.store.refresh()
            return
        self.app.tap()
        self.app.push(player_view(self.app))

    async def _swipe(self, e: ft.DragEndEvent):
        velocity = e.primary_velocity or 0
        if abs(velocity) < 250 or not self.store.track:
            return
        await self.store.jump(1 if velocity < 0 else -1)


def player_view(app) -> ft.View:
    store = app.player
    backdrop = ft.Container(expand=True, animate_opacity=ft.Animation(600, EASE), opacity=0.55)
    vinyl_grooves = ft.Container(
        width=300,
        height=300,
        shape=ft.BoxShape.CIRCLE,
        gradient=ft.SweepGradient(
            colors=[BLACK, "#1A1A1A", BLACK, "#222222", BLACK, "#1A1A1A", BLACK],
        ),
        border=ft.Border.all(2, "#262626"),
        content=ft.Container(
            width=96,
            height=96,
            shape=ft.BoxShape.CIRCLE,
            bgcolor=GREEN,
            border=ft.Border.all(3, BLACK),
            content=ft.Container(width=12, height=12, shape=ft.BoxShape.CIRCLE, bgcolor=BLACK),
            alignment=ft.Alignment.CENTER,
        ),
        alignment=ft.Alignment.CENTER,
    )
    vinyl = ft.Container(
        vinyl_grooves,
        rotate=ft.Rotate(0),
        animate_rotation=ft.Animation(1000, ft.AnimationCurve.LINEAR),
        offset=ft.Offset(0, 0),
        animate_offset=ft.Animation(900, SPRING),
    )
    art_slot = ft.Container(width=280, height=280)
    art_box = ft.Container(
        art_slot,
        shadow=hard_shadow(GREEN, 8),
        border=border(WHITE, 3),
        animate_scale=ft.Animation(500, SPRING),
        scale=1,
    )
    title = txt("", size=24, bold=True, lines=2, height=1.15)
    artists = txt("", size=14, color=TEXT_2, lines=1)
    album = txt("", size=11, color=TEXT_3, upper=True, spacing=1, lines=1)
    meta = ft.Container(
        ft.Column([title, artists, album], spacing=6),
        animate_offset=ft.Animation(320, EASE_SOFT),
        animate_opacity=ft.Animation(260, EASE),
    )
    progress = ProgressLine(height=6, track=SURFACE_2)
    elapsed = txt("0:00", size=11, color=TEXT_2)
    total = txt("0:00", size=11, color=TEXT_2)
    play = IconSquare(ft.Icons.PLAY_ARROW, store.toggle, size=84, bg=GREEN, fg=BLACK, edge=BLACK, depth=6, icon_size=42)
    prev = IconSquare(ft.Icons.SKIP_PREVIOUS, lambda e: store.jump(-1), size=64, depth=4, icon_size=30)
    nxt = IconSquare(ft.Icons.SKIP_NEXT, lambda e: store.jump(1), size=64, depth=4, icon_size=30)
    state = {"id": None, "spin": 0.0, "queue_req": 0}
    upnext = ft.Column(spacing=2)
    upnext_box = ft.Container(animate_size=ft.Animation(420, EASE), clip_behavior=ft.ClipBehavior.HARD_EDGE)

    async def load_queue():
        state["queue_req"] += 1
        token = state["queue_req"]
        await asyncio.sleep(0.6)
        try:
            data = await app.api.queue()
        except ApiError:
            data = {}
        if token != state["queue_req"]:
            return
        items = (data.get("queue") or [])[:6]
        rows = []
        for i, t in enumerate(items):
            row = ft.Container(
                ft.Row(
                    [
                        txt(f"{i + 1:02d}", size=10, bold=True, color=GREEN, width=22),
                        cover(t.get("image"), 36, edge=None),
                        ft.Column([txt(t.get("name", ""), size=12, bold=True, lines=1), txt(", ".join(t.get("artists") or []), size=10, color=TEXT_2, lines=1)], spacing=1, tight=True, expand=True),
                    ],
                    spacing=10,
                ),
                padding=ft.Padding.symmetric(vertical=4),
                opacity=0,
                offset=ft.Offset(0.2, 0),
                animate_opacity=ft.Animation(260, EASE),
                animate_offset=ft.Animation(420, EASE_SOFT),
            )
            rows.append(row)
        upnext.controls = rows
        upnext_box.content = ft.Column([label("Up next", GREEN), upnext], spacing=10) if rows else None
        try:
            view.update()
        except Exception:
            return
        for row in rows:
            await asyncio.sleep(0.05)
            row.opacity = 1
            row.offset = ft.Offset(0, 0)
            try:
                row.update()
            except Exception:
                return

    def render(reason: str):
        track = store.track
        if reason in ("next", "prev"):
            meta.offset = ft.Offset(-0.3 if reason == "next" else 0.3, 0)
            meta.opacity = 0
            art_box.scale = 0.88
            view.update()
            return
        if track and track["id"] != state["id"]:
            state["id"] = track["id"]
            art_slot.content = ft.Hero(tag="np-art", content=cover(track.get("image"), 280, edge=None))
            backdrop.image = ft.DecorationImage(src=track["image"], fit=ft.BoxFit.COVER) if track.get("image") else None
            title.value = track["name"]
            artists.value = ", ".join(track.get("artists", []))
            album.value = track.get("album", "")
            total.value = mmss(track.get("duration_ms", 0))
            spawn(load_queue())
        meta.offset = ft.Offset(0, 0)
        meta.opacity = 1
        art_box.scale = 1
        if not track:
            title.value = "Nothing playing"
            artists.value = "Start Spotify on any device"
            album.value = ""
        playing = store.is_playing
        play.set_icon(ft.Icons.PAUSE if playing else ft.Icons.PLAY_ARROW)
        vinyl.offset = ft.Offset(0.32 if playing else 0.0, 0)
        if playing:
            state["spin"] += math.pi * 0.66
            vinyl.rotate = ft.Rotate(state["spin"])
        progress.show(store.fraction, smooth=reason == "tick")
        elapsed.value = mmss(store.progress_ms)
        try:
            view.update()
        except Exception:
            pass

    async def analyze(e):
        if store.track_url:
            app.go("track_stats", url=store.track_url)

    async def open_spotify(e):
        if store.track_url:
            app.tap()
            await app.open_url(store.track_url)

    def swipe_down(e: ft.DragEndEvent):
        if (e.primary_velocity or 0) > 450:
            app.tap()
            app.back()

    top = ft.Row(
        [
            IconSquare(ft.Icons.KEYBOARD_ARROW_DOWN, app.back, size=44, haptic=app.tap),
            label("Now playing", WHITE),
            IconSquare(ft.Icons.OPEN_IN_NEW, open_spotify, size=44),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    disc = ft.Container(
        ft.Stack([ft.Container(vinyl, left=-10, top=-10), art_box], width=300, height=300, clip_behavior=ft.ClipBehavior.NONE),
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding.only(right=60),
    )
    controls = ft.Row([prev, play, nxt], alignment=ft.MainAxisAlignment.CENTER, spacing=22, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    analyze_btn = ft.Container(
        ft.Row([ft.Icon(ft.Icons.QUERY_STATS, color=TEXT_2, size=16), label("Analyze this track")], spacing=8, tight=True),
        on_click=analyze,
        padding=ft.Padding.symmetric(vertical=10, horizontal=14),
        border=border(BORDER_DIM),
    )
    content = ft.Column(
        [
            top,
            ft.Container(height=8),
            disc,
            ft.Container(height=10),
            meta,
            ft.Column([progress, ft.Row([elapsed, total], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)], spacing=8),
            controls,
            ft.Row([analyze_btn], alignment=ft.MainAxisAlignment.CENTER),
            upnext_box,
        ],
        spacing=22,
        scroll=ft.ScrollMode.HIDDEN,
        expand=True,
    )
    layers = ft.Stack(
        [
            backdrop,
            ft.Container(expand=True, blur=ft.Blur(40, 40), gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=[ft.Colors.with_opacity(0.55, BLACK), ft.Colors.with_opacity(0.92, BLACK), BLACK],
            )),
            ft.SafeArea(ft.Container(content, padding=ft.Padding.symmetric(horizontal=22, vertical=12)), expand=True),
        ],
        expand=True,
    )

    class PlayerView(ft.View):
        def enter(self):
            store.subscribe(render)
            render("track")

        def leave(self):
            store.unsubscribe(render)

    view = PlayerView(
        route="/player",
        controls=[ft.GestureDetector(content=layers, on_vertical_drag_end=swipe_down, expand=True)],
        padding=0,
        bgcolor=BLACK,
        fullscreen_dialog=True,
    )
    return view
