import re

import flet as ft

from app.ui.widgets import IconSquare

SPOTIFY_ID = re.compile(r"(?:open\.spotify\.com/(?:intl-[a-z]+/)?|spotify:)(track|playlist|artist|album)[/:]([A-Za-z0-9]+)")


def spotify_kind(url: str) -> tuple[str | None, str | None]:
    match = SPOTIFY_ID.search(url or "")
    return (match.group(1), match.group(2)) if match else (None, None)


def normalize(url: str) -> str | None:
    kind, sid = spotify_kind(url)
    return f"https://open.spotify.com/{kind}/{sid}" if kind else None


def paste_button(app, field, kind: str | None = None, after=None) -> IconSquare:
    async def paste(e):
        text = await app.paste()
        found_kind, _ = spotify_kind(text)
        if not text:
            app.toast("Clipboard is empty", "error")
            return
        if kind and found_kind != kind:
            app.toast(f"Clipboard has no Spotify {kind} link", "error")
            return
        field.value = normalize(text) or text
        field.update()
        app.select()
        if after:
            await after(field.value)

    return IconSquare(ft.Icons.CONTENT_PASTE, paste, size=40, depth=0, haptic=app.tap, tooltip="Paste")
