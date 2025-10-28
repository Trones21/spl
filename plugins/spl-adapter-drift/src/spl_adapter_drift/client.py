# plugins/spl-adapter-drift/src/spl_adapter_drift/client.py
from solana.rpc.async_api import AsyncClient
from anchorpy import Wallet
from solders.keypair import Keypair
from driftpy.drift_client import DriftClient
from driftpy.accounts import AccountSubscriptionConfig
from .async_bridge import AsyncBridge

# Encapsulates the low-level connection and DriftClient bootstrap.
# Responsibilities:
#     - Spin up the Solana RPC + WS connections.
#     - Manage the async → sync bridge.
#     - Hold the active DriftClient.

class DriftHandle:
    def __init__(self, cfg: dict):
        self.bridge = AsyncBridge()

        http = cfg["rpc"]["url"]
        ws   = cfg["rpc"].get("ws")  # optional but recommended
        commitment = cfg.get("commitment", "confirmed")
        env = cfg.get("network", "mainnet")  # "mainnet" or "devnet"

        kp = Keypair.from_bytes(open(cfg["wallet"]["keypair_path"], "rb").read())
        self.wallet = Wallet(kp)

        self.conn = AsyncClient(http, ws_url=ws, commitment=commitment)

        # Prefer websocket accounts to avoid batch polling issues
        sub_cfg = AccountSubscriptionConfig(type="websocket", commitment=commitment)

        self.dc = DriftClient(
            self.conn,
            wallet=self.wallet,
            env=env,
            account_subscription=sub_cfg,
        )

        # subscribe once (async) behind the bridge
        self.bridge.run(self.dc.subscribe())

    def close(self):
        # optional: self.bridge.run(self.dc.unsubscribe())
        self.bridge.stop()
