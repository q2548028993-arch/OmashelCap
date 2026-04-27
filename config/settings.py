import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class Settings:
    # Deriv connection
    APP_ID: str = os.getenv("DERIV_APP_ID", "")
    API_TOKEN: str = os.getenv("DERIV_API_TOKEN", "")
    WS_URL: str = f"wss://ws.derivws.com/websockets/v3?app_id={os.getenv('DERIV_APP_ID', '')}"

    # Trading
    TRADING_MODE: str = os.getenv("TRADING_MODE", "demo")
    SYMBOL: str = os.getenv("SYMBOL", "R_75")
    CANDLE_GRANULARITY: int = int(os.getenv("CANDLE_GRANULARITY", "60"))
    CONTRACT_TYPE: str = os.getenv("CONTRACT_TYPE", "CALL")
    TRADE_DURATION: int = int(os.getenv("TRADE_DURATION", "5"))
    TRADE_DURATION_UNIT: str = os.getenv("TRADE_DURATION_UNIT", "m")

    # Risk
    RISK_PER_TRADE: float = float(os.getenv("RISK_PER_TRADE", "0.01"))
    MIN_STAKE: float = float(os.getenv("MIN_STAKE", "0.35"))
    MAX_STAKE: float = float(os.getenv("MAX_STAKE", "10.0"))

    # Circuit breakers
    MAX_CONSECUTIVE_LOSSES: int = int(os.getenv("MAX_CONSECUTIVE_LOSSES", "5"))
    DAILY_DRAWDOWN_LIMIT: float = float(os.getenv("DAILY_DRAWDOWN_LIMIT", "0.05"))

    # Data
    CANDLE_HISTORY_COUNT: int = 300
    TICK_BUFFER_SIZE: int = 1000

    # Heartbeat
    PING_INTERVAL: int = 25

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    def validate(self) -> None:
        if not self.APP_ID:
            raise ValueError("DERIV_APP_ID is not set in .env")
        if not self.API_TOKEN:
            raise ValueError("DERIV_API_TOKEN is not set in .env")


settings = Settings()
