---
name: futures-trading
description: AI-driven futures trading system for Binance USDT-M perpetuals. Use when the user wants to start a trading session, scan markets, analyze pairs, execute trades, check positions, review performance, or modify trading strategy. Covers full lifecycle: scanning, analysis, entry, exit, journaling, and strategy evolution.
---

# Futures Trading System

AI-driven trading on Binance crypto futures (USDT-M perpetuals). You are the trader, not a bot.

## Quick Start

1. Read `MASTER.md` for identity and hard rules
2. Read `STRATEGY.md` for current signal logic
3. Read `STATE.md` for current account state
4. Run market scan via `engine.py` and `executor.py`
5. Execute trades through `executor.py`
6. Log results via `monitor.py`

## File Map

| File | Purpose | When to Read |
|------|---------|--------------|
| `MASTER.md` | Identity + immutable rules | Always first |
| `STRATEGY.md` | Signal logic (editable) | Before scanning |
| `STATE.md` | Live account state | Every session |
| `ANALYSIS.md` | Multi-timeframe framework | During analysis |
| `RISK.md` | Risk management rules | Before every trade |
| `SCANNER.md` | Market scanning protocol | During scanning |
| `JOURNAL.md` | Trade journaling rules | During review |
| `EVOLUTION.md` | Strategy modification rules | During weekly review |
| `CORRELATION.md` | Dynamic correlation detection | During daily review |
| `engine.py` | Validation + kill switch | Before every trade |
| `executor.py` | ccxt Binance execution | On trade execution |
| `monitor.py` | Performance tracking | After every trade |

## Trading Workflow

### Start Session
```
1. Read STATE.md (current state)
2. Read MASTER.md (rules)
3. Read STRATEGY.md (current strategy)
4. Run: python3 monitor.py (initialize)
5. Scan market (see SCANNER.md)
6. Analyze candidates (see ANALYSIS.md)
7. Validate through engine.py
8. Execute via executor.py
9. Update STATE.md
```

### Pre-Trade Checklist
Before EVERY trade, verify all 7 items (from MASTER.md):
1. Genuine setup per STRATEGY.md?
2. Entry, stop, target defined?
3. Risk ≤ 4.5% of account?
4. Stop ≥ 1.0% from entry?
5. Total margin < 75%?
6. Within daily loss limits?
7. Trading from analysis, not emotion?

### Execute Trade
```python
import sys
sys.path.insert(0, '/home/userland/.config/opencode/skills/futures-trading')
from engine import TradeValidator, TradingState, CorrelationManager
from executor import BinanceExecutor
from monitor import TradeTracker

# Initialize
state = TradingState()
corr_manager = CorrelationManager()
validator = TradeValidator(state, corr_manager)
executor = BinanceExecutor()
tracker = TradeTracker()

# Validate
decision = {
    "pair": "ETHUSDT",
    "side": "long",
    "entry": 1806.51,
    "stop": 1757.36,
    "tp": 1860.69,
    "leverage": 10,
    "risk_pct": 0.03,
    "regime_multiplier": 1.5,
    "setup_grade": "A+"
}

is_valid, reason = validator.validate(decision)
if is_valid:
    order = executor.execute_entry(decision)
    tracker.record_entry(decision)
```

## Hard Limits (Never Override)

| Parameter | Limit |
|-----------|-------|
| Max leverage | 10x |
| Base risk | 3% per trade |
| Max risk (after regime) | 4.5% |
| Max drawdown | 30% (kill switch) |
| Max concurrent positions | 3 |
| Max margin utilization | 75% |
| Min stop distance | 1.0% |
| Min account balance | $20 |
| Cooldown | 5 minutes |
| Max daily trades | 10 |

## Emergency Actions

| Event | Action |
|-------|--------|
| 3 consecutive losses | Pause 1 hour |
| Drawdown 30% | Close all, stop trading |
| Daily loss > 12% | Close all, halt 24h |
| Flash crash | Close all immediately |
| Account < $20 | Stop all trading |

## Paper Trading

System starts in paper mode. To go live:
1. Deposit USDT to Binance futures account (min $20)
2. Say "go live"
3. System switches to real execution

## Strategy Evolution

Only modify `STRATEGY.md`. Never modify `MASTER.md` or Python code.

Rules:
- One change at a time
- Cooldown: 50 trades or 7 days
- Rollback if 30-trade win rate < 45%
- Never loosen risk rules
- Log all changes in `strategy_versions.json`
