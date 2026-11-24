"""Persistencia SQLite (stdlib)."""
from __future__ import annotations
import json, os, sqlite3
from datetime import datetime
from typing import Any

DEFAULT_PATH = os.path.expanduser("~/pocketlab/lab.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS captures(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL, kind TEXT NOT NULL, label TEXT, data TEXT
);
CREATE INDEX IF NOT EXISTS idx_kind ON captures(kind);
CREATE INDEX IF NOT EXISTS idx_ts ON captures(ts);
CREATE TABLE IF NOT EXISTS devices(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE, category TEXT, location TEXT, notes TEXT, created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS device_links(
    capture_id INTEGER NOT NULL, device_id INTEGER NOT NULL,
    PRIMARY KEY (capture_id, device_id)
);
"""

class Store:
    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def log(self, kind, label="", data=None):
        cur = self._conn.execute(
            "INSERT INTO captures(ts,kind,label,data) VALUES(?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), kind, label,
             json.dumps(data, ensure_ascii=False)))
        self._conn.commit()
        return int(cur.lastrowid)

    def recent(self, limit=25, kind=None):
        q = "SELECT id,ts,kind,label FROM captures"
        args = []
        if kind:
            q += " WHERE kind=?"; args.append(kind)
        q += " ORDER BY id DESC LIMIT ?"; args.append(limit)
        return self._conn.execute(q, args).fetchall()

    def all_rows(self):
        return self._conn.execute("SELECT id,ts,kind,label,data FROM captures ORDER BY id").fetchall()

    def count(self):
        return self._conn.execute("SELECT COUNT(*) FROM captures").fetchone()[0]

    def add_device(self, name, category="", location="", notes=""):
        cur = self._conn.execute(
            "INSERT INTO devices(name,category,location,notes,created) VALUES(?,?,?,?,?)",
            (name, category, location, notes, datetime.now().isoformat(timespec="seconds")))
        self._conn.commit()
        return int(cur.lastrowid)

    def list_devices(self):
        return self._conn.execute("SELECT id,name,category,location,notes FROM devices ORDER BY name").fetchall()

    def get_device(self, device_id):
        return self._conn.execute("SELECT id,name,category,location,notes FROM devices WHERE id=?", (device_id,)).fetchone()

    def delete_device(self, device_id):
        self._conn.execute("DELETE FROM device_links WHERE device_id=?", (device_id,))
        self._conn.execute("DELETE FROM devices WHERE id=?", (device_id,))
        self._conn.commit()

    def link(self, capture_id, device_id):
        self._conn.execute("INSERT OR IGNORE INTO device_links(capture_id,device_id) VALUES(?,?)", (capture_id, device_id))
        self._conn.commit()

    def captures_for_device(self, device_id, limit=50):
        return self._conn.execute(
            "SELECT c.id,c.ts,c.kind,c.label FROM captures c JOIN device_links l ON l.capture_id=c.id WHERE l.device_id=? ORDER BY c.id DESC LIMIT ?",
            (device_id, limit)).fetchall()

    def close(self):
        self._conn.close()
