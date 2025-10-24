from ..core.types import Side, OrdType, Quote

def paper_px_for_market(side: Side, q: Quote, slippage_bps: float) -> float:
    ref = q.ask if side == Side.BUY else q.bid
    return ref * (1 + (slippage_bps / 1e4) * (1 if side == Side.BUY else -1))
