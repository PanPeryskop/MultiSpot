from collections.abc import Callable

import flet as ft

from app.theme import BLACK, GUTTER, TEXT_2, WHITE
from app.ui.motion import cascade, curtain, lift, prime
from app.ui.player import MiniPlayer
from app.ui.widgets import IconSquare, border, spawn, tag, txt


class Screen(ft.View):
    def __init__(
        self,
        app,
        route: str,
        controls: list[ft.Control],
        accent: str = WHITE,
        footer: ft.Control | None = None,
        player: bool = True,
        on_refresh: Callable | None = None,
        on_ready: Callable | None = None,
        wipe: bool = True,
        reveal: int = 14,
    ):
        self.app = app
        self.on_ready = on_ready
        self.revealing = controls[:reveal]
        for control in self.revealing:
            prime(control)
        bottom = 28 + (92 if player and not footer else 0) + (86 if footer else 0)
        self.list = ft.ListView(
            controls,
            padding=ft.Padding.only(left=GUTTER, right=GUTTER, top=12, bottom=bottom),
            spacing=22,
            expand=True,
        )
        body: ft.Control = self.list
        if on_refresh:
            body = ft.RefreshIndicator(self.list, on_refresh=on_refresh, color=BLACK, bgcolor=accent, stroke_width=3)
        dock_items: list[ft.Control] = []
        if footer:
            dock_items.append(footer)
        elif player:
            dock_items.append(MiniPlayer(app))
        layers: list[ft.Control] = [body]
        if dock_items:
            layers.append(
                ft.Container(
                    ft.Column(dock_items, spacing=10, tight=True),
                    left=0,
                    right=0,
                    bottom=0,
                    padding=ft.Padding.only(left=GUTTER - 4, right=GUTTER - 4, top=28, bottom=14),
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_CENTER,
                        end=ft.Alignment.BOTTOM_CENTER,
                        colors=[ft.Colors.with_opacity(0, BLACK), ft.Colors.with_opacity(0.92, BLACK), BLACK],
                        stops=[0, 0.35, 1],
                    ),
                )
            )
        self.curtain = curtain(accent) if wipe else None
        if self.curtain:
            layers.append(self.curtain)
        super().__init__(
            route=route,
            controls=[ft.SafeArea(ft.Stack(layers, expand=True), expand=True)],
            padding=0,
            bgcolor=BLACK,
        )

    def enter(self):
        if self.curtain:
            spawn(lift(self.curtain, 0.06))
        spawn(cascade(self.revealing, start=0.22 if self.curtain else 0.05))
        if self.on_ready:
            spawn(self.on_ready())


def header(app, title: str, subtitle: str, accent: str, icon: ft.IconData, number: str) -> list[ft.Control]:
    top = ft.Row(
        [
            IconSquare(ft.Icons.ARROW_BACK, app.back, haptic=app.tap),
            ft.Row([tag(number, accent), tag("tool", WHITE)], spacing=6, tight=True),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    badge = ft.Container(
        ft.Icon(icon, color=BLACK, size=30),
        width=64,
        height=64,
        bgcolor=accent,
        border=border(BLACK),
        alignment=ft.Alignment.CENTER,
        rotate=ft.Rotate(-0.06),
    )
    words = title.upper().split(" ")
    stacked = ft.Column(
        [txt(w, size=40 if len(w) < 9 else 32, bold=True, height=0.95, color=accent if i == len(words) - 1 else WHITE) for i, w in enumerate(words)],
        spacing=0,
        tight=True,
    )
    hero = ft.Row([stacked, badge], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START)
    return [top, hero, txt(subtitle, size=13, color=TEXT_2, height=1.5)]
