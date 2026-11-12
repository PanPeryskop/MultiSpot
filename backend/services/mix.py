import asyncio
import math
import random
import re
from dataclasses import dataclass, field

from services.client import Spotify, SpotifyError

_TAIL = re.compile(r"\s*[\(\[\-–].*$")
FILLER = re.compile(r"\b(skit|interlude|intro|outro|instrumentale?)\b", re.I)


def is_song(track: dict) -> bool:
    duration = track.get("duration_ms") or 0
    return bool(track.get("id")) and (duration == 0 or duration >= 75000) and not FILLER.search(track.get("name") or "")


def song_key(track: dict) -> tuple[str, str]:
    name = _TAIL.sub("", (track.get("name") or "").lower()).strip() or (track.get("name") or "").lower()
    artists = track.get("artists") or [{}]
    return name, (artists[0].get("id") or artists[0].get("name") or "")


def primary_artist(track: dict) -> str:
    artists = track.get("artists") or [{}]
    return artists[0].get("id") or ""


@dataclass
class Seed:
    queries: list[str]
    artist_ids: set[str] = field(default_factory=set)
    artist_names: dict[str, str] = field(default_factory=dict)
    track: dict | None = None


def seed_from_track(track: dict) -> Seed:
    artists = [a for a in track.get("artists") or [] if a.get("id")]
    lead = artists[0]["name"] if artists else ""
    queries = [f"{track.get('name', '')} {lead}".strip()]
    if lead:
        queries += [lead, f"{lead} radio"]
    return Seed(queries, {a["id"] for a in artists[:2]}, {a["id"]: a["name"] for a in artists[:2]}, track)


def seed_from_artist(artist: dict) -> Seed:
    return Seed([artist["name"], f"{artist['name']} radio"], {artist["id"]}, {artist["id"]: artist["name"]})


def seed_from_album(album: dict) -> Seed:
    artists = [a for a in album.get("artists") or [] if a.get("id")]
    lead = artists[0]["name"] if artists else ""
    queries = [f"{album.get('name', '')} {lead}".strip()]
    if lead:
        queries.append(lead)
    return Seed(queries, {a["id"] for a in artists[:2]}, {a["id"]: a["name"] for a in artists[:2]})


