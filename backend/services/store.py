import base64
import hashlib
import json
import os
import sqlite3
import threading
import time
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

SCHEMA = """
create table if not exists users (
    user_id text primary key,
    refresh_token text not null,
    updated_at integer not null
);
create table if not exists automations (
    id integer primary key autoincrement,
    user_id text not null,
    kind text not null,
    settings text not null default '{}',
    enabled integer not null default 1,
    playlist_id text,
    playlist_url text,
    last_run integer,
    next_run integer not null,
    last_status text,
    last_count integer,
    created_at integer not null
);
create index if not exists automations_due on automations (enabled, next_run);
"""

FIELDS = {"settings", "enabled", "playlist_id", "playlist_url", "last_run", "next_run", "last_status", "last_count"}


class Store:
    def __init__(self):
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.Lock()

    def _db(self) -> sqlite3.Connection:
        if self._conn is None:
            raw = os.getenv("MULTISPOT_DB")
            path = Path(raw).expanduser() if raw else Path.home() / ".multispot" / "multispot.db"
            path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.executescript(SCHEMA)
            conn.commit()
            self._conn = conn
        return self._conn

    def _fernet(self) -> Fernet:
        secret = os.getenv("SESSION_SECRET_KEY") or ""
        key = base64.urlsafe_b64encode(hashlib.sha256(f"multispot-store:{secret}".encode()).digest())
        return Fernet(key)

    def _row(self, row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        item = dict(row)
        item["settings"] = json.loads(item.get("settings") or "{}")
        item["enabled"] = bool(item.get("enabled"))
        return item

    def save_user(self, user_id: str, refresh_token: str | None):
        if not user_id or not refresh_token:
            return
        sealed = self._fernet().encrypt(refresh_token.encode()).decode()
        with self._lock:
            db = self._db()
            db.execute(
                "insert into users (user_id, refresh_token, updated_at) values (?, ?, ?) "
                "on conflict(user_id) do update set refresh_token = excluded.refresh_token, updated_at = excluded.updated_at",
                (user_id, sealed, int(time.time())),
            )
            db.commit()

    def user_token(self, user_id: str) -> str | None:
        with self._lock:
            row = self._db().execute("select refresh_token from users where user_id = ?", (user_id,)).fetchone()
        if not row:
            return None
        try:
            return self._fernet().decrypt(row["refresh_token"].encode()).decode()
        except InvalidToken:
            return None

    def has_automations(self, user_id: str) -> bool:
        with self._lock:
            row = self._db().execute("select 1 from automations where user_id = ? limit 1", (user_id,)).fetchone()
        return row is not None

    def list_automations(self, user_id: str) -> list[dict]:
        with self._lock:
            rows = self._db().execute("select * from automations where user_id = ? order by id", (user_id,)).fetchall()
        return [self._row(r) for r in rows]

    def get_automation(self, automation_id: int) -> dict | None:
        with self._lock:
            row = self._db().execute("select * from automations where id = ?", (automation_id,)).fetchone()
        return self._row(row)

    def find_automation(self, user_id: str, kind: str) -> dict | None:
        with self._lock:
            row = self._db().execute("select * from automations where user_id = ? and kind = ?", (user_id, kind)).fetchone()
        return self._row(row)

    def create_automation(self, user_id: str, kind: str, settings: dict, next_run: int) -> dict:
        with self._lock:
            db = self._db()
            cur = db.execute(
                "insert into automations (user_id, kind, settings, enabled, next_run, created_at) values (?, ?, ?, 1, ?, ?)",
                (user_id, kind, json.dumps(settings), next_run, int(time.time())),
            )
            db.commit()
            new_id = cur.lastrowid
        return self.get_automation(new_id)

    def update_automation(self, automation_id: int, **fields) -> dict | None:
        clean = {k: v for k, v in fields.items() if k in FIELDS}
        if "settings" in clean:
            clean["settings"] = json.dumps(clean["settings"])
        if "enabled" in clean:
            clean["enabled"] = 1 if clean["enabled"] else 0
        if clean:
            assignments = ", ".join(f"{k} = ?" for k in clean)
            with self._lock:
                db = self._db()
                db.execute(f"update automations set {assignments} where id = ?", (*clean.values(), automation_id))
                db.commit()
        return self.get_automation(automation_id)

    def delete_automation(self, automation_id: int):
        with self._lock:
            db = self._db()
            db.execute("delete from automations where id = ?", (automation_id,))
            db.commit()

    def due(self, now: float) -> list[dict]:
        with self._lock:
            rows = self._db().execute("select * from automations where enabled = 1 and next_run <= ? order by next_run", (int(now),)).fetchall()
        return [self._row(r) for r in rows]


store = Store()
