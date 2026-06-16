# JOURNAL — Trade Journaling Rules

> How you record and learn from trades. Read this during daily review.

## Journal Philosophy

**If it's not written down, it didn't happen.**

Every trade gets recorded. Every review gets documented. Every pattern gets tracked. The journal is how you improve.

## What You Record

### Per Trade (Entry)
| Field | Source | Example |
|-------|--------|---------|
| ID | Auto-generated | #1 |
| Pair | Exchange | ETHUSDT |
| Side | Decision | LONG |
| Entry price | Order fill | $1806.51 |
| Stop loss | Pre-defined | $1757.36 |
| Take profit | Pre-defined | $1860.69 |
| Leverage | Decision | 10x |
| Notional | Calculated | $82.72 |
| Margin | Calculated | $8.27 |
| Risk amount | Calculated | $2.25 |
| Risk % | Calculated | 4.5% |
| Setup grade | Analysis | A+ |
| Regime | Detection | Trending Up |
| Entry time | Timestamp | 2026-06-16 13:34 |

### Per Trade (Exit)
| Field | Source | Example |
|-------|--------|---------|
| Exit price | Order fill | $1860.69 |
| Exit time | Timestamp | 2026-06-16 18:45 |
| P&L | Calculated | +$2.25 |
| P&L % | Calculated | +27.2% |
| Fees | Exchange | $0.16 |
| Exit reason | Decision | TP hit |
| Duration | Calculated | 5h 11m |

### Per Trade (Notes)
- Why you entered
- What you expected
- What actually happened
- What you learned
- Emotional state (honest)

## Journal Files

### LEDGER.md
**Location:** `~/trading-journal/LEDGER.md`
**Auto-updated by:** monitor.py
**Contents:**
- Summary table (all-time metrics)
- Trade log (last 50 trades)
- Performance by setup grade

### PERFORMANCE.md
**Location:** `~/trading-journal/PERFORMANCE.md`
**Auto-updated by:** monitor.py
**Contents:**
- Daily metrics
- Weekly metrics
- All-time metrics

### trades.json
**Location:** `~/trading-journal/trades.json`
**Auto-updated by:** monitor.py
**Contents:**
- Machine-readable trade data
- Used for calculations

## Review Schedule

### End of Day (After Last Trade or Market Close)
1. Review all trades taken today
2. Check P&L vs expectations
3. Note any rule violations
4. Update strategy if needed (see EVOLUTION.md)
5. Set watchlist for tomorrow

### Weekly (Sunday)
1. Review all trades from the week
2. Calculate weekly metrics
3. Identify patterns (winning/losing)
4. Adjust strategy parameters if needed
5. Update correlation groups

### Monthly
1. Full performance review
2. Compare to previous months
3. Assess strategy evolution
4. Set goals for next month
5. Archive old data

## Pattern Recognition

### Track These Patterns
| Pattern | What to Note |
|---------|--------------|
| Winning setups | Grade, regime, timeframe, pair |
| Losing setups | Grade, regime, timeframe, pair |
| Time of day | When trades work best |
| Day of week | Which days are best |
| Pair behavior | Which pairs suit your style |
| Regime performance | Which regimes you trade best |

### Pattern Output Format
```
=== Pattern Analysis [DATE] ===

Winning Patterns:
- A+ setups in trending regime: 80% win rate
- Long entries on 1H pullback: 75% win rate
- ETH/SOL trades: Best performers

Losing Patterns:
- B setups in ranging regime: 40% win rate
- Short entries: 45% win rate (avoid?)
- Late-day entries: Lower success rate

Adjustments:
- Focus on A/A+ setups only
- Avoid shorts in current market
- Stop trading after 6 PM
```

## Rule Violation Tracking

### If You Break a Rule
1. Record it immediately
2. Note the rule broken
3. Note why you broke it
4. Note the outcome
5. Add to violation count

### Violation Categories
| Category | Severity | Response |
|----------|----------|----------|
| Position size too large | High | Review risk rules |
| Moved stop away | Critical | Pause trading 24h |
| FOMO entry | High | Review emotional rules |
| Averaging into loser | Critical | Pause trading 24h |
| Overleveraging | Critical | Reduce max leverage |
| Ignored cooldown | Medium | Review discipline |

## Emotional Tracking

### Record Your State
- **Confident:** Normal trading
- **Anxious:** Reduce size, widen stops
- **Excited:** Pause, check for FOMO
- **Frustrated:** Stop trading, review
- **Revenge:** STOP. Walk away.

### Emotional Patterns
Track if certain emotions correlate with:
- Winning or losing trades
- Rule violations
- Specific pairs or setups
- Time of day

## Performance Metrics

### Key Metrics to Track
| Metric | Target | Why |
|--------|--------|-----|
| Win rate | > 50% | Must be profitable with R:R |
| Profit factor | > 1.5 | Gross profit / gross loss |
| Max drawdown | < 20% | Sustainability |
| Average R:R | > 1.5 | Risk/reward efficiency |
| Expectancy | > 0 | Positive expected value |
| Sharpe ratio | > 1.0 | Risk-adjusted returns |

### Calculations
```
Win rate = winning_trades / total_trades
Profit factor = gross_profit / gross_loss
Max drawdown = max(peak - current) / peak
Average R:R = average_win / average_loss
Expectancy = (win_rate × avg_win) - ((1-win_rate) × avg_loss)
```

## Learning Integration

### From Winning Trades
- What made this setup A+?
- Can I replicate this?
- Should I increase size on similar setups?

### From Losing Trades
- Was this a valid setup that failed (normal)?
- Did I break any rules?
- Was the market regime different than expected?
- Should I avoid this type of trade?

### From Rule Violations
- What triggered the violation?
- How can I prevent it next time?
- Do I need additional hard limits?

## Journal Output Format

### Daily Summary
```
=== Daily Review [DATE] ===

Trades: [X] total, [Y] wins, [Z] losses
Win rate: [%]
Net P&L: $[amount] ([%])
Fees: $[amount]

Best trade: [PAIR] +$[amount] ([%])
Worst trade: [PAIR] -$[amount] ([%])

Rule violations: [X]
Emotional state: [state]

Notes:
[Detailed notes]

Adjustments for tomorrow:
[Any strategy changes]
```

### Weekly Summary
```
=== Weekly Review [WEEK] ===

Trades: [X] total, [Y] wins, [Z] losses
Win rate: [%]
Net P&L: $[amount] ([%])
Profit factor: [value]
Max drawdown: [%]

Patterns identified:
[Pattern analysis]

Strategy adjustments:
[Changes made]
```
