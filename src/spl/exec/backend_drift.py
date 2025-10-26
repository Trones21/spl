# src/spl/exec/backend_drift.py
from driftpy.drift_client import DriftClient
from solders.keypair import Keypair
from solana.rpc.api import Client as SolClient

class DriftExec:
    def __init__(self, cfg, store):
        rpc = cfg["rpc_url"]                # e.g. https://mainnet.helius.rpc...
        kp_path = cfg["keypair_path"]       # or a base58 secret
        self.store = store
        self.conn = SolClient(rpc)
        self.kp = Keypair.from_bytes(open(kp_path,"rb").read())
        self.client = DriftClient(self.conn, self.kp)   # more opts as needed

    def place(self, req):
        # translate OrderReq -> driftpy place_perp_order(...)
        # returns tx sig / order id; store event
        ...

    def on_quote(self, q): return []
    def on_trade(self, t): return []
