import asyncio
import time
from datetime import date, timedelta

from services.client import Spotify, SpotifyError, track_of
from services.mix import MixEngine, is_song, seed_from_track, song_key
from services.spotify import _queue_tracks, _save_playlist, album_card, image_of, parse_link, track_card


async def more_like_this(sp: Spotify, count: int, track_url: str | None = None) -> dict:
    if track_url:
        _, track_id = parse_link(track_url, "track")
        track = await sp.get(f"/tracks/{track_id}", market="from_token")
    else:
        current = await sp.get("/me/player/currently-playing")
        track = (current or {}).get("item")
        if not track or track.get("type", "track") != "track" or not track.get("id"):
            raise ValueError("Nothing is playing right now. Start a song first.")
    exclude = {track["id"]}
    try:
        recent = await sp.get("/me/player/recently-played", limit=50)
        exclude |= {t["id"] for t in (track_of(i) for i in recent.get("items") or []) if t}
    except SpotifyError:
        pass
    try:
        queued = await sp.get("/me/player/queue")
        exclude |= {t.get("id") for t in queued.get("queue") or [] if t and t.get("id")}
    except SpotifyError:
        pass
    engine = MixEngine(sp, playlists_per_seed=10, max_playlists=20)
    tracks = await engine.build([seed_from_track(track)], count, exclude=exclude, seed_share=0.15)
    if not tracks:
        raise ValueError("Could not find anything similar right now, try another song.")
    added, errors = await _queue_tracks(sp, tracks)
    lead = (track.get("artists") or [{}])[0].get("name", "")
    return {
        "added": added,
        "errors": errors,
        "seed": {"name": track.get("name"), "artists": lead, "image": image_of(track.get("album"))},
        "tracks": [track_card(t) for t in tracks[:12]],
        "ids": [t["id"] for t in tracks],
    }


async def _top_artists(sp: Spotify, time_range: str) -> list[dict]:
    try:
        data = await sp.get("/me/top/artists", limit=50, time_range=time_range)
    except SpotifyError:
        return []
    return [a for a in data.get("items") or [] if a and a.get("id")]


async def _followed_artists(sp: Spotify, cap: int = 200) -> list[dict]:
    out: list[dict] = []
    after = None
    while len(out) < cap:
        try:
            data = await sp.get("/me/following", type="artist", limit=50, after=after)
        except SpotifyError:
            break
        page = data.get("artists") or {}
        items = [a for a in page.get("items") or [] if a and a.get("id")]
        out += items
        after = (page.get("cursors") or {}).get("after")
        if not items or not after:
            break
    return out


async def watched_artists(sp: Spotify, cap: int = 80) -> list[dict]:
    followed, short, medium, long_, recent = await asyncio.gather(
        _followed_artists(sp),
        _top_artists(sp, "short_term"),
        _top_artists(sp, "medium_term"),
        _top_artists(sp, "long_term"),
        sp.get("/me/player/recently-played", limit=50),
        return_exceptions=True,
    )
    pools = [p if isinstance(p, list) else [] for p in (short, followed, medium, long_)]
    recent_artists: list[dict] = []
    if isinstance(recent, dict):
        for entry in recent.get("items") or []:
            track = track_of(entry)
            if track:
                recent_artists += [a for a in (track.get("artists") or [])[:1] if a.get("id")]
    pools.append(recent_artists)
    picked: dict[str, dict] = {}
    longest = max((len(p) for p in pools), default=0)
    for i in range(longest):
        for pool in pools:
            if i < len(pool) and len(picked) < cap:
                picked.setdefault(pool[i]["id"], pool[i])
    return list(picked.values())


RELEASE_TTL = 3 * 3600
_release_cache: dict[tuple[str, str], tuple[float, list[dict]]] = {}


async def _artist_releases(sp: Spotify, artist_id: str, group: str) -> list[dict]:
    key = (artist_id, group)
    hit = _release_cache.get(key)
    if hit and time.time() - hit[0] < RELEASE_TTL:
        return hit[1]
    try:
        data = await sp.get(f"/artists/{artist_id}/albums", include_groups=group, limit=5)
    except SpotifyError:
        return []
    items = [a for a in data.get("items") or [] if a and a.get("id")]
    _release_cache[key] = (time.time(), items)
    if len(_release_cache) > 20000:
        for stale in sorted(_release_cache, key=lambda k: _release_cache[k][0])[:5000]:
            _release_cache.pop(stale, None)
    return items


def _release_day(album: dict) -> date | None:
    raw = album.get("release_date") or ""
    if album.get("release_date_precision", "day") != "day" or len(raw) != 10:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


async def find_releases(sp: Spotify, days: int) -> tuple[list[dict], int]:
    cutoff = date.today() - timedelta(days=days)
    artists = await watched_artists(sp, cap=60)

    async def latest(artist: dict, group: str) -> list[dict]:
        out = []
        for album in await _artist_releases(sp, artist["id"], group):
            day = _release_day(album)
            if day and day >= cutoff:
                out.append(album)
        return out

    jobs = [latest(a, g) for a in artists for g in ("album", "single")]
    found = await asyncio.gather(*jobs)
    unique: dict[str, dict] = {}
    keys: set[tuple[str, str]] = set()
    for album in sorted((a for group in found for a in group), key=lambda a: a.get("release_date", ""), reverse=True):
        key = ((album.get("name") or "").lower().strip(), ((album.get("artists") or [{}])[0]).get("id", ""))
        if album["id"] in unique or key in keys:
            continue
        keys.add(key)
        unique[album["id"]] = album
    return list(unique.values()), len(artists)


async def release_radar(sp: Spotify, days: int) -> dict:
    releases, checked = await find_releases(sp, days)
    cards = []
    for album in releases:
        card = album_card(album)
        card["album_type"] = album.get("album_type")
        card["total_tracks"] = album.get("total_tracks")
        cards.append(card)
    return {"releases": cards, "artists_checked": checked, "days": days}


async def release_radar_tracks(sp: Spotify, days: int, per_album: int = 3, cap: int = 100) -> list[dict]:
    releases, _ = await find_releases(sp, days)

    async def tracks_of(album: dict) -> list[dict]:
        try:
            data = await sp.get(f"/albums/{album['id']}/tracks", limit=50)
        except SpotifyError:
            return []
        items = [t for t in data.get("items") or [] if t and is_song(t)]
        if album.get("album_type") == "album":
            items = items[:per_album]
        shell = {"id": album["id"], "name": album.get("name"), "images": album.get("images") or [], "release_date": album.get("release_date")}
        return [{**t, "album": shell} for t in items[:8]]

    groups = await asyncio.gather(*(tracks_of(a) for a in releases))
    out: list[dict] = []
    keys: set[tuple[str, str]] = set()
    for group in groups:
        for t in group:
            key = song_key(t)
            if key in keys:
                continue
            keys.add(key)
            out.append(t)
    return out[:cap]


async def create_release_radar_playlist(sp: Spotify, days: int, playlist_name: str | None) -> dict:
    tracks = await release_radar_tracks(sp, days)
    if not tracks:
        raise ValueError(f"None of your artists released anything in the last {days} days.")
    return await _save_playlist(sp, playlist_name or "", tracks, f"Release Radar: last {days} days")
