# RISK — Risk Management Rules

> How you protect capital. Read this before every trade decision.

## Core Risk Principle

**Capital preservation first, growth second.**

You risk a small, fixed percentage per trade. You never risk more than the rules allow. You compound as the account grows.

## Position Sizing Formula

```
base_risk = account_balance × 0.03
adjusted_risk = base_risk × regime_multiplier
stop_distance_pct = abs(entry - stop) / entry
notional = adjusted_risk / stop_distance_pct
margin = notional / leverage
```

### Apply Caps (In Order)
1. If margin > account × 0.35 → cap at 35%
2. If total margin + new margin > account × 0.75 → skip trade
3. If adjusted_risk > account × 0.045 → cap at 4.5%

### Example ($50 account, A+ setup, trending regime)
```
base_risk = $50 × 0.03 = $1.50
adjusted_risk = $1.50 × 1.5 = $2.25 (4.5% — max allowed)
stop_distance = 2.72%
notional = $2.25 / 0.0272 = $82.72
margin = $82.72 / 10 = $8.27 (16.5% of account — OK)
```

## Leverage Selection

| Setup Quality | Leverage | When |
|--------------|----------|------|
| B / B+ | 3x | Most trades. Adequate setup. |
| A | 5x | Strong trend + volume + clear structure |
| A+ | 10x | ALL criteria align. Wide stop available. |

**Never exceed 10x.** Even A+ setups.

## Risk Per Trade Tiers

| Account Size | 3% Risk | Max (4.5%) | Notes |
|--------------|---------|------------|-------|
| $20 | $0.60 | $0.90 | Minimum viable |
| $50 | $1.50 | $2.25 | Starting capital |
| $100 | $3.00 | $4.50 | Compound target |
| $200 | $6.00 | $9.00 | Growth phase |
| $500 | $15.00 | $22.50 | Scaling up |

## Drawdown Management

### Current Drawdown
```
drawdown = (peak_balance - current_balance) / peak_balance
```

### Drawdown Response
| Drawdown | Action |
|----------|--------|
| 0-10% | Normal trading |
| 10-20% | Reduce position sizes by 25% |
| 20-30% | Reduce position sizes by 50% |
| 30%+ | **KILL SWITCH** — Close all, stop trading |

### Peak Balance Tracking
- Updated automatically when balance increases
- Never manually reset
- Used for drawdown calculation only

## Daily Loss Management

Tracks rolling 24h from first trade of the day.

| Daily Loss | Action | Reason |
|------------|--------|--------|
| < 6% | Normal | Within acceptable range |
| 6-10% | Half size | Reducing exposure |
| > 10% | Halt entries | Too much loss |
| > 12% | Close all + halt 24h | Catastrophic day |

### Daily Reset
- Resets 24h after first trade of the day
- Not at midnight
- Balances tracked automatically

## Correlation Risk

### Rule
Never open positions in the same correlation group simultaneously.

### Why
- BTC + ETH = 1 risk, not 2
- When BTC drops 5%, ETH drops 5-8%
- Correlated positions amplify drawdowns

### Dynamic Groups
Groups are calculated automatically based on rolling 48h correlation.
- Correlation > 0.7 = same group
- Updated every 4 hours
- See CORRELATION.md for calculation details

## Cooldown Rules

| Event | Cooldown | Reason |
|-------|----------|--------|
| Any trade | 5 minutes | Prevents rapid-fire entries |
| 3 consecutive losses | 1 hour | Mental reset required |
| Daily loss > 10% | Until next day | Preserve capital |
| Kill switch triggered | Manual review | System failure |

## Stop Loss Rules

### Minimum Distance
- **1.0% from entry** — Hard minimum, no exceptions
- Wider stops preferred (1.5-2.0x ATR)

### Placement Logic
1. Below swing low (for longs)
2. Above swing high (for shorts)
3. Never at exact round numbers ( hunted)
4. Always have a stop before entry

### Moving Stops
- **Toward entry:** Allowed (breakeven, lock profit)
- **Away from entry:** NEVER (this is how accounts die)

## Take Profit Rules

| Grade | Target R:R | Exit Method |
|-------|------------|-------------|
| A+ | 2.5:1 | Trailing stop |
| A | 2.0:1 | Trailing stop |
| B+ | 1.5:1 | Fixed TP or trail |
| B | 1.2:1 | Fixed TP |

### Trailing Stop Logic
1. At 1x risk (1:1): Move stop to breakeven
2. At 2x risk: Trail to 1x risk level
3. At 3x risk: Trail to 2x risk level
4. Continue trailing at 50% of unrealized profit

## Compounding Rules

Position sizes grow automatically with account balance:
- Risk is always % of CURRENT balance
- No manual adjustment needed
- Formula handles scaling

| Balance | 3% Risk | Position Size (10x, 2% stop) |
|---------|---------|------------------------------|
| $50 | $1.50 | $75 notional |
| $100 | $3.00 | $150 notional |
| $200 | $6.00 | $300 notional |
| $500 | $15.00 | $750 notional |

## Emergency Exits

Close immediately (no questions):
- Flash crash (>5% in 1 minute)
- Kill switch triggered (30% drawdown)
- API error on position monitoring
- Funding rate > 0.1% per 8h against position
- Exchange maintenance imminent

## Risk Checklist

Before EVERY trade, verify:

- [ ] Base risk ≤ 3% of account
- [ ] Adjusted risk ≤ 4.5% (after regime multiplier)
- [ ] Stop ≥ 1.0% from entry
- [ ] Total margin < 75% of account
- [ ] Single position margin < 35% of account
- [ ] Not correlated with existing position
- [ ] Within daily loss limits
- [ ] Not in cooldown period
- [ ] Account balance ≥ $20

**If ANY item fails → DO NOT TRADE**
