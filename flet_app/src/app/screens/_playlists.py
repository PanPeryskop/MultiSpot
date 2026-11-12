import flet as ft

from app.api import ApiError
from app.theme import BLACK, BORDER_DIM, EASE, SPRING, SURFACE, TEXT_2, TEXT_3
from app.ui.widgets import BrutalButton, Field, border, cover, empty_state, hard_shadow, skeleton_rows, txt


class PlaylistRow(ft.Container):
    def __init__(self, item: dict, accent: str, on_toggle):
        self.item = item
        self.accent = accent
        self.marker_text = txt("", size=12, bold=True, color=BLACK)
        self.marker = ft.Container(
            self.marker_text,
            width=30,
            height=30,
            bgcolor=accent,
            alignment=ft.Alignment.CENTER,
            scale=0.001,
            rotate=ft.Rotate(-0.5),
            animate_scale=ft.Animation(420, SPRING),
            animate_rotation=ft.Animation(420, SPRING),
        )
        ring = ft.Container(width=30, height=30, border=border(BORDER_DIM))
        super().__init__(
            ft.Row(
                [
                    cover(item.get("image"), 52, edge=None, icon=ft.Icons.LIBRARY_MUSIC),
                    ft.Column(
                        [
                            txt(item.get("name") or "Untitled", size=13, bold=True, lines=1),
                            txt(f"{item.get('tracks_total', 0)} tracks · {item.get('owner') or ''}", size=11, color=TEXT_2, lines=1),
                        ],
                        spacing=3,
                        tight=True,
                        expand=True,
                    ),
                    ft.Stack([ring, self.marker], width=30, height=30),
                ],
                spacing=14,
            ),
            padding=10,
            bgcolor=SURFACE,
            border=border(BORDER_DIM),
            animate=ft.Animation(200, EASE),
            on_click=lambda e: on_toggle(self),
        )

    def mark(self, order: int | None):
        on = order is not None
        self.marker.scale = 1 if on else 0.001
        self.marker.rotate = ft.Rotate(0 if on else -0.5)
        self.marker_text.value = str(order) if on and order > 0 else ("✓" if on else "")
        self.border = border(self.accent if on else BORDER_DIM)
        self.shadow = hard_shadow(self.accent, 4) if on else None
        self.offset = ft.Offset(-0.012, -0.04) if on else ft.Offset(0, 0)
        self.animate_offset = ft.Animation(260, SPRING)


class PlaylistPicker(ft.Column):
    def __init__(self, app, accent: str, multi: bool, on_change):
        self.app = app
        self.accent = accent
        self.multi = multi
        self.handler = on_change
        self.rows: list[PlaylistRow] = []
        self.picked: list[PlaylistRow] = []
        self.total = 0
        self.query = ""
        self.search = Field("", "", "Filter your playlists", accent=accent, prefix_icon=ft.Icons.SEARCH, on_change=self._filter)
        self.list = ft.Column(spacing=10)
        self.more = BrutalButton("Load more", ft.Icons.EXPAND_MORE, self._more, variant="ghost", haptic=app.tap, height=46)
        self.more.visible = False
        self.body = ft.Container(skeleton_rows(6))
        super().__init__([self.search, self.body, self.more], spacing=14)

    async def load(self):
        try:
            data = await self.app.api.playlists(0)
        except ApiError as exc:
            self.body.content = empty_state(ft.Icons.WIFI_OFF, "Couldn't load playlists", exc.message, self.accent)
            self.update()
            return
        self.total = data.get("total", 0)
        self.rows = [PlaylistRow(p, self.accent, self._toggle) for p in data.get("playlists", [])]
        self.body.content = self.list
        self._render(animate=True)

    async def _more(self, e):
        self.more.set_busy(True)
        try:
            data = await self.app.api.playlists(len(self.rows))
        except ApiError as exc:
            self.app.toast(exc.message, "error")
            return
        finally:
            self.more.set_busy(False)
        self.rows += [PlaylistRow(p, self.accent, self._toggle) for p in data.get("playlists", [])]
        self._render()

    def _visible(self) -> list[PlaylistRow]:
        q = self.query.lower()
        return [r for r in self.rows if q in (r.item.get("name") or "").lower()] if q else self.rows

    def _render(self, animate: bool = False):
        visible = self._visible()
        if not visible:
            self.list.controls = [empty_state(ft.Icons.LIBRARY_MUSIC, "No playlists", "Nothing matches that filter." if self.query else "Your library is empty.", TEXT_3)]
        else:
            self.list.controls = visible
        if animate:
            for i, row in enumerate(visible[:10]):
                row.opacity = 0
                row.offset = ft.Offset(0.08, 0)
                row.animate_opacity = ft.Animation(300 + i * 60, EASE)
                row.animate_offset = ft.Animation(420 + i * 60, SPRING)
        self.more.visible = len(self.rows) < self.total and not self.query
        self.update()
        if animate:
            for row in visible[:10]:
                row.opacity = 1
                row.offset = ft.Offset(0, 0)
            self.update()

    def _filter(self, value: str):
        self.query = value
        self._render()

    def _toggle(self, row: PlaylistRow):
        self.app.select()
        if row in self.picked:
            self.picked.remove(row)
            row.mark(None)
        else:
            if not self.multi:
                for other in self.picked:
                    other.mark(None)
                self.picked = []
            self.picked.append(row)
        for i, r in enumerate(self.picked):
            r.mark(i + 1 if self.multi else 0)
        self.update()
        self.handler([r.item for r in self.picked])


