import sqlite3, json, time
from ..core.types import Fill, AccountSnapshot

class SQLiteStore:
    def __init__(self, cfg: dict):
        dsn = cfg.get("storage", {}).get("dsn", "sqlite:///spl.db")
        path = dsn.split("sqlite:///")[-1]
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._init()

    def _init(self):
        cur = self.conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS events(
            ts INTEGER, kind TEXT, payload TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS fills(
            ts INTEGER, client_id TEXT, symbol TEXT, side TEXT, px REAL, sz REAL, fee REAL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS snapshots(
            ts INTEGER, payload TEXT)""")
        self.conn.commit()

    def write_event(self, kind: str, payload: dict) -> None:
        self.conn.execute("INSERT INTO events VALUES (?, ?, ?)",
                          (int(time.time()*1000), kind, json.dumps(payload)))
        self.conn.commit()

    def write_fill(self, f: Fill) -> None:
        self.conn.execute("INSERT INTO fills VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (f.ts, f.client_id, f.symbol, f.side.value, f.px, f.sz, f.fee))
        self.conn.commit()

    def write_snapshot(self, s: AccountSnapshot) -> None:
        self.conn.execute("INSERT INTO snapshots VALUES (?, ?)",
                          (s.ts, json.dumps({"balance": s.balance, "positions": s.positions})))
        self.conn.commit()
