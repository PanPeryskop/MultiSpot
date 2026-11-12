import asyncio
import random

import flet as ft

from app.theme import BLACK, ELASTIC, GREEN, GUTTER, SPRING, SURFACE, TEXT_2, TEXT_3, WHITE, YELLOW
from app.ui.marquee import Marquee
from app.ui.widgets import BrutalButton, Field, IconSquare, border, hard_shadow, label, spawn, txt


def kinetic_word(word: str, color: str, size: float = 76) -> tuple[ft.Row, list[ft.Container]]:
    letters = []
    for ch in word:
        letter = ft.Container(
            ft.Text(ch, size=size, color=color, font_family="MonoBold", style=ft.TextStyle(height=0.92)),
            offset=ft.Offset(0, -2.5),
            rotate=ft.Rotate(random.uniform(-0.6, 0.6)),
            opacity=0,
            animate_offset=ft.Animation(900, SPRING),
            animate_rotation=ft.Animation(1100, ELASTIC),
            animate_opacity=ft.Animation(260),
        )
        letters.append(letter)
    return ft.Row(letters, spacing=-4, tight=True), letters


def server_sheet(app) -> ft.BottomSheet:
    field = Field("Backend URL", app.api.base_url, "http://192.168.1.10:8000", keyboard=ft.KeyboardType.URL, prefix_icon=ft.Icons.DNS)
    status = txt("Phone and backend must share a network. Run uvicorn with --host 0.0.0.0.", size=11, color=TEXT_2, height=1.5)

    async def test(e):
        test_btn.set_busy(True)
        url = await app.set_server(field.value or app.api.base_url)
        ok = await app.api.ping()
        test_btn.set_busy(False)
        status.value = f"Connected to {url}" if ok else f"No answer from {url}"
        status.color = GREEN if ok else "#FF2D55"
        status.update()
        app.toast("Server reachable" if ok else "Server unreachable", "success" if ok else "error")

    async def save(e):
        await app.set_server(field.value or app.api.base_url)
        app.page.pop_dialog()
        app.toast("Server saved", "info")

    test_btn = BrutalButton("Test connection", ft.Icons.WIFI_TETHERING, test, variant="ghost", haptic=app.tap, height=46)
    save_btn = BrutalButton("Save", ft.Icons.CHECK, save, haptic=app.thud)
    return ft.BottomSheet(
        ft.Container(
            ft.Column(
                [
                    ft.Row([label("Connection", WHITE), ft.Icon(ft.Icons.DNS, color=GREEN, size=18)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    field,
                    status,
                    test_btn,
                    save_btn,
                ],
                spacing=18,
                tight=True,
            ),
            padding=ft.Padding.only(left=GUTTER, right=GUTTER, top=24, bottom=32),
            border=ft.Border.only(top=ft.BorderSide(2, WHITE)),
        ),
        bgcolor=SURFACE,
        shape=ft.RoundedRectangleBorder(radius=0),
        show_drag_handle=False,
    )


class LoginView(ft.View):
    def __init__(self, app):
        self.app = app
        multi, l1 = kinetic_word("MULTI", WHITE)
        spot, l2 = kinetic_word("SPOT", GREEN)
        self.letters = l1 + l2
        self.logo = ft.Container(
            txt("MS", size=22, bold=True, color=BLACK),
            width=64,
            height=64,
            bgcolor=GREEN,
            border=border(BLACK, 2),
            shadow=hard_shadow(WHITE, 4),
            alignment=ft.Alignment.CENTER,
            rotate=ft.Rotate(-0.12),
            scale=0.001,
            animate_scale=ft.Animation(800, ELASTIC),
            animate_rotation=ft.Animation(900, SPRING),
            on_click=self._spin_badge,
        )
        self.tagline = ft.Container(
            ft.Column(
                [
                    txt("Your Spotify.", size=22, bold=True),
                    ft.Container(
                        txt("Supercharged.", size=22, bold=True, color=BLACK),
                        bgcolor=YELLOW,
                        padding=ft.Padding.symmetric(horizontal=6),
                    ),
                    ft.Container(height=6),
                    txt("Random queues, playlist surgery, fusion recommendations and your musical DNA - in your pocket.", size=13, color=TEXT_2, height=1.55),
                ],
                spacing=4,
                tight=True,
            ),
            opacity=0,
            offset=ft.Offset(0, 0.3),
            animate_opacity=ft.Animation(600),
            animate_offset=ft.Animation(800, SPRING),
        )
        self.cta = BrutalButton("Continue with Spotify", ft.Icons.GRAPHIC_EQ, self._login, haptic=app.thud)
        self.cta_box = ft.Container(
            ft.Column(
                [
                    self.cta,
                    ft.Row(
                        [ft.Icon(ft.Icons.LOCK_OUTLINE, size=12, color=TEXT_3), txt("Credentials never touch this app", size=10, color=TEXT_3)],
                        spacing=6,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=14,
                tight=True,
            ),
            opacity=0,
            offset=ft.Offset(0, 0.6),
            animate_opacity=ft.Animation(500),
            animate_offset=ft.Animation(900, SPRING),
        )
        tape_a = Marquee("RANDOM HUB ✦ FUSION CENTER ✦ STATS HUB ✦ TIME MACHINE ✦ MAGIC ✦ ", size=13, bgcolor=GREEN, seconds=18, rotate=-0.05, intro_delay=1.0)
        tape_b = Marquee("QUEUE SETTER ✦ TRUE SHUFFLE ✦ TRACK RADIO ✦ TRACK X-RAY ✦ ", size=13, color=WHITE, bgcolor=BLACK, seconds=22, reverse=True, rotate=0.04, intro_delay=1.15)
        tapes = ft.Container(
            ft.Stack(
                [
                    ft.Container(ft.Container(tape_b, border=ft.Border.symmetric(vertical=ft.BorderSide(2, WHITE))), left=-30, right=-30, top=31),
                    ft.Container(ft.Container(tape_a, border=ft.Border.symmetric(vertical=ft.BorderSide(2, BLACK))), left=-30, right=-30, top=31),
                ],
                height=96,
                clip_behavior=ft.ClipBehavior.NONE,
            ),
            margin=ft.Margin.symmetric(horizontal=-GUTTER),
        )
        top = ft.Row(
            [self.logo, IconSquare(ft.Icons.TUNE, self._settings, haptic=app.tap, tooltip="Server")],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        content = ft.Column(
            [
                top,
                ft.Container(expand=True),
                ft.Column([multi, spot], spacing=-10, tight=True),
                ft.Container(height=8),
                self.tagline,
                ft.Container(expand=True),
                tapes,
                ft.Container(expand=True),
                self.cta_box,
            ],
            spacing=0,
            expand=True,
        )
        super().__init__(
            route="/login",
            controls=[ft.SafeArea(ft.Container(content, padding=ft.Padding.only(left=GUTTER, right=GUTTER, top=14, bottom=20)), expand=True)],
            padding=0,
            bgcolor=BLACK,
        )

    def enter(self):
        spawn(self._intro())

    async def _intro(self):
        await asyncio.sleep(0.15)
        self.logo.scale = 1
        self.logo.update()
        for letter in self.letters:
            await asyncio.sleep(0.065)
            letter.offset = ft.Offset(0, 0)
            letter.rotate = ft.Rotate(random.uniform(-0.04, 0.04))
            letter.opacity = 1
            letter.update()
            self.app.select()
        await asyncio.sleep(0.25)
        self.tagline.opacity = 1
        self.tagline.offset = ft.Offset(0, 0)
        self.tagline.update()
        await asyncio.sleep(0.18)
        self.cta_box.opacity = 1
        self.cta_box.offset = ft.Offset(0, 0)
        self.cta_box.update()

    def _spin_badge(self, e):
        self.app.thud()
        angle = self.logo.rotate.angle if isinstance(self.logo.rotate, ft.Rotate) else 0
        self.logo.rotate = ft.Rotate(angle + 6.283)
        self.logo.update()
        for letter in self.letters:
            letter.rotate = ft.Rotate(random.uniform(-0.25, 0.25))
        self.update()
        spawn(self._settle_letters())

    async def _settle_letters(self):
        await asyncio.sleep(0.12)
        for letter in self.letters:
            letter.rotate = ft.Rotate(random.uniform(-0.04, 0.04))
        self.update()

    def _settings(self, e):
        self.app.page.show_dialog(server_sheet(self.app))

    async def _login(self, e):
        from app.screens.auth import AuthView

        self.cta.set_busy(True)
        try:
            url = await self.app.api.authorize_url()
        except Exception as exc:
            self.cta.set_busy(False)
            self.app.toast(getattr(exc, "message", str(exc)), "error")
            self.app.page.show_dialog(server_sheet(self.app))
            return
        self.cta.set_busy(False)
        self.app.push(AuthView(self.app, url))


def login_view(app) -> ft.View:
    return LoginView(app)


def splash_view() -> ft.View:
    return ft.View(
        route="/splash",
        controls=[ft.Container(ft.Image(src="splash.png", width=256, height=256), expand=True, alignment=ft.Alignment.CENTER)],
        bgcolor=BLACK,
        padding=0,
    )
