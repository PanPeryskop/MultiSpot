import asyncio
import json
import os
import random
import re

from services.client import Spotify, SpotifyError, track_of
from services.mix import MixEngine, Seed, is_song, seed_from_album, seed_from_artist, seed_from_track, song_key

GENRES_PATH = os.path.join(os.path.dirname(__file__), "..", "genres.json")
with open(GENRES_PATH, "r", encoding="utf-8") as f:
    GENRES: list[str] = json.load(f)

LINK = re.compile(r"(?:open\.spotify\.com/(?:intl-[a-z]{2}(?:-[a-z]{2})?/)?(?:embed/)?|spotify:)(track|artist|album|playlist)[/:]([A-Za-z0-9]{22})")
BARE_ID = re.compile(r"^[A-Za-z0-9]{22}$")
DESCRIPTION = "Made with MultiSpot"
def parse_link(value: str, expected: str | None = None) -> tuple[str, str]:
    value = (value or "").strip()
    match = LINK.search(value)
    if match:
        kind, sid = match.groups()
    elif expected and BARE_ID.match(value):
        kind, sid = expected, value
    else:
        raise ValueError(f"Not a valid Spotify {expected or ''} link".replace("  ", " "))
    if expected and kind != expected:
        raise ValueError(f"Expected a Spotify {expected} link, got a {kind} link")
    return kind, sid


def image_of(obj: dict | None, prefer: int = 0) -> str | None:
    images = (obj or {}).get("images") or []
    if not images:
        return None
    return images[min(prefer, len(images) - 1)].get("url")


def track_card(t: dict) -> dict:
    return {
        "id": t.get("id"),
        "name": t.get("name"),
        "artists": [a.get("name") for a in t.get("artists") or []],
        "album": (t.get("album") or {}).get("name"),
        "image": image_of(t.get("album")),
        "url": (t.get("external_urls") or {}).get("spotify") or f"https://open.spotify.com/track/{t.get('id')}",
        "uri": t.get("uri") or f"spotify:track:{t.get('id')}",
        "popularity": t.get("popularity"),
        "duration_ms": t.get("duration_ms") or 0,
        "explicit": bool(t.get("explicit")),
    }


def artist_card(a: dict) -> dict:
    return {
        "id": a.get("id"),
        "name": a.get("name"),
        "image": image_of(a),
        "url": (a.get("external_urls") or {}).get("spotify") or f"https://open.spotify.com/artist/{a.get('id')}",
        "followers": (a.get("followers") or {}).get("total"),
        "popularity": a.get("popularity"),
        "genres": a.get("genres") or [],
    }


def album_card(a: dict) -> dict:
    return {
        "id": a.get("id"),
        "name": a.get("name"),
        "artists": [x.get("name") for x in a.get("artists") or []],
        "image": image_of(a),
        "url": (a.get("external_urls") or {}).get("spotify") or f"https://open.spotify.com/album/{a.get('id')}",
        "release_date": a.get("release_date"),
    }


def uri_of(t: dict) -> str:
    return t.get("uri") or f"spotify:track:{t['id']}"


async def _save_playlist(sp: Spotify, name: str, tracks: list[dict], fallback_name: str) -> dict:
    if not tracks:
        raise ValueError("Spotify returned no usable tracks for these seeds. Try different ones.")
    playlist = await sp.create_playlist((name or "").strip() or fallback_name, DESCRIPTION)
    await sp.add_to_playlist(playlist["id"], [uri_of(t) for t in tracks])
    return {
        "playlist_url": (playlist.get("external_urls") or {}).get("spotify") or f"https://open.spotify.com/playlist/{playlist['id']}",
        "playlist_id": playlist["id"],
        "track_count": len(tracks),
        "tracks": [track_card(t) for t in tracks[:12]],
    }


async def _queue_tracks(sp: Spotify, tracks: list[dict]) -> tuple[int, int]:
    added = errors = 0
    for t in tracks:
        try:
            await sp.queue(uri_of(t))
            added += 1
        except SpotifyError as exc:
            if exc.status in (401, 403) or "device" in exc.message.lower():
                if added == 0:
                    raise
                errors += len(tracks) - added - errors
                break
            errors += 1
    return added, errors


