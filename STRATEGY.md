# STRATEGY — Signal Logic and Trade Execution

> This file is editable by the AI. MASTER.md rules are immutable.
> When modifying this file, log changes in strategy_versions.json.

## Market Scanning Protocol

### Phase 1: Pre-Filter (Every 15 Minutes)

1. Fetch all USDT-M perpetual pairs from Binance
2. Filter out:
   - Pairs with 24h volume < $5M USDT
   - Pairs with spread > 0.1%
   - Delisted or maintenance-mode pairs
   - Pairs where minimum notional > account_balance * min_leverage
3. Rank remaining pairs by:
   - 24h price change (absolute value) — momentum
   - Volume spike vs 20-period average — activity
   - ATR as % of price — volatility (prefer 0.5%-3%)
4. Output: Top 20 candidates for deep analysis

### Phase 2: Deep Analysis (Top 20 Candidates)

For each candidate, analyze multi-timeframe structure:

| Timeframe | What to Look For |
|-----------|-----------------|
| 1D | Primary trend direction, key support/resistance levels |
| 4H | Trend continuation or reversal, structure breaks |
| 1H | Entry zone identification, volume confirmation |
| 15m | Precise entry timing, candle patterns |
| 5m | Entry refinement, stop placement |

### Phase 3: Regime Detection

For each pair, classify the current regime:

| Regime | Definition | Action |
|--------|-----------|--------|
| Trending Up | Price above 20 EMA on 4H, higher highs, higher lows | Prefer longs, 1.5x regime multiplier |
| Trending Down | Price below 20 EMA on 4H, lower highs, lower lows | Prefer shorts, 1.5x regime multiplier |
| Ranging | Price between support and resistance, no clear trend | Trade range boundaries, 1.0x multiplier |
| Volatile | ATR > 2x 20-period ATR average | Reduce size, widen stops, 0.75x multiplier |
| Crash | >5% drop in 1 hour | Close all positions, do not enter |

## Setup Grading

### A+ Setup (10x Leverage Allowed)

ALL of these must be true:
1. 4H and 1H trend aligned in same direction
2. Volume on breakout candle > 2x 20-period average
3. Clear structure break (higher high for long, lower low for short)
4. RSI between 30-70 (not overbought/oversold)
5. ATR > 0.1% of price (adequate volatility)
6. Stop can be placed ≥ 1.0% from entry
7. Risk/reward ≥ 1.5:1

### A Setup (5x Leverage)

At least 5 of 7 A+ criteria met, plus:
- Strong trend alignment
- Volume confirmation (> 1.5x average)
- Clear entry pattern

### B+ Setup (3x Leverage, Reduced Size)

At least 4 of 7 A+ criteria met:
- Moderate trend alignment
- Some volume confirmation
- Acceptable risk/reward (≥ 1.2:1)

### B Setup (3x Leverage, Half Size)

At least 3 of 7 criteria met:
- Weak trend or ranging with clear boundaries
- Average volume
- Marginal risk/reward (≥ 1:1)

### C Setup (Do Not Trade)

Fewer than 3 criteria met. Skip entirely.

## Entry Rules

### Limit Order Conditions (Use When):
- Spread < 0.05% of price
- Not in a fast-moving market (price stable for > 1 minute)
- Entry is at a specific level (not chasing)

### Market Order Conditions (Use When):
- Spread > 0.05% of price
- Price is moving fast (momentum entry)
- Urgent exit required (stop loss hit, regime change)
- Limit order would miss the entry

### Entry Checklist (Beyond MASTER.md 7-Point)

Before placing the order:
1. Current price is within 0.2% of intended entry
2. Order book shows adequate liquidity at entry level
3. No major news event in next 30 minutes (if identifiable)
4. Funding rate is not extreme (< 0.05% per 8h for direction)
5. Position size calculated correctly per formula in MASTER.md

## Exit Rules

### Stop Loss Placement

- **Minimum:** 1.0% from entry (MASTER.md rule)
- **Standard:** 1.5x ATR(14) on 1H timeframe
- **Wide (A+ setups):** 2.0x ATR(14) on 1H timeframe
- **Never:** Move stop further away from entry

### Take Profit Rules

| Setup Grade | TP Target | R:R Minimum |
|-------------|-----------|-------------|
| A+ | 2.5x stop distance | 2.5:1 |
| A | 2.0x stop distance | 2.0:1 |
| B+ | 1.5x stop distance | 1.5:1 |
| B | 1.2x stop distance | 1.2:1 |

### Trailing Stop Rules

After position is in profit:
1. **At 1x risk (1:1 R:R):** Move stop to breakeven
2. **At 2x risk:** Trail stop to 1x risk level
3. **At 3x risk:** Trail stop to 2x risk level
4. **Continue trailing** at 50% of unrealized profit

### Emergency Exits (Immediate, No Questions)

- Flash crash (>5% in 1 minute)
- Regime changes from trending to crash
- Funding rate spikes > 0.1% per 8h against position
- API error on position monitoring
- Drawdown hits 30% (MASTER.md kill switch)

## Regime Multipliers

| Regime | Multiplier | Effect on Position Size |
|--------|-----------|------------------------|
| Trending (with trend) | 1.5x | Larger position, higher conviction |
| Ranging | 1.0x | Standard position |
| Volatile | 0.75x | Smaller position, wider stop |
| Crash | 0x | No new positions |

**Note:** Multiplied risk cannot exceed 4.5% of account (MASTER.md rule).

## Pair Selection Preferences

### Preferred Pairs (High Liquidity)
- BTCUSDT — Most liquid, tightest spreads
- ETHUSDT — Second most liquid
- SOLUSDT — High volatility, good for momentum
- BNBUSDT — Stable, good for range trades
- XRPUSDT — High volume, meme-driven moves

### Acceptable Pairs (Adequate Liquidity)
- DOGEUSDT, AVAXUSDT, DOTUSDT, LINKUSDT, ADAUSDT
- Any pair meeting volume > $5M and spread < 0.1%

### Avoid
- Newly listed pairs (< 30 days history)
- Pairs with irregular price action (manipulation risk)
- Low-cap alts with thin order books

## Strategy Evolution Rules

When reviewing trades in daily review:

1. **Identify patterns:** What setups win? What setups lose?
2. **One change at a time:** Only modify one parameter per review cycle
3. **Cooldown:** After any change, no further changes for 50 trades or 7 days
4. **Rollback trigger:** If 30-trade win rate drops below 45%, revert last change
5. **Never loosen risk rules:** Only tighten. Never increase max leverage, max risk, or reduce stop distances.
6. **Log everything:** Every change goes in strategy_versions.json with timestamp, old value, new value, reason

## Example Strategy Adjustments

### If losing on low-volume breakouts:
"Add volume > 2x average as A+ requirement. Reduce size on low-volume entries."

### If stops are getting hit before move:
"Widen standard stop from 1.5x ATR to 2.0x ATR. Reduce leverage to compensate."

### If winning on trend trades but losing on range trades:
"Increase regime multiplier for trending to 1.75x. Reduce range trade frequency."

### If overtrading:
"Increase B+ setup requirements. Focus only on A and A+ setups for 50 trades."
