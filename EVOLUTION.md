# EVOLUTION — Strategy Modification Rules

> How you improve over time. Read this during weekly review.

## Evolution Philosophy

**One change at a time. Measure everything. Revert if it fails.**

You evolve based on evidence, not hunches. Every change gets logged, tested, and evaluated.

## When to Evolve

### Trigger Events
| Event | Action | Cooldown |
|-------|--------|----------|
| Weekly review | Optional adjustment | 50 trades or 7 days |
| 30-trade win rate < 45% | Revert last change | Immediate |
| 3 consecutive losses on same setup | Review setup rules | 1 hour pause |
| New pattern identified | Consider adaptation | 50 trades |

### Cooldown Rules
- **After any change:** No further changes for 50 trades or 7 days
- **After revert:** No changes for 30 trades
- **During cooldown:** Trade normally, collect data

## What You Can Modify

### STRATEGY.md Only
- Entry criteria
- Exit rules
- Leverage selection
- Pair preferences
- Scanning parameters

### Never Modify
- MASTER.md (identity and rules)
- engine.py (Python enforcement)
- Hard limits (leverage caps, max risk, drawdown)

## Change Categories

### Tier 1: Parameter Adjustments (Low Risk)
| Change | Example | Impact |
|--------|---------|--------|
| Stop distance | 1.5x ATR → 2.0x ATR | Moderate |
| Volume threshold | 1.5x → 2.0x average | Moderate |
| RSI filter | 30-70 → 35-65 | Low |
| Pair preferences | Add/remove from list | Low |

### Tier 2: Rule Changes (Medium Risk)
| Change | Example | Impact |
|--------|---------|--------|
| Entry pattern | Add new pattern requirement | High |
| Exit logic | Change trailing stop rules | High |
| Regime multipliers | Adjust sizing | Moderate |
| Cooldown periods | Extend/shorten | Moderate |

### Tier 3: Structural Changes (High Risk)
| Change | Example | Impact |
|--------|---------|--------|
| Setup grading | Change criteria | Very High |
| Leverage tiers | Modify allowed leverage | Very High |
| Risk formula | Alter position sizing | Critical |
| Correlation rules | Change grouping logic | High |

## Change Process

### Step 1: Identify Need
```
Observation: [What you noticed]
Data: [Supporting evidence]
Hypothesis: [What you think will help]
```

### Step 2: Define Change
```
Current: [Current rule/parameter]
Proposed: [New rule/parameter]
Expected impact: [What you expect]
Risk: [What could go wrong]
```

### Step 3: Log Change
```json
{
  "version": 2,
  "date": "2026-06-23",
  "change": "Increased volume filter from 1.5x to 2.0x",
  "details": "Losing on low-volume breakouts",
  "metrics_at_change": {
    "trades": 30,
    "win_rate": 48,
    "profit_factor": 1.3
  },
  "triggered_by": "pattern_analysis"
}
```

### Step 4: Implement
- Update STRATEGY.md
- Update strategy_versions.json
- Note in LEDGER.md

### Step 5: Evaluate
After 50 trades or 7 days:
```
Before: [metric] = [value]
After: [metric] = [value]
Change: [improvement/decline]
Verdict: [keep/revert]
```

## Rollback Triggers

### Automatic Revert
If ANY of these happen after a change, revert immediately:
- 30-trade win rate drops below 45%
- Profit factor drops below 1.0
- Max drawdown increases by > 10%

### Manual Review
Consider reverting if:
- Win rate drops by > 5% from baseline
- Average R:R drops by > 0.3
- Emotional stress increases significantly

### Revert Process
1. Restore previous STRATEGY.md version from strategy_versions.json
2. Log revert with reason
3. Wait 30 trades before next change
4. Analyze why change failed

## Baseline Metrics

### Track These
| Metric | Baseline | Current | Target |
|--------|----------|---------|--------|
| Win rate | [value] | [value] | > 50% |
| Profit factor | [value] | [value] | > 1.5 |
| Average R:R | [value] | [value] | > 1.5 |
| Max drawdown | [value] | [value] | < 20% |
| Expectancy | [value] | [value] | > 0 |

### How to Establish Baseline
- Trade 50 trades with current strategy
- Calculate all metrics
- This is your baseline
- All future changes measured against this

## Strategy Versions

### Version Format
```json
{
  "current_version": 3,
  "versions": [
    {
      "version": 1,
      "date": "2026-06-16",
      "change": "Initial strategy",
      "metrics_at_change": null,
      "triggered_by": "system_init"
    },
    {
      "version": 2,
      "date": "2026-06-20",
      "change": "Tightened volume filter",
      "details": "Added 2x volume requirement for A+ setups",
      "metrics_at_change": {
        "trades": 30,
        "win_rate": 48,
        "profit_factor": 1.3
      },
      "triggered_by": "losing_pattern"
    }
  ]
}
```

### Rollback History
Track all reverts:
```
Reverted from v3 to v2 on 2026-06-25
Reason: Win rate dropped to 42% after 30 trades
Outcome: Win rate recovered to 52% after 30 trades
```

## Learning Patterns

### Pattern Categories
| Category | What to Track |
|----------|---------------|
| Setup performance | Which grades/regimes win |
| Time patterns | Best/worst times to trade |
| Pair behavior | Which pairs suit your style |
| Emotional patterns | When emotions affect decisions |
| Market conditions | Which conditions you trade best |

### Pattern Output
```
=== Pattern Report [DATE] ===

Best setups: A+ in trending regime (75% win rate)
Best pairs: ETH, SOL (most consistent)
Best times: 8-12 UTC, 18-22 UTC
Worst conditions: Ranging market (avoid)

Avoid: B setups in ranging regime (35% win rate)
Adjustment: Focus only on A/A+ for next 50 trades
```

## Anti-Regression Rules

### Never Loosen Risk Rules
- Only tighten max leverage
- Only increase stop distances
- Only reduce position sizes
- Never increase max risk per trade

### Never Remove Safety Features
- Keep kill switch active
- Keep cooldown rules
- Keep daily loss limits
- Keep correlation checks

### Always Measure Impact
- Compare before/after metrics
- Require 50 trades minimum sample
- Document everything
- Be honest about results

## Evolution Review Checklist

During weekly review, ask:

- [ ] Did I follow my strategy this week?
- [ ] What worked? What didn't?
- [ ] Any rule violations?
- [ ] Any patterns identified?
- [ ] Need any strategy adjustments?
- [ ] Are baseline metrics still valid?
- [ ] Any rollback triggers hit?

## Output Format

### Weekly Evolution Review
```
=== Evolution Review [WEEK] ===

Current version: [X]
Trades since last review: [Y]

Performance:
- Win rate: [%] (baseline: [%])
- Profit factor: [value] (baseline: [value])
- Max drawdown: [%]

Pattern analysis:
[Findings]

Proposed changes:
[Changes or "None"]

Rollback check:
- Win rate > 45%: [PASS/FAIL]
- Profit factor > 1.0: [PASS/FAIL]
- Drawdown < 30%: [PASS/FAIL]

Verdict: [No change needed / Change proposed / Revert needed]
```
