# CORRELATION — Dynamic Correlation Detection

> How you detect and manage correlated positions. Read this during daily review.

## Correlation Philosophy

**Correlated positions = single risk, not multiple.**

When two pairs move together, holding both amplifies your risk. You detect correlations dynamically and avoid stacking correlated positions.

## Correlation Calculation

### Method
Calculate Pearson correlation coefficient between all traded pairs.

### Formula
```
correlation(X, Y) = Σ((X - X̄)(Y - Ȳ)) / √(Σ(X - X̄)² × Σ(Y - Ȳ)²)
```

### Simplified for Trading
```python
import numpy as np

def calculate_correlation(returns_x, returns_y):
    """Calculate correlation between two return series."""
    correlation = np.corrcoef(returns_x, returns_y)[0, 1]
    return correlation
```

## Data Requirements

### Return Series
- **Timeframe:** 1-hour returns
- **Lookback:** 48 hours (48 data points)
- **Minimum data:** 30 data points required
- **Update frequency:** Every 4 hours

### Data Collection
```python
def get_returns(symbol, lookback=48):
    """Get hourly returns for correlation calculation."""
    ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=lookback + 1)
    closes = [c[4] for c in ohlcv]
    returns = [(closes[i] - closes[i-1]) / closes[i-1] 
               for i in range(1, len(closes))]
    return returns[-lookback:]
```

## Correlation Thresholds

### Group Classification
| Correlation | Classification | Action |
|-------------|----------------|--------|
| > 0.8 | Strong positive | Same group, never hold both |
| 0.7 - 0.8 | Moderate positive | Same group, prefer one |
| 0.5 - 0.7 | Weak positive | Different groups OK |
| -0.5 - 0.5 | Uncorrelated | Different groups, no restriction |
| -0.7 - -0.5 | Weak negative | Different groups, hedge potential |
| < -0.7 | Strong negative | Opposite groups, hedge potential |

### Default Threshold
**0.7** — Pairs with correlation > 0.7 are in the same group.

## Group Management

### Dynamic Groups
Groups are recalculated every 4 hours based on current correlation.

### Group Structure
```python
correlation_groups = [
    {"id": 1, "pairs": ["BTCUSDT", "ETHUSDT"], "correlation": 0.85},
    {"id": 2, "pairs": ["SOLUSDT", "AVAXUSDT", "DOTUSDT"], "correlation": 0.72},
    {"id": 3, "pairs": ["BNBUSDT"], "correlation": null},  # Uncorrelated
]
```

