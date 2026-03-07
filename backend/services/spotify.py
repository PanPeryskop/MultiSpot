import spotipy, os, random, re, json, time
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

GENRES_PATH = os.path.join(os.path.dirname(__file__), "..", "genres.json")
with open(GENRES_PATH, "r", encoding="utf-8") as f:
    GENRES: list[str] = json.load(f)

def get_spotify(token_info: dict) -> tuple[spotipy.Spotify, dict]:
    am = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        cache_handler=None,
        open_browser=False,
    )
    refreshed = am.validate_token(token_info)
    token = refreshed if refreshed else token_info
    return spotipy.Spotify(auth=token["access_token"]), token

def _get_random_tracks(sp: spotipy.Spotify, count: int) -> list[str]:
    track_ids = []
    max_attempts = count * 5
    attempts = 0
    
    while len(track_ids) < count and attempts < max_attempts:
        attempts += 1
        genre = random.choice(GENRES)
        try:
            results = sp.search(q=f'genre:"{genre}"', type="track", limit=50)
            tracks = results["tracks"]["items"]
            if not tracks:
                continue
            track = random.choice(tracks)
            if track["id"] not in track_ids:
                track_ids.append(track["id"])
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                time.sleep(int(e.headers.get("Retry-After", 1)))
                
    return track_ids

def add_random_tracks_to_queue(token_info: dict, count: int) -> dict:
    sp, token = get_spotify(token_info)
    track_ids = _get_random_tracks(sp, count)
    
    added = 0
    errors = 0
    for tid in track_ids:
        try:
            sp.add_to_queue(uri=f"spotify:track:{tid}")
            added += 1
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                time.sleep(int(e.headers.get("Retry-After", 1)))
            errors += 1
            
    return {"added": added, "errors": errors, "token": token}

def create_random_playlist(token_info: dict, count: int, playlist_name: str) -> dict:
    sp, token = get_spotify(token_info)
    track_ids = _get_random_tracks(sp, count)
    
    if not track_ids:
        raise ValueError("Could not find any random tracks.")
        
    user_id = sp.me()["id"]
    playlist = sp.user_playlist_create(user_id, playlist_name)
    sp.playlist_add_items(playlist["id"], track_ids)
    
    return {"playlist_url": playlist["external_urls"]["spotify"], "track_count": len(track_ids), "token": token}

def create_playlist_from_track(token_info: dict, track_url: str, playlist_name: str) -> dict:
    sp, token = get_spotify(token_info)
    track_id = track_url.split("/")[-1].split("?")[0]
    track = sp.track(track_id)
    
    artist_id = track["artists"][0]["id"]
    try:
        related = sp.artist_related_artists(artist_id)
        artist_ids = [artist_id] + [a["id"] for a in related["artists"][:4]]
    except spotipy.exceptions.SpotifyException:
        artist_ids = [artist_id]
        
    all_uris = []
    for aid in artist_ids:
        try:
            top_tracks = sp.artist_top_tracks(aid)
            for t in top_tracks["tracks"][:10]:
                if t["uri"] not in all_uris:
                    all_uris.append(t["uri"])
        except spotipy.exceptions.SpotifyException:
            continue
                
    random.shuffle(all_uris)
    all_uris = all_uris[:50]
    
    user_id = sp.me()["id"]
    playlist = sp.user_playlist_create(user_id, playlist_name, public=True)
    sp.playlist_add_items(playlist["id"], all_uris)
    return {"playlist_url": playlist["external_urls"]["spotify"], "track_count": len(all_uris), "token": token}

def _add_to_queue_with_retry(sp: spotipy.Spotify, track_id: str):
    while True:
        try:
            sp.add_to_queue(track_id)
            break
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                time.sleep(int(e.headers.get("Retry-After", 1)))
            else:
                raise

def set_interleaved_queue(token_info: dict, playlist_urls: list[str]) -> dict:
    sp, token = get_spotify(token_info)
    playlist_tracks = []
    for url in playlist_urls:
        pid = url.split("/")[-1].split("?")[0]
        results = sp.playlist_items(pid)
        ids = [item["track"]["id"] for item in results["items"] if item.get("track")]
        playlist_tracks.append(ids)
    max_len = max(len(p) for p in playlist_tracks)
    queue = [p[i] for i in range(max_len) for p in playlist_tracks if i < len(p)]
    for tid in queue:
        _add_to_queue_with_retry(sp, tid)
    return {"queued": len(queue), "token": token}

