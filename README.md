<div align="center">

# OmashelCap

**Automated trading bot for Deriv synthetic indices — with a real-time web dashboard**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?style=flat-square)](https://docs.astral.sh/uv/)
[![CI](https://img.shields.io/github/actions/workflow/status/iamMashel/OmashelCap/ci.yml?style=flat-square&label=CI&logo=githubactions&logoColor=white)](https://github.com/iamMashel/OmashelCap/actions)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

<br/>

![Dashboard Preview](https://placehold.co/900x480/030712/22c55e?text=OmashelCap+Dashboard&font=monospace)

</div>

---

## What is this?

OmashelCap is a full-stack algorithmic trading system built for **Deriv synthetic indices** — markets that trade 24/7, are unaffected by news events, and are accessible to retail traders worldwide.

The system connects to Deriv's WebSocket API, analyses market structure in real time, scores trading signals using multi-factor confluence, manages risk automatically, and streams everything live to a web dashboard — all with strict safety rules to protect your capital.

**Mock mode included** — runs fully without an API key so you can explore the dashboard and strategy logic before going live.

---

## Features

| Category | What it does |
|---|---|
| **Signal Engine** | Market structure (HH/HL), EMA alignment, RSI, Bollinger Bands, Supply & Demand zones |
| **Confluence Scoring** | 0–5 score — only fires when ≥3 conditions align |
| **Risk Management** | Fixed 1% fractional position sizing, hard max stake cap |
| **Circuit Breaker** | Auto-halts after 5 consecutive losses or 5% daily drawdown |
| **Live Dashboard** | Real-time signals, trade history, P&L, win rate via WebSocket |
| **Telegram Alerts** | Trade open/close and circuit breaker notifications |
| **Trade Logging** | Every trade logged to SQLite with full signal context |
| **Mock Mode** | Full simulation — no API key needed for development |
| **Docker Ready** | API + frontend containerised with docker-compose |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser Dashboard                     │
│         React + TypeScript + Tailwind + Zustand          │
└───────────────────────┬─────────────────────────────────┘
                        │  WebSocket + REST
┌───────────────────────▼─────────────────────────────────┐
│                    FastAPI (API Layer)                    │
│          /api/bot  /api/trades  /api/signals  /ws        │
└───────────────────────┬─────────────────────────────────┘
                        │  shared state
┌───────────────────────▼─────────────────────────────────┐
│                    Bot Engine (Python)                    │
│   WebSocket Client → Data Feed → Signal Engine           │
│   Risk Manager → Order Manager → Trade Logger            │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│              Deriv WebSocket API (wss://)                 │
│         Synthetic Indices — 24/7 live markets            │
└─────────────────────────────────────────────────────────┘
```

---

## Stack

| Layer | Technology |
|---|---|
| Bot engine | Python 3.12 · asyncio · websockets |
| API server | FastAPI · Uvicorn · WebSocket |
| Dashboard | React 19 · TypeScript · Vite · Tailwind CSS v4 |
| State | Zustand · TanStack Query |
| Database | SQLite (dev) → PostgreSQL (prod) |
| Python packages | [uv](https://docs.astral.sh/uv/) |
| Node packages | pnpm |
| Containers | Docker · docker-compose |
| CI | GitHub Actions (lint · typecheck · test) |

---

## Quick Start

### Mock Mode — no API key needed

```bash
# 1. Clone
git clone https://github.com/iamMashel/OmashelCap.git
cd OmashelCap

# 2. Set up environment
cp .env.example .env        # USE_MOCK=true by default

# 3. Install Python dependencies
uv sync

# 4. Install frontend dependencies
cd frontend && pnpm install && cd ..

# 5. Start API (Terminal 1)
uv run uvicorn api.main:app --reload --port 9000

# 6. Start dashboard (Terminal 2)
cd frontend && pnpm dev
```

Open **http://localhost:5173**, click **START BOT** — live mock signals and trades start flowing immediately.

---

### Live Trading Setup

> ⚠️ **Always start on a demo account. Never risk money you haven't tested with.**

1. Create a free account at [deriv.com](https://deriv.com)
2. Go to **Account → Security & Limits → API Token**
   - Create a token with scopes: `read` + `trade`
3. Register an app at [api.deriv.com](https://api.deriv.com) to get an `APP_ID`
4. Edit your `.env`:

```env
USE_MOCK=false
DERIV_APP_ID=your_app_id
DERIV_API_TOKEN=your_token
TRADING_MODE=demo           # keep this on demo until you're confident
SYMBOL=R_75                 # Volatility 75 Index
RISK_PER_TRADE=0.01         # 1% of balance per trade
MAX_STAKE=10.00             # hard ceiling — never exceeded
```

---

## Project Structure

```
OmashelCap/
│
├── core/               WebSocket client, session auth, message router
├── data/               Tick/candle models, rolling data store, feed subscriptions
├── analysis/           Indicators, market structure, supply/demand zones, signal scoring
├── risk/               Fixed fractional sizing, circuit breaker
├── trading/            Order lifecycle (proposal → buy → monitor), trade tracker
├── strategies/         Pluggable strategy interface + StructureConfluence v1
├── mock/               Mock bot — simulates real bot behaviour for development
│
├── api/                FastAPI — REST endpoints + WebSocket real-time push
│   └── routers/        /bot  /trades  /signals
│
├── frontend/           React dashboard
│   └── src/
│       ├── components/ StatCard, SignalPanel, BotControls, TradeHistory
│       ├── hooks/      useWebSocket (auto-reconnecting)
│       └── store/      Zustand bot state
│
├── storage/            SQLite trade logger
├── notify/             Telegram alerts
├── tests/              pytest test suite
│
├── docker-compose.yml
├── Dockerfile.api
├── .env.example        ← copy this to .env
└── dev.sh              ← starts both servers
```

---

## Signal Engine

The strategy scores each potential trade on 5 conditions. It only enters when **3 or more align**:

| Condition | CALL (buy) | PUT (sell) |
|---|---|---|
| Market structure | Higher Highs + Higher Lows | Lower Highs + Lower Lows |
| EMA alignment | EMA9 > EMA21 > EMA50 | EMA9 < EMA21 < EMA50 |
| RSI | < 35 (oversold) | > 65 (overbought) |
| Zone | Price at demand zone | Price at supply zone |
| Bollinger Bands | Price at lower band | Price at upper band |

---

## Risk Rules

| Rule | Value |
|---|---|
| Stake per trade | 1% of account balance |
| Minimum stake | $0.35 |
| Maximum stake | $10.00 (hard cap) |
| Circuit breaker — consecutive losses | Halts after 5 |
| Circuit breaker — daily drawdown | Halts at 5% loss from day open |
| Recovery method | **Fixed fractional only — no Martingale** |

---

## Running Tests

```bash
uv run pytest tests/ -v
```

```
tests/test_risk.py::test_stake_is_1_percent_of_balance   PASSED
tests/test_risk.py::test_stake_capped_at_max             PASSED
tests/test_risk.py::test_stake_minimum_enforced          PASSED
tests/test_risk.py::test_circuit_breaker_trips_on_max    PASSED
tests/test_risk.py::test_circuit_breaker_resets_on_win   PASSED
tests/test_risk.py::test_daily_drawdown_trips_circuit    PASSED
tests/test_structure.py::test_uptrend_detected           PASSED
tests/test_structure.py::test_ema_uptrend                PASSED
8 passed in 0.62s
```

---

## Docker

```bash
cp .env.example .env
# fill in your credentials
docker-compose up --build
```

Dashboard → `http://localhost:5173`
API → `http://localhost:8000`

---

## Roadmap

- [ ] TradingView Lightweight Charts price feed
- [ ] Crash/Boom spike detection strategy
- [ ] Backtesting engine against historical candles
- [ ] PostgreSQL migration for production
- [ ] Telegram signal-only mode (no auto-trade)
- [ ] Multi-symbol simultaneous trading
- [ ] ML regime detection (trending vs ranging)

---

## Risk Disclaimer

Synthetic indices are generated by a cryptographically secure RNG. Binary options have a structural house edge — at 85% payout you need a **>54% win rate just to break even**. Past performance of any strategy does not guarantee future results.

**Never trade with money you cannot afford to lose entirely. Always validate on a demo account first.**

---

## License

MIT © [Mashel Odera](https://github.com/iamMashel)
