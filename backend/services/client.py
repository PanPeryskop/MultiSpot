import asyncio
import base64
import os
import time
from typing import Any
from urllib.parse import urlencode

import httpx

API = "https://api.spotify.com/v1"
ACCOUNTS = "https://accounts.spotify.com"

SCOPE = " ".join(
    [
        "playlist-read-private",
        "playlist-read-collaborative",
        "playlist-modify-public",
        "playlist-modify-private",
        "user-modify-playback-state",
        "user-read-playback-state",
        "user-read-currently-playing",
        "user-read-recently-played",
        "user-top-read",
    ]
)

_http: httpx.AsyncClient | None = None


def http() -> httpx.AsyncClient:
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=10.0),
            limits=httpx.Limits(max_connections=40, max_keepalive_connections=20),
        )
    return _http


async def close_http():
    global _http
    if _http is not None and not _http.is_closed:
        await _http.aclose()
    _http = None


class SpotifyError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _credentials() -> tuple[str, str, str]:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect = os.getenv("SPOTIFY_REDIRECT_URI")
    if not client_id or not secret or not redirect:
        raise SpotifyError(500, "Spotify credentials are not configured on the server")
    return client_id, secret, redirect


def authorize_url(state: str) -> str:
    client_id, _, redirect = _credentials()
    query = urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect,
            "scope": SCOPE,
            "state": state,
            "show_dialog": "true",
        }
    )
    return f"{ACCOUNTS}/authorize?{query}"


async def _token_request(data: dict) -> dict:
    client_id, secret, _ = _credentials()
    basic = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    try:
        response = await http().post(
            f"{ACCOUNTS}/api/token",
            data=data,
            headers={"Authorization": f"Basic {basic}"},
        )
    except httpx.HTTPError as exc:
        raise SpotifyError(502, "Could not reach Spotify") from exc
    payload = _json(response)
    if response.status_code >= 400:
        detail = payload.get("error_description") or payload.get("error") or "Spotify login failed"
        raise SpotifyError(401 if response.status_code in (400, 401) else 502, str(detail))
    payload["expires_at"] = int(time.time()) + int(payload.get("expires_in", 3600))
    return payload


async def exchange_code(code: str) -> dict:
    _, _, redirect = _credentials()
    return await _token_request({"grant_type": "authorization_code", "code": code, "redirect_uri": redirect})


async def refresh_token(token: dict) -> dict:
    refresh = token.get("refresh_token")
    if not refresh:
        raise SpotifyError(401, "Session expired, log in again")
    fresh = await _token_request({"grant_type": "refresh_token", "refresh_token": refresh})
    fresh.setdefault("refresh_token", refresh)
    return fresh


def _json(response: httpx.Response) -> dict:
    if not response.content:
        return {}
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {"items": data}


def _error_message(status: int, payload: dict) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message") or ""
        reason = error.get("reason") or ""
        if reason == "NO_ACTIVE_DEVICE":
            return "No active Spotify device. Start playing something on any device first."
        if reason == "PREMIUM_REQUIRED":
            return "Spotify Premium is required for playback control."
        if message:
            return message
    elif isinstance(error, str):
        return error
    return {
        401: "Session expired, log in again",
        403: "Spotify refused this action",
        404: "Not found on Spotify",
        429: "Spotify rate limit hit, try again in a moment",
    }.get(status, f"Spotify error ({status})")


