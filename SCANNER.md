# SCANNER — Market Scanning Protocol

> How you find opportunities. Read this before scanning.

## Scanning Schedule

| Scan Type | Frequency | Duration |
|-----------|-----------|----------|
| Quick scan | Every 15 minutes | 2-3 minutes |
| Deep analysis | Every 4 hours | 10-15 minutes |
| Full market review | Once daily | 30-45 minutes |

## Quick Scan (Every 15 Minutes)

### Phase 1: Fetch Data
1. Get all USDT-M perpetual tickers from Binance
2. Get order books for top 20 by volume
3. Calculate spreads

### Phase 2: Filter
Remove pairs that fail ANY of these:
- 24h volume < $5M USDT
- Spread > 0.1% of price
- Delisted or maintenance mode
- Minimum notional > account balance × min leverage
- Listed < 30 days ago

### Phase 3: Rank
Rank remaining pairs by:
1. **Volume change** (vs 20-period average) — 40% weight
2. **Price change** (absolute 24h%) — 30% weight
3. **ATR as % of price** (prefer 0.5-3%) — 30% weight

### Phase 4: Output
Top 20 candidates for deep analysis.

## Deep Analysis (Every 4 Hours)

For each of the top 20 candidates:

### Multi-Timeframe Check
| Timeframe | Data Needed |
|-----------|-------------|
| 1D | Last 30 candles, 20/50/200 EMA |
| 4H | Last 30 candles, 20 EMA, ATR |
| 1H | Last 30 candles, RSI, volume |
| 15m | Last 20 candles, entry patterns |

### Calculate
- Regime (trending up/down, ranging, volatile, crash)
- Structure (swing points, BOS, CHoCH)
- Volume profile (confirming or not)
- RSI (overbought/oversold/divergence)
- Setup grade (A+, A, B+, B, C)

### Output
Ranked list of setups with grades and entry parameters.

## Full Market Review (Daily)

### What You Review
1. All open positions (P&L, stop adjustments)
2. All pairs that triggered signals in last 24h
3. Correlation matrix (update groups)
4. Regime changes across market
5. Funding rates for held positions

### What You Update
- Correlation groups (see CORRELATION.md)
- Support/resistance levels
- Watchlist for next day
- Strategy adjustments (see EVOLUTION.md)

## Symbol Processing

### Standard Format
```
ETH/USDT:USDT  (ccxt format)
ETHUSDT         (Binance format)
```

### Always Convert
- Input from user: ETHUSDT
- Internal processing: ETH/USDT:USDT
- Output to user: ETHUSDT

## Data Requirements

### Minimum Data Points
| Indicator | Candles Needed |
|-----------|----------------|
| 20 EMA | 20 |
| 50 EMA | 50 |
| 200 EMA | 200 |
| ATR(14) | 15 |
| RSI(14) | 15 |
| Volume MA(20) | 20 |

### Timeframe Data
| Timeframe | Candles to Fetch | Why |
|-----------|------------------|-----|
| 1D | 200 | 200 EMA calculation |
| 4H | 50 | 50 EMA + structure |
| 1H | 30 | Entry analysis |
| 15m | 20 | Entry timing |

## Candidate Scoring

Each candidate gets a score from 0-100:

### Scoring Components
| Component | Weight | Calculation |
|-----------|--------|-------------|
| Volume spike | 30% | (current_vol / avg_vol) × 10 |
| Price momentum | 25% | abs(24h_change) × 5 |
| ATR quality | 20% | ATR% within 0.5-3% = full score |
| Spread quality | 15% | Tighter = better |
| Regime clarity | 10% | Clear trend = full score |

### Score Interpretation
| Score | Action |
|-------|--------|
| 80-100 | Priority deep analysis |
| 60-79 | Standard deep analysis |
| 40-59 | Quick check only |
| < 40 | Skip |

## Watchlist Management

### Adding to Watchlist
- Score > 60
- Clear regime
- Adequate volume
- Acceptable spread

### Removing from Watchlist
- Score < 40 for 3 consecutive scans
- Volume drops below $5M
- Spread widens > 0.2%
- Enters crash regime

### Watchlist Size
- Maximum 30 pairs
- If full, remove lowest scoring pair
- Prioritize liquidity and volatility

## Output Format

```
=== Quick Scan [TIMESTAMP] ===
Scanned: [X] tickers | Passed: [Y] | Top candidates:

| Rank | Symbol | Price | 24h% | Vol($M) | Spread | Score |
|------|--------|-------|------|---------|--------|-------|
| 1 | ETHUSDT | $1805 | +2.3% | 10969 | 0.001% | 87 |
| 2 | SOLUSDT | $74.2 | +1.8% | 1888 | 0.014% | 82 |
...

=== Deep Analysis [SYMBOL] ===
[Full ANALYSIS.md format]
```

## Error Handling

| Error | Action |
|-------|--------|
| API rate limit | Wait 60s, retry |
| Data unavailable | Skip pair, note in log |
| Partial data | Use available, note gaps |
| Connection lost | Pause scan, retry in 5 min |

## Performance Tracking

Track scanning efficiency:
- % of scans that produce actionable setups
- Average time per scan
- False positive rate (signals that failed)
- Update scanning parameters based on results
