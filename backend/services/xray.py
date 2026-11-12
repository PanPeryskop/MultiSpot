from collections import Counter

from services.client import Spotify
from services.mix import song_key
from services.spotify import image_of, parse_link, track_card


def _mini(t: dict) -> dict:
    card = track_card(t)
    return {k: card[k] for k in ("id", "name", "artists", "image", "url", "duration_ms", "popularity")}


def _year(t: dict) -> int | None:
    raw = ((t.get("album") or {}).get("release_date") or "")[:4]
    return int(raw) if raw.isdigit() and raw != "0000" else None


async def playlist_xray(sp: Spotify, playlist_url: str) -> dict:
    _, pid = parse_link(playlist_url, "playlist")
    meta = await sp.get(
        f"/playlists/{pid}",
        fields="id,name,description,public,collaborative,images,owner(id,display_name),followers(total),external_urls",
    )
    entries, skipped = await sp.playlist_entries(pid, limit=2000, market="from_token")
    tracks = [e["track"] for e in entries]

    duration = sum(t.get("duration_ms") or 0 for t in tracks)
    artist_counts: Counter = Counter()
    artist_names: dict[str, str] = {}
    for t in tracks:
        for a in t.get("artists") or []:
            if a.get("id"):
                artist_counts[a["id"]] += 1
                artist_names[a["id"]] = a.get("name") or ""
    albums = {(t.get("album") or {}).get("id") for t in tracks if (t.get("album") or {}).get("id")}
    explicit = sum(1 for t in tracks if t.get("explicit"))
    pops = [t["popularity"] for t in tracks if isinstance(t.get("popularity"), int)]

    decades: Counter = Counter()
    years: list[tuple[int, dict]] = []
    for t in tracks:
        year = _year(t)
        if year:
            decades[f"{year // 10 * 10}s"] += 1
            years.append((year, t))

    added: Counter = Counter()
    for e in entries:
        stamp = (e.get("added_at") or "")[:4]
        if stamp.isdigit() and stamp != "1970":
            added[stamp] += 1

    by_id: Counter = Counter(t["id"] for t in tracks)
    by_song: dict[tuple[str, str], list[dict]] = {}
    for t in tracks:
        by_song.setdefault(song_key(t), []).append(t)
    duplicates = []
    for group in by_song.values():
        if len(group) > 1:
            first = group[0]
            exact = by_id[first["id"]] > 1
            duplicates.append({**_mini(first), "count": len(group), "exact": exact})
    duplicates.sort(key=lambda d: d["count"], reverse=True)

    unavailable = [_mini(t) for t in tracks if t.get("is_playable") is False]
    by_length = sorted(tracks, key=lambda t: t.get("duration_ms") or 0)
    years.sort(key=lambda x: x[0])

    owner = meta.get("owner") or {}
    return {
        "playlist": {
            "id": meta.get("id"),
            "name": meta.get("name"),
            "description": meta.get("description") or None,
            "owner": owner.get("display_name") or owner.get("id"),
            "image": image_of(meta),
            "url": (meta.get("external_urls") or {}).get("spotify") or f"https://open.spotify.com/playlist/{pid}",
            "followers": (meta.get("followers") or {}).get("total"),
            "public": meta.get("public"),
            "collaborative": bool(meta.get("collaborative")),
        },
        "totals": {
            "tracks": len(tracks),
            "skipped": skipped,
            "duration_ms": duration,
            "artists": len(artist_counts),
            "albums": len(albums),
            "explicit_pct": round(explicit * 100 / len(tracks)) if tracks else 0,
            "avg_popularity": round(sum(pops) / len(pops)) if pops else None,
            "avg_year": round(sum(y for y, _ in years) / len(years)) if years else None,
        },
        "top_artists": [
            {"id": aid, "name": artist_names[aid], "count": n, "share": round(n * 100 / len(tracks)) if tracks else 0, "url": f"https://open.spotify.com/artist/{aid}"}
            for aid, n in artist_counts.most_common(10)
        ],
        "decades": [{"decade": d, "count": n} for d, n in sorted(decades.items())],
        "added_by_year": [{"year": y, "count": n} for y, n in sorted(added.items())],
        "duplicates": duplicates[:30],
        "unavailable": unavailable[:50],
        "extremes": {
            "oldest": {**_mini(years[0][1]), "year": years[0][0]} if years else None,
            "newest": {**_mini(years[-1][1]), "year": years[-1][0]} if years else None,
            "shortest": _mini(by_length[0]) if tracks else None,
            "longest": _mini(by_length[-1]) if tracks else None,
        },
        "most_popular": [_mini(t) for t in sorted(tracks, key=lambda t: t.get("popularity") or 0, reverse=True)[:5]] if pops else [],
        "least_popular": [_mini(t) for t in sorted(tracks, key=lambda t: t.get("popularity") or 0)[:5]] if pops else [],
    }
