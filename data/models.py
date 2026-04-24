from dataclasses import dataclass
from datetime import datetime


@dataclass
class Tick:
    symbol: str
    epoch: int
    quote: float
    pip_size: float = 0.0001

    @property
    def time(self) -> datetime:
        return datetime.utcfromtimestamp(self.epoch)


@dataclass
class Candle:
    symbol: str
    epoch: int
    open: float
    high: float
    low: float
    close: float
    granularity: int

    @property
    def time(self) -> datetime:
        return datetime.utcfromtimestamp(self.epoch)

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        return self.close < self.open

    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)

    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low


@dataclass
class TradeSignal:
    symbol: str
    direction: str       # "CALL" | "PUT" | "NONE"
    score: int           # 0–5 confluence score
    reason: str          # human-readable explanation
    trend: str           # "UPTREND" | "DOWNTREND" | "RANGE"
    zone: str            # "DEMAND" | "SUPPLY" | "NONE"
    rsi: float
    stake: float = 0.0
