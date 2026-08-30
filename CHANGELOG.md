# Changelog

All notable changes to the IVN-Alpacca-Trader project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-08-30

### Added
- **Project Foundation:** Initialized repository with MIT License, `.gitignore` for API key protection, and a professional `README.md`.
- **Environment:** Created `.env.example` and `config.py` to securely manage Alpaca Paper API keys and Trading Constants (e.g., `PAPER_TRADING`, `MAX_LOSS_PER_TRADE_USD`, `MAX_POSITIONS`).
- **Dependencies:** Set up virtual environment and `requirements.txt` (`alpaca-py`, `pandas`, `pandas-ta`, `python-dotenv`, `numpy`).
- **Data Layer (`src/data/market_data.py`):** Added `MarketDataFetcher` class to pull historical 1-minute OHLCV bars for SPY/QQQ and fetch active Options chains.
- **Strategy Layer (`src/strategy/volume_profile.py`):** Implemented mathematical calculation of High Volume Nodes (HVNs) and Low Volume Nodes (LVNs) to act as dynamic Support/Resistance supply zones.
- **Logic Layer (`src/strategy/signal_generator.py`):** Built the core AI decision engine to detect "turns" (price action rejecting/bouncing off LVNs on 2x average volume spikes). Integrated Topstep-style hard daily loss limits.
- **Execution Layer (`src/execution/order_manager.py`):** Built standard routing for Options Limit Orders and Equity Market Orders via Alpaca's `TradingClient`. Included automated position closing capabilities.
- **Hackathon Requirement (MCP):** Created `src/mcp_server.py`, a lightweight JSON-RPC Model Context Protocol server exposing `get_account_balance` and `get_active_positions` to external AI evaluators.
- **Core Loop (`src/main.py`):** Tied all modules into a continuous daemon loop that updates the profile, scans live ticks, executes trades, and handles graceful shutdowns.
- **Testing:** Created unit test scripts in `tests/` for all modules and validated end-to-end API connectivity with Alpaca.

### Enforced
- **IVN Alpaca Deployment SOP:** Established a strict 7-step checklist (Test, Regression, Backtest, Document, Compile, Approval, Publish) enforced via `AGENTS.md` to prevent any broken or unprofitable logic from being deployed.
