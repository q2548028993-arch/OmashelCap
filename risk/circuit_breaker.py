import logging
from datetime import UTC, date, datetime

from config.settings import settings

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Enforces trading safety limits:
      - Max consecutive losses
      - Daily drawdown limit (% of day-open balance)
    When tripped, trading halts until manually reset or next day.
    """

    def __init__(self, opening_balance: float):
        self._opening_balance = opening_balance
        self._consecutive_losses = 0
        self._tripped = False
        self._trip_reason = ""
        self._last_reset_date: date = datetime.now(UTC).date()

    # ── State checks ──────────────────────────────────────────────────────────

    @property
    def is_tripped(self) -> bool:
        self._check_day_reset()
        return self._tripped

    @property
    def trip_reason(self) -> str:
        return self._trip_reason

    def can_trade(self) -> bool:
        return not self.is_tripped

    # ── Event handlers ────────────────────────────────────────────────────────

    def on_win(self) -> None:
        self._consecutive_losses = 0
        logger.debug("Circuit breaker: win recorded, loss streak reset")

    def on_loss(self, current_balance: float) -> None:
        self._consecutive_losses += 1
        logger.warning(
            f"Circuit breaker: loss #{self._consecutive_losses} | balance={current_balance:.2f}"
        )
        self._check_consecutive_losses()
        self._check_daily_drawdown(current_balance)

    # ── Internal checks ───────────────────────────────────────────────────────

    def _check_consecutive_losses(self) -> None:
        if self._consecutive_losses >= settings.MAX_CONSECUTIVE_LOSSES:
            self._trip(
                f"Max consecutive losses reached ({self._consecutive_losses}). "
                f"Manual review required."
            )

    def _check_daily_drawdown(self, current_balance: float) -> None:
        drawdown = (self._opening_balance - current_balance) / self._opening_balance
        if drawdown >= settings.DAILY_DRAWDOWN_LIMIT:
            self._trip(
                f"Daily drawdown limit hit: {drawdown * 100:.1f}% "
                f"(limit={settings.DAILY_DRAWDOWN_LIMIT * 100:.1f}%)"
            )

    def _trip(self, reason: str) -> None:
        if not self._tripped:
            self._tripped = True
            self._trip_reason = reason
            logger.critical(f"CIRCUIT BREAKER TRIPPED: {reason}")

    def _check_day_reset(self) -> None:
        today = datetime.now(UTC).date()
        if today > self._last_reset_date:
            self._reset_for_new_day()
            self._last_reset_date = today

    def _reset_for_new_day(self) -> None:
        logger.info("New trading day — circuit breaker reset")
        self._consecutive_losses = 0
        self._tripped = False
        self._trip_reason = ""

    def manual_reset(self, new_opening_balance: float) -> None:
        logger.warning(
            f"Circuit breaker manually reset. New opening balance: {new_opening_balance:.2f}"
        )
        self._opening_balance = new_opening_balance
        self._consecutive_losses = 0
        self._tripped = False
        self._trip_reason = ""

    def status(self) -> dict:
        return {
            "tripped": self._tripped,
            "reason": self._trip_reason,
            "consecutive_losses": self._consecutive_losses,
            "opening_balance": self._opening_balance,
        }
