def fee_from_bps(notional: float, bps: float) -> float:
    return abs(notional) * (bps / 1e4)
