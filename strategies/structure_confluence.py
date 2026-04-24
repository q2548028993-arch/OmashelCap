from analysis.signals import evaluate
from config.settings import settings
from data.models import TradeSignal
from data.store import DataStore
from strategies.base import BaseStrategy


class StructureConfluenceStrategy(BaseStrategy):
    """
    Structure + Zone + RSI + EMA + Bollinger Band confluence.

    Entry logic (CALL example):
      - Market structure shows Higher Highs / Higher Lows (UPTREND)
      - EMA 9 > EMA 21 > EMA 50 (trend aligned)
      - RSI < 35 (oversold pullback)
      - Price at a demand zone (strong prior bullish move origin)
      - Price touching lower Bollinger Band (confirming oversold)
      Score >= 3 of these 5 conditions → signal fires

    This is the V1 strategy. It is deliberately conservative —
    misses some trades but filters the worst noise.
    """

    @property
    def name(self) -> str:
        return "StructureConfluence_v1"

    def evaluate(self, store: DataStore) -> TradeSignal:
        if not store.has_enough_data(min_candles=50):
            return TradeSignal(
                symbol=settings.SYMBOL,
                direction="NONE",
                score=0,
                reason="Not enough candles yet",
                trend="RANGE",
                zone="NONE",
                rsi=50.0,
            )
        return evaluate(store.df, settings.SYMBOL)
