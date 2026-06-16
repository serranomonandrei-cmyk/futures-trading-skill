# ANALYSIS — Multi-Timeframe Analysis Framework

> How you analyze markets across timeframes. Read this before scanning.

## Analysis Hierarchy

You analyze from **top-down**: macro structure first, then refine to micro entry.

| Timeframe | Role | Weight | What You Look For |
|-----------|------|--------|-------------------|
| 1D | Strategic | 40% | Primary trend, key S/R, market regime |
| 4H | Tactical | 30% | Trend continuation/reversal, structure breaks |
| 1H | Entry zone | 20% | Volume confirmation, entry patterns |
| 15m | Timing | 10% | Precise entry, candle patterns |

**Rule:** Never enter a trade where 1D and 4H disagree. Alignment is non-negotiable.

## Regime Detection

You classify every pair into one of 5 regimes. This determines your bias and position sizing.

### Trending Up
- Price above 20 EMA on 4H
- Higher highs, higher lows on 4H
- Volume increasing on up candles
- **Action:** Prefer longs. 1.5x regime multiplier.

### Trending Down
- Price below 20 EMA on 4H
- Lower highs, lower lows on 4H
- Volume increasing on down candles
- **Action:** Prefer shorts. 1.5x regime multiplier.

### Ranging
- Price between clear support and resistance
- No directional bias on 4H
- Volume balanced between buyers/sellers
- **Action:** Trade range boundaries only. 1.0x multiplier.

### Volatile
- ATR > 2x the 20-period ATR average
- Large candles in both directions
- No clear structure
- **Action:** Reduce size, widen stops. 0.75x multiplier.

### Crash
- >5% drop in 1 hour
- Volume spikes on sell side
- All EMAs turning down
- **Action:** Close all positions. No new entries.

## Structure Analysis

### Swing Points
- **Swing High:** Candle where high > high of candle before and after
- **Swing Low:** Candle where low < low of candle before and after
- Use 4H swing points for structure, 1H for entry zones

### Trend Structure
- **Uptrend:** Series of higher swing highs + higher swing lows
- **Downtrend:** Series of lower swing highs + lower swing lows
- **Break of Structure (BOS):** When price breaks a swing point in trend direction
- **Change of Character (CHoCH):** When price breaks a swing point against trend (reversal signal)

### Support/Resistance Zones
- Not exact lines, but zones (0.5% wide)
- Validated by: multiple touches, volume profile, round numbers
- Prefer S/R on 4H and 1D timeframes

## Volume Analysis

### Volume Confirmation
- Breakouts need volume > 1.5x 20-period average
- Low-volume breakouts are traps (70% fail)
- Volume should increase in trend direction

### Volume Profile
- High volume nodes = strong S/R
- Low volume nodes = price moves through quickly
- Use 30-day volume profile for major levels

## Indicator Toolkit

### Primary (Always Use)
| Indicator | Settings | Purpose |
|-----------|----------|---------|
| EMA | 20, 50, 200 | Trend direction |
| ATR | 14 | Volatility, stop placement |
| RSI | 14 | Overbought/oversold, divergence |
| Volume | 20-period MA | Confirmation |

### Secondary (Confirmatory)
| Indicator | Settings | Purpose |
|-----------|----------|---------|
| MACD | 12, 26, 9 | Momentum, divergence |
| Bollinger | 20, 2 | Volatility squeeze |
| VWAP | Default | Intraday fair value |

### Never Use
- Lagging indicators with no edge (Stochastic, CCI, Williams %R)
- Indicators you don't fully understand
- More than 3 indicators on one chart (clutter)

## Entry Pattern Recognition

### Long Setups
| Pattern | Description | Reliability |
|---------|-------------|-------------|
| Break + Retest | Break resistance, retest as support | High |
| Double Bottom | Two touches of support, second with divergence | High |
| Bullish Engulfing | Large green candle engulfs previous red | Medium |
| Volume Spike | Volume > 2x average with price increase | Medium |

### Short Setups
| Pattern | Description | Reliability |
|---------|-------------|-------------|
| Break + Retest | Break support, retest as resistance | High |
| Double Top | Two touches of resistance, second with divergence | High |
| Bearish Engulfing | Large red candle engulfs previous green | Medium |
| Volume Spike | Volume > 2x average with price decrease | Medium |

## Divergence Detection

### Regular Divergence (Reversal)
- **Bullish:** Price makes lower low, RSI makes higher low
- **Bearish:** Price makes higher high, RSI makes lower high
- Wait for confirmation candle before entering

### Hidden Divergence (Continuation)
- **Bullish:** Price makes higher low, RSI makes lower low
- **Bearish:** Price makes lower high, RSI makes higher high
- Trade in trend direction only

## Analysis Output Format

When analyzing a pair, produce this output:

```
=== [PAIR] Analysis ===
Regime: [TRENDING UP/DOWN | RANGING | VOLATILE | CRASH]
1D: [Trend direction] | Key S/R: [levels]
4H: [Trend direction] | Structure: [BOS/CHoCH/None]
1H: [Entry zone] | Volume: [confirming/not confirming]
15m: [Pattern] | RSI: [value]

Grade: [A+/A/B+/B/C]
Bias: [LONG/SHORT/NONE]
Entry: [price]
Stop: [price] ([%] from entry)
Target: [price] ([R:R ratio])
Leverage: [x]
```
