import secrets
import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from services.client import Spotify, SpotifyError, authorize_url, exchange_code

STATE_TTL = 600

_pending_states: dict[str, float] = {}

router = APIRouter()


def _prune_states():
    now = time.time()
    for state, expiry in list(_pending_states.items()):
        if expiry < now:
            _pending_states.pop(state, None)


def _profile(user: dict) -> dict:
    images = user.get("images") or []
    return {
        "authenticated": True,
        "id": user.get("id"),
        "display_name": user.get("display_name") or user.get("id"),
        "email": user.get("email"),
        "image": images[0].get("url") if images else None,
    }


@router.get("/login")
def login():
    _prune_states()
    state = secrets.token_urlsafe(16)
    _pending_states[state] = time.time() + STATE_TTL
    try:
        return RedirectResponse(authorize_url(state))
    except SpotifyError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.message) from exc


class ExchangeRequest(BaseModel):
    code: str
    state: str


@router.post("/exchange")
async def exchange(body: ExchangeRequest, request: Request):
    expiry = _pending_states.pop(body.state, None)
    if expiry is None or time.time() > expiry:
        raise HTTPException(status_code=400, detail="Login link expired, try again")
    try:
        token = await exchange_code(body.code)
        sp = Spotify(token)
        user = await sp.me()
    except SpotifyError as exc:
        raise HTTPException(status_code=400 if exc.status == 401 else exc.status, detail=exc.message) from exc
    request.session["token_info"] = sp.token
    return _profile(user)


@router.get("/me")
async def me(request: Request):
    token = request.session.get("token_info")
    if not token:
        return JSONResponse({"authenticated": False}, status_code=401)
    sp = Spotify(token)
    try:
        user = await sp.me()
    except SpotifyError as exc:
        if exc.status == 401:
            request.session.clear()
            return JSONResponse({"authenticated": False}, status_code=401)
        raise HTTPException(status_code=502, detail=exc.message) from exc
    if sp.changed:
        request.session["token_info"] = sp.token
    return _profile(user)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"logged_out": True}
