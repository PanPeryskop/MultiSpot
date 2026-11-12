from collections.abc import Awaitable, Callable
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from services import spotify as svc
from services.client import Spotify, SpotifyError

router = APIRouter()

TimeRange = Literal["short_term", "medium_term", "long_term"]


def require_token(request: Request) -> dict:
    token = request.session.get("token_info")
    if not token or not token.get("access_token"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token


async def run(request: Request, action: Callable[[Spotify], Awaitable[dict]]) -> dict:
    sp = Spotify(require_token(request))
    try:
        return await action(sp)
    except SpotifyError as exc:
        if exc.status == 401:
            request.session.pop("token_info", None)
        status = exc.status if exc.status in (400, 401, 403, 404, 429) else 502
        raise HTTPException(status_code=status, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        if sp.changed and "token_info" in request.session:
            request.session["token_info"] = sp.token


class RandomHubRequest(BaseModel):
    count: int = Field(20, ge=1, le=200)
    playlist_name: str | None = Field(None, max_length=100)
    genre: str | None = Field(None, max_length=80)


class RewindRequest(BaseModel):
    source: Literal["recent", "short_term", "medium_term", "long_term"] = "short_term"
    playlist_name: str | None = Field(None, max_length=100)
    count: int = Field(50, ge=5, le=100)


class TrackToPlaylistRequest(BaseModel):
    track_url: str = Field(min_length=1)
    playlist_name: str | None = Field(None, max_length=100)
    track_count: int = Field(50, ge=5, le=100)


class QueueSetterRequest(BaseModel):
    playlist_urls: list[str] = Field(min_length=1, max_length=20)


class PlaylistShufflerRequest(BaseModel):
    playlist_url: str = Field(min_length=1)


class MagicRecommenderRequest(BaseModel):
    playlist_name: str | None = Field("Magic Mix", max_length=100)
    track_count: int = Field(25, ge=5, le=100)


class FusionCenterRequest(BaseModel):
    seed_urls: list[str] = Field(min_length=1, max_length=20)
    playlist_name: str | None = Field("Fusion Mix", max_length=100)
    track_count: int = Field(25, ge=5, le=100)


class TimeMachineRequest(BaseModel):
    decade: int = Field(1980, ge=1950, le=2020, multiple_of=10)
    count: int = Field(10, ge=1, le=50)


@router.get("/playlists")
async def playlists(request: Request, limit: int = Query(50, ge=1, le=50), offset: int = Query(0, ge=0)):
    return await run(request, lambda sp: svc.get_user_playlists(sp, limit=limit, offset=offset))


@router.post("/random-hub/queue")
async def random_hub_queue(request: Request, body: RandomHubRequest):
    return await run(request, lambda sp: svc.add_random_tracks_to_queue(sp, body.count, (body.genre or "").strip() or None))


@router.post("/random-hub/playlist")
async def random_hub_playlist(request: Request, body: RandomHubRequest):
    return await run(request, lambda sp: svc.create_random_playlist(sp, body.count, body.playlist_name, (body.genre or "").strip() or None))


@router.post("/track-to-playlist")
async def track_to_playlist(request: Request, body: TrackToPlaylistRequest):
    return await run(request, lambda sp: svc.create_playlist_from_track(sp, body.track_url, body.playlist_name or "", body.track_count))


@router.post("/queue-setter")
async def queue_setter(request: Request, body: QueueSetterRequest):
    return await run(request, lambda sp: svc.set_interleaved_queue(sp, body.playlist_urls))


@router.post("/playlist-shuffler")
async def playlist_shuffler(request: Request, body: PlaylistShufflerRequest):
    return await run(request, lambda sp: svc.shuffle_playlist(sp, body.playlist_url))


@router.post("/magic-recommender")
async def magic_recommender(request: Request, body: MagicRecommenderRequest):
    return await run(request, lambda sp: svc.create_magic_playlist(sp, body.playlist_name or "", body.track_count))


@router.post("/fusion-center")
async def fusion_center(request: Request, body: FusionCenterRequest):
    urls = [u for u in body.seed_urls if u and u.strip()]
    if not urls:
        raise HTTPException(status_code=422, detail="Add at least one seed")
    return await run(request, lambda sp: svc.create_fusion_playlist(sp, urls, body.playlist_name or "", body.track_count))


@router.post("/time-machine")
async def time_machine(request: Request, body: TimeMachineRequest):
    return await run(request, lambda sp: svc.add_time_machine_tracks(sp, body.decade, body.count))


@router.get("/track-stats")
async def track_stats(request: Request, track_url: str = Query(min_length=1)):
    return await run(request, lambda sp: svc.get_track_stats(sp, track_url))


@router.get("/now-playing")
async def now_playing(request: Request):
    return await run(request, svc.get_now_playing)


@router.post("/playback/{action}")
async def playback(request: Request, action: Literal["skip", "previous", "play", "pause"]):
    return await run(request, lambda sp: svc.playback(sp, action))


@router.get("/top-tracks")
async def top_tracks(request: Request, limit: int = Query(50, ge=1, le=50), time_range: TimeRange = "medium_term"):
    return await run(request, lambda sp: svc.get_top_tracks(sp, limit=limit, time_range=time_range))


@router.get("/top-artists")
async def top_artists(request: Request, limit: int = Query(50, ge=1, le=50), time_range: TimeRange = "medium_term"):
    return await run(request, lambda sp: svc.get_top_artists(sp, limit=limit, time_range=time_range))


@router.get("/top-genres")
async def top_genres(request: Request, limit: int = Query(50, ge=1, le=100), time_range: TimeRange = "medium_term"):
    return await run(request, lambda sp: svc.get_top_genres(sp, limit=limit, time_range=time_range))


@router.get("/search")
async def search(request: Request, q: str = "", limit: int = Query(10, ge=1, le=50)):
    if not q.strip():
        return {"tracks": [], "artists": [], "albums": []}
    return await run(request, lambda sp: svc.search_spotify(sp, query=q.strip(), limit=limit))


@router.get("/fusion-suggestions")
async def fusion_suggestions(request: Request):
    return await run(request, svc.get_fusion_suggestions)


@router.get("/genres")
async def genres(request: Request, q: str = "", limit: int = Query(30, ge=1, le=100)):
    require_token(request)
    return {"genres": svc.find_genres(q, limit), "total": len(svc.GENRES)}


@router.post("/rewind")
async def rewind(request: Request, body: RewindRequest):
    return await run(request, lambda sp: svc.create_rewind_playlist(sp, body.source, body.playlist_name, body.count))


@router.get("/queue")
async def queue(request: Request):
    return await run(request, svc.get_queue)
