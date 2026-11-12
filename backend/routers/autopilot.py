from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from routers.spotify import run
from services import autopilot
from services.client import Spotify
from services.store import store

router = APIRouter()


class CreateRequest(BaseModel):
    kind: Literal["daily_mix", "weekly_radar", "monthly_rewind"]
    track_count: int | None = Field(None, ge=10, le=100)
    days: int | None = Field(None, ge=3, le=30)
    playlist_name: str | None = Field(None, max_length=80)


class UpdateRequest(BaseModel):
    enabled: bool


async def _owned(sp: Spotify, automation_id: int) -> tuple[dict, dict]:
    me = await sp.me()
    item = store.get_automation(automation_id)
    if not item or item["user_id"] != me["id"]:
        raise HTTPException(status_code=404, detail="Autopilot not found")
    return me, item


@router.get("")
async def list_autopilots(request: Request):
    async def action(sp: Spotify) -> dict:
        me = await sp.me()
        return {"automations": [autopilot.describe(a) for a in store.list_automations(me["id"])], "kinds": autopilot.catalog()}

    return await run(request, action)


@router.post("")
async def create_autopilot(request: Request, body: CreateRequest):
    async def action(sp: Spotify) -> dict:
        me = await sp.me()
        if store.find_automation(me["id"], body.kind):
            raise HTTPException(status_code=409, detail="This autopilot is already set up")
        store.save_user(me["id"], sp.token.get("refresh_token"))
        settings = {k: v for k, v in (("track_count", body.track_count), ("days", body.days), ("name", (body.playlist_name or "").strip() or None)) if v is not None}
        item = store.create_automation(me["id"], body.kind, settings, autopilot.next_run(body.kind))
        try:
            return await autopilot.run_now(sp, item)
        except Exception:
            store.delete_automation(item["id"])
            raise

    return await run(request, action)


@router.post("/{automation_id}/run")
async def run_autopilot(request: Request, automation_id: int):
    async def action(sp: Spotify) -> dict:
        me, item = await _owned(sp, automation_id)
        store.save_user(me["id"], sp.token.get("refresh_token"))
        return await autopilot.run_now(sp, item)

    return await run(request, action)


@router.patch("/{automation_id}")
async def update_autopilot(request: Request, automation_id: int, body: UpdateRequest):
    async def action(sp: Spotify) -> dict:
        me, item = await _owned(sp, automation_id)
        fields = {"enabled": body.enabled}
        if body.enabled:
            fields["next_run"] = autopilot.next_run(item["kind"])
            store.save_user(me["id"], sp.token.get("refresh_token"))
        return autopilot.describe(store.update_automation(automation_id, **fields))

    return await run(request, action)


@router.delete("/{automation_id}")
async def delete_autopilot(request: Request, automation_id: int):
    async def action(sp: Spotify) -> dict:
        await _owned(sp, automation_id)
        store.delete_automation(automation_id)
        return {"deleted": True}

    return await run(request, action)
