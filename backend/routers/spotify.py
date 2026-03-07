from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from services import spotify as svc
from typing import Optional

router = APIRouter()

def require_auth(request: Request) -> dict:
    token_info = request.session.get("token_info")
    if not token_info:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token_info

def save_token(request: Request, result: dict):
    if result.get("token"):
        request.session["token_info"] = result["token"]

class RandomHubRequest(BaseModel):
    count: int = 20
    playlist_name: Optional[str] = "Random Hub Playlist"

class TrackToPlaylistRequest(BaseModel):
    track_url: str
    playlist_name: str

class QueueSetterRequest(BaseModel):
    playlist_urls: list[str]

class PlaylistShufflerRequest(BaseModel):
    playlist_url: str

class MagicRecommenderRequest(BaseModel):
    playlist_name: str
    track_count: int = 25

class FusionCenterRequest(BaseModel):
    seed_urls: list[str]
    playlist_name: str
    track_count: int = 25

class TimeMachineRequest(BaseModel):
    decade: int = 1980
    count: int = 10

@router.get("/playlists")
def playlists(request: Request, limit: int = 50, offset: int = 0):
    token = require_auth(request)
    result = svc.get_user_playlists(token, limit=limit, offset=offset)
    save_token(request, result)
    return result

@router.post("/random-hub/queue")
def random_hub_queue(request: Request, body: RandomHubRequest):
    token = require_auth(request)
    if not 1 <= body.count <= 200:
        raise HTTPException(status_code=422, detail="Count must be 1–200")
    result = svc.add_random_tracks_to_queue(token, count=body.count)
    save_token(request, result)
    return result

@router.post("/random-hub/playlist")
def random_hub_playlist(request: Request, body: RandomHubRequest):
    token = require_auth(request)
    if not 1 <= body.count <= 200:
        raise HTTPException(status_code=422, detail="Count must be 1–200")
    result = svc.create_random_playlist(token, count=body.count, playlist_name=body.playlist_name)
    save_token(request, result)
    return result

@router.post("/track-to-playlist")
def track_to_playlist(request: Request, body: TrackToPlaylistRequest):
    token = require_auth(request)
    result = svc.create_playlist_from_track(token, body.track_url, body.playlist_name)
    save_token(request, result)
    return result

@router.post("/queue-setter")
def queue_setter(request: Request, body: QueueSetterRequest):
    token = require_auth(request)
    if not body.playlist_urls:
        raise HTTPException(status_code=422, detail="Select at least one playlist")
    result = svc.set_interleaved_queue(token, body.playlist_urls)
    save_token(request, result)
    return result

@router.post("/playlist-shuffler")
def playlist_shuffler(request: Request, body: PlaylistShufflerRequest):
    token = require_auth(request)
    result = svc.shuffle_playlist(token, body.playlist_url)
    save_token(request, result)
    return result

@router.post("/magic-recommender")
def magic_recommender(request: Request, body: MagicRecommenderRequest):
    token = require_auth(request)
    if not 1 <= body.track_count <= 100:
        raise HTTPException(status_code=422, detail="Track count must be 1–100")
    result = svc.create_magic_playlist(token, body.playlist_name, body.track_count)
    save_token(request, result)
    return result

@router.post("/fusion-center")
def fusion_center(request: Request, body: FusionCenterRequest):
    token = require_auth(request)
    if not 1 <= body.track_count <= 100:
        raise HTTPException(status_code=422, detail="Track count must be 1–100")
    if not body.seed_urls:
         raise HTTPException(status_code=422, detail="Must provide at least one seed URL")
    try:
        result = svc.create_fusion_playlist(token, body.seed_urls, body.playlist_name, body.track_count)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    save_token(request, result)
    return result

@router.post("/time-machine")
def time_machine(request: Request, body: TimeMachineRequest):
    token = require_auth(request)
    if not 1 <= body.count <= 100:
        raise HTTPException(status_code=422, detail="Count must be 1–100")
    if body.decade < 1900 or body.decade > 2030:
        raise HTTPException(status_code=422, detail="Invalid decade")
    result = svc.add_time_machine_tracks(token, body.decade, body.count)
    save_token(request, result)
    return result

@router.get("/track-stats")
def track_stats(request: Request, track_url: str):
    token = require_auth(request)
    if not track_url:
        raise HTTPException(status_code=422, detail="Missing track URL")
    result = svc.get_track_stats(token, track_url)
    save_token(request, result)
    return result

@router.get("/now-playing")
def now_playing(request: Request):
    token = require_auth(request)
    result = svc.get_now_playing(token)
    save_token(request, result)
    return result

@router.post("/playback/skip")
def skip(request: Request):
    token = require_auth(request)
    result = svc.skip_track(token)
    save_token(request, result)
    return result

@router.post("/playback/previous")
def previous(request: Request):
    token = require_auth(request)
    result = svc.previous_track(token)
    save_token(request, result)
    return result

@router.post("/playback/play")
def play(request: Request):
    token = require_auth(request)
    result = svc.play_track(token)
    save_token(request, result)
    return result

@router.post("/playback/pause")
def pause(request: Request):
    token = require_auth(request)
    result = svc.pause_track(token)
    save_token(request, result)
    return result

@router.get("/top-tracks")
def top_tracks(request: Request, limit: int = 50, time_range: str = "medium_term"):
    token = require_auth(request)
    result = svc.get_top_tracks(token, limit=limit, time_range=time_range)
    save_token(request, result)
    return result

@router.get("/top-artists")
def top_artists(request: Request, limit: int = 50, time_range: str = "medium_term"):
    token = require_auth(request)
    result = svc.get_top_artists(token, limit=limit, time_range=time_range)
    save_token(request, result)
    return result

@router.get("/top-genres")
def top_genres(request: Request, limit: int = 50, time_range: str = "medium_term"):
    token = require_auth(request)
    result = svc.get_top_genres(token, limit=limit, time_range=time_range)
    save_token(request, result)
    return result

@router.get("/search")
def search(request: Request, q: str, limit: int = 15):
    token = require_auth(request)
    if not q or not q.strip():
        return {"tracks": [], "artists": [], "albums": []}
    result = svc.search_spotify(token, query=q.strip(), limit=limit)
    save_token(request, result)
    return result

@router.get("/fusion-suggestions")
def fusion_suggestions(request: Request):
    token = require_auth(request)
    result = svc.get_fusion_suggestions(token)
    save_token(request, result)
    return result
