from ..core.types import Side

def trade_crosses_limit(side: Side, limit_px: float, trade_px: float) -> bool:
    if side == Side.BUY and trade_px <= limit_px: return True
    if side == Side.SELL and trade_px >= limit_px: return True
    return False