class Spotify:
    def __init__(self, token: dict, concurrency: int = 8):
        self.token = dict(token)
        self.changed = False
        self._lock = asyncio.Lock()
        self._gate = asyncio.Semaphore(concurrency)
        self._me: dict | None = None
        self.search_limit = 50

    async def _ensure_fresh(self):
        if self.token.get("expires_at", 0) - time.time() > 60:
            return
        async with self._lock:
            if self.token.get("expires_at", 0) - time.time() > 60:
                return
            self.token = await refresh_token(self.token)
            self.changed = True

    async def request(self, method: str, path: str, *, params: dict | None = None, json: Any = None, retries: int = 4) -> dict:
        await self._ensure_fresh()
        url = path if path.startswith("http") else f"{API}{path}"
        clean = {k: v for k, v in (params or {}).items() if v is not None}
        refreshed = False
        attempt = 0
        while True:
            attempt += 1
            async with self._gate:
                try:
                    response = await http().request(
                        method,
                        url,
                        params=clean or None,
                        json=json,
                        headers={"Authorization": f"Bearer {self.token['access_token']}"},
                    )
                except httpx.HTTPError as exc:
                    if attempt <= retries:
                        await asyncio.sleep(0.5 * attempt)
                        continue
                    raise SpotifyError(502, "Could not reach Spotify") from exc
            status = response.status_code
            if status == 429 and attempt <= retries:
                wait = min(float(response.headers.get("Retry-After", "1") or 1), 10.0)
                await asyncio.sleep(max(wait, 0.5))
                continue
            if status >= 500 and attempt <= retries:
                await asyncio.sleep(0.6 * attempt)
                continue
            if status == 401 and not refreshed:
                refreshed = True
                async with self._lock:
                    self.token = await refresh_token(self.token)
                    self.changed = True
                continue
            payload = _json(response)
            if status >= 400:
                raise SpotifyError(status, _error_message(status, payload))
            return payload

    async def get(self, path: str, **params) -> dict:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, body: Any = None, **params) -> dict:
        return await self.request("POST", path, params=params, json=body)

    async def put(self, path: str, body: Any = None, **params) -> dict:
        return await self.request("PUT", path, params=params, json=body)

    async def delete(self, path: str, body: Any = None, **params) -> dict:
        return await self.request("DELETE", path, params=params, json=body)

    async def me(self) -> dict:
        if self._me is None:
            self._me = await self.get("/me")
        return self._me

    async def search(self, query: str, kind: str, limit: int = 50, offset: int = 0) -> list[dict]:
        key = f"{kind}s"
        out: list[dict] = []
        while len(out) < limit and offset < 1000:
            step = min(self.search_limit, limit - len(out), 1000 - offset)
            try:
                data = await self.get("/search", q=query, type=kind, limit=step, offset=offset)
            except SpotifyError as exc:
                if exc.status == 400 and self.search_limit > 10 and "limit" in exc.message.lower():
                    self.search_limit = 10
                    continue
                if exc.status == 400 and out:
                    break
                raise
            page = data.get(key) or {}
            items = [i for i in page.get("items") or [] if i]
            out.extend(items)
            if not items or not page.get("next"):
                break
            offset += step
        return out

    async def playlist_items(self, playlist_id: str, limit: int | None = None, offset: int = 0) -> list[dict]:
        out: list[dict] = []
        path = f"/playlists/{playlist_id}/items"
        fallback = f"/playlists/{playlist_id}/tracks"
        while True:
            step = 100 if limit is None else min(100, limit - len(out))
            if step <= 0:
                break
            try:
                data = await self.get(path, limit=step, offset=offset, additional_types="track")
            except SpotifyError as exc:
                if exc.status in (403, 404) and path != fallback:
                    path = fallback
                    continue
                raise
            items = data.get("items") or []
            for entry in items:
                track = track_of(entry)
                if track:
                    out.append(track)
            if not items or not data.get("next"):
                break
            offset += len(items)
        return out

    async def create_playlist(self, name: str, description: str = "", public: bool = False) -> dict:
        body = {"name": name[:100] or "MultiSpot", "public": public, "description": description[:300]}
        try:
            return await self.post("/me/playlists", body)
        except SpotifyError as exc:
            if exc.status not in (403, 404, 405):
                raise
        me = await self.me()
        return await self.post(f"/users/{me['id']}/playlists", body)

    async def add_to_playlist(self, playlist_id: str, uris: list[str]):
        path = f"/playlists/{playlist_id}/items"
        for i in range(0, len(uris), 100):
            chunk = uris[i : i + 100]
            try:
                await self.post(path, {"uris": chunk})
            except SpotifyError as exc:
                if exc.status in (403, 404) and path.endswith("/items"):
                    path = f"/playlists/{playlist_id}/tracks"
                    await self.post(path, {"uris": chunk})
                else:
                    raise

    async def unfollow_playlist(self, playlist_id: str):
        try:
            await self.delete(f"/playlists/{playlist_id}/followers")
        except SpotifyError as exc:
            if exc.status not in (403, 404, 405):
                raise
            await self.delete("/me/library", uris=f"spotify:playlist:{playlist_id}")

    async def queue(self, uri: str):
        await self.post("/me/player/queue", uri=uri)


def track_of(entry: dict | None) -> dict | None:
    if not entry:
        return None
    track = entry.get("item") or entry.get("track")
    if not isinstance(track, dict):
        return None
    if track.get("type", "track") != "track" or track.get("is_local") or not track.get("id"):
        return None
    return track
