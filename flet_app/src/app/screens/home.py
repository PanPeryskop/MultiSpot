import random
from datetime import datetime

import flet as ft

from app.screens.registry import FEATURES, Feature, number_of
from app.theme import BLACK, BORDER_DIM, GREEN, GUTTER, RED, SPRING, SURFACE, TEXT_2, TEXT_3, WHITE, YELLOW
from app.ui.marquee import Marquee
from app.ui.screen import Screen
from app.ui.widgets import BrutalButton, Pressable, border, cover, label, tag, txt


def greeting() -> str:
    hour = datetime.now().hour
    if hour < 5:
        return "Late night"
    if hour < 12:
        return "Morning"
    if hour < 18:
        return "Afternoon"
    return "Evening"


class Tile(Pressable):
    def __init__(self, app, feature: Feature, tilt: float, wide: bool = False, badge: str = "Featured"):
        self.app = app
        self.feature = feature
        self.tilt = tilt
        icon_box = ft.Container(
            ft.Icon(feature.icon, color=BLACK, size=24 if not wide else 30),
            width=46 if not wide else 58,
            height=46 if not wide else 58,
            bgcolor=feature.accent,
            border=border(BLACK),
            alignment=ft.Alignment.CENTER,
        )
        title = txt(feature.title.upper(), size=16 if not wide else 24, bold=True, lines=2, height=1.05)
        blurb = txt(feature.blurb, size=11, color=TEXT_2, lines=2, height=1.4)
        number = txt(number_of(feature.key), size=11, bold=True, color=TEXT_3)
        if wide:
            body = ft.Row(
                [
                    ft.Column([ft.Row([tag(badge, feature.accent, True), number], spacing=8), title, blurb], spacing=8, expand=True),
                    ft.Column([icon_box, ft.Icon(ft.Icons.NORTH_EAST, color=feature.accent, size=26)], horizontal_alignment=ft.CrossAxisAlignment.END, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ],
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        else:
            body = ft.Column(
                [
                    ft.Row([icon_box, number], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START),
                    ft.Container(expand=True),
                    title,
                    blurb,
                ],
                spacing=6,
            )
        face = ft.Container(body, bgcolor=SURFACE, border=border(WHITE), padding=16, height=150 if wide else 184)
        super().__init__(face, on_press=self._open, shadow=feature.accent, depth=5, haptic=app.tap, expand=True)
        self.holder.rotate = ft.Rotate(tilt)
        self.holder.animate_rotation = ft.Animation(420, SPRING)

    def _set_pressed(self, pressed: bool):
        self.holder.rotate = ft.Rotate(0 if pressed else self.tilt)
        super()._set_pressed(pressed)

    def _open(self, e):
        self.app.go(self.feature.key)


def profile_sheet(app) -> ft.BottomSheet:
    user = app.user or {}

    async def logout(e):
        app.page.pop_dialog()
        await app.logout()

    return ft.BottomSheet(
        ft.Container(
            ft.Column(
                [
                    ft.Row(
                        [
                            cover(user.get("image"), 64, icon=ft.Icons.PERSON),
                            ft.Column(
                                [
                                    txt(user.get("display_name") or "Spotify user", size=18, bold=True, lines=1),
                                    txt(user.get("email") or user.get("id") or "", size=11, color=TEXT_2, lines=1),
                                ],
                                spacing=4,
                                tight=True,
                                expand=True,
                            ),
                        ],
                        spacing=16,
                    ),
                    ft.Container(
                        ft.Row([ft.Icon(ft.Icons.DNS, size=16, color=GREEN), txt(app.api.base_url, size=11, color=TEXT_2, lines=1, expand=True)], spacing=10),
                        border=border(BORDER_DIM),
                        padding=12,
                    ),
                    BrutalButton("Log out", ft.Icons.LOGOUT, logout, variant="danger", accent=RED, haptic=app.thud),
                ],
                spacing=20,
                tight=True,
            ),
            padding=ft.Padding.only(left=GUTTER, right=GUTTER, top=26, bottom=32),
            border=ft.Border.only(top=ft.BorderSide(2, WHITE)),
        ),
        bgcolor=SURFACE,
        shape=ft.RoundedRectangleBorder(radius=0),
    )


def home_view(app) -> ft.View:
    user = app.user or {}
    first = (user.get("display_name") or "friend").split(" ")[0]
    badge = ft.Container(
        txt("MS", size=15, bold=True, color=BLACK),
        width=44,
        height=44,
        bgcolor=GREEN,
        border=border(BLACK),
        alignment=ft.Alignment.CENTER,
        rotate=ft.Rotate(-0.1),
        animate_rotation=ft.Animation(900, SPRING),
    )

    def spin(e):
        app.boom()
        badge.rotate = ft.Rotate(badge.rotate.angle + 6.2832)
        badge.update()

    badge.on_click = spin
    avatar = Pressable(
        ft.Container(cover(user.get("image"), 40, edge=None, icon=ft.Icons.PERSON), border=border(WHITE)),
        on_press=lambda e: app.page.show_dialog(profile_sheet(app)),
        depth=3,
        shadow=GREEN,
        haptic=app.tap,
    )
    top = ft.Row(
        [
            ft.Row([badge, ft.Column([label(greeting()), txt(first, size=16, bold=True, lines=1)], spacing=0, tight=True)], spacing=14, tight=True),
            avatar,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    headline = ft.Column(
        [
            txt("WHAT'S", size=46, bold=True, height=0.95),
            ft.Row(
                [
                    txt("THE", size=46, bold=True, height=0.95),
                    ft.Container(
                        txt("MOVE?", size=46, bold=True, color=BLACK, height=0.95),
                        bgcolor=YELLOW,
                        padding=ft.Padding.symmetric(horizontal=6),
                        rotate=ft.Rotate(-0.03),
                    ),
                ],
                spacing=12,
                tight=True,
            ),
        ],
        spacing=2,
        tight=True,
    )
    ticker = ft.Container(
        Marquee("TAP A TOOL ✦ SWIPE THE PLAYER TO SKIP ✦ PULL TO REFRESH ✦ ", size=12, bgcolor=GREEN, seconds=16, height=30),
        border=ft.Border.symmetric(vertical=ft.BorderSide(2, WHITE)),
        margin=ft.Margin.symmetric(horizontal=-GUTTER),
        rotate=ft.Rotate(-0.015),
    )
    tiles: list[ft.Control] = [ft.Row([Tile(app, FEATURES[0], 0, wide=True)])]
    rest = FEATURES[1:]
    rng = random.Random(7)
    for i in range(0, len(rest), 2):
        pair = rest[i : i + 2]
        if len(pair) == 1:
            tiles.append(ft.Row([Tile(app, pair[0], 0.012, wide=True, badge="New")]))
            continue
        tiles.append(ft.Row([Tile(app, f, rng.choice([-0.025, -0.015, 0.015, 0.025])) for f in pair], spacing=14, vertical_alignment=ft.CrossAxisAlignment.START))
    footer_note = ft.Row(
        [txt("MULTISPOT ✦ MOBILE", size=10, color=TEXT_3, bold=True), txt(f"{len(FEATURES)} TOOLS", size=10, color=TEXT_3, bold=True)],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    async def refresh(e):
        app.thud()
        try:
            app.user = await app.api.me()
        except Exception:
            pass
        await app.player.refresh()

    return Screen(
        app,
        "/",
        [top, headline, ticker, *tiles, footer_note],
        accent=GREEN,
        on_refresh=refresh,
        wipe=False,
    )


