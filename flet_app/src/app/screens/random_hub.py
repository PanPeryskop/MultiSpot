import flet as ft

from app.api import ApiError
from app.screens.registry import number_of
from app.theme import TEXT_2
from app.ui.genres import GenrePicker
from app.ui.result import ResultSlot
from app.ui.screen import Screen, header
from app.ui.widgets import BrutalButton, CountPicker, Field, Segmented, label, txt

CHAOS_HINT = "Every track comes from a different random genre. Bigger batches take a while."
GENRE_HINT = "A whole station from one genre, max three tracks per artist."


def build(app, feature, **_) -> ft.View:
    accent = feature.accent
    result = ResultSlot()
    name = Field("Playlist name", "", "Random Hub", accent=accent)
    name_slot = ft.Container(animate_size=ft.Animation(380, ft.AnimationCurve.EASE_OUT_CUBIC), clip_behavior=ft.ClipBehavior.HARD_EDGE)
    count = CountPicker("How many tracks", 20, 1, 100, accent=accent, haptic=app.select)
    hint = txt(CHAOS_HINT, size=11, color=TEXT_2, height=1.5)

    def genre_changed(value: str | None):
        hint.value = GENRE_HINT if value else CHAOS_HINT
        name.input.hint_text = f"{value.title()} Roulette" if value else "Random Hub"
        hint.update()
        if name_slot.content is name:
            name.update()

    genre = GenrePicker(app, accent, genre_changed)

    async def submit(e):
        to_playlist = mode.value == "playlist"
        button.set_busy(True)
        try:
            data = await app.api.random_hub(count.value, name.value or None, genre.value, to_playlist)
        except ApiError as exc:
            app.toast(exc.message, "error")
            return
        finally:
            button.set_busy(False)
        flavour = genre.value.upper() if genre.value else "pure genre roulette"
        if to_playlist:
            result.show(
                app,
                "Playlist created",
                f"{data.get('track_count', 0)} tracks",
                f"{flavour}, saved to your library.",
                accent,
                data.get("playlist_url"),
                tracks=data.get("tracks"),
                total=data.get("track_count"),
            )
        else:
            result.show(
                app,
                "Injected",
                f"{data.get('added', 0)} tracks queued",
                f"{flavour}. Hit play, your queue just got weird.",
                accent,
                None,
                [("added", str(data.get("added", 0))), ("skipped", str(data.get("errors", 0)))],
                tracks=data.get("tracks"),
                total=data.get("added"),
            )
            await app.player.refresh()

    def switch(value):
        name_slot.content = name if value == "playlist" else None
        count.hi = 200 if value == "playlist" else 100
        count.slider.max = count.hi
        count.slider.divisions = count.hi - count.lo
        if count.value > count.hi:
            count._apply(count.hi, False)
        button.set_text("Create playlist" if value == "playlist" else "Inject tracks", ft.Icons.PLAYLIST_ADD if value == "playlist" else ft.Icons.BOLT)
        name_slot.update()
        count.update()
        button.update()

    mode = Segmented([("queue", "Add to queue"), ("playlist", "New playlist")], "queue", switch, accent, app.select)
    button = BrutalButton("Inject tracks", ft.Icons.BOLT, submit, accent=accent, haptic=app.thud)
    return Screen(
        app,
        "/random-hub",
        [
            *header(app, feature.title, "Random tracks from 6000+ genres, or a whole station from one genre you pick.", accent, feature.icon, number_of(feature.key)),
            ft.Column([label("Destination"), mode], spacing=8),
            genre,
            name_slot,
            count,
            hint,
            button,
            result,
        ],
        accent=accent,
    )