class MixEngine:
    def __init__(self, sp: Spotify, playlists_per_seed: int = 5, max_playlists: int = 32):
        self.sp = sp
        self.rng = random.Random()
        self.playlists_per_seed = playlists_per_seed
        self.max_playlists = max_playlists
        self._artist_tracks: dict[str, list[dict]] = {}
        self._playlist_tracks: dict[str, list[dict]] = {}
        self._top_tracks_ok = True

    async def artist_tracks(self, artist_id: str, name: str | None = None) -> list[dict]:
        if artist_id in self._artist_tracks:
            return self._artist_tracks[artist_id]
        tracks: list[dict] = []
        if self._top_tracks_ok:
            try:
                data = await self.sp.get(f"/artists/{artist_id}/top-tracks", market="from_token")
                tracks = [t for t in data.get("tracks") or [] if t and t.get("id")]
            except SpotifyError as exc:
                if exc.status in (403, 404, 410):
                    self._top_tracks_ok = False
        if len(tracks) < 6 and name:
            try:
                found = await self.sp.search(f'artist:"{name}"', "track", limit=30)
                tracks += [t for t in found if any(a.get("id") == artist_id for a in t.get("artists") or [])]
            except SpotifyError:
                pass
        if len(tracks) < 4:
            tracks += await self._album_tracks(artist_id)
        unique: dict[tuple[str, str], dict] = {}
        for t in tracks:
            unique.setdefault(song_key(t), t)
        self._artist_tracks[artist_id] = list(unique.values())
        return self._artist_tracks[artist_id]

    async def _album_tracks(self, artist_id: str) -> list[dict]:
        try:
            albums = await self.sp.get(f"/artists/{artist_id}/albums", include_groups="album,single", limit=10)
        except SpotifyError:
            return []
        picks = [a for a in albums.get("items") or [] if a][:4]
        out: list[dict] = []
        for album in picks:
            try:
                data = await self.sp.get(f"/albums/{album['id']}/tracks", limit=20)
            except SpotifyError:
                continue
            for t in data.get("items") or []:
                if t and t.get("id"):
                    out.append({**t, "album": {"id": album["id"], "name": album.get("name"), "images": album.get("images") or []}})
        return out

    async def _playlists_for(self, query: str) -> list[dict]:
        try:
            found = await self.sp.search(query, "playlist", limit=20)
        except SpotifyError:
            return []
        out = []
        for p in found:
            owner = (p.get("owner") or {}).get("id")
            total = ((p.get("items") or p.get("tracks")) or {}).get("total") or 0
            if owner == "spotify" or not 15 <= total <= 600:
                continue
            out.append({"id": p["id"], "total": total, "name": (p.get("name") or "").lower()})
        return out

    async def playlist_tracks(self, playlist_id: str, total: int = 0) -> list[dict]:
        if playlist_id in self._playlist_tracks:
            return self._playlist_tracks[playlist_id]
        offset = 0
        try:
            tracks = await self.sp.playlist_items(playlist_id, limit=100, offset=offset)
        except SpotifyError:
            tracks = []
        self._playlist_tracks[playlist_id] = tracks
        return tracks

    async def _gather_playlists(self, seeds: list[Seed]) -> list[tuple[int, dict]]:
        query_jobs = [(i, q) for i, s in enumerate(seeds) for q in s.queries]
        results = await asyncio.gather(*(self._playlists_for(q) for _, q in query_jobs))
        per_seed: dict[int, list[dict]] = {}
        seen: set[str] = set()
        for (i, _), found in zip(query_jobs, results, strict=True):
            bucket = per_seed.setdefault(i, [])
            for p in found:
                if p["id"] in seen or len(bucket) >= self.playlists_per_seed:
                    continue
                seen.add(p["id"])
                bucket.append(p)
        budget = max(2, self.max_playlists // max(1, len(seeds)))
        chosen = []
        for i, bucket in per_seed.items():
            for p in bucket[:budget]:
                chosen.append((i, p))
        return chosen[: self.max_playlists]

    async def build(
        self,
        seeds: list[Seed],
        target: int,
        exclude: set[str] | None = None,
        pinned: list[dict] | None = None,
        seed_share: float = 0.25,
    ) -> list[dict]:
        exclude = set(exclude or ())
        pinned = [t for t in pinned or [] if t and t.get("id")]
        seed_artists: dict[str, str] = {}
        for s in seeds:
            seed_artists.update(s.artist_names)

        chosen_playlists, seed_pools = await asyncio.gather(
            self._gather_playlists(seeds),
            asyncio.gather(*(self.artist_tracks(aid, name) for aid, name in list(seed_artists.items())[:14])),
        )
        playlist_tracks = await asyncio.gather(*(self.playlist_tracks(p["id"], p["total"]) for _, p in chosen_playlists))

        score: dict[str, float] = {}
        plays: dict[str, int] = {}
        hits: dict[str, set[int]] = {}
        meta: dict[str, dict] = {}
        artist_score: dict[str, float] = {}
        artist_names: dict[str, str] = {}
        seed_ids_all = {aid for s in seeds for aid in s.artist_ids}
        seed_titles = {song_key(s.track)[0] for s in seeds if s.track}
        for pool in seed_pools:
            seed_titles.update(song_key(t)[0] for t in pool[:10])
        seed_titles = {t for t in seed_titles if len(t) >= 4}

        def derivative(track: dict) -> bool:
            if primary_artist(track) in seed_ids_all:
                return False
            name = (track.get("name") or "").lower()
            return any(title in name for title in seed_titles)

        for (seed_index, playlist), tracks in zip(chosen_playlists, playlist_tracks, strict=True):
            if not tracks:
                continue
            seed = seeds[seed_index]
            own = sum(1 for t in tracks if primary_artist(t) in seed.artist_ids)
            if is_spam(tracks, seed_ids_all):
                continue
            weight = 0.15 + min(1.0, 6 * own / len(tracks))
            if seed.track and any(t["id"] == seed.track.get("id") for t in tracks):
                weight += 0.4
            if any(name and name.lower() in playlist["name"] for name in seed.artist_names.values()):
                weight += 0.5
            seen_here: set[str] = set()
            artist_here: dict[str, int] = {}
            for t in tracks:
                tid = t["id"]
                if tid in seen_here:
                    continue
                if derivative(t):
                    continue
                lead = primary_artist(t)
                artist_here[lead] = artist_here.get(lead, 0) + 1
                if artist_here[lead] > 3 and lead not in seed.artist_ids:
                    continue
                seen_here.add(tid)
                plays[tid] = plays.get(tid, 0) + 1
                score[tid] = score.get(tid, 0.0) + weight
                hits.setdefault(tid, set()).add(seed_index)
                meta.setdefault(tid, t)
                artist_names.setdefault(lead, ((t.get("artists") or [{}])[0]).get("name") or "")
            for lead in artist_here:
                if lead:
                    artist_score[lead] = artist_score.get(lead, 0.0) + weight

        cap = max(2, math.ceil(target / 10))
        picked: list[dict] = []
        used_ids: set[str] = set()
        used_keys: set[tuple[str, str]] = set()
        per_artist: dict[str, int] = {}

        def take(track: dict, limit: int) -> bool:
            tid = track.get("id")
            if not tid or tid in used_ids or tid in exclude or not is_song(track):
                return False
            key = song_key(track)
            if key in used_keys:
                return False
            artist = primary_artist(track)
            if per_artist.get(artist, 0) >= limit:
                return False
            picked.append(track)
            used_ids.add(tid)
            used_keys.add(key)
            per_artist[artist] = per_artist.get(artist, 0) + 1
            return True

        for t in pinned:
            take(t, target)
            exclude.discard(t["id"])

        quota = len(picked) + round(target * seed_share)
        pools = [list(p) for p in seed_pools if p]
        for pool in pools:
            self.rng.shuffle(pool)
        while len(picked) < min(quota, target) and any(pools):
            for pool in pools:
                while pool:
                    if take(pool.pop(), cap + 1):
                        break
                if len(picked) >= min(quota, target):
                    break

        ranked = sorted(
            score,
            key=lambda tid: score[tid] * (1 + 0.7 * (len(hits[tid]) - 1)) * (1.0 if plays[tid] > 1 else 0.3) + self.rng.uniform(0, 0.6),
            reverse=True,
        )
        for tid in ranked:
            if len(picked) >= target:
                break
            take(meta[tid], cap)

        if len(picked) < target:
            neighbours = [
                aid
                for aid in sorted(artist_score, key=lambda a: artist_score[a] + self.rng.uniform(0, 0.5), reverse=True)
                if per_artist.get(aid, 0) < cap
            ][:16]
            extra = await asyncio.gather(*(self.artist_tracks(aid, artist_names.get(aid)) for aid in neighbours))
            extra_pools = [list(p) for p in extra if p] + [list(p) for p in seed_pools if p]
            for pool in extra_pools:
                self.rng.shuffle(pool)
            for limit in (cap, cap * 2, target):
                progress = True
                while len(picked) < target and progress:
                    progress = False
                    for pool in extra_pools:
                        while pool:
                            if take(pool.pop(), limit):
                                progress = True
                                break
                        if len(picked) >= target:
                            break
                if len(picked) >= target:
                    break
                for tid in ranked:
                    if len(picked) >= target:
                        break
                    take(meta[tid], limit)

        head = picked[: len(pinned)]
        body = picked[len(pinned) :]
        self.rng.shuffle(body)
        return head + spread(body)


def is_spam(tracks: list[dict], seed_artists: set[str]) -> bool:
    if len(tracks) < 12:
        return True
    foreign: dict[str, int] = {}
    for t in tracks:
        lead = primary_artist(t)
        if lead not in seed_artists:
            foreign[lead] = foreign.get(lead, 0) + 1
    if not foreign:
        return False
    top = sum(sorted(foreign.values(), reverse=True)[:3])
    return top / len(tracks) > 0.45


def spread(tracks: list[dict]) -> list[dict]:
    out: list[dict] = []
    rest = list(tracks)
    while rest:
        last = primary_artist(out[-1]) if out else None
        index = next((i for i, t in enumerate(rest) if primary_artist(t) != last), 0)
        out.append(rest.pop(index))
    return out
