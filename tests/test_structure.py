import pandas as pd

from analysis.structure import get_ema_trend, get_trend


def _make_df(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "ema_9": closes,
            "ema_21": [c - 2 for c in closes],
            "ema_50": [c - 4 for c in closes],
        }
    )


def test_uptrend_detected():
    # Oscillating uptrend: trend rises but with pullbacks so swing points form
    prices = [10 + i * 0.5 + (3 if i % 10 < 5 else -1) for i in range(60)]
    df = _make_df(prices)
    assert get_trend(df) == "UPTREND"


def test_ema_uptrend():
    closes = [50.0] * 60
    df = _make_df(closes)
    # ema_9 > ema_21 > ema_50 by construction above
    assert get_ema_trend(df) == "UPTREND"
