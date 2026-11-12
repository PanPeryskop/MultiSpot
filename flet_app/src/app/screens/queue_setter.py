import flet as ft

from app.api import ApiError
from app.screens._playlists import PlaylistPicker
from app.screens.registry import number_of
from app.ui.result import ResultSlot
from app.ui.screen import Screen, header
from app.ui.widgets import BrutalButton


def build(app, feature, **_) -> ft.View:
    accent = feature.accent
    result = ResultSlot()
    chosen: list[dict] = []

    def changed(items: list[dict]):
        chosen[:] = items
        n = len(items)
        button.set_text(f"Weave {n} playlist{'s' if n != 1 else ''}" if n else "Pick playlists")
        button.set_enabled(n > 0)
        button.update()

    async def submit(e):
        if not chosen:
            return
        button.set_busy(True)
        try:
            data = await app.api.queue_setter([p["url"] for p in chosen])
        except ApiError as exc:
            app.toast(exc.message, "error")
            return
        finally:
            button.set_busy(False)
        result.show(app, "Queue woven", f"{data.get('queued', 0)} tracks interleaved", " → ".join(p["name"] for p in chosen[:4]), accent)
        await app.player.refresh()

    picker = PlaylistPicker(app, accent, True, changed)
    button = BrutalButton("Pick playlists", ft.Icons.QUEUE_MUSIC, submit, accent=accent, haptic=app.thud)
    button.set_enabled(False)

    async def ready():
        await picker.load()

    return Screen(
        app,
        "/queue-setter",
        [
            *header(app, feature.title, "Tap playlists in the order you want them. We alternate one track from each, up to 100 per playlist.", accent, feature.icon, number_of(feature.key)),
            result,
            picker,
        ],
        accent=accent,
        footer=button,
        on_ready=ready,
    )
