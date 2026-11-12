import importlib
from dataclasses import dataclass

import flet as ft

from app.theme import CYAN, GOLD, GREEN, LIME, MINT, ORANGE, PINK, PURPLE, YELLOW


@dataclass(frozen=True)
class Feature:
    key: str
    title: str
    blurb: str
    icon: ft.IconData
    accent: str
    module: str


FEATURES = [
    Feature("stats", "Stats Hub", "Top tracks, artists and your musical DNA.", ft.Icons.INSIGHTS, GOLD, "stats"),
    Feature("random_hub", "Random Hub", "Genre roulette or one-genre stations.", ft.Icons.CASINO, GREEN, "random_hub"),
    Feature("fusion", "Fusion Center", "Fuse tracks and artists into one mix.", ft.Icons.HUB, MINT, "fusion"),
    Feature("time_machine", "Time Machine", "Queue hits from any decade.", ft.Icons.HISTORY, YELLOW, "time_machine"),
    Feature("magic", "Magic Mix", "A fresh playlist from your taste.", ft.Icons.AUTO_AWESOME, CYAN, "magic"),
    Feature("track_to_playlist", "Track Radio", "One track in, full playlist out.", ft.Icons.RADIO, PURPLE, "track_to_playlist"),
    Feature("queue_setter", "Queue Setter", "Interleave playlists into a queue.", ft.Icons.QUEUE_MUSIC, ORANGE, "queue_setter"),
    Feature("shuffler", "True Shuffle", "Recreate a playlist in real random order.", ft.Icons.SHUFFLE, PINK, "shuffler"),
    Feature("track_stats", "Track X-Ray", "Deep stats for any single track.", ft.Icons.QUERY_STATS, LIME, "track_stats"),
    Feature("rewind", "Rewind", "Save your top or recent plays as a playlist.", ft.Icons.HISTORY, PURPLE, "rewind"),
]

BY_KEY = {f.key: f for f in FEATURES}


def number_of(key: str) -> str:
    return f"{[f.key for f in FEATURES].index(key) + 1:02d}"


def build(app, key: str, **kwargs) -> ft.View:
    feature = BY_KEY[key]
    module = importlib.import_module(f"app.screens.{feature.module}")
    return module.build(app, feature, **kwargs)
