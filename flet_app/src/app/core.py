import asyncio

import flet as ft

from app.api import Api
from app.theme import BLACK, EASE, GREEN, RED, SPRING, SURFACE, WHITE
from app.ui.widgets import border, hard_shadow, spawn, txt

DEFAULT_SERVER = "https://multispot.bogo.edu.pl"
LEGACY_DEFAULT_SERVER = "http://127.0.0.1:8000"
LEGACY_PUBLIC_SERVER = "http://srv17.mikr.us:40354"
KEY_SERVER = "multispot.server"
KEY_SESSION = "multispot.session"

TOAST_STYLE = {
    "success": (GREEN, ft.Icons.CHECK),
    "error": (RED, ft.Icons.PRIORITY_HIGH),
    "info": (WHITE, ft.Icons.BOLT),
}


class Toaster:
    def __init__(self, app: "App"):
        self.app = app
        self.current: ft.Container | None = None
        self.task: asyncio.Task | None = None

    def show(self, message: str, kind: str = "info", seconds: float = 2.8):
        if self.task:
            self.task.cancel()
        self.task = spawn(self._run(message, kind, seconds))

    def _build(self, message: str, kind: str, seconds: float) -> tuple[ft.Container, ft.Container]:
        color, icon = TOAST_STYLE.get(kind, TOAST_STYLE["info"])
        timer = ft.Container(
            bgcolor=color,
            height=3,
            scale=ft.Scale(scale_y=1, scale_x=1, alignment=ft.Alignment.CENTER_LEFT),
            animate_scale=ft.Animation(int(seconds * 1000), ft.AnimationCurve.LINEAR),
        )
        body = ft.Container(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                ft.Icon(icon, color=BLACK, size=18),
                                bgcolor=color,
                                width=34,
                                height=34,
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Container(txt(message, size=13, bold=True, lines=3), expand=True),
                        ],
                        spacing=12,
                    ),
                    timer,
                ],
                spacing=10,
            ),
            bgcolor=SURFACE,
            border=border(color),
            shadow=hard_shadow(color, 5),
            padding=ft.Padding.only(left=12, right=14, top=12, bottom=0),
        )
        top = self.app.inset_top + 10
        holder = ft.Container(
            body,
            top=top,
            left=16,
            right=21,
            offset=ft.Offset(0, -2.2),
            rotate=ft.Rotate(-0.05),
            animate_offset=ft.Animation(620, SPRING),
            animate_rotation=ft.Animation(620, SPRING),
            animate_opacity=ft.Animation(260, EASE),
            on_click=lambda e: self.dismiss(),
        )
        return holder, timer

    async def _run(self, message: str, kind: str, seconds: float):
        page = self.app.page
        old = self.current
        if old:
            old.offset = ft.Offset(0, -2.2)
            old.opacity = 0
            old.update()
        holder, timer = self._build(message, kind, seconds)
        self.current = holder
        page.overlay.append(holder)
        page.update()
        await asyncio.sleep(0.02)
        holder.offset = ft.Offset(0, 0)
        holder.rotate = ft.Rotate(0)
        timer.scale = ft.Scale(scale_y=1, scale_x=0.001, alignment=ft.Alignment.CENTER_LEFT)
        page.update()
        try:
            await asyncio.sleep(seconds)
        finally:
            holder.offset = ft.Offset(0, -2.2)
            holder.opacity = 0
            try:
                holder.update()
            except Exception:
                pass
            await asyncio.sleep(0.4)
            for item in (old, holder):
                if item in page.overlay:
                    page.overlay.remove(item)
            if self.current is holder:
                self.current = None
            page.update()

    def dismiss(self):
        if self.task:
            self.task.cancel()


