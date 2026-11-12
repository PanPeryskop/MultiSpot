# MultiSpot

Spotify toolkit - FastAPI (backend), React/Vite (web) and Flet (mobile).

## Features

- **Random Hub** - random tracks from 6000+ genres, or a station from one picked genre, into your queue or a new playlist
- **Track Radio** - one track in, a playlist of what listeners play next to it out
- **Magic Mix** - a fresh playlist seeded from your top artists and tracks, skipping what you already have on repeat
- **Fusion Center** - tracks, artists, albums and playlists as seeds, fused into one playlist
- **Queue Setter** - interleave multiple playlists into one queue
- **Playlist Shuffler** - true-shuffle any playlist (recreates it in random order)
- **Time Machine** - queue popular tracks from any decade (1950s-2020s)
- **Track X-Ray** - release info, album tracklist, popularity, artist discography and top tracks
- **Stats Hub** - top tracks, artists and genres by time range
- **Rewind** - save recently played or top tracks of a period as a playlist
- **Now Playing** - live player with controls and the upcoming queue

## How recommendations work

Spotify removed `related-artists`, `recommendations` and `audio-features` for apps in Development Mode and
is phasing out more endpoints (see the February 2026 Web API changelog). MultiSpot does not depend on them.
Track Radio, Magic Mix, Fusion and genre stations search public listener playlists around the seeds,
score tracks by how often they co-occur (weighted by how strongly each playlist features the seed artists),
drop spam playlists, covers and mashups of the seed songs, cap tracks per artist and fill gaps with the
top tracks of the strongest neighbouring artists.

The backend talks to the Web API directly with `httpx`, prefers the new endpoints
(`POST /me/playlists`, `/playlists/{id}/items`) and falls back to the legacy ones when needed.

## Setup

### 1. Spotify App

Create an app at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard).
Add your redirect URI (for example `http://127.0.0.1:5173/callback`) and add your account to the app's users.

### 2. Environment

Create `.env` in the repository root:

```
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5173/callback
SESSION_SECRET_KEY=<long random string>
FRONTEND_URL=http://localhost:5173
SESSION_HTTPS_ONLY=false
```

`FRONTEND_URL` accepts a comma separated list of allowed origins. Set `SESSION_HTTPS_ONLY=true` when serving over HTTPS.
Without `SESSION_SECRET_KEY` a random key is generated on start and every restart logs everyone out.

### 3. Install

```bash
cd backend
uv sync
```

```bash
cd frontend
npm install
npm run build
```

```bash
cd flet_app
uv sync
```

### 4. Run

```bash
start_backend.bat
```

```bash
start_frontend.bat
```

Mobile app during development:

```bash
cd flet_app
uv run flet run src/main.py
```

Android build:

```bash
cd flet_app
uv run flet build apk
```
