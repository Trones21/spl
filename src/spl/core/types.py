from dataclasses import dataclass
from enum import Enum

class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrdType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

@dataclass
class Quote:
    ts: int
    bid: float
    ask: float
    bid_sz: float
    ask_sz: float

@dataclass
class Trade:
    ts: int
    price: float
    size: float
    side: Side  # aggressor

@dataclass
class OrderReq:
    client_id: str
    symbol: str
    side: Side
    type: OrdType
    px: float | None
    sz: float
    tif: str = "GTC"
    meta: dict | None = None

@dataclass
class Fill:
    ts: int
    client_id: str
    symbol: str
    side: Side
    px: float
    sz: float
    fee: float

@dataclass
class AccountSnapshot:
    ts: int
    balance: float
    positions: dict  # symbol -> dict(base, pnl_unreal, pnl_real)