def shuffle_playlist(token_info: dict, playlist_url: str) -> dict:
    sp, token = get_spotify(token_info)
    pid = playlist_url.split("/")[-1].split("?")[0]
    playlist = sp.playlist(pid)
    results = sp.playlist_items(pid)
    tracks_data = results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks_data.extend(results["items"])
    track_ids = list({
        t["track"]["id"] for t in tracks_data
        if t.get("track") and re.match(r"^[a-zA-Z0-9]+$", t["track"].get("id", ""))
    })
    random.shuffle(track_ids)
    user_id = sp.me()["id"]
    is_own = playlist["owner"]["id"] == user_id
    new_pl = sp.user_playlist_create(user_id, playlist["name"] if is_own else playlist["name"] + " (Shuffled)")
    if is_own:
        sp.current_user_unfollow_playlist(pid)
    new_id = new_pl["id"]
    for i in range(0, len(track_ids), 100):
        sp.playlist_add_items(new_id, [f"spotify:track:{t}" for t in track_ids[i:i + 100]])
    return {"playlist_url": new_pl["external_urls"]["spotify"], "track_count": len(track_ids), "token": token}

def create_magic_playlist(token_info: dict, playlist_name: str, track_count: int) -> dict:
    sp, token = get_spotify(token_info)
    top_artists = sp.current_user_top_artists(limit=10, time_range="medium_term")
    if not top_artists or not top_artists["items"]:
        raise ValueError("No top artists found to build recommendations.")
        
    artist_ids = [a["id"] for a in top_artists["items"]]
    
    related_ids = []
    for aid in random.sample(artist_ids, min(3, len(artist_ids))):
        try:
            related = sp.artist_related_artists(aid)
            related_ids.extend([a["id"] for a in related["artists"][:3]])
        except spotipy.exceptions.SpotifyException:
            continue
            
    all_artist_ids = list(set(artist_ids + related_ids))
    
    track_ids = []
    for aid in random.sample(all_artist_ids, min(min(track_count * 2, 100), len(all_artist_ids))):
        try:
            top_tracks = sp.artist_top_tracks(aid)
            for t in top_tracks["tracks"]:
                if t["id"] not in track_ids:
                    track_ids.append(t["id"])
                    break
        except spotipy.exceptions.SpotifyException:
            continue
                
    random.shuffle(track_ids)
    track_ids = track_ids[:track_count]
                
    user_id = sp.me()["id"]
    playlist = sp.user_playlist_create(user_id, playlist_name)
    sp.playlist_add_items(playlist["id"], track_ids)
    return {"playlist_url": playlist["external_urls"]["spotify"], "track_count": len(track_ids), "token": token}

def _resolve_artist_ids(sp: spotipy.Spotify, urls: list[str]) -> list[str]:
    import re
    artist_ids = []
    for url in urls:
        if not url: continue
        match = re.search(r"/(track|artist|album|playlist)/([a-zA-Z0-9]+)", url)
        if match:
            type_, id_ = match.groups()
            try:
                if type_ == "artist":
                    artist_ids.append(id_)
                elif type_ == "track":
                    track = sp.track(id_)
                    artist_ids.append(track["artists"][0]["id"])
                elif type_ == "album":
                    album = sp.album(id_)
                    artist_ids.append(album["artists"][0]["id"])
                elif type_ == "playlist":
                    results = sp.playlist_items(id_, limit=20)
                    for item in results["items"]:
                        if item.get("track") and item["track"].get("artists"):
                            artist_ids.append(item["track"]["artists"][0]["id"])
            except spotipy.exceptions.SpotifyException:
                pass
    return list(set(artist_ids))

def create_fusion_playlist(token_info: dict, seed_urls: list[str], playlist_name: str, track_count: int) -> dict:
    sp, token = get_spotify(token_info)
    artist_ids = _resolve_artist_ids(sp, seed_urls)
    
    if not artist_ids:
        raise ValueError("Could not resolve any playable artists from the provided URLs.")
        
    related_ids = []
    for aid in artist_ids:
        try:
            related = sp.artist_related_artists(aid)
            related_ids.extend([a["id"] for a in related["artists"][:5]])
        except spotipy.exceptions.SpotifyException:
            continue
            
    all_artist_ids = list(set(artist_ids + related_ids))
    
    track_ids = []
    for aid in random.sample(all_artist_ids, min(min(track_count * 2, 100), len(all_artist_ids))):
        try:
            top_tracks = sp.artist_top_tracks(aid)
            for t in top_tracks["tracks"]:
                if t["id"] not in track_ids:
                    track_ids.append(t["id"])
                    break
        except spotipy.exceptions.SpotifyException:
            continue
            
    random.shuffle(track_ids)
    track_ids = track_ids[:track_count]
                
    user_id = sp.me()["id"]
    playlist = sp.user_playlist_create(user_id, playlist_name)
    sp.playlist_add_items(playlist["id"], track_ids)
    return {"playlist_url": playlist["external_urls"]["spotify"], "track_count": len(track_ids), "token": token}

