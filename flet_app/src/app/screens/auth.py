import asyncio
from urllib.parse import urlparse

import flet as ft

from app.api import ApiError, parse_callback, redirect_uri_of
from app.theme import BLACK, BORDER_DIM, GREEN, GUTTER, SURFACE, TEXT_2, WHITE
from app.ui.widgets import BrutalButton, Field, IconSquare, border, label, spawn, txt

SUCCESS_PAGE = (
    "<html><body style='background:#000;color:#fff;font-family:monospace;display:flex;"
    "align-items:center;justify-content:center;height:100vh;margin:0;flex-direction:column'>"
    "<div style='background:#1db954;color:#000;padding:18px 26px;border:3px solid #fff;"
    "box-shadow:6px 6px 0 #fff;font-size:22px;font-weight:bold'>MULTISPOT CONNECTED</div>"
    "<p style='opacity:.6;margin-top:28px'>Go back to the app.</p></body></html>"
)


class LoopbackCatcher:
    def __init__(self, redirect_uri: str, on_hit):
        parsed = urlparse(redirect_uri)
        self.host = parsed.hostname or "127.0.0.1"
        self.port = parsed.port or 80
        self.path = parsed.path or "/"
        self.on_hit = on_hit
        self.server: asyncio.base_events.Server | None = None

    async def start(self) -> bool:
        if self.host not in ("127.0.0.1", "localhost"):
            return False
        try:
            self.server = await asyncio.start_server(self._handle, self.host, self.port)
        except OSError:
            return False
        return True

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            line = (await reader.readline()).decode(errors="ignore")
            target = line.split(" ")[1] if line.count(" ") >= 2 else ""
            while (await reader.readline()) not in (b"\r\n", b"\n", b""):
                pass
            body = SUCCESS_PAGE.encode()
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
            await writer.drain()
            if target.startswith(self.path) and ("code=" in target or "error=" in target):
                await self.on_hit(f"http://{self.host}:{self.port}{target}")
        finally:
            writer.close()

    def close(self):
        if self.server:
            self.server.close()
            self.server = None


class AuthView(ft.View):
    def __init__(self, app, authorize_url: str):
        self.app = app
        self.authorize_url = authorize_url
        self.redirect_uri = redirect_uri_of(authorize_url) or ""
        self.done = False
        self.catcher: LoopbackCatcher | None = None
        self.status = txt("Waiting for Spotify", size=12, color=TEXT_2, upper=True, spacing=1.2, bold=True)
        self.progress = ft.ProgressBar(color=GREEN, bgcolor=SURFACE, bar_height=3, value=None)
        self.use_webview = app.mobile
        bar = ft.Container(
            ft.Row(
                [
                    IconSquare(ft.Icons.CLOSE, self._close, haptic=app.tap),
                    ft.Column([label("Spotify login", WHITE), self.status], spacing=2, tight=True, expand=True),
                    IconSquare(ft.Icons.OPEN_IN_BROWSER, self._external, tooltip="Open in browser") if self.use_webview else ft.Container(),
                ],
                spacing=14,
            ),
            padding=ft.Padding.symmetric(horizontal=GUTTER, vertical=10),
        )
        self.slot = ft.Container(self._webview() if self.use_webview else self._desktop(), expand=True)
        super().__init__(
            route="/auth",
            controls=[ft.SafeArea(ft.Column([bar, self.progress, self.slot], spacing=0, expand=True), expand=True)],
            padding=0,
            bgcolor=BLACK,
            fullscreen_dialog=True,
        )

    def _webview(self) -> ft.Control:
        import flet_webview as fwv

        return fwv.WebView(
            url=self.authorize_url,
            bgcolor=BLACK,
            expand=True,
            on_page_started=self._web_event,
            on_url_change=self._web_event,
            on_page_ended=self._web_loaded,
            on_web_resource_error=self._web_event,
        )

    def _desktop(self) -> ft.Control:
        self.paste_field = Field("Or paste the redirect URL", hint="http://127.0.0.1:5173/callback?code=…", prefix_icon=ft.Icons.LINK, on_submit=self._submit_paste)
        steps = ft.Column(
            [
                self._step("01", "Browser opens Spotify", "Approve MultiSpot access."),
                self._step("02", "We catch the redirect", "Automatically, if port is free."),
                self._step("03", "Fallback", "Copy the final URL from the address bar and paste it below."),
            ],
            spacing=12,
        )
        return ft.ListView(
            [
                txt("Finish login in your browser", size=26, bold=True, height=1.1),
                steps,
                self.paste_field,
                BrutalButton("Use pasted URL", ft.Icons.CHECK, self._submit_paste, haptic=self.app.thud),
                BrutalButton("Reopen browser", ft.Icons.OPEN_IN_BROWSER, self._external, variant="ghost", haptic=self.app.tap),
            ],
            spacing=22,
            padding=ft.Padding.all(GUTTER),
        )

    def _step(self, n: str, title: str, body: str) -> ft.Control:
        return ft.Container(
            ft.Row(
                [
                    ft.Container(txt(n, size=12, bold=True, color=BLACK), bgcolor=GREEN, width=36, height=36, alignment=ft.Alignment.CENTER),
                    ft.Column([txt(title, size=13, bold=True), txt(body, size=11, color=TEXT_2)], spacing=2, tight=True, expand=True),
                ],
                spacing=14,
            ),
            border=border(BORDER_DIM),
            padding=12,
            bgcolor=SURFACE,
        )

    def enter(self):
        if not self.use_webview:
            spawn(self._start_desktop())

    def leave(self):
        if self.catcher:
            self.catcher.close()

    async def _start_desktop(self):
        self.catcher = LoopbackCatcher(self.redirect_uri, self._finish)
        listening = await self.catcher.start()
        self.status.value = "Listening for redirect" if listening else "Paste the redirect URL"
        self.update()
        await self.app.open_url(self.authorize_url)

    async def _external(self, e=None):
        self.app.tap()
        await self.app.open_url(self.authorize_url)
        if self.use_webview:
            self.use_webview = False
            self.slot.content = self._desktop()
            self.status.value = "Paste the redirect URL"
            self.progress.value = 0
            self.update()

    def _is_callback(self, url: str) -> bool:
        if not url:
            return False
        if self.redirect_uri and url.startswith(self.redirect_uri):
            return True
        host = urlparse(url).hostname or ""
        return "spotify.com" not in host and ("code=" in url or "error=" in url)

    async def _web_event(self, e):
        url = e.data if isinstance(e.data, str) else ""
        if self._is_callback(url):
            await self._finish(url)

    def _web_loaded(self, e):
        if not self.done:
            self.progress.value = 0
            self.status.value = "Log in and approve"
            self.update()

    async def _submit_paste(self, e=None):
        url = self.paste_field.value or await self.app.paste()
        if not self._is_callback(url):
            self.app.toast("That doesn't look like the callback URL", "error")
            return
        await self._finish(url)

    async def _finish(self, url: str):
        if self.done:
            return
        code, state, error = parse_callback(url)
        if error or not code or not state:
            self.app.toast(f"Spotify said: {error or 'missing code'}", "error")
            self.app.back()
            return
        self.done = True
        if self.catcher:
            self.catcher.close()
        self.progress.value = None
        self.status.value = "Exchanging token"
        self.status.color = GREEN
        self.update()
        try:
            user = await self.app.api.exchange(code, state)
        except ApiError as exc:
            self.done = False
            self.app.toast(exc.message, "error")
            self.app.back()
            return
        await self.app.signed_in(user)

    def _close(self, e):
        self.app.back()


