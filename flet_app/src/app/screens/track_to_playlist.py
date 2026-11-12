import flet as ft

from app.api import ApiError
from app.screens._shared import normalize, paste_button, spotify_kind
from app.screens.registry import number_of
from app.theme import TEXT_2
from app.ui.result import ResultSlot
from app.ui.screen import Screen, header
from app.ui.widgets import BrutalButton, CountPicker, Field, txt


def build(app, feature, url: str | None = None, **_) -> ft.View:
    accent = feature.accent
    result = ResultSlot()
    link = Field("Seed track", url or "", "open.spotify.com/track/…", accent=accent, keyboard=ft.KeyboardType.URL, prefix_icon=ft.Icons.LINK)
    link.box.content.controls.append(ft.Container(paste_button(app, link, "track"), padding=ft.Padding.only(right=6)))
    name = Field("Playlist name", "", "<track> Radio", accent=accent)
    count = CountPicker("Radio length", 50, 10, 100, accent=accent, haptic=app.select)

    async def use_now_playing(e):
        if not app.player.track_url:
            app.toast("Nothing is playing", "error")
            return
        link.value = app.player.track_url
        link.update()
        app.select()

    async def submit(e):
        if spotify_kind(link.value)[0] != "track":
            app.toast("Paste a Spotify track link", "error")
            return
        button.set_busy(True)
        try:
            data = await app.api.track_to_playlist(normalize(link.value), name.value or None, count.value)
        except ApiError as exc:
            app.toast(exc.message, "error")
            return
        finally:
            button.set_busy(False)
        seed = data.get("seed") or {}
        result.show(
            app,
            "Radio ready",
            f"{data.get('track_count', 0)} tracks",
            f"Built around {seed.get('name', 'your seed')} by {seed.get('artists', '?')}.",
            accent,
            data.get("playlist_url"),
            tracks=data.get("tracks"),
            total=data.get("track_count"),
        )

    button = BrutalButton("Build radio", ft.Icons.RADIO, submit, accent=accent, haptic=app.thud)
    return Screen(
        app,
        "/track-radio",
        [
            *header(app, feature.title, "Drop one track. We find what listeners keep playing right next to it and build a radio around the seed.", accent, feature.icon, number_of(feature.key)),
            link,
            BrutalButton("Use what's playing", ft.Icons.GRAPHIC_EQ, use_now_playing, variant="ghost", haptic=app.tap, height=46),
            name,
            count,
            txt("Mined from thousands of listener playlists, spam filtered out.", size=11, color=TEXT_2),
            button,
            result,
        ],
        accent=accent,
    )