def get_now_playing(token_info: dict) -> dict:
    sp, token = get_spotify(token_info)
    current = sp.currently_playing()
    if not current or not current.get("item"):
        return {"playing": False, "token": token}
    item = current["item"]
    return {
        "playing": True,
        "is_playing": current.get("is_playing", False),
        "track": {
            "id": item["id"],
            "name": item["name"],
            "artists": [a["name"] for a in item["artists"]],
            "album": item["album"]["name"],
            "image": item["album"]["images"][0]["url"] if item["album"]["images"] else None,
            "progress_ms": current.get("progress_ms", 0),
            "duration_ms": item["duration_ms"],
        },
        "token": token,
    }

def skip_track(token_info: dict) -> dict:
    sp, token = get_spotify(token_info)
    sp.next_track()
    return {"skipped": True, "token": token}

def previous_track(token_info: dict) -> dict:
    sp, token = get_spotify(token_info)
    sp.previous_track()
    return {"previous": True, "token": token}

def play_track(token_info: dict) -> dict:
    sp, token = get_spotify(token_info)
    sp.start_playback()
    return {"playing": True, "token": token}

def pause_track(token_info: dict) -> dict:
    sp, token = get_spotify(token_info)
    sp.pause_playback()
    return {"paused": True, "token": token}

def get_user_playlists(token_info: dict, limit: int = 50, offset: int = 0) -> dict:
    sp, token = get_spotify(token_info)
    result = sp.current_user_playlists(limit=limit, offset=offset)
    playlists = [
        {
            "id": p["id"],
            "name": p["name"],
            "url": p["external_urls"]["spotify"],
            "image": p["images"][0]["url"] if p.get("images") else None,
            "tracks_total": p["tracks"]["total"],
            "owner": p["owner"]["display_name"],
        }
        for p in result["items"]
    ]
    return {"playlists": playlists, "total": result["total"], "token": token}

def get_top_tracks(token_info: dict, limit: int = 20, time_range: str = "medium_term") -> dict:
    sp, token = get_spotify(token_info)
    result = sp.current_user_top_tracks(limit=limit, time_range=time_range)
    tracks = [
        {
            "id": t["id"],
            "name": t["name"],
            "artists": [a["name"] for a in t["artists"]],
            "album": t["album"]["name"],
            "image": t["album"]["images"][0]["url"] if t["album"]["images"] else None,
            "url": t["external_urls"]["spotify"],
            "popularity": t.get("popularity", 0),
            "duration_ms": t.get("duration_ms", 0),
            "explicit": t.get("explicit", False),
        }
        for t in result["items"]
    ]
    return {"tracks": tracks, "token": token}

def get_top_artists(token_info: dict, limit: int = 50, time_range: str = "medium_term") -> dict:
    sp, token = get_spotify(token_info)
    result = sp.current_user_top_artists(limit=limit, time_range=time_range)
    artists = [
        {
            "id": a["id"],
            "name": a["name"],
            "image": a["images"][0]["url"] if a.get("images") else None,
            "url": a["external_urls"]["spotify"],
            "followers": a["followers"]["total"],
            "popularity": a["popularity"],
            "genres": a["genres"],
        }
        for a in result["items"]
    ]
    return {"artists": artists, "token": token}

def get_top_genres(token_info: dict, limit: int = 50, time_range: str = "medium_term") -> dict:
    sp, token = get_spotify(token_info)
    result = sp.current_user_top_artists(limit=50, time_range=time_range)
    counts = {}
    for a in result["items"]:
        for g in a.get("genres", []):
            counts[g] = counts.get(g, 0) + 1
            
    sorted_genres = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    genres = [{"name": k, "count": v} for k, v in sorted_genres]
    return {"genres": genres, "token": token}

