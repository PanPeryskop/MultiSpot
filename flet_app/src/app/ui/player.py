import asyncio
import math
import time
from collections.abc import Callable

import flet as ft

from app.api import ApiError
from app.theme import BLACK, BORDER_DIM, EASE, EASE_SOFT, GREEN, SPRING, SURFACE, SURFACE_2, TEXT_2, TEXT_3, WHITE
from app.ui.widgets import IconSquare, border, cover, hard_shadow, label, mmss, spawn, txt

POLL_SECONDS = 5
RED_SOFT = "#FF5C7A"


class PlayerStore:
    def __init__(self, app):
        self.app = app
        self.track: dict | None = None
        self.is_playing = False
        self.loaded = False
        self.synced_at = 0.0
        self.base_progress = 0
        self.listeners: set[Callable[[str], None]] = set()
        self.added: set[str] = set()
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

    async def seek(self, position_ms: int):
        if not self.track:
            return
        self.app.select()
        self.base_progress = max(0, min(position_ms, self.track.get("duration_ms", 0)))
        self.synced_at = time.monotonic()
        self.emit("state")
        try:
            await self.app.api.seek(self.base_progress)
        except ApiError as exc:
            self.app.toast(_playback_error(exc), "error")
        await asyncio.sleep(0.8)
        await self.refresh()

    async def more_like_this(self, *_):
        if not self.track or self.track.get("type") == "episode":
            self.app.toast("Play a song first", "error")
            return
        self.app.boom()
        self.app.toast(f"Finding tracks like {self.track.get('name', 'this')}…", "info")
        try:
            data = await self.app.api.more_like_this(15)
        except ApiError as exc:
            self.app.toast(_playback_error(exc), "error")
            return
        self.added |= set(data.get("ids") or [])
        self.app.toast(f"Added {data.get('added', 0)} similar tracks after your queue", "success")
        self.emit("queue")

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
    if "restriction" in exc.message.lower():
        return "Spotify blocked that right now, try again in a moment"
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
            on_long_press=self.store.more_like_this,
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
        width=262,
        height=262,
        shape=ft.BoxShape.CIRCLE,
        gradient=ft.SweepGradient(
            colors=[BLACK, "#1A1A1A", BLACK, "#222222", BLACK, "#1A1A1A", BLACK],
        ),
        border=ft.Border.all(2, "#262626"),
        content=ft.Container(
            width=84,
            height=84,
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
        animate_scale=ft.Animation(260, SPRING),
        scale=1,
    )
    art_slot = ft.Container(width=256, height=256)
    flash_icon = ft.Icon(ft.Icons.PAUSE, size=86, color=WHITE)
    flash = ft.Container(
        ft.Container(flash_icon, bgcolor=ft.Colors.with_opacity(0.55, BLACK), padding=18, border=border(WHITE)),
        alignment=ft.Alignment.CENTER,
        width=256,
        height=256,
        opacity=0,
        scale=0.6,
        animate_opacity=ft.Animation(260, EASE),
        animate_scale=ft.Animation(420, SPRING),
        ignore_interactions=True,
    )
    art_box = ft.Container(
        ft.Stack([art_slot, flash], width=256, height=256),
        shadow=hard_shadow(GREEN, 8),
        border=border(WHITE, 3),
        animate_scale=ft.Animation(500, SPRING),
        animate_offset=ft.Animation(460, SPRING),
        animate_rotation=ft.Animation(460, SPRING),
        offset=ft.Offset(0, 0),
        rotate=ft.Rotate(0),
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
    drag = {"on": False}

    def seek_start(e):
        drag["on"] = True
        app.tap()

    def seek_move(e):
        if store.track:
            elapsed.value = mmss(float(e.control.value or 0) * store.track.get("duration_ms", 0))
            elapsed.color = GREEN
            elapsed.update()

    async def seek_end(e):
        drag["on"] = False
        elapsed.color = TEXT_2
        if store.track:
            await store.seek(int(float(e.control.value or 0) * store.track.get("duration_ms", 0)))

    progress = ft.Slider(
        value=0,
        min=0,
        max=1,
        active_color=GREEN,
        inactive_color=SURFACE_2,
        thumb_color=WHITE,
        overlay_color=ft.Colors.with_opacity(0.2, GREEN),
        on_change_start=seek_start,
        on_change=seek_move,
        on_change_end=seek_end,
        padding=ft.Padding.symmetric(horizontal=0, vertical=6),
    )
    elapsed = txt("0:00", size=11, color=TEXT_2)
    total = txt("0:00", size=11, color=TEXT_2)
    play = IconSquare(ft.Icons.PLAY_ARROW, store.toggle, size=84, bg=GREEN, fg=BLACK, edge=BLACK, depth=6, icon_size=42)
    prev = IconSquare(ft.Icons.SKIP_PREVIOUS, lambda e: store.jump(-1), size=64, depth=4, icon_size=30)
    nxt = IconSquare(ft.Icons.SKIP_NEXT, lambda e: store.jump(1), size=64, depth=4, icon_size=30)
    state = {"id": None, "spin": 0.0, "queue_req": 0, "playing": False}
    swipe = {"dx": 0.0}
    scratch = {"on": False, "acc": 0.0, "base": 0, "pos": 0, "tick": 0}
    scratch_ms_per_px = 120
    bubble_time = txt("0:00", size=30, bold=True, color=WHITE, height=1)
    bubble_delta = txt("±0s", size=13, bold=True, color=GREEN)
    bubble = ft.Container(
        ft.Container(
            ft.Column([bubble_time, bubble_delta], spacing=2, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.with_opacity(0.85, BLACK),
            border=border(GREEN),
            shadow=hard_shadow(GREEN, 4),
            padding=ft.Padding.symmetric(horizontal=18, vertical=10),
        ),
        alignment=ft.Alignment.CENTER,
        width=256,
        height=256,
        opacity=0,
        scale=0.7,
        animate_opacity=ft.Animation(180, EASE),
        animate_scale=ft.Animation(320, SPRING),
        ignore_interactions=True,
    )

    def art_drag(e: ft.DragUpdateEvent):
        swipe["dx"] += e.primary_delta or 0
        art_box.animate_offset = None
        art_box.animate_rotation = None
        art_box.offset = ft.Offset(swipe["dx"] / 262, 0)
        art_box.rotate = ft.Rotate(swipe["dx"] / 262 * 0.22)
        art_box.update()

    async def art_release(e: ft.DragEndEvent):
        dx, swipe["dx"] = swipe["dx"], 0.0
        velocity = e.primary_velocity or 0
        direction = 1 if (dx < -110 or (dx < -60 and velocity < -900)) else -1 if (dx > 110 or (dx > 60 and velocity > 900)) else 0
        if direction and store.track:
            art_box.animate_offset = ft.Animation(240, EASE)
            art_box.animate_rotation = ft.Animation(240, EASE)
            art_box.offset = ft.Offset(-1.5 * direction, 0)
            art_box.rotate = ft.Rotate(-0.35 * direction)
            art_box.update()
            await asyncio.sleep(0.22)
            art_box.animate_offset = None
            art_box.animate_rotation = None
            art_box.offset = ft.Offset(1.5 * direction, 0)
            art_box.rotate = ft.Rotate(0.35 * direction)
            art_box.update()
            spawn(store.jump(direction))
            await asyncio.sleep(0.05)
        art_box.animate_offset = ft.Animation(520, SPRING)
        art_box.animate_rotation = ft.Animation(520, SPRING)
        art_box.offset = ft.Offset(0, 0)
        art_box.rotate = ft.Rotate(0)
        art_box.update()

    async def art_double(e):
        if not store.track:
            return
        flash_icon.icon = ft.Icons.PAUSE if store.is_playing else ft.Icons.PLAY_ARROW
        spawn(store.toggle())
        flash.opacity = 1
        flash.scale = 1
        art_box.scale = 0.92
        art_box.update()
        await asyncio.sleep(0.16)
        art_box.scale = 1
        art_box.update()
        await asyncio.sleep(0.45)
        flash.opacity = 0
        flash.scale = 0.6
        flash.update()

    def bubble_show(on: bool):
        bubble.opacity = 1 if on else 0
        bubble.scale = 1 if on else 0.7
        vinyl.scale = 1.05 if on else 1
        bubble.update()
        vinyl.update()

    def scratch_start(e: ft.DragStartEvent):
        if not store.track:
            return
        scratch.update(on=True, acc=0.0, base=store.progress_ms, pos=store.progress_ms, tick=0)
        drag["on"] = True
        vinyl.animate_rotation = None
        bubble_time.value = mmss(store.progress_ms)
        bubble_delta.value = "±0s"
        bubble_show(True)
        app.thud()

    def scratch_move(e: ft.DragUpdateEvent):
        if not scratch["on"] or not store.track:
            return
        step = e.primary_delta
        if step is None and e.local_delta:
            step = e.local_delta.y
        step = step or 0
        scratch["acc"] += step
        duration = store.track.get("duration_ms", 0) or 1
        scratch["pos"] = int(max(0, min(duration - 1500, scratch["base"] + scratch["acc"] * scratch_ms_per_px)))
        shift = (scratch["pos"] - scratch["base"]) // 1000
        if shift // 5 != scratch["tick"]:
            scratch["tick"] = shift // 5
            app.select()
        vinyl.rotate = ft.Rotate(state["spin"] + scratch["acc"] / 60)
        elapsed.value = mmss(scratch["pos"])
        elapsed.color = GREEN
        progress.value = scratch["pos"] / duration
        bubble_time.value = mmss(scratch["pos"])
        bubble_delta.value = f"{'+' if shift >= 0 else '−'}{abs(shift)}s"
        bubble_delta.color = GREEN if shift >= 0 else RED_SOFT
        vinyl.update()
        elapsed.update()
        progress.update()
        bubble.update()

    async def scratch_end(e):
        if not scratch["on"]:
            return
        scratch["on"] = False
        drag["on"] = False
        state["spin"] += scratch["acc"] / 60
        vinyl.animate_rotation = ft.Animation(1000, ft.AnimationCurve.LINEAR)
        elapsed.color = TEXT_2
        bubble_show(False)
        if abs(scratch["pos"] - scratch["base"]) >= 1000:
            app.boom()
            await store.seek(scratch["pos"])

    def track_sheet(t: dict):
        link = t.get("url")

        async def act(kind: str):
            app.page.pop_dialog()
            if not link:
                return
            if kind == "xray":
                app.go("track_stats", url=link)
            elif kind == "radio":
                app.go("track_to_playlist", url=link)
            elif kind == "open":
                await app.open_url(link)
            else:
                app.toast(f"Finding tracks like {t.get('name', 'this')}…", "info")
                try:
                    data = await app.api.more_like_this(15, link)
                except ApiError as exc:
                    app.toast(_playback_error(exc), "error")
                    return
                store.added |= set(data.get("ids") or [])
                app.toast(f"Added {data.get('added', 0)} similar tracks after your queue", "success")
                spawn(load_queue())

        def option(icon: ft.IconData, text: str, color: str, kind: str) -> ft.Control:
            async def tapped(e):
                app.tap()
                await act(kind)

            return ft.Container(
                ft.Row(
                    [
                        ft.Container(ft.Icon(icon, size=18, color=BLACK), width=38, height=38, bgcolor=color, border=border(BLACK), alignment=ft.Alignment.CENTER),
                        txt(text, size=13, bold=True, upper=True, spacing=0.8, expand=True),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXT_3, size=20),
                    ],
                    spacing=14,
                ),
                padding=ft.Padding.symmetric(vertical=8),
                ink=True,
                on_click=tapped,
            )

        sheet = ft.BottomSheet(
            ft.Container(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(cover(t.get("image"), 60, edge=WHITE), shadow=hard_shadow(GREEN, 4)),
                                ft.Column([txt(t.get("name", ""), size=16, bold=True, lines=2), txt(", ".join(t.get("artists") or []), size=12, color=TEXT_2, lines=1)], spacing=4, tight=True, expand=True),
                            ],
                            spacing=14,
                        ),
                        ft.Container(height=1, bgcolor=BORDER_DIM),
                        option(ft.Icons.AUTO_AWESOME, "Queue more like this", GREEN, "more"),
                        option(ft.Icons.RADIO, "Build a radio from it", "#8F87FF", "radio"),
                        option(ft.Icons.QUERY_STATS, "X-ray this track", "#B8F25C", "xray"),
                        option(ft.Icons.OPEN_IN_NEW, "Open in Spotify", WHITE, "open"),
                    ],
                    spacing=10,
                    tight=True,
                ),
                padding=ft.Padding.only(left=22, right=22, top=22, bottom=30),
                border=ft.Border.only(top=ft.BorderSide(2, GREEN)),
            ),
            bgcolor=SURFACE,
            shape=ft.RoundedRectangleBorder(radius=0),
        )
        app.thud()
        app.page.show_dialog(sheet)
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
        items = (data.get("queue") or [])[:20]
        rows = []
        for i, t in enumerate(items):
            row = ft.Container(
                ft.Row(
                    [
                        txt(f"{i + 1:02d}", size=10, bold=True, color=GREEN, width=22),
                        cover(t.get("image"), 36, edge=None),
                        *([ft.Container(txt("+", size=12, bold=True, color=BLACK), bgcolor=GREEN, width=18, height=18, alignment=ft.Alignment.CENTER)] if t.get("id") in store.added else []),
                        ft.Column([txt(t.get("name", ""), size=12, bold=True, lines=1), txt(", ".join(t.get("artists") or []), size=10, color=TEXT_2, lines=1)], spacing=1, tight=True, expand=True),
                    ],
                    spacing=10,
                ),
                padding=ft.Padding.symmetric(vertical=4, horizontal=4),
                opacity=0,
                offset=ft.Offset(0.2, 0),
                animate_opacity=ft.Animation(260, EASE),
                animate_offset=ft.Animation(420, EASE_SOFT),
                ink=True,
                on_click=lambda e, t=t: track_sheet(t),
                on_long_press=lambda e, t=t: track_sheet(t),
            )
            rows.append(row)
        upnext.controls = rows
        upnext_box.content = ft.Column([ft.Row([label("Up next", GREEN), txt("tap for options", size=10, color=TEXT_3)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), upnext], spacing=10) if rows else None
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
            art_slot.content = ft.Hero(tag="np-art", content=cover(track.get("image"), 256, edge=None))
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
        vinyl.offset = ft.Offset(0.27 if playing else 0.2, 0)
        if not scratch["on"]:
            if playing:
                vinyl.animate_rotation = ft.Animation(1000, ft.AnimationCurve.LINEAR if state["playing"] else ft.AnimationCurve.EASE_IN)
                state["spin"] += math.pi * 0.66
                vinyl.rotate = ft.Rotate(state["spin"])
            elif state["playing"]:
                vinyl.animate_rotation = ft.Animation(1600, ft.AnimationCurve.DECELERATE)
                state["spin"] += math.pi * 0.55
                vinyl.rotate = ft.Rotate(state["spin"])
        state["playing"] = playing
        if reason == "queue":
            spawn(load_queue())
        if not drag["on"]:
            progress.value = max(0.0, min(1.0, store.fraction))
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
        ft.Stack(
            [
                ft.Container(vinyl, left=0, top=1),
                ft.GestureDetector(
                    content=ft.Container(bgcolor=ft.Colors.TRANSPARENT, width=338, height=268),
                    on_vertical_drag_start=scratch_start,
                    on_vertical_drag_update=scratch_move,
                    on_vertical_drag_end=scratch_end,
                    on_horizontal_drag_start=scratch_start,
                    on_horizontal_drag_update=scratch_move,
                    on_horizontal_drag_end=scratch_end,
                    drag_interval=16,
                    left=0,
                    top=0,
                ),
                ft.GestureDetector(
                    content=art_box,
                    on_horizontal_drag_update=art_drag,
                    on_horizontal_drag_end=art_release,
                    on_double_tap=art_double,
                    drag_interval=16,
                ),
                ft.Container(bubble, left=0, top=0, ignore_interactions=True),
            ],
            width=338,
            height=268,
            clip_behavior=ft.ClipBehavior.NONE,
        ),
        alignment=ft.Alignment.CENTER,
    )
    controls = ft.Row([prev, play, nxt], alignment=ft.MainAxisAlignment.CENTER, spacing=22, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    more_btn = ft.Container(
        ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME, color=BLACK, size=16), txt("More like this", size=11, bold=True, upper=True, spacing=1, color=BLACK)], spacing=8, tight=True),
        on_click=store.more_like_this,
        padding=ft.Padding.symmetric(vertical=10, horizontal=14),
        bgcolor=GREEN,
        border=border(BLACK),
        shadow=hard_shadow(WHITE, 3),
        animate_scale=ft.Animation(160, SPRING),
        on_hover=lambda e: (setattr(e.control, "scale", 1.05 if e.data in (True, "true") else 1), e.control.update()),
    )
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
            ft.Row([analyze_btn, more_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True),
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
