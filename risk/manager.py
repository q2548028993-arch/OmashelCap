import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Computes position size using fixed fractional risk.
    Stakes 1% of current balance per trade, bounded by MIN_STAKE and MAX_STAKE.
    """

    def __init__(self, balance: float):
        self._balance = balance

    def update_balance(self, balance: float) -> None:
        self._balance = balance

    def compute_stake(self) -> float:
        raw = self._balance * settings.RISK_PER_TRADE
        stake = max(settings.MIN_STAKE, min(raw, settings.MAX_STAKE))
        logger.debug(
            f"Stake computed: {stake:.2f} "
            f"(balance={self._balance:.2f}, risk={settings.RISK_PER_TRADE*100:.1f}%)"
        )
        return round(stake, 2)

    @property
    def balance(self) -> float:
        return self._balance
