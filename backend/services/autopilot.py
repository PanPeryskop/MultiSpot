import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from services.client import Spotify, SpotifyError
from services.discover import release_radar_tracks
from services.spotify import DESCRIPTION, build_magic_tracks, rewind_tracks, track_card, uri_of
from services.store import store

log = logging.getLogger("multispot.autopilot")

RUN_HOUR = 6
KINDS = {
    "daily_mix": {
        "label": "Daily Magic Mix",
        "description": "A fresh Magic Mix every morning, in the same playlist.",
        "schedule": "Every day at 6:00",
        "defaults": {"track_count": 30},
    },
    "weekly_radar": {
        "label": "Weekly Release Radar",
        "description": "New releases from your artists, refreshed every Friday.",
        "schedule": "Every Friday at 6:00",
        "defaults": {"days": 7},
    },
    "monthly_rewind": {
        "label": "Monthly Rewind",
        "description": "Your top tracks of the month saved as a new playlist.",
        "schedule": "1st of every month at 6:00",
        "defaults": {"track_count": 50},
    },
}

_running: set[int] = set()


def zone() -> ZoneInfo:
    return ZoneInfo(os.getenv("MULTISPOT_TZ", "Europe/Warsaw"))


def next_run(kind: str, after: float | None = None) -> int:
    now = datetime.fromtimestamp(after or time.time(), zone())
    slot = now.replace(hour=RUN_HOUR, minute=0, second=0, microsecond=0)
    if kind == "daily_mix":
        if slot <= now:
            slot += timedelta(days=1)
    elif kind == "weekly_radar":
        slot += timedelta(days=(4 - slot.weekday()) % 7)
        if slot <= now:
            slot += timedelta(days=7)
    else:
        slot = slot.replace(day=1)
        if slot <= now:
            year, month = (slot.year + 1, 1) if slot.month == 12 else (slot.year, slot.month + 1)
            slot = slot.replace(year=year, month=month)
    return int(slot.timestamp())


def describe(item: dict) -> dict:
    meta = KINDS.get(item["kind"], {})
    tz = zone()
    stamp = lambda v: datetime.fromtimestamp(v, tz).isoformat() if v else None
    return {
        "id": item["id"],
        "kind": item["kind"],
        "label": meta.get("label", item["kind"]),
        "description": meta.get("description"),
        "schedule": meta.get("schedule"),
        "settings": item["settings"],
        "enabled": item["enabled"],
        "playlist_url": item.get("playlist_url"),
        "last_run": stamp(item.get("last_run")),
        "next_run": stamp(item.get("next_run")) if item["enabled"] else None,
        "last_status": item.get("last_status"),
        "last_count": item.get("last_count"),
    }


def catalog() -> list[dict]:
    return [{"kind": k, **{f: v[f] for f in ("label", "description", "schedule", "defaults")}} for k, v in KINDS.items()]


async def _write(sp: Spotify, item: dict, tracks: list[dict], name: str) -> tuple[str, str]:
    uris = [uri_of(t) for t in tracks]
    playlist_id = item.get("playlist_id")
    if playlist_id:
        try:
            await sp.replace_playlist(playlist_id, uris)
            return playlist_id, item.get("playlist_url") or f"https://open.spotify.com/playlist/{playlist_id}"
        except SpotifyError as exc:
            if exc.status != 404:
                raise
    created = await sp.create_playlist(name, f"{DESCRIPTION} Autopilot")
    await sp.add_to_playlist(created["id"], uris)
    return created["id"], (created.get("external_urls") or {}).get("spotify") or f"https://open.spotify.com/playlist/{created['id']}"


async def execute(sp: Spotify, item: dict, scheduled: bool) -> dict:
    kind = item["kind"]
    settings = {**KINDS[kind]["defaults"], **(item.get("settings") or {})}
    now = datetime.now(zone())
    fields: dict = {"last_run": int(time.time())}
    tracks: list[dict] = []
    if kind == "daily_mix":
        tracks, _ = await build_magic_tracks(sp, int(settings["track_count"]))
        playlist_id, url = await _write(sp, item, tracks, settings.get("name") or "Daily Magic Mix")
        fields.update(playlist_id=playlist_id, playlist_url=url, last_status=f"Refreshed with {len(tracks)} tracks")
    elif kind == "weekly_radar":
        tracks = await release_radar_tracks(sp, int(settings["days"]))
        if tracks:
            playlist_id, url = await _write(sp, item, tracks, settings.get("name") or "Weekly Release Radar")
            fields.update(playlist_id=playlist_id, playlist_url=url, last_status=f"{len(tracks)} new tracks")
        else:
            fields.update(last_status="No new releases from your artists this week")
    else:
        month = (now.replace(day=1) - timedelta(days=1)) if scheduled else now
        label = month.strftime("%B %Y")
        tracks = await rewind_tracks(sp, "short_term", int(settings["track_count"]))
        created = await sp.create_playlist(f"{settings.get('name') or 'Rewind'}: {label}", f"{DESCRIPTION} Autopilot")
        await sp.add_to_playlist(created["id"], [uri_of(t) for t in tracks])
        url = (created.get("external_urls") or {}).get("spotify") or f"https://open.spotify.com/playlist/{created['id']}"
        fields.update(playlist_url=url, last_status=f"Saved Rewind: {label}")
    fields["last_count"] = len(tracks)
    if scheduled:
        fields["next_run"] = next_run(kind)
    updated = store.update_automation(item["id"], **fields)
    result = describe(updated)
    result["tracks"] = [track_card(t) for t in tracks[:12]]
    return result


async def run_scheduled(item: dict):
    token = store.user_token(item["user_id"])
    if not token:
        store.update_automation(item["id"], next_run=next_run(item["kind"]), last_status="Open MultiSpot to reconnect Spotify")
        return
    sp = Spotify({"access_token": "", "refresh_token": token, "expires_at": 0})
    try:
        await execute(sp, item, scheduled=True)
    except SpotifyError as exc:
        status = "Spotify login expired, open MultiSpot to reconnect" if exc.status == 401 else f"Failed: {exc.message}"
        store.update_automation(item["id"], next_run=next_run(item["kind"]), last_status=status, last_run=int(time.time()))
    except ValueError as exc:
        store.update_automation(item["id"], next_run=next_run(item["kind"]), last_status=str(exc), last_run=int(time.time()))
    if sp.changed and sp.token.get("refresh_token") and sp.token["refresh_token"] != token:
        store.save_user(item["user_id"], sp.token["refresh_token"])


async def tick():
    for item in store.due(time.time()):
        if item["id"] in _running:
            continue
        _running.add(item["id"])
        try:
            await run_scheduled(item)
        except Exception:
            log.exception("Autopilot run %s failed", item["id"])
            store.update_automation(item["id"], next_run=next_run(item["kind"]), last_status="Failed unexpectedly")
        finally:
            _running.discard(item["id"])


async def scheduler(interval: float = 60):
    while True:
        try:
            await tick()
        except Exception:
            log.exception("Autopilot tick failed")
        await asyncio.sleep(interval)


async def run_now(sp: Spotify, item: dict) -> dict:
    if item["id"] in _running:
        raise ValueError("This autopilot is already running")
    _running.add(item["id"])
    try:
        return await execute(sp, item, scheduled=False)
    finally:
        _running.discard(item["id"])
