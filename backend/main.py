import logging
import os
import secrets
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from routers import auth, spotify
from services.client import close_http

load_dotenv()

log = logging.getLogger("multispot")

secret = os.getenv("SESSION_SECRET_KEY")
if not secret:
    secret = secrets.token_urlsafe(48)
    log.warning("SESSION_SECRET_KEY is not set, sessions will not survive a restart")

origins = [o.strip() for o in os.getenv("FRONTEND_URL", "http://localhost:5173").split(",") if o.strip()]


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_http()


app = FastAPI(title="MultiSpot API", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=secret,
    max_age=3600 * 24 * 30,
    same_site="lax",
    https_only=os.getenv("SESSION_HTTPS_ONLY", "").lower() in ("1", "true", "yes"),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(spotify.router, prefix="/api", tags=["spotify"])


@app.get("/health")
def health():
    return {"ok": True}
