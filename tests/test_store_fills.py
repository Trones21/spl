from spltrader.storage.sqlite_store import SQLiteStore 

def test_fills_written(tmp_path, monkeypatch):
    db = tmp_path/"spl.db"
    cfg = {"storage": {"path": str(db)}}
    store = SQLiteStore(cfg)

    # fake fill
    from spltrader.core.types import Fill, Side
    f = Fill(ts=123, client_id="t1", symbol="SOL-PERP", side=Side.BUY, px=100.0, sz=0.01, fee=0.0)
    store.write_fill(f)

    import sqlite3
    conn = sqlite3.connect(db)
    n, = conn.execute("select count(*) from fills").fetchone()
    assert n == 1
