# src/spl/storage/sqlite_store.py
import sqlite3, time, json
from pathlib import Path
from ..core.types import Fill

class SQLiteStore:
    def __init__(self, cfg: dict):
        dbpath = cfg.get("storage", {}).get("path", "spl.db")
        self.conn = sqlite3.connect(Path(dbpath))
        self.conn.execute("""CREATE TABLE IF NOT EXISTS fills(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER, client_id TEXT, symbol TEXT, side TEXT,
            px REAL, sz REAL, fee REAL
        )""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER, kind TEXT, payload TEXT
        )""")
        self.conn.commit()
    
    def write_fill(self, f: Fill):
        self.conn.execute(
            "INSERT INTO fills(ts, client_id, symbol, side, px, sz, fee) VALUES (?,?,?,?,?,?,?)",
            (f.ts, f.client_id, f.symbol, f.side.value, f.px, f.sz, f.fee),
        )
        self.conn.commit()

    def write_event(self, kind: str, payload: dict):
        self.conn.execute(
            "INSERT INTO events(ts, kind, payload) VALUES (?,?,?)",
            (int(time.time()*1000), kind, json.dumps(payload)),
        )
        self.conn.commit()
