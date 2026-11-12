
import flet as ft

from app.api import ApiError
from app.screens._shared import normalize, paste_button, spotify_kind
from app.screens.registry import number_of
from app.theme import BLACK, BORDER_DIM, RED, SURFACE, TEXT_2, TEXT_3, WHITE
from app.ui.motion import cascade, prime
from app.ui.screen import Screen, header
from app.ui.widgets import BrutalButton, Field, border, compact, cover, fill_meters, hard_shadow, label, meter, mmss, tag, txt


def tile(name: str, value: str, accent: str, extra: ft.Control | None = None) -> ft.Container:
    return ft.Container(
        ft.Column([label(name), txt(value, size=24, bold=True, color=accent, lines=1), extra or ft.Container()], spacing=6, tight=True),
        padding=14,
        bgcolor=SURFACE,
        border=border(BORDER_DIM),
        expand=True,
    )


def build(app, feature, url: str | None = None, **_) -> ft.View:
    accent = feature.accent
    link = Field("Track link", url or "", "open.spotify.com/track/…", accent=accent, keyboard=ft.KeyboardType.URL, prefix_icon=ft.Icons.LINK)
    output = ft.Column(spacing=16)

    async def analyze(e=None):
        if spotify_kind(link.value)[0] != "track":
            app.toast("Paste a Spotify track link", "error")
            return
        button.set_busy(True)
        try:
            data = await app.api.track_stats(normalize(link.value))
        except ApiError as exc:
            app.toast(exc.message, "error")
            return
        finally:
            button.set_busy(False)
        app.boom()
        sections = render(data)
        for s in sections:
            prime(s, dy=0.25)
        output.controls = sections
        output.update()
        await cascade(sections, start=0.02, step=0.07)
        fill_meters(output)
        output.update()

    def render(data: dict) -> list[ft.Control]:
        track, album, artists = data.get("track", {}), data.get("album", {}), data.get("artists", [])
        art = ft.Container(
            cover(album.get("image"), 132, edge=WHITE),
            shadow=hard_shadow(accent, 6),
            rotate=ft.Rotate(-0.04),
        )
        year = (album.get("release_date") or "")[:4] or "?"
        badges = [tag(year, accent)]
        if album.get("album_type"):
            badges.append(tag(album["album_type"], WHITE))
        if track.get("explicit"):
            badges.append(tag("explicit", RED))
        if track.get("playable") is False:
            badges.append(tag("not in your market", RED))
        hero = ft.Row(
            [
                art,
                ft.Column(
                    [
                        txt(track.get("name", ""), size=20, bold=True, lines=3, height=1.1),
                        txt(album.get("name", ""), size=12, color=TEXT_2, lines=2),
                        ft.Row(badges, spacing=6, run_spacing=6, wrap=True),
                    ],
                    spacing=8,
                    expand=True,
                ),
            ],
            spacing=18,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        pop = track.get("popularity")
        position = track.get("album_position")
        first_row = [tile("length", mmss(track.get("duration_ms", 0)), WHITE)]
        if pop is not None:
            first_row.insert(0, tile("popularity", f"{pop}", accent, meter(pop / 100, accent, 6)))
        else:
            first_row.insert(0, tile("position", f"{position}/{album.get('total_tracks', '?')}" if position else "?", accent))
        grid = ft.Column(
            [
                ft.Row(first_row, spacing=10),
                ft.Row([tile("album tracks", str(album.get("total_tracks") or "?"), WHITE), tile("released", album.get("release_date") or "?", WHITE)], spacing=10),
            ],
            spacing=10,
        )
        facts = [ft.Row([ft.Icon(ft.Icons.ALBUM, color=TEXT_2, size=16), txt(album.get("label") or "Unknown label", size=12, color=TEXT_2, lines=1, expand=True)], spacing=10)]
        if track.get("isrc"):
            facts.append(ft.Row([ft.Icon(ft.Icons.TAG, color=TEXT_2, size=16), txt(track["isrc"], size=12, color=TEXT_2, lines=1, expand=True)], spacing=10))
        if album.get("duration_ms"):
            facts.append(ft.Row([ft.Icon(ft.Icons.TIMER, color=TEXT_2, size=16), txt(f"Album runs {mmss(album['duration_ms'])}", size=12, color=TEXT_2, lines=1, expand=True)], spacing=10))
        if album.get("copyright"):
            facts.append(txt(album["copyright"], size=10, color=TEXT_3, lines=2))
        label_row = ft.Container(ft.Column(facts, spacing=8), padding=12, border=border(BORDER_DIM))
        tracklist = [
            ft.Container(
                ft.Row(
                    [
                        txt(str(t.get("number") or ""), size=11, bold=True, color=BLACK if t.get("current") else TEXT_3, width=22),
                        txt(t.get("name", ""), size=12, bold=bool(t.get("current")), color=BLACK if t.get("current") else WHITE, lines=1, expand=True),
                        txt(mmss(t.get("duration_ms", 0)), size=11, color=BLACK if t.get("current") else TEXT_2),
                    ],
                    spacing=8,
                ),
                bgcolor=accent if t.get("current") else None,
                padding=ft.Padding.symmetric(vertical=6, horizontal=8),
            )
            for t in album.get("tracks", [])
        ]
        artist_cards = [artist_card(a) for a in artists]
        sections: list[ft.Control] = [hero, grid, label_row]
        if tracklist:
            sections += [label("Tracklist"), ft.Container(ft.Column(tracklist, spacing=0), border=border(BORDER_DIM), bgcolor=SURFACE)]
        sections += [label("Artists"), *artist_cards]
        return sections

    def artist_card(a: dict) -> ft.Control:
        stats_line = []
        if a.get("followers") is not None:
            stats_line.append(f"{compact(a['followers'])} followers")
        if a.get("albums_total") is not None:
            stats_line.append(f"{a['albums_total']} albums")
        if a.get("singles_total") is not None:
            stats_line.append(f"{a['singles_total']} singles")
        rows: list[ft.Control] = [
            ft.Row(
                [
                    cover(a.get("image"), 52, edge=None, circle=True, icon=ft.Icons.PERSON),
                    ft.Column([txt(a["name"], size=16, bold=True, lines=1), txt(" · ".join(stats_line), size=11, color=TEXT_2, lines=1)], spacing=2, tight=True, expand=True),
                ],
                spacing=12,
            )
        ]
        if a.get("popularity") is not None:
            rows += [ft.Row([label("popularity"), txt(str(a["popularity"]), size=11, bold=True)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), meter(a["popularity"] / 100, WHITE, 4)]
        if a.get("genres"):
            rows.append(ft.Row([tag(g, accent) for g in a["genres"][:4]], wrap=True, spacing=6, run_spacing=6))
        top = a.get("top_tracks") or []
        if top:
            rows.append(label("Most played"))
            for i, t in enumerate(top):
                link_url = t.get("url")

                async def open_top(e, link_url=link_url):
                    if link_url:
                        app.tap()
                        await app.open_url(link_url)

                rows.append(
                    ft.Container(
                        ft.Row(
                            [
                                txt(f"{i + 1}", size=11, bold=True, color=BLACK if t.get("current") else accent, width=16),
                                cover(t.get("image"), 30, edge=None),
                                txt(t.get("name", ""), size=12, bold=True, color=BLACK if t.get("current") else WHITE, lines=1, expand=True),
                            ],
                            spacing=10,
                        ),
                        bgcolor=accent if t.get("current") else None,
                        padding=ft.Padding.symmetric(vertical=4, horizontal=6),
                        ink=True,
                        on_click=open_top,
                    )
                )
        return ft.Container(ft.Column(rows, spacing=10), padding=16, bgcolor=SURFACE, border=border(WHITE))

    async def use_now_playing(e):
        if not app.player.track_url:
            app.toast("Nothing is playing", "error")
            return
        link.value = app.player.track_url
        link.update()
        await analyze()

    async def after_paste(_):
        await analyze()

    link.box.content.controls.append(ft.Container(paste_button(app, link, "track", after_paste), padding=ft.Padding.only(right=6)))
    button = BrutalButton("X-ray it", ft.Icons.QUERY_STATS, analyze, accent=accent, haptic=app.thud)

    async def ready():
        if url:
            await analyze()

    return Screen(
        app,
        "/track-stats",
        [
            *header(app, feature.title, "Release info, album context, popularity and the people behind any track.", accent, feature.icon, number_of(feature.key)),
            link,
            BrutalButton("Use what's playing", ft.Icons.GRAPHIC_EQ, use_now_playing, variant="ghost", haptic=app.tap, height=46),
            button,
            output,
        ],
        accent=accent,
        on_ready=ready,
    )


