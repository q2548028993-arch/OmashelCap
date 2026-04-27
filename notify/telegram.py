import logging

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
        self._bot: tg.Bot | None = None  # type: ignore[name-defined]
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

    @property
    def enabled(self) -> bool:
        return self._enabled

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

    async def send_startup(self, balance: float, currency: str, symbol: str, mode: str) -> None:
        await self.send(
            f"🤖 *OmashelCap Bot Started*\n"
            f"Symbol: `{symbol}`\n"
            f"Balance: `{balance:.2f} {currency}`\n"
            f"Mode: `{mode}`\n"
            f"Risk per trade: `{settings.RISK_PER_TRADE * 100:.1f}%`\n"
            f"Max stake: `${settings.MAX_STAKE:.2f}`"
        )

    async def send_signal(
        self,
        direction: str,
        symbol: str,
        score: int,
        trend: str,
        zone: str,
        rsi: float,
        reason: str,
    ) -> None:
        arrow = "📈" if direction == "CALL" else "📉"
        await self.send(
            f"{arrow} *Signal Detected*\n"
            f"Direction: `{direction}` on `{symbol}`\n"
            f"Score: `{score}/5`\n"
            f"Trend: `{trend}` | Zone: `{zone}` | RSI: `{rsi:.1f}`\n"
            f"_{reason}_"
        )

    async def trade_opened(
        self, direction: str, symbol: str, stake: float, score: int, reason: str
    ) -> None:
        arrow = "📈" if direction == "CALL" else "📉"
        await self.send(
            f"{arrow} *Trade Opened*\n"
            f"`{direction}` on `{symbol}`\n"
            f"Stake: `${stake:.2f}` | Score: `{score}/5`\n"
            f"_{reason}_"
        )

    async def trade_closed(
        self,
        direction: str,
        symbol: str,
        profit: float,
        balance: float,
        wins: int,
        losses: int,
        session_pnl: float,
    ) -> None:
        emoji = "✅" if profit > 0 else "❌"
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0
        await self.send(
            f"{emoji} *Trade Closed*\n"
            f"`{direction}` on `{symbol}`\n"
            f"Profit: `{profit:+.2f}`\n"
            f"Balance: `${balance:.2f}`\n"
            f"Session P&L: `{session_pnl:+.2f}`\n"
            f"Win rate: `{win_rate:.1f}%` ({wins}W/{losses}L)"
        )

    async def circuit_tripped(self, reason: str) -> None:
        await self.send(
            f"🚨 *Circuit Breaker Tripped*\n{reason}\n_Bot has stopped. Manual review required._"
        )

    async def send_daily_summary(
        self, wins: int, losses: int, session_pnl: float, balance: float
    ) -> None:
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0
        emoji = "📊"
        await self.send(
            f"{emoji} *Daily Summary*\n"
            f"Trades: `{total}` | W/L: `{wins}/{losses}`\n"
            f"Win rate: `{win_rate:.1f}%`\n"
            f"Session P&L: `{session_pnl:+.2f}`\n"
            f"Balance: `${balance:.2f}`"
        )

    async def test_message(self) -> None:
        await self.send(
            "✅ *OmashelCap — Telegram connected*\n_You will receive trade alerts here._"
        )
