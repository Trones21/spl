# plugins/spl-adapter-drift/src/spl_adapter_drift/backend.py
from spl.core.types import OrderReq, Fill, Side, OrdType
from spl.core.utils import fee_from_bps
from spl.core.types import AccountSnapshot
import time

# When you go live:
# from driftpy.drift_client import DriftClient
# from solders.keypair import Keypair
# from solana.rpc.api import Client as SolClient

class DriftExec:
    def __init__(self, cfg, store):
        self.store = store
        self.cfg = cfg
        # rpc = cfg["rpc_url"]
        # kp_path = cfg["keypair_path"]
        # self.conn = SolClient(rpc)
        # self.kp = Keypair.from_bytes(open(kp_path, "rb").read())
        # self.client = DriftClient(self.conn, self.kp)

    def place(self, req: OrderReq) -> str:
        # TODO: implement via driftpy when live
        # tx = self.client.place_perp_order(...)
        self.store.write_event("place_live_drift", {"client_id": req.client_id, "symbol": req.symbol})
        return req.client_id

    def cancel(self, client_order_id: str) -> bool:
        # TODO: self.client.cancel_order(...)
        self.store.write_event("cancel_live_drift", {"client_id": client_order_id})
        return True

    def on_quote(self, q): return []      # live fills come from program logs/indexer
    def on_trade(self, t): return []       # you can map trades -> fills later

    def snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(ts=int(time.time()*1000), balance=0.0, positions={})