class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.haptics = ft.HapticFeedback()
        self.prefs = ft.SharedPreferences()
        self.clipboard = ft.Clipboard()
        self.launcher = ft.UrlLauncher()
        self.sharer = ft.Share()
        self.api = Api(DEFAULT_SERVER)
        self.user: dict | None = None
        self.toaster = Toaster(self)
        from app.ui.player import PlayerStore

        self.player = PlayerStore(self)

    @property
    def mobile(self) -> bool:
        return not self.page.web and self.page.platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS)

    @property
    def inset_top(self) -> float:
        media = self.page.media
        if media and media.padding:
            return media.padding.top or 0
        return 0

    async def boot(self):
        server = await self._pref(KEY_SERVER)
        if not server or server in (LEGACY_DEFAULT_SERVER, LEGACY_PUBLIC_SERVER):
            server = DEFAULT_SERVER
        session = await self._pref(KEY_SESSION)
        self.api = Api(server, session)
        self.api.on_session_change = lambda value: spawn(self._store_session(value))
        self.api.on_unauthorized = self._expired

    async def _pref(self, key: str) -> str | None:
        try:
            value = await self.prefs.get(key)
        except Exception:
            return None
        return value if isinstance(value, str) and value else None

    async def _store_session(self, value: str | None):
        try:
            if value:
                await self.prefs.set(KEY_SESSION, value)
            else:
                await self.prefs.remove(KEY_SESSION)
        except Exception:
            pass

    async def set_server(self, url: str):
        url = url.strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        await self.api.set_base_url(url)
        try:
            await self.prefs.set(KEY_SERVER, url)
        except Exception:
            pass
        return url

    def _haptic(self, name: str):
        async def run():
            try:
                await getattr(self.haptics, name)()
            except Exception:
                pass

        spawn(run())

    def tap(self, *_):
        self._haptic("light_impact")

    def select(self, *_):
        self._haptic("selection_click")

    def thud(self, *_):
        self._haptic("medium_impact")

    def boom(self, *_):
        self._haptic("heavy_impact")

    def buzz(self, *_):
        self._haptic("vibrate")

    def toast(self, message: str, kind: str = "info"):
        if kind == "success":
            self.boom()
        elif kind == "error":
            self.buzz()
        self.toaster.show(message, kind)

    async def open_url(self, url: str):
        try:
            await self.launcher.launch_url(url, mode=ft.LaunchMode.EXTERNAL_APPLICATION)
        except Exception:
            await self.launcher.launch_url(url)

    async def share(self, text: str):
        try:
            await self.sharer.share_text(text)
        except Exception:
            await self.clipboard.set(text)
            self.toast("Link copied", "info")

    async def paste(self) -> str:
        try:
            return (await self.clipboard.get() or "").strip()
        except Exception:
            return ""

    @staticmethod
    def _hook(view: ft.View, name: str):
        hook = getattr(view, name, None)
        if callable(hook):
            hook()

    def push(self, view: ft.View):
        self.page.views.append(view)
        self.page.update()
        self._hook(view, "enter")

    def _remove(self, view: ft.View):
        self.page.views.remove(view)
        self._hook(view, "leave")

    def back(self, *_):
        if len(self.page.views) > 1:
            self._remove(self.page.views[-1])
            self.page.update()

    def root(self, view: ft.View):
        for old in list(self.page.views):
            self._remove(old)
        self.page.views.append(view)
        self.page.update()
        self._hook(view, "enter")

    def on_view_pop(self, e: ft.ViewPopEvent):
        if len(self.page.views) <= 1:
            return
        target = e.view if e.view in self.page.views else self.page.views[-1]
        self._remove(target)
        self.page.update()

    def go(self, name: str, **kwargs):
        from app.screens import registry

        self.tap()
        self.push(registry.build(self, name, **kwargs))

    def show_home(self):
        from app.screens.home import home_view

        self.player.start()
        self.root(home_view(self))

    def show_login(self):
        from app.screens.login import login_view

        self.player.stop()
        self.root(login_view(self))

    def _expired(self):
        if self.user is None:
            return
        self.user = None
        self.toast("Session expired, log in again", "error")
        self.show_login()

    async def logout(self):
        self.thud()
        try:
            await self.api.logout()
        except Exception:
            pass
        self.user = None
        self.show_login()

    async def signed_in(self, user: dict):
        self.user = user
        self.show_home()
        name = (user.get("display_name") or "").split(" ")[0]
        self.toast(f"Welcome, {name}" if name else "Logged in", "success")