def find_genres(query: str, limit: int = 30) -> list[str]:
    q = (query or "").strip().lower()
    if not q:
        return random.sample(GENRES[:400], min(limit, 400))
    starts = [g for g in GENRES if g.startswith(q)]
    contains = [g for g in GENRES if q in g and not g.startswith(q)]
    return (starts + contains)[:limit]


async def _single_genre_tracks(sp: Spotify, genre: str, count: int) -> list[dict]:
    offsets = [0, 50, 100, 150, 200, 300, 400, 500]
    pages = await asyncio.gather(
        *(sp.search(f'genre:"{genre}"', "track", limit=50, offset=o) for o in offsets[: max(2, min(len(offsets), count // 20 + 2))]),
        return_exceptions=True,
    )
    pool: dict[tuple[str, str], dict] = {}
    for page in pages:
        if isinstance(page, BaseException):
            continue
        for t in page:
            if is_song(t):
                pool.setdefault(song_key(t), t)
    tracks = list(pool.values())
    random.shuffle(tracks)
    per_artist: dict[str, int] = {}
    out = []
    for t in tracks:
        lead = (t.get("artists") or [{}])[0].get("id", "")
        if per_artist.get(lead, 0) >= 3:
            continue
        per_artist[lead] = per_artist.get(lead, 0) + 1
        out.append(t)
        if len(out) >= count:
            break
    if len(out) < count:
        engine = MixEngine(sp, playlists_per_seed=8, max_playlists=16)
        more = await engine.build([Seed([genre, f"{genre} mix", f"best {genre}"])], count - len(out), exclude={t["id"] for t in out}, seed_share=0)
        out += more
    return out[:count]


async def _random_genre_tracks(sp: Spotify, count: int, genre: str | None = None) -> list[dict]:
    if genre:
        return await _single_genre_tracks(sp, genre, count)
    picked: list[dict] = []
    seen: set[str] = set()
    keys: set[tuple[str, str]] = set()
    pool = list(GENRES)
    random.shuffle(pool)

    async def one(genre: str) -> list[dict]:
        offset = random.choice((0, 0, 0, 50, 100, 150))
        try:
            found = await sp.search(f'genre:"{genre}"', "track", limit=50, offset=offset)
            if not found and offset:
                found = await sp.search(f'genre:"{genre}"', "track", limit=50)
        except SpotifyError:
            return []
        return found

    rounds = 0
    while len(picked) < count and pool and rounds < 6:
        rounds += 1
        batch = [pool.pop() for _ in range(min(len(pool), max(4, int((count - len(picked)) * 1.5))))]
        results = await asyncio.gather(*(one(g) for g in batch))
        for found in results:
            if len(picked) >= count:
                break
            random.shuffle(found)
            for t in found:
                if is_song(t) and t["id"] not in seen and song_key(t) not in keys:
                    seen.add(t["id"])
                    keys.add(song_key(t))
                    picked.append(t)
                    break
    return picked[:count]


async def add_random_tracks_to_queue(sp: Spotify, count: int, genre: str | None = None) -> dict:
    tracks = await _random_genre_tracks(sp, count, genre)
    if not tracks:
        raise ValueError("Could not find any random tracks right now, try again.")
    added, errors = await _queue_tracks(sp, tracks)
    return {"added": added, "errors": errors, "tracks": [track_card(t) for t in tracks[:12]]}


async def create_random_playlist(sp: Spotify, count: int, playlist_name: str | None, genre: str | None = None) -> dict:
    tracks = await _random_genre_tracks(sp, count, genre)
    return await _save_playlist(sp, playlist_name or "", tracks, f"{genre.title()} Roulette" if genre else "Random Hub")


async def create_playlist_from_track(sp: Spotify, track_url: str, playlist_name: str, track_count: int = 50) -> dict:
    _, track_id = parse_link(track_url, "track")
    track = await sp.get(f"/tracks/{track_id}", market="from_token")
    engine = MixEngine(sp, playlists_per_seed=10, max_playlists=24)
    tracks = await engine.build([seed_from_track(track)], track_count, pinned=[track], seed_share=0.2)
    lead = (track.get("artists") or [{}])[0].get("name", "")
    result = await _save_playlist(sp, playlist_name, tracks, f"{track.get('name')} Radio")
    result["seed"] = {"name": track.get("name"), "artists": lead}
    return result


async def _playlist_meta(sp: Spotify, pid: str) -> dict:
    return await sp.get(f"/playlists/{pid}", fields="id,name,owner(id),public,collaborative,description")


async def set_interleaved_queue(sp: Spotify, playlist_urls: list[str], per_playlist: int = 100) -> dict:
    ids = []
    for url in playlist_urls:
        _, pid = parse_link(url, "playlist")
        if pid not in ids:
            ids.append(pid)
    lists = await asyncio.gather(*(sp.playlist_items(pid, limit=per_playlist) for pid in ids))
    lists = [lst for lst in lists if lst]
    if not lists:
        raise ValueError("Those playlists have no playable tracks.")
    longest = max(len(lst) for lst in lists)
    order = [lst[i] for i in range(longest) for lst in lists if i < len(lst)]
    added, errors = await _queue_tracks(sp, order)
    return {"queued": added, "errors": errors, "playlists": len(lists)}


async def shuffle_playlist(sp: Spotify, playlist_url: str) -> dict:
    _, pid = parse_link(playlist_url, "playlist")
    playlist = await _playlist_meta(sp, pid)
    tracks = await sp.playlist_items(pid)
    uris = list(dict.fromkeys(uri_of(t) for t in tracks))
    if not uris:
        raise ValueError("This playlist has no tracks that can be shuffled.")
    random.shuffle(uris)
    me = await sp.me()
    is_own = (playlist.get("owner") or {}).get("id") == me["id"]
    name = playlist.get("name") or "Playlist"
    new_pl = await sp.create_playlist(
        name if is_own else f"{name} (Shuffled)",
        playlist.get("description") or "",
        public=bool(playlist.get("public")) if is_own else False,
    )
    await sp.add_to_playlist(new_pl["id"], uris)
    if is_own:
        await sp.unfollow_playlist(pid)
    return {
        "playlist_url": (new_pl.get("external_urls") or {}).get("spotify") or f"https://open.spotify.com/playlist/{new_pl['id']}",
        "track_count": len(uris),
    }


async def _top(sp: Spotify, kind: str, time_range: str, limit: int = 50) -> list[dict]:
    try:
        data = await sp.get(f"/me/top/{kind}", limit=limit, time_range=time_range)
    except SpotifyError:
        return []
    return [x for x in data.get("items") or [] if x and x.get("id")]


async def _recent(sp: Spotify) -> dict:
    try:
        return await sp.get("/me/player/recently-played", limit=50)
    except SpotifyError:
        return {}


async def build_magic_tracks(sp: Spotify, track_count: int) -> tuple[list[dict], list[str]]:
    short_a, medium_a, short_t, medium_t, recent = await asyncio.gather(
        _top(sp, "artists", "short_term", 20),
        _top(sp, "artists", "medium_term", 30),
        _top(sp, "tracks", "short_term", 50),
        _top(sp, "tracks", "medium_term", 50),
        _recent(sp),
    )
    recent_tracks = [track_of(i) for i in recent.get("items") or []]
    recent_tracks = [t for t in recent_tracks if t]
    artists: dict[str, dict] = {}
    for a in short_a + medium_a:
        artists.setdefault(a["id"], a)
    tracks: dict[str, dict] = {}
    for t in short_t + medium_t + recent_tracks:
        tracks.setdefault(t["id"], t)
    if not artists and not tracks:
        raise ValueError("Not enough listening history yet. Play some music and try again.")

    artist_list = list(artists.values())
    weights = [1 / (i + 2) for i in range(len(artist_list))]
    chosen_artists: list[dict] = []
    while artist_list and len(chosen_artists) < min(5, len(artists)):
        pick = random.choices(range(len(artist_list)), weights=weights)[0]
        chosen_artists.append(artist_list.pop(pick))
        weights.pop(pick)
    track_list = list(tracks.values())
    chosen_tracks = random.sample(track_list, min(4, len(track_list)))

    seeds: list[Seed] = [seed_from_artist(a) for a in chosen_artists] + [seed_from_track(t) for t in chosen_tracks]
    engine = MixEngine(sp, playlists_per_seed=4, max_playlists=30)
    mix = await engine.build(seeds, track_count, exclude=set(tracks), seed_share=0.25)
    if len(mix) < track_count:
        more = await engine.build(seeds, track_count - len(mix), exclude=set(tracks) | {t["id"] for t in mix}, seed_share=0.5)
        mix += more
    return mix[:track_count], [a["name"] for a in chosen_artists] + [t["name"] for t in chosen_tracks]


async def create_magic_playlist(sp: Spotify, playlist_name: str, track_count: int) -> dict:
    mix, seeds = await build_magic_tracks(sp, track_count)
    result = await _save_playlist(sp, playlist_name, mix, "Magic Mix")
    result["seeds"] = seeds
    return result


async def _resolve_seeds(sp: Spotify, urls: list[str]) -> list[Seed]:
    parsed: list[tuple[str, str]] = []
    for url in urls:
        try:
            item = parse_link(url)
        except ValueError:
            continue
        if item not in parsed:
            parsed.append(item)
    if not parsed:
        raise ValueError("None of the seeds are valid Spotify track, artist, album or playlist links.")

    async def resolve(kind: str, sid: str) -> list[Seed]:
        try:
            if kind == "track":
                return [seed_from_track(await sp.get(f"/tracks/{sid}", market="from_token"))]
            if kind == "artist":
                return [seed_from_artist(await sp.get(f"/artists/{sid}"))]
            if kind == "album":
                return [seed_from_album(await sp.get(f"/albums/{sid}"))]
            items = await sp.playlist_items(sid, limit=100)
        except SpotifyError:
            return []
        if not items:
            return []
        counts: dict[str, int] = {}
        names: dict[str, str] = {}
        for t in items:
            for a in (t.get("artists") or [])[:1]:
                if a.get("id"):
                    counts[a["id"]] = counts.get(a["id"], 0) + 1
                    names[a["id"]] = a.get("name") or ""
        top = sorted(counts, key=counts.get, reverse=True)[:2]
        seeds = [seed_from_artist({"id": aid, "name": names[aid]}) for aid in top]
        seeds += [seed_from_track(t) for t in random.sample(items, min(2, len(items)))]
        return seeds

    groups = await asyncio.gather(*(resolve(k, s) for k, s in parsed[:12]))
    return [seed for group in groups for seed in group]


async def create_fusion_playlist(sp: Spotify, seed_urls: list[str], playlist_name: str, track_count: int) -> dict:
    seeds = await _resolve_seeds(sp, seed_urls)
    if not seeds:
        raise ValueError("Could not read any of the seeds from Spotify.")
    per_seed = max(2, min(8, 30 // len(seeds)))
    engine = MixEngine(sp, playlists_per_seed=per_seed, max_playlists=32)
    mix = await engine.build(seeds, track_count, seed_share=0.3)
    return await _save_playlist(sp, playlist_name, mix, "Fusion Mix")


async def add_time_machine_tracks(sp: Spotify, decade: int, count: int) -> dict:
    query = f"year:{decade}-{decade + 9}"
    offsets = random.sample(range(0, 400, 25), min(16, max(3, count // 4 + 2)))

    async def page(offset: int) -> list[dict]:
        try:
            return await sp.search(query, "track", limit=50, offset=offset)
        except SpotifyError:
            return []

    pages = await asyncio.gather(*(page(o) for o in offsets))
    pool: dict[tuple[str, str], dict] = {}
    for found in pages:
        for t in found:
            year = ((t.get("album") or {}).get("release_date") or "0")[:4]
            if is_song(t) and year.isdigit() and decade <= int(year) <= decade + 9:
                pool.setdefault(song_key(t), t)
    tracks = list(pool.values())
    random.shuffle(tracks)
    if any(t.get("popularity") is not None for t in tracks):
        tracks.sort(key=lambda t: (t.get("popularity") or 0) + random.uniform(0, 35), reverse=True)
    picked: list[dict] = []
    per_artist: dict[str, int] = {}
    for t in tracks:
        artist = (t.get("artists") or [{}])[0].get("id", "")
        if per_artist.get(artist, 0) >= 2:
            continue
        per_artist[artist] = per_artist.get(artist, 0) + 1
        picked.append(t)
        if len(picked) >= count:
            break
    if not picked:
        raise ValueError("Spotify returned nothing for that decade, try again.")
    random.shuffle(picked)
    added, errors = await _queue_tracks(sp, picked)
    return {"added": added, "errors": errors, "tracks": [track_card(t) for t in picked[:12]]}


async def get_track_stats(sp: Spotify, track_url: str) -> dict:
    _, track_id = parse_link(track_url, "track")
    track = await sp.get(f"/tracks/{track_id}", market="from_token")
    linked = (track.get("linked_from") or {}).get("id")
    if track.get("id"):
        track_id = track["id"]
    album_id = (track.get("album") or {}).get("id")
    artist_refs = [a for a in track.get("artists") or [] if a.get("id")][:4]
    engine = MixEngine(sp)

    async def artist_info(ref: dict) -> dict:
        async def safe(coro, default):
            try:
                return await coro
            except SpotifyError:
                return default

        full, albums, singles, top = await asyncio.gather(
            safe(sp.get(f"/artists/{ref['id']}"), ref),
            safe(sp.get(f"/artists/{ref['id']}/albums", include_groups="album", limit=1), {}),
            safe(sp.get(f"/artists/{ref['id']}/albums", include_groups="single", limit=1), {}),
            safe(engine.artist_tracks(ref["id"], ref.get("name")), []),
        )
        card = artist_card(full)
        card["albums_total"] = albums.get("total")
        card["singles_total"] = singles.get("total")
        card["top_tracks"] = [
            {"name": t.get("name"), "url": track_card(t)["url"], "image": image_of(t.get("album"), 2), "current": t.get("id") in (track_id, linked) or t.get("name") == track.get("name")}
            for t in top[:5]
        ]
        return card

    album_task = sp.get(f"/albums/{album_id}") if album_id else asyncio.sleep(0, result={})
    album, artists = await asyncio.gather(album_task, asyncio.gather(*(artist_info(a) for a in artist_refs)))
    album = album or track.get("album") or {}
    album_tracks = [t for t in ((album.get("tracks") or {}).get("items") or []) if t]

    def is_current(t: dict) -> bool:
        if t.get("id") in (track_id, linked):
            return True
        return t.get("track_number") == track.get("track_number") and t.get("disc_number") == track.get("disc_number") and t.get("name") == track.get("name")

    total_ms = sum(t.get("duration_ms") or 0 for t in album_tracks)
    position = next((i for i, t in enumerate(album_tracks) if is_current(t)), None)
    return {
        "track": {
            "name": track.get("name"),
            "url": track_card(track)["url"],
            "popularity": track.get("popularity"),
            "explicit": bool(track.get("explicit")),
            "duration_ms": track.get("duration_ms") or 0,
            "track_number": track.get("track_number"),
            "disc_number": track.get("disc_number"),
            "isrc": (track.get("external_ids") or {}).get("isrc"),
            "preview_url": track.get("preview_url"),
            "playable": track.get("is_playable"),
            "album_position": position + 1 if position is not None else None,
        },
        "album": {
            "name": album.get("name"),
            "url": (album.get("external_urls") or {}).get("spotify"),
            "album_type": album.get("album_type"),
            "release_date": album.get("release_date") or "",
            "release_date_precision": album.get("release_date_precision"),
            "total_tracks": album.get("total_tracks"),
            "duration_ms": total_ms or None,
            "image": image_of(album),
            "label": album.get("label") or None,
            "popularity": album.get("popularity"),
            "copyright": next((c.get("text") for c in album.get("copyrights") or [] if c.get("text")), None),
            "tracks": [
                {"name": t.get("name"), "duration_ms": t.get("duration_ms") or 0, "number": t.get("track_number"), "current": is_current(t)}
                for t in album_tracks[:40]
            ],
        },
        "artists": list(artists),
    }


async def get_now_playing(sp: Spotify) -> dict:
    current = await sp.get("/me/player/currently-playing", additional_types="track,episode")
    item = current.get("item") if current else None
    if not item:
        return {"playing": False}
    if item.get("type") == "episode":
        show = item.get("show") or {}
        artists = [show.get("name") or "Podcast"]
        image = image_of(item) or image_of(show)
        album = show.get("name")
    else:
        artists = [a.get("name") for a in item.get("artists") or []]
        image = image_of(item.get("album"))
        album = (item.get("album") or {}).get("name")
    return {
        "playing": True,
        "is_playing": bool(current.get("is_playing")),
        "track": {
            "id": item.get("id"),
            "type": item.get("type", "track"),
            "name": item.get("name"),
            "artists": artists,
            "album": album,
            "image": image,
            "url": (item.get("external_urls") or {}).get("spotify"),
            "progress_ms": current.get("progress_ms") or 0,
            "duration_ms": item.get("duration_ms") or 0,
        },
    }


async def playback(sp: Spotify, action: str) -> dict:
    if action == "skip":
        await sp.post("/me/player/next")
    elif action == "previous":
        await sp.post("/me/player/previous")
    elif action == "play":
        await sp.put("/me/player/play")
    elif action == "pause":
        await sp.put("/me/player/pause")
    else:
        raise ValueError("Unknown playback action")
    return {action: True}


async def get_user_playlists(sp: Spotify, limit: int = 50, offset: int = 0) -> dict:
    data = await sp.get("/me/playlists", limit=limit, offset=offset)
    me = await sp.me()
    playlists = []
    for p in data.get("items") or []:
        if not p or not p.get("id"):
            continue
        owner = p.get("owner") or {}
        playlists.append(
            {
                "id": p["id"],
                "name": p.get("name") or "Untitled",
                "url": (p.get("external_urls") or {}).get("spotify") or f"https://open.spotify.com/playlist/{p['id']}",
                "image": image_of(p),
                "tracks_total": ((p.get("items") or p.get("tracks")) or {}).get("total") or 0,
                "owner": owner.get("display_name") or owner.get("id"),
                "own": owner.get("id") == me.get("id") or bool(p.get("collaborative")),
            }
        )
    return {"playlists": playlists, "total": data.get("total", len(playlists))}


async def get_top_tracks(sp: Spotify, limit: int = 50, time_range: str = "medium_term") -> dict:
    data = await sp.get("/me/top/tracks", limit=limit, time_range=time_range)
    return {"tracks": [track_card(t) for t in data.get("items") or [] if t]}


async def get_top_artists(sp: Spotify, limit: int = 50, time_range: str = "medium_term") -> dict:
    data = await sp.get("/me/top/artists", limit=limit, time_range=time_range)
    return {"artists": [artist_card(a) for a in data.get("items") or [] if a]}


async def get_top_genres(sp: Spotify, limit: int = 50, time_range: str = "medium_term") -> dict:
    data = await sp.get("/me/top/artists", limit=50, time_range=time_range)
    items = [a for a in data.get("items") or [] if a]
    counts: dict[str, float] = {}
    tagged = 0
    for rank, a in enumerate(items):
        genres = a.get("genres") or []
        if genres:
            tagged += 1
        for g in genres:
            counts[g] = counts.get(g, 0) + 1 + (50 - rank) / 100
    ordered = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    raw = {g: sum(1 for a in items if g in (a.get("genres") or [])) for g, _ in ordered}
    return {
        "genres": [{"name": g, "count": raw[g]} for g, _ in ordered],
        "artists_total": len(items),
        "artists_tagged": tagged,
    }


async def search_spotify(sp: Spotify, query: str, limit: int = 10) -> dict:
    limit = max(1, min(limit, sp.search_limit, 50))
    try:
        data = await sp.get("/search", q=query, type="track,artist,album", limit=limit)
    except SpotifyError as exc:
        if exc.status != 400 or limit <= 10:
            raise
        sp.search_limit = 10
        data = await sp.get("/search", q=query, type="track,artist,album", limit=10)
    return {
        "tracks": [track_card(t) for t in (data.get("tracks") or {}).get("items") or [] if t],
        "artists": [artist_card(a) for a in (data.get("artists") or {}).get("items") or [] if a],
        "albums": [album_card(a) for a in (data.get("albums") or {}).get("items") or [] if a],
    }


async def get_fusion_suggestions(sp: Spotify) -> dict:
    async def safe(coro):
        try:
            return await coro
        except SpotifyError:
            return {}

    recent, top_t, top_a = await asyncio.gather(
        safe(sp.get("/me/player/recently-played", limit=30)),
        safe(sp.get("/me/top/tracks", limit=12, time_range="short_term")),
        safe(sp.get("/me/top/artists", limit=12, time_range="short_term")),
    )
    recent_tracks: list[dict] = []
    seen: set[str] = set()
    for entry in recent.get("items") or []:
        t = track_of(entry)
        if t and t["id"] not in seen:
            seen.add(t["id"])
            recent_tracks.append(track_card(t))
        if len(recent_tracks) >= 12:
            break
    return {
        "recent_tracks": recent_tracks,
        "top_tracks": [track_card(t) for t in top_t.get("items") or [] if t],
        "top_artists": [artist_card(a) for a in top_a.get("items") or [] if a],
    }


REWIND_SOURCES = {
    "recent": "Recently Played",
    "short_term": "Last 4 Weeks",
    "medium_term": "Last 6 Months",
    "long_term": "All Time",
}


async def rewind_tracks(sp: Spotify, source: str, count: int) -> list[dict]:
    if source == "recent":
        data = await sp.get("/me/player/recently-played", limit=50)
        tracks = [t for t in (track_of(i) for i in data.get("items") or []) if t]
    else:
        tracks = []
        for offset in range(0, count, 50):
            data = await sp.get("/me/top/tracks", limit=min(50, count - offset), offset=offset, time_range=source)
            items = [t for t in data.get("items") or [] if t and t.get("id")]
            tracks += items
            if len(items) < 50:
                break
    unique: dict[str, dict] = {}
    for t in tracks:
        unique.setdefault(t["id"], t)
    picked = list(unique.values())[:count]
    if not picked:
        raise ValueError("Nothing to rewind yet, listen to some music first.")
    return picked


async def create_rewind_playlist(sp: Spotify, source: str, playlist_name: str | None, count: int) -> dict:
    picked = await rewind_tracks(sp, source, count)
    return await _save_playlist(sp, playlist_name or "", picked, f"Rewind: {REWIND_SOURCES[source]}")


async def get_queue(sp: Spotify) -> dict:
    data = await sp.get("/me/player/queue")
    current = data.get("currently_playing")
    upcoming = [t for t in data.get("queue") or [] if t and t.get("type", "track") == "track"]
    return {
        "current": track_card(current) if current and current.get("type", "track") == "track" else None,
        "queue": [track_card(t) for t in upcoming[:30]],
        "note": "Spotify only lets apps append to the queue, so new tracks play after your queued ones and before the rest of the playlist.",
    }


async def seek(sp: Spotify, position_ms: int) -> dict:
    await sp.put("/me/player/seek", position_ms=position_ms)
    return {"position_ms": position_ms}