def search_spotify(token_info: dict, query: str, limit: int = 15) -> dict:
    sp, token = get_spotify(token_info)
    result = sp.search(q=query, limit=limit, type="track,artist,album")
    
    tracks = [
        {
            "id": t["id"],
            "name": t["name"],
            "artists": [a["name"] for a in t["artists"]],
            "image": t["album"]["images"][0]["url"] if t["album"].get("images") else None,
            "url": t["external_urls"]["spotify"]
        }
        for t in result.get("tracks", {}).get("items", [])
    ]
    
    artists = [
        {
            "id": a["id"],
            "name": a["name"],
            "image": a["images"][0]["url"] if a.get("images") else None,
            "url": a["external_urls"]["spotify"]
        }
        for a in result.get("artists", {}).get("items", [])
    ]
    
    albums = [
        {
            "id": a["id"],
            "name": a["name"],
            "artists": [ar["name"] for ar in a["artists"]],
            "image": a["images"][0]["url"] if a.get("images") else None,
            "url": a["external_urls"]["spotify"]
        }
        for a in result.get("albums", {}).get("items", [])
    ]
    
    return {
        "tracks": tracks,
        "artists": artists,
        "albums": albums,
        "token": token
    }

def add_time_machine_tracks(token_info: dict, decade: int, count: int) -> dict:
    sp, token = get_spotify(token_info)
    added = 0
    errors = 0
    query = f"year:{decade}-{decade+9}"
    
    for _ in range(count):
        offset = random.randint(0, 900)
        try:
            results = sp.search(q=query, type="track", limit=50, offset=offset)
            tracks = results["tracks"]["items"]
            if not tracks:
                continue
            track = random.choice(tracks)
            sp.add_to_queue(uri=track["uri"])
            added += 1
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                time.sleep(int(e.headers.get("Retry-After", 1)))
            errors += 1
    return {"added": added, "errors": errors, "token": token}

def get_track_stats(token_info: dict, track_url: str) -> dict:
    sp, token = get_spotify(token_info)
    track_id = track_url.split("/")[-1].split("?")[0]
    track = sp.track(track_id)
    
    artist_ids = [a["id"] for a in track["artists"]]
    artists = sp.artists(artist_ids)["artists"]
    
    album = sp.album(track["album"]["id"])
    
    return {
        "track": {
            "name": track["name"],
            "popularity": track["popularity"],
            "explicit": track["explicit"],
            "duration_ms": track["duration_ms"],
        },
        "album": {
            "name": album["name"],
            "release_date": album["release_date"],
            "total_tracks": album["total_tracks"],
            "image": album["images"][0]["url"] if album["images"] else None,
            "label": album.get("label", ""),
        },
        "artists": [
            {
                "name": a["name"],
                "popularity": a["popularity"],
                "followers": a["followers"]["total"],
                "genres": a["genres"],
            } for a in artists
        ],
        "token": token,
    }

def get_fusion_suggestions(token_info: dict) -> dict:
    sp, token = get_spotify(token_info)
    
    recent_res = sp.current_user_recently_played(limit=10)
    recent_tracks = []
    seen_rt = set()
    for item in recent_res.get("items", []):
        t = item["track"]
        if t["id"] not in seen_rt:
            seen_rt.add(t["id"])
            recent_tracks.append({
                "id": t["id"],
                "name": t["name"],
                "artists": [a["name"] for a in t["artists"]],
                "image": t["album"]["images"][0]["url"] if t["album"].get("images") else None,
                "url": t["external_urls"]["spotify"]
            })

    top_t_res = sp.current_user_top_tracks(limit=10, time_range="short_term")
    top_tracks = [
        {
            "id": t["id"],
            "name": t["name"],
            "artists": [a["name"] for a in t["artists"]],
            "image": t["album"]["images"][0]["url"] if t["album"].get("images") else None,
            "url": t["external_urls"]["spotify"]
        }
        for t in top_t_res.get("items", [])
    ]

    top_art_res = sp.current_user_top_artists(limit=10, time_range="short_term")
    top_artists = [
        {
            "id": a["id"],
            "name": a["name"],
            "image": a["images"][0]["url"] if a.get("images") else None,
            "url": a["external_urls"]["spotify"]
        }
        for a in top_art_res.get("items", [])
    ]
    
    return {
        "recent_tracks": recent_tracks,
        "top_tracks": top_tracks,
        "top_artists": top_artists,
        "token": token
    }
