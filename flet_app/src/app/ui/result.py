import flet as ft

from app.theme import BLACK, BORDER_DIM, SURFACE, TEXT_2
from app.ui.motion import cascade, prime, prime_stamp, stamp
from app.ui.widgets import BrutalButton, border, cover, hard_shadow, spawn, txt


class ResultSlot(ft.Container):
    def __init__(self):
        super().__init__(animate_size=ft.Animation(420, ft.AnimationCurve.EASE_OUT_CUBIC))

    def show(
        self,
        app,
        title: str,
        headline: str,
        body: str,
        accent: str,
        url: str | None = None,
        stats: list[tuple[str, str]] | None = None,
        tracks: list[dict] | None = None,
        total: int | None = None,
    ):
        rows = track_rows(app, tracks or [], accent)
        card = result_card(app, title, headline, body, accent, url, stats, rows, (total or 0) - len(rows))
        prime_stamp(card)
        self.content = card
        self.update()
        spawn(self._land(app, card, rows))

    async def _land(self, app, card: ft.Control, rows: list[ft.Control]):
        import asyncio

        await asyncio.sleep(0.05)
        stamp(card)
        card.update()
        await asyncio.sleep(0.16)
        app.boom()
        if rows:
            await cascade(rows, start=0.12, step=0.045)

    def clear(self):
        self.content = None


def track_rows(app, tracks: list[dict], accent: str, limit: int = 10) -> list[ft.Control]:
    rows: list[ft.Control] = []
    for i, t in enumerate(tracks[:limit]):
        link = t.get("url")

        async def open_track(e, link=link):
            if link:
                app.tap()
                await app.open_url(link)

        row = ft.Container(
            ft.Row(
                [
                    txt(f"{i + 1:02d}", size=11, bold=True, color=accent, width=24),
                    cover(t.get("image"), 40, edge=None),
                    ft.Column(
                        [txt(t.get("name", ""), size=12, bold=True, lines=1), txt(", ".join(t.get("artists") or []), size=10, color=TEXT_2, lines=1)],
                        spacing=1,
                        tight=True,
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.Padding.symmetric(vertical=5, horizontal=6),
            border=ft.Border.only(bottom=ft.BorderSide(1, BORDER_DIM)),
            ink=True,
            on_click=open_track,
        )
        prime(row, dy=0, dx=0.18)
        rows.append(row)
    return rows


def result_card(
    app,
    title: str,
    headline: str,
    body: str,
    accent: str,
    url: str | None,
    stats: list[tuple[str, str]] | None,
    rows: list[ft.Control] | None = None,
    more: int = 0,
) -> ft.Container:
    stat_row = ft.Row(
        [
            ft.Container(
                ft.Column([txt(v, size=26, bold=True, color=accent, height=1), txt(k, size=10, color=TEXT_2, upper=True, bold=True, spacing=1)], spacing=4, tight=True),
                expand=True,
                padding=12,
                border=border(ft.Colors.with_opacity(0.4, accent)),
            )
            for k, v in (stats or [])
        ],
        spacing=10,
    )
    actions: list[ft.Control] = []
    if url:
        async def open_url(e):
            await app.open_url(url)

        async def share(e):
            await app.share(url)

        actions = [
            BrutalButton("Open in Spotify", ft.Icons.OPEN_IN_NEW, open_url, accent=accent, haptic=app.thud),
            BrutalButton("Share link", ft.Icons.SHARE, share, variant="ghost", haptic=app.tap, height=46),
        ]
    return ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(ft.Icon(ft.Icons.CHECK, color=BLACK, size=18), bgcolor=accent, width=30, height=30, alignment=ft.Alignment.CENTER),
                        txt(title, size=11, bold=True, upper=True, spacing=1.6, color=accent),
                    ],
                    spacing=10,
                ),
                txt(headline, size=24, bold=True, height=1.1),
                txt(body, size=12, color=TEXT_2, height=1.5) if body else ft.Container(),
                stat_row if stats else ft.Container(),
                ft.Column(rows, spacing=0) if rows else ft.Container(),
                txt(f"+ {more} more", size=11, color=TEXT_2, bold=True) if rows and more > 0 else ft.Container(),
                *actions,
            ],
            spacing=14,
        ),
        bgcolor=SURFACE,
        border=border(accent),
        shadow=hard_shadow(accent, 6),
        padding=20,
        margin=ft.Margin.only(right=6, bottom=6),
    )


