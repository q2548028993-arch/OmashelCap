import asyncio
import logging
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)


class Session:
    """
    Manages Deriv API authorization state.
    Tracks account balance and login info after auth.
    """

    def __init__(self):
        self.authorized = asyncio.Event()
        self.balance: float = 0.0
        self.currency: str = "USD"
        self.account_id: Optional[str] = None
        self.is_virtual: bool = True

    async def authorize(self, send_fn) -> None:
        logger.info("Authorizing with Deriv API...")
        await send_fn({"authorize": settings.API_TOKEN})

    def on_authorize(self, data: dict) -> None:
        account = data.get("authorize", {})
        self.balance = float(account.get("balance", 0))
        self.currency = account.get("currency", "USD")
        self.account_id = account.get("loginid")
        self.is_virtual = account.get("is_virtual", 1) == 1
        self.authorized.set()
        logger.info(
            f"Authorized | Account: {self.account_id} | "
            f"Balance: {self.balance} {self.currency} | "
            f"Virtual: {self.is_virtual}"
        )

    def on_balance(self, data: dict) -> None:
        balance_data = data.get("balance", {})
        self.balance = float(balance_data.get("balance", self.balance))

    async def wait_authorized(self) -> None:
        await self.authorized.wait()