### Group Rules
1. Maximum 1 position per group
2. If opening position in group, cannot open another in same group
3. Existing positions grandfathered (don't force close)
4. New positions must check current groups

## Correlation Matrix

### Full Matrix Calculation
Calculate correlation between all pairs in watchlist.

### Matrix Output
```
=== Correlation Matrix [TIMESTAMP] ===

        BTC   ETH   SOL   AVAX  DOT   BNB   XRP
BTC     1.00  0.85  0.62  0.58  0.55  0.45  0.40
ETH     0.85  1.00  0.68  0.65  0.60  0.50  0.42
SOL     0.62  0.68  1.00  0.78  0.72  0.35  0.38
AVAX    0.58  0.65  0.78  1.00  0.70  0.30  0.35
DOT     0.55  0.60  0.72  0.70  1.00  0.32  0.33
BNB     0.45  0.50  0.35  0.30  0.32  1.00  0.28
XRP     0.40  0.42  0.38  0.35  0.33  0.28  1.00

Groups (threshold > 0.7):
- Group 1: BTC, ETH (0.85)
- Group 2: SOL, AVAX, DOT (0.72, 0.78, 0.70)
- Group 3: BNB, XRP (uncorrelated with others)
```

## Implementation

### Correlation Calculator Class
```python
class CorrelationManager:
    def __init__(self, exchange, threshold=0.7):
        self.exchange = exchange
        self.threshold = threshold
        self.groups = []
        self.last_update = None
    
    def update(self, symbols):
        """Recalculate correlation groups."""
        returns = {}
        for symbol in symbols:
            returns[symbol] = self.get_returns(symbol)
        
        # Calculate correlation matrix
        matrix = {}
        for s1 in symbols:
            for s2 in symbols:
                if s1 != s2:
                    corr = calculate_correlation(returns[s1], returns[s2])
                    matrix[(s1, s2)] = corr
        
        # Form groups
        self.groups = self.form_groups(matrix)
        self.last_update = datetime.now()
    
    def form_groups(self, matrix):
        """Group pairs by correlation."""
        groups = []
        assigned = set()
        
        for (s1, s2), corr in matrix.items():
            if corr > self.threshold and s1 not in assigned and s2 not in assigned:
                group = [s1, s2]
                assigned.add(s1)
                assigned.add(s2)
                
                # Check for other correlated pairs
                for s3, corr2 in matrix.items():
                    if s3 not in assigned and corr2 > self.threshold:
                        group.append(s3)
                        assigned.add(s3)
                
                groups.append({
                    "pairs": group,
                    "correlation": corr
                })
        
        return groups
    
    def can_open_position(self, symbol, existing_positions):
        """Check if opening a position would violate correlation rules."""
        for group in self.groups:
            if symbol in group["pairs"]:
                for pos in existing_positions:
                    if pos["pair"] in group["pairs"] and pos["pair"] != symbol:
                        return False, f"Correlated with {pos['pair']} (corr: {group['correlation']:.2f})"
        
        return True, "OK"
    
    def get_group(self, symbol):
        """Get the correlation group for a symbol."""
        for group in self.groups:
            if symbol in group["pairs"]:
                return group
        return None
```

## Integration with Engine

### Pre-Trade Check
Before any trade, check correlation:

```python
def check_correlation(symbol, existing_positions, correlation_manager):
    """Check if trade violates correlation rules."""
    can_open, reason = correlation_manager.can_open_position(
        symbol, existing_positions
    )
    return can_open, reason
```

### Engine Integration
Add to TradeValidator checks:
```python
def _check_correlation(self, decision: dict) -> tuple[bool, str]:
    symbol = decision.get("pair", "")
    existing = self.state.state["open_positions"]
    
    can_open, reason = self.correlation_manager.can_open_position(
        symbol, existing
    )
    
    if not can_open:
        return False, f"Correlation violation: {reason}"
    
    return True, ""
```

## Update Schedule

### Automatic Updates
- **Every 4 hours:** Full recalculation
- **On startup:** Initial calculation
- **On new pair added:** Add to calculation

### Manual Updates
- During daily review
- When market regime changes significantly
- When adding new pairs to watchlist

## Correlation Changes Over Time

### What Affects Correlation
| Factor | Effect |
|--------|--------|
| Market stress | Correlations increase (everything falls together) |
| Trending market | Correlations decrease (individual moves) |
| News events | Temporary correlation spike |
| Regime change | Correlation structure shifts |

### Adapting to Changes
- Monitor correlation changes weekly
- Adjust threshold if needed (0.6-0.8 range)
- Note when correlations break down
- Use as regime indicator (high correlation = stress)

## Error Handling

### Missing Data
- If pair has < 30 data points, exclude from calculation
- Use last known correlation if recent data unavailable
- Note gaps in correlation matrix

### Calculation Errors
- If correlation matrix is invalid, use previous groups
- Log calculation errors
- Fall back to hard-coded groups if persistent failure

## Output Format

### Correlation Update
```
=== Correlation Update [TIMESTAMP] ===

Calculated for [X] pairs using 48h hourly returns.

Correlation Matrix:
[Matrix output]

Groups (threshold > 0.7):
- Group 1: [pairs] (corr: [value])
- Group 2: [pairs] (corr: [value])
...

Open positions correlation check:
[Position] vs [Existing]: [PASS/FAIL] (corr: [value])

Next update: [TIME]
```

### Daily Correlation Review
```
=== Daily Correlation Review [DATE] ===

Current groups:
[Group list]

Correlation changes since yesterday:
- BTC-ETH: 0.85 → 0.82 (-0.03)
- SOL-AVAX: 0.78 → 0.81 (+0.03)
...

Notable changes:
[Analysis]

Adjustments needed:
[Any changes to threshold or groups]
```
