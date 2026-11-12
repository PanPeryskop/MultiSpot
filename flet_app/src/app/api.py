from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

SESSION_COOKIE = "session"


class ApiError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.message = message
        self.status = status

    @property
    def unauthorized(self) -> bool:
        return self.status == 401


class Api:
    def __init__(self, base_url: str, session: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = session
        self.on_session_change: Callable[[str | None], None] | None = None
        self.on_unauthorized: Callable[[], None] | None = None
        self._client = self._make_client()

    def _make_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            follow_redirects=False,
            timeout=httpx.Timeout(20.0, read=300.0),
        )

    async def set_base_url(self, base_url: str):
        await self._client.aclose()
        self.base_url = base_url.rstrip("/")
        self._client = self._make_client()

    def _headers(self) -> dict[str, str]:
        if self.session:
            return {"Cookie": f"{SESSION_COOKIE}={self.session}"}
        return {}

    def _capture_session(self, response: httpx.Response):
        for header in response.headers.get_list("set-cookie"):
            name, _, rest = header.partition("=")
            if name.strip() != SESSION_COOKIE:
                continue
            value = rest.split(";", 1)[0].strip()
            expired = value in ("", "null") or "1970" in header
            new_value = None if expired else value
            if new_value != self.session:
                self.session = new_value
                if self.on_session_change:
                    self.on_session_change(new_value)

    async def _send(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        self._client.cookies.clear()
        try:
            response = await self._client.request(method, path, headers=self._headers(), **kwargs)
        except httpx.TimeoutException as exc:
            raise ApiError("Server took too long to respond") from exc
        except httpx.HTTPError as exc:
            raise ApiError(f"Can't reach server at {self.base_url}") from exc
        self._capture_session(response)
        return response

    async def request(self, method: str, path: str, **kwargs: Any) -> dict:
        response = await self._send(method, path, **kwargs)
        try:
            data = response.json()
        except ValueError:
            data = {}
        if response.status_code >= 400:
            detail = data.get("detail") if isinstance(data, dict) else None
            if isinstance(detail, list):
                detail = "; ".join(str(d.get("msg", d)) for d in detail)
            if response.status_code == 401 and self.on_unauthorized and not path.startswith("/auth"):
                self.on_unauthorized()
            raise ApiError(detail or _status_message(response.status_code), response.status_code)
        if isinstance(data, dict):
            data.pop("token", None)
            return data
        return {"items": data}

    async def get(self, path: str, **params: Any) -> dict:
        return await self.request("GET", path, params={k: v for k, v in params.items() if v is not None})

    async def post(self, path: str, body: dict | None = None) -> dict:
        return await self.request("POST", path, json=body)

    async def ping(self) -> bool:
        try:
            response = await self._send("GET", "/auth/me")
        except ApiError:
            return False
        return response.status_code in (200, 401)

    async def authorize_url(self) -> str:
        response = await self._send("GET", "/auth/login")
        location = response.headers.get("location")
        if not location:
            raise ApiError("Backend did not return a Spotify login URL", response.status_code)
        return location

    async def exchange(self, code: str, state: str) -> dict:
        return await self.post("/auth/exchange", {"code": code, "state": state})

    async def me(self) -> dict:
        return await self.get("/auth/me")

    async def logout(self):
        try:
            await self.post("/auth/logout")
        finally:
            self.session = None
            if self.on_session_change:
                self.on_session_change(None)

    async def playlists(self, offset: int = 0, limit: int = 50) -> dict:
        return await self.get("/api/playlists", limit=limit, offset=offset)

    async def random_hub(self, count: int, playlist_name: str | None, genre: str | None = None, to_playlist: bool = False) -> dict:
        if not to_playlist:
            return await self.post("/api/random-hub/queue", {"count": count, "genre": genre})
        return await self.post("/api/random-hub/playlist", {"count": count, "playlist_name": playlist_name, "genre": genre})

    async def genres(self, query: str = "", limit: int = 24) -> dict:
        return await self.get("/api/genres", q=query, limit=limit)

    async def track_to_playlist(self, track_url: str, playlist_name: str | None, track_count: int = 50) -> dict:
        return await self.post("/api/track-to-playlist", {"track_url": track_url, "playlist_name": playlist_name, "track_count": track_count})

    async def rewind(self, source: str, playlist_name: str | None, count: int) -> dict:
        return await self.post("/api/rewind", {"source": source, "playlist_name": playlist_name, "count": count})

    async def queue(self) -> dict:
        return await self.get("/api/queue")

    async def queue_setter(self, playlist_urls: list[str]) -> dict:
        return await self.post("/api/queue-setter", {"playlist_urls": playlist_urls})

    async def shuffle(self, playlist_url: str) -> dict:
        return await self.post("/api/playlist-shuffler", {"playlist_url": playlist_url})

    async def magic(self, playlist_name: str, track_count: int) -> dict:
        return await self.post("/api/magic-recommender", {"playlist_name": playlist_name, "track_count": track_count})

    async def fusion(self, seed_urls: list[str], playlist_name: str, track_count: int) -> dict:
        return await self.post(
            "/api/fusion-center",
            {"seed_urls": seed_urls, "playlist_name": playlist_name, "track_count": track_count},
        )

    async def fusion_suggestions(self) -> dict:
        return await self.get("/api/fusion-suggestions")

    async def search(self, query: str, limit: int = 12) -> dict:
        return await self.get("/api/search", q=query, limit=limit)

    async def time_machine(self, decade: int, count: int) -> dict:
        return await self.post("/api/time-machine", {"decade": decade, "count": count})

    async def track_stats(self, track_url: str) -> dict:
        return await self.get("/api/track-stats", track_url=track_url)

    async def now_playing(self) -> dict:
        return await self.get("/api/now-playing")

    async def playback(self, action: str) -> dict:
        return await self.post(f"/api/playback/{action}")

    async def top(self, kind: str, time_range: str, limit: int = 50) -> dict:
        return await self.get(f"/api/top-{kind}", time_range=time_range, limit=limit)


def _status_message(status: int) -> str:
    if status == 401:
        return "Session expired, log in again"
    if status == 403:
        return "Spotify refused this action (Premium required?)"
    if status == 404:
        return "Nothing found, is a Spotify device active?"
    if status == 429:
        return "Spotify is rate limiting, try again in a moment"
    if status >= 500:
        return "Server error, try again"
    return f"Request failed ({status})"


def parse_callback(url: str) -> tuple[str | None, str | None, str | None]:
    query = parse_qs(urlparse(url.strip()).query)
    pick = lambda key: (query.get(key) or [None])[0]
    return pick("code"), pick("state"), pick("error")


def redirect_uri_of(authorize_url: str) -> str | None:
    query = parse_qs(urlparse(authorize_url).query)
    return (query.get("redirect_uri") or [None])[0]
