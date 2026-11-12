import flet as ft

from app.api import ApiError
from app.screens._playlists import PlaylistPicker
from app.screens.registry import number_of
from app.theme import BORDER_DIM, PURPLE, SURFACE, TEXT_2, WHITE, YELLOW
from app.ui.motion import cascade, prime
from app.ui.screen import Screen, header
from app.ui.widgets import BrutalButton, border, compact, cover, fill_meters, hard_shadow, label, meter, mmss, txt


def build(app, feature, **_) -> ft.View:
    accent = feature.accent
    chosen: list[dict] = []
    report = ft.Column(spacing=18)
    picker_box = ft.Container(animate_size=ft.Animation(360, ft.AnimationCurve.EASE_OUT_CUBIC), clip_behavior=ft.ClipBehavior.HARD_EDGE)

    def changed(items: list[dict]):
        chosen[:] = items
        button.set_text(f"X-ray '{items[0]['name'][:18]}'" if items else "Pick a playlist")
        button.set_enabled(bool(items))
        button.update()

    def tile(name: str, value: str, color: str = WHITE) -> ft.Control:
        return ft.Container(
            ft.Column([txt(value, size=22, bold=True, color=color, lines=1), txt(name, size=10, color=TEXT_2, upper=True, bold=True, spacing=1)], spacing=2, tight=True),
            padding=12,
            bgcolor=SURFACE,
            border=border(BORDER_DIM),
            expand=True,
        )

    def bars(items: list[tuple[str, int]], color: str) -> ft.Control:
        top = max([n for _, n in items] or [1])
        return ft.Column(
            [
                ft.Column(
                    [ft.Row([txt(name, size=12, bold=True, lines=1, expand=True), txt(str(n), size=11, color=TEXT_2, bold=True)]), meter(n / top, color, 8, 900 + i * 60)],
                    spacing=4,
                )
                for i, (name, n) in enumerate(items)
            ],
            spacing=10,
        )

    def track_line(t: dict, extra: str = "") -> ft.Control:
        link = t.get("url")

        async def open_track(e):
            if link:
                app.tap()
                await app.open_url(link)

        return ft.Container(
            ft.Row(
                [
                    cover(t.get("image"), 38, edge=None),
                    ft.Column([txt(t.get("name", ""), size=12, bold=True, lines=1), txt(", ".join(t.get("artists") or []), size=10, color=TEXT_2, lines=1)], spacing=1, tight=True, expand=True),
                    txt(extra, size=10, bold=True, color=YELLOW) if extra else ft.Container(),
                ],
                spacing=10,
            ),
            padding=ft.Padding.symmetric(vertical=4),
            ink=True,
            on_click=open_track,
        )

    def section(title: str, body: ft.Control, color: str = WHITE) -> ft.Control:
        return ft.Container(ft.Column([label(title, color), body], spacing=12), padding=16, bgcolor=SURFACE, border=border(BORDER_DIM))

    def render(d: dict) -> list[ft.Control]:
        p, t = d["playlist"], d["totals"]
        hero = ft.Container(
            ft.Row(
                [
                    ft.Container(cover(p.get("image"), 96, edge=WHITE), shadow=hard_shadow(accent, 5), rotate=ft.Rotate(-0.03)),
                    ft.Column(
                        [
                            label(f"{'collab' if p.get('collaborative') else 'public' if p.get('public') else 'private'} · {p.get('owner', '')}"),
                            txt(p.get("name", ""), size=20, bold=True, lines=3, height=1.1),
                            txt(f"{compact(p['followers'])} followers" if p.get("followers") is not None else "", size=11, color=TEXT_2),
                        ],
                        spacing=6,
                        expand=True,
                    ),
                ],
                spacing=16,
            )
        )
        grid = ft.Column(
            [
                ft.Row([tile("tracks", str(t["tracks"]), accent), tile("runtime", mmss(t["duration_ms"]) if t["duration_ms"] < 3600000 else f"{t['duration_ms'] // 3600000}h {t['duration_ms'] % 3600000 // 60000}m")], spacing=10),
                ft.Row([tile("artists", str(t["artists"])), tile("avg year", str(t.get("avg_year") or "?"))], spacing=10),
                ft.Row([tile("explicit", f"{t['explicit_pct']}%"), tile("avg pop", str(t["avg_popularity"]) if t.get("avg_popularity") is not None else "?")], spacing=10),
            ],
            spacing=10,
        )
        out: list[ft.Control] = [hero, grid]
        if d["top_artists"]:
            out.append(section("Who owns it", bars([(f"{a['name']} · {a['share']}%", a["count"]) for a in d["top_artists"][:8]], accent), accent))
        if d["decades"]:
            out.append(section("Decades", bars([(x["decade"], x["count"]) for x in d["decades"]], YELLOW), YELLOW))
        if len(d["added_by_year"]) > 1:
            out.append(section("Added per year", bars([(x["year"], x["count"]) for x in d["added_by_year"]], PURPLE), PURPLE))
        dups = d["duplicates"]
        out.append(section(f"Duplicates · {len(dups)}", ft.Column([track_line(x, f"×{x['count']}") for x in dups[:10]], spacing=2) if dups else txt("No duplicates. Clean.", size=12, color=accent)))
        gone = d["unavailable"]
        out.append(section(f"Unavailable · {len(gone)}", ft.Column([track_line(x) for x in gone[:10]], spacing=2) if gone else txt("Everything is playable in your country.", size=12, color=accent)))
        ex = d["extremes"]
        lines = []
        if ex.get("oldest"):
            lines.append(track_line(ex["oldest"], f"oldest {ex['oldest']['year']}"))
        if ex.get("newest"):
            lines.append(track_line(ex["newest"], f"newest {ex['newest']['year']}"))
        if ex.get("shortest"):
            lines.append(track_line(ex["shortest"], mmss(ex["shortest"]["duration_ms"])))
        if ex.get("longest"):
            lines.append(track_line(ex["longest"], mmss(ex["longest"]["duration_ms"])))
        if lines:
            out.append(section("Extremes", ft.Column(lines, spacing=2)))
        if d.get("most_popular"):
            out.append(section("Biggest hits", ft.Column([track_line(x, f"★{x['popularity']}") for x in d["most_popular"]], spacing=2)))
            out.append(section("Hidden gems", ft.Column([track_line(x, f"★{x['popularity']}") for x in d["least_popular"]], spacing=2)))
        return out

    async def scan(e=None):
        if not chosen:
            return
        button.set_busy(True)
        try:
            data = await app.api.playlist_xray(chosen[0]["url"])
        except ApiError as exc:
            app.toast(exc.message, "error")
            return
        finally:
            button.set_busy(False)
        app.boom()
        sections = render(data)
        for s in sections:
            prime(s, dy=0.2)
        report.controls = sections
        picker_box.content = again
        view.update()
        await view.list.scroll_to(offset=0, duration=400)
        await cascade(sections, start=0.05, step=0.06)
        fill_meters(report)
        report.update()

    async def pick_another(e):
        report.controls = []
        picker_box.content = picker
        view.update()

    picker = PlaylistPicker(app, accent, False, changed)
    picker_box.content = picker
    again = BrutalButton("Pick another playlist", ft.Icons.SWAP_HORIZ, pick_another, variant="ghost", haptic=app.tap, height=46)
    button = BrutalButton("Pick a playlist", ft.Icons.DOCUMENT_SCANNER, scan, accent=accent, haptic=app.thud)
    button.set_enabled(False)

    async def ready():
        await picker.load()

    view = Screen(
        app,
        "/playlist-xray",
        [
            *header(app, feature.title, "Who dominates a playlist, which decades it lives in, duplicates and tracks you can't play anymore. Read only.", accent, feature.icon, number_of(feature.key)),
            report,
            picker_box,
        ],
        accent=accent,
        footer=button,
        on_ready=ready,
    )
    return view
