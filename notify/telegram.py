import logging
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)

try:
    import telegram as tg
    _TELEGRAM_AVAILABLE = True
except ImportError:
    _TELEGRAM_AVAILABLE = False


class TelegramNotifier:
    """
    Sends trade alerts to a Telegram chat.
    Gracefully disabled if token/chat_id are not set or library missing.
    """

    def __init__(self):
        self._bot: Optional[object] = None
        self._enabled = False

        if not _TELEGRAM_AVAILABLE:
            logger.warning("python-telegram-bot not installed — notifications disabled")
            return

        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            self._bot = tg.Bot(token=settings.TELEGRAM_BOT_TOKEN)
            self._enabled = True
            logger.info("Telegram notifications enabled")
        else:
            logger.info("Telegram not configured — notifications disabled")

    async def send(self, text: str) -> None:
        if not self._enabled or self._bot is None:
            return
        try:
            await self._bot.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                text=text,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning(f"Telegram send failed: {e}")

    async def trade_opened(self, direction: str, stake: float, score: int, reason: str) -> None:
        await self.send(
            f"*TRADE OPEN*\n"
            f"Direction: `{direction}`\n"
            f"Stake: `${stake:.2f}`\n"
            f"Score: `{score}/5`\n"
            f"Reason: _{reason}_"
        )

    async def trade_closed(self, direction: str, profit: float, win_rate: float, total_pnl: float) -> None:
        emoji = "✅" if profit > 0 else "❌"
        await self.send(
            f"{emoji} *TRADE CLOSED*\n"
            f"Direction: `{direction}`\n"
            f"Profit: `{profit:+.2f}`\n"
            f"Win rate: `{win_rate*100:.1f}%`\n"
            f"Session P&L: `{total_pnl:+.2f}`"
        )

    async def circuit_tripped(self, reason: str) -> None:
        await self.send(f"🚨 *CIRCUIT BREAKER TRIPPED*\n{reason}")
