import logging
from collections import deque

import pandas as pd

from config.settings import settings
from data.models import Candle, Tick

logger = logging.getLogger(__name__)


class DataStore:
    """
    Rolling in-memory store for ticks and candles per symbol.
    Exposes a pandas DataFrame of candles for indicator computation.
    """

    def __init__(self, symbol: str):
        self.symbol = symbol
        self._ticks: deque[Tick] = deque(maxlen=settings.TICK_BUFFER_SIZE)
        self._candles: list[Candle] = []
        self._df: pd.DataFrame | None = None
        self._df_dirty = True

    # ── Ticks ────────────────────────────────────────────────────────────────

    def add_tick(self, tick: Tick) -> None:
        self._ticks.append(tick)

    @property
    def latest_tick(self) -> Tick | None:
        return self._ticks[-1] if self._ticks else None

    @property
    def ticks(self) -> list[Tick]:
        return list(self._ticks)

    # ── Candles ──────────────────────────────────────────────────────────────

    def load_candles(self, candles: list[Candle]) -> None:
        self._candles = sorted(candles, key=lambda c: c.epoch)
        self._df_dirty = True
        logger.info(f"[{self.symbol}] Loaded {len(self._candles)} candles")

    def update_candle(self, candle: Candle) -> None:
        if self._candles and self._candles[-1].epoch == candle.epoch:
            self._candles[-1] = candle
        else:
            self._candles.append(candle)
            if len(self._candles) > settings.CANDLE_HISTORY_COUNT:
                self._candles.pop(0)
        self._df_dirty = True

    @property
    def df(self) -> pd.DataFrame:
        if self._df_dirty or self._df is None:
            self._df = self._build_df()
            self._df_dirty = False
        return self._df

    def _build_df(self) -> pd.DataFrame:
        if not self._candles:
            return pd.DataFrame(columns=["epoch", "open", "high", "low", "close"])
        records = [
            {
                "epoch": c.epoch,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
            }
            for c in self._candles
        ]
        df = pd.DataFrame(records)
        df["time"] = pd.to_datetime(df["epoch"], unit="s", utc=True)
        df.set_index("time", inplace=True)
        return df

    def has_enough_data(self, min_candles: int = 50) -> bool:
        return len(self._candles) >= min_candles
