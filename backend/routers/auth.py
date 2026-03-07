import os
import time
import secrets
import spotipy
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

SCOPE = (
    "playlist-read-private "
    "user-modify-playback-state "
    "playlist-modify-public "
    "playlist-modify-private "
    "user-top-read "
    "user-read-currently-playing "
    "user-read-playback-state "
    "user-read-recently-played"
)

_pending_states: dict[str, float] = {}

router = APIRouter()

def _auth_manager() -> SpotifyOAuth:
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope=SCOPE,
        cache_handler=None,
        open_browser=False,
        show_dialog=True,
    )

@router.get("/login")
def login():
    state = secrets.token_urlsafe(16)
    _pending_states[state] = time.time() + 600
    am = _auth_manager()
    url = am.get_authorize_url(state=state)
    return RedirectResponse(url)

class ExchangeRequest(BaseModel):
    code: str
    state: str

@router.post("/exchange")
def exchange(body: ExchangeRequest, request: Request):
    expiry = _pending_states.pop(body.state, None)
    if expiry is None or time.time() > expiry:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    am = _auth_manager()
    token_info = am.get_access_token(body.code, as_dict=True, check_cache=False)
    request.session["token_info"] = token_info

    sp = spotipy.Spotify(auth=token_info["access_token"])
    user = sp.me()
    return {
        "authenticated": True,
        "id": user["id"],
        "display_name": user.get("display_name"),
        "email": user.get("email"),
        "image": user["images"][0]["url"] if user.get("images") else None,
    }

@router.get("/me")
def me(request: Request):
    token_info = request.session.get("token_info")
    if not token_info:
        return JSONResponse({"authenticated": False}, status_code=401)

    am = _auth_manager()
    refreshed = am.validate_token(token_info)
    if refreshed:
        request.session["token_info"] = refreshed
        token_info = refreshed

    sp = spotipy.Spotify(auth=token_info["access_token"])
    user = sp.me()
    return {
        "authenticated": True,
        "id": user["id"],
        "display_name": user.get("display_name"),
        "email": user.get("email"),
        "image": user["images"][0]["url"] if user.get("images") else None,
    }

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"logged_out": True}
