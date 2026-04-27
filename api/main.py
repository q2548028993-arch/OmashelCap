"""
FastAPI application — exposes bot state and controls to the dashboard.
The bot engine runs as a background asyncio task.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import bot, signals, trades
from api.routers.backtest import router as backtest_router
from api.routers.settings_router import router as settings_router
from api.state import bot_state
from api.ws import ws_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API starting up")
    yield
    logger.info("API shutting down")
    await bot_state.stop()


app = FastAPI(
    title="OmashelCap Trading Bot API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bot.router, prefix="/api/bot", tags=["bot"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(backtest_router, prefix="/api/backtest", tags=["backtest"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
app.include_router(ws_router, prefix="/ws", tags=["websocket"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
