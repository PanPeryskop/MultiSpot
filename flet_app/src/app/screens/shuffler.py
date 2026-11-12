import flet as ft

from app.api import ApiError
from app.screens._playlists import PlaylistPicker
from app.screens.registry import number_of
from app.theme import TEXT_2
from app.ui.result import ResultSlot
from app.ui.screen import Screen, header
from app.ui.widgets import BrutalButton, border, txt


def build(app, feature, **_) -> ft.View:
    accent = feature.accent
    result = ResultSlot()
    chosen: list[dict] = []

    def changed(items: list[dict]):
        chosen[:] = items
        button.set_text(f"Shuffle '{items[0]['name'][:18]}'" if items else "Pick a playlist")
        button.set_enabled(bool(items))
        button.update()

    async def submit(e):
        if not chosen:
            return
        button.set_busy(True)
        try:
            data = await app.api.shuffle(chosen[0]["url"])
        except ApiError as exc:
            app.toast(exc.message, "error")
            return
        finally:
            button.set_busy(False)
        result.show(app, "Truly shuffled", f"{data.get('track_count', 0)} tracks, new order", "Spotify will now play it the way chaos intended.", accent, data.get("playlist_url"))

    warning = ft.Container(
        ft.Row(
            [
                ft.Icon(ft.Icons.INFO_OUTLINE, color=accent, size=18),
                txt("Your own playlists are rebuilt in place (the old copy is unfollowed). Others are saved as a new (Shuffled) copy.", size=11, color=TEXT_2, height=1.5, expand=True),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        border=border(accent, 1.5),
        padding=12,
    )
    picker = PlaylistPicker(app, accent, False, changed)
    button = BrutalButton("Pick a playlist", ft.Icons.SHUFFLE, submit, accent=accent, haptic=app.thud)
    button.set_enabled(False)

    async def ready():
        await picker.load()

    return Screen(
        app,
        "/shuffler",
        [
            *header(app, feature.title, "Spotify's shuffle has favourites. This one doesn't: we rebuild the playlist in a genuinely random order.", accent, feature.icon, number_of(feature.key)),
            warning,
            result,
            picker,
        ],
        accent=accent,
        footer=button,
        on_ready=ready,
    )
