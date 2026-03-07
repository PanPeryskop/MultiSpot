# MultiSpot

Spotify toolkit — FastAPI (backend) + React/Vite (frontend).

## Features

- **Random Hub** — inject random tracks from 6000+ genres into your queue or a new playlist
- **Track to Playlist** — paste a track URL, get a recommendation playlist
- **Queue Setter** — interleave multiple playlists into one queue
- **Playlist Shuffler** — true-shuffle any playlist (recreates in random order)
- **Magic Recommender** — generate a playlist from your top tracks
- **Fusion Center** — search/paste tracks, artists, albums and fuse them into a custom playlist
- **Stats Hub** — top tracks, artists, genre breakdown (by time period)
- **Time Machine** — queue popular tracks from any decade (1950s–2020s)
- **Now Playing** — live track display + skip in navbar

## Setup

### 1. Spotify App

Create an app at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard).
Add redirect URI: `http://127.0.0.1:5173/callback`
Add your email to registered users in app settings.

### 2. Environment

Create `backend/.env`:

```
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5173/callback
SESSION_SECRET_KEY=<random string>
FRONTEND_URL=http://localhost:5173
```

### 3. Install

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run build
```

### 4. Run

```bash
start_backend.bat
start_frontend.bat
```
