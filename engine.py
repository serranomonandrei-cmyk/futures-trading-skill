"""
engine.py — Trading System Validation Engine

Enforces hard limits that the AI cannot override.
Every trade decision passes through this before execution.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# =============================================================================
# HARD LIMITS (IMMUTABLE — DO NOT MODIFY WITHOUT HUMAN APPROVAL)
# =============================================================================

MAX_LEVERAGE = 10
BASE_RISK_PER_TRADE = 0.03  # 3%
MAX_RISK_AFTER_REGIME = 0.045  # 4.5% (3% * 1.5x max multiplier)
MAX_DRAWDOWN = 0.30  # 30%
MAX_CONCURRENT_POSITIONS = 3
MAX_MARGIN_UTILIZATION = 0.75  # 75% of account
MAX_SINGLE_POSITION_MARGIN = 0.35  # 35% of account
MIN_STOP_DISTANCE = 0.01  # 1.0% of price
MIN_ACCOUNT_BALANCE = 20.0  # USDT
COOLDOWN_SECONDS = 300  # 5 minutes
MAX_DAILY_TRADES = 10
MIN_NOTIONAL = 5.0  # Binance minimum

# Daily loss tiers (rolling 24h)
DAILY_LOSS_TIER_1 = 0.06  # 6% — reduce size
DAILY_LOSS_TIER_2 = 0.10  # 10% — halt entries
DAILY_LOSS_TIER_3 = 0.12  # 12% — close all, halt 24h

# Correlation threshold for grouping
CORRELATION_THRESHOLD = 0.7  # Pairs with corr > 0.7 are in same group

# Default fallback groups (used if dynamic calculation fails)
DEFAULT_CORRELATION_GROUPS = [
    ["BTCUSDT", "ETHUSDT"],
    ["SOLUSDT", "AVAXUSDT", "DOTUSDT"],
]

# Leverage tiers
LEVERAGE_TIERS = {
    "standard": 3,      # B/B+ setups
    "high_conviction": 5,  # A setups
    "a_plus": 10,       # A+ setups only
}


# =============================================================================
# STATE TRACKING
# =============================================================================

class TradingState:
    """Tracks account state, positions, and daily metrics."""

    def __init__(self, state_file: str = "trading_state.json"):
        self.state_file = Path(state_file)
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {
            "peak_balance": 0.0,
            "current_balance": 0.0,
            "open_positions": [],
            "daily_trades": 0,
            "daily_pnl": 0.0,
            "daily_start_balance": 0.0,
            "daily_start_time": None,
            "consecutive_losses": 0,
            "last_trade_time": None,
            "halt_until": None,
            "total_trades": 0,
            "winning_trades": 0,
        }

    def save(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def update_balance(self, balance: float):
        self.state["current_balance"] = balance
        if balance > self.state["peak_balance"]:
            self.state["peak_balance"] = balance
        self.save()

    def get_drawdown(self) -> float:
        if self.state["peak_balance"] == 0:
            return 0.0
        return (self.state["peak_balance"] - self.state["current_balance"]) / self.state["peak_balance"]

    def get_daily_loss_pct(self) -> float:
        if self.state["daily_start_balance"] == 0:
            return 0.0
        return (self.state["daily_start_balance"] - self.state["current_balance"]) / self.state["daily_start_balance"]

    def get_daily_loss_tier(self) -> str:
        loss = self.get_daily_loss_pct()
        if loss > DAILY_LOSS_TIER_3:
            return "close_all_halt_24h"
        elif loss > DAILY_LOSS_TIER_2:
            return "halt_entries"
        elif loss > DAILY_LOSS_TIER_1:
            return "reduce_size_50pct"
        else:
            return "normal"

    def check_daily_reset(self):
        if self.state["daily_start_time"] is None:
            return
        start = datetime.fromisoformat(self.state["daily_start_time"])
        if datetime.now() - start > timedelta(hours=24):
            self.state["daily_start_balance"] = self.state["current_balance"]
            self.state["daily_start_time"] = datetime.now().isoformat()
            self.state["daily_trades"] = 0
            self.state["daily_pnl"] = 0.0
            self.save()

    def record_trade(self, pnl: float):
        self.state["daily_trades"] += 1
        self.state["daily_pnl"] += pnl
        self.state["total_trades"] += 1
        self.state["last_trade_time"] = datetime.now().isoformat()

        if self.state["daily_start_balance"] == 0:
            self.state["daily_start_balance"] = self.state["current_balance"]
            self.state["daily_start_time"] = datetime.now().isoformat()

        if pnl < 0:
            self.state["consecutive_losses"] += 1
        else:
            self.state["consecutive_losses"] = 0
            self.state["winning_trades"] += 1

        self.save()

    def is_halted(self) -> tuple[bool, str]:
        if self.state["halt_until"] is not None:
            halt_time = datetime.fromisoformat(self.state["halt_until"])
            if datetime.now() < halt_time:
                remaining = (halt_time - datetime.now()).seconds // 60
                return True, f"Trading halted for {remaining} more minutes"
            else:
                self.state["halt_until"] = None
                self.save()

        drawdown = self.get_drawdown()
        if drawdown >= MAX_DRAWDOWN:
            return True, f"Max drawdown hit: {drawdown:.1%} >= {MAX_DRAWDOWN:.1%}"

        return False, ""

    def get_position_margin_used(self) -> float:
        return sum(p.get("margin", 0) for p in self.state["open_positions"])


# =============================================================================
# DYNAMIC CORRELATION MANAGER
# =============================================================================

class CorrelationManager:
    """Manages dynamic correlation groups between trading pairs."""

    def __init__(self, exchange=None, threshold=CORRELATION_THRESHOLD):
        self.exchange = exchange
        self.threshold = threshold
        self.groups = []
        self.correlation_matrix = {}
        self.last_update = None
        self._use_default = exchange is None

    def update(self, symbols: list):
        """Recalculate correlation groups for given symbols."""
        if self._use_default or self.exchange is None:
            self.groups = [g.copy() for g in DEFAULT_CORRELATION_GROUPS]
            self.last_update = datetime.now()
            return

        try:
            returns = {}
            for symbol in symbols:
                returns[symbol] = self._get_returns(symbol)

            # Calculate correlation matrix
            self.correlation_matrix = {}
            for s1 in symbols:
                for s2 in symbols:
                    if s1 != s2 and s1 in returns and s2 in returns:
                        corr = self._calculate_correlation(returns[s1], returns[s2])
                        self.correlation_matrix[(s1, s2)] = corr

            # Form groups
            self.groups = self._form_groups()
            self.last_update = datetime.now()

        except Exception as e:
            # Fallback to default groups on error
            self.groups = [g.copy() for g in DEFAULT_CORRELATION_GROUPS]
            self.last_update = datetime.now()

    def _get_returns(self, symbol: str, lookback: int = 48) -> list:
        """Get hourly returns for correlation calculation."""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=lookback + 1)
            closes = [c[4] for c in ohlcv]
            returns = [(closes[i] - closes[i-1]) / closes[i-1]
                       for i in range(1, len(closes))]
            return returns[-lookback:]
        except Exception:
            return []

    def _calculate_correlation(self, returns_x: list, returns_y: list) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(returns_x) < 10 or len(returns_y) < 10:
            return 0.0

        n = min(len(returns_x), len(returns_y))
        x = returns_x[-n:]
        y = returns_y[-n:]

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denom_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denom_y = sum((y[i] - mean_y) ** 2 for i in range(n))

        if denom_x == 0 or denom_y == 0:
            return 0.0

        return numerator / (denom_x * denom_y) ** 0.5

    def _form_groups(self) -> list:
        """Group pairs by correlation threshold."""
        groups = []
        assigned = set()

        # Sort pairs by number of high correlations (most connected first)
        pair_scores = {}
        for (s1, s2), corr in self.correlation_matrix.items():
            if corr > self.threshold:
                pair_scores[s1] = pair_scores.get(s1, 0) + 1
                pair_scores[s2] = pair_scores.get(s2, 0) + 1

        sorted_pairs = sorted(pair_scores.keys(), key=lambda p: pair_scores[p], reverse=True)

        for pair in sorted_pairs:
            if pair in assigned:
                continue

            # Find all pairs correlated with this one
            group = [pair]
            assigned.add(pair)

            for other_pair in pair_scores:
                if other_pair in assigned:
                    continue

                # Check if other_pair is correlated with all pairs in group
                all_correlated = True
                for g_pair in group:
                    corr = self.correlation_matrix.get((g_pair, other_pair), 0)
                    if corr <= self.threshold:
                        all_correlated = False
                        break

                if all_correlated:
                    group.append(other_pair)
                    assigned.add(other_pair)

            if len(group) > 1:
                avg_corr = self._average_group_correlation(group)
                groups.append({"pairs": group, "correlation": avg_corr})

        return groups

    def _average_group_correlation(self, group: list) -> float:
        """Calculate average correlation within a group."""
        correlations = []
        for i, s1 in enumerate(group):
            for s2 in group[i+1:]:
                corr = self.correlation_matrix.get((s1, s2), 0)
                correlations.append(abs(corr))
        return sum(correlations) / len(correlations) if correlations else 0.0

    def can_open_position(self, symbol: str, existing_positions: list) -> tuple[bool, str]:
        """Check if opening a position would violate correlation rules."""
        for group in self.groups:
            if symbol in group["pairs"]:
                for pos in existing_positions:
                    pos_pair = pos.get("pair", "")
                    if pos_pair in group["pairs"] and pos_pair != symbol:
                        return False, f"Correlated with {pos_pair} (corr: {group['correlation']:.2f})"

        return True, "OK"

    def get_group(self, symbol: str) -> dict:
        """Get the correlation group for a symbol."""
        for group in self.groups:
            if symbol in group["pairs"]:
                return group
        return None

    def needs_update(self, hours: int = 4) -> bool:
        """Check if correlation data needs updating."""
        if self.last_update is None:
            return True
        elapsed = (datetime.now() - self.last_update).total_seconds() / 3600
        return elapsed >= hours


# =============================================================================
# VALIDATION ENGINE
# =============================================================================

class TradeValidator:
    """Validates every trade decision against hard limits."""

    def __init__(self, state: TradingState, correlation_manager: CorrelationManager = None):
        self.state = state
        self.correlation_manager = correlation_manager or CorrelationManager()

    def validate(self, decision: dict) -> tuple[bool, str]:
        """
        Validate a trade decision.

        Args:
            decision: {
                "pair": "ETHUSDT",
                "side": "long" or "short",
                "entry": 3420.50,
                "stop": 3395.00,
                "tp": 3480.00,
                "leverage": 5,
                "risk_pct": 0.02,
                "regime_multiplier": 1.5,
                "setup_grade": "A"
            }

        Returns:
            (is_valid, reason)
        """
        checks = [
            self._check_halted,
            self._check_min_balance,
            self._check_leverage,
            self._check_risk_per_trade,
            self._check_stop_distance,
            self._check_concurrent_positions,
            self._check_margin_utilization,
            self._check_single_position_margin,
            self._check_daily_trades,
            self._check_cooldown,
            self._check_correlation,
            self._check_min_notional,
        ]

        for check in checks:
            is_valid, reason = check(decision)
            if not is_valid:
                return False, reason

        return True, "All checks passed"

    def _check_halted(self, decision: dict) -> tuple[bool, str]:
        is_halted, reason = self.state.is_halted()
        if is_halted:
            return False, f"HALTED: {reason}"
        return True, ""

    def _check_min_balance(self, decision: dict) -> tuple[bool, str]:
        balance = self.state.state["current_balance"]
        if balance < MIN_ACCOUNT_BALANCE:
            return False, f"Balance ${balance:.2f} below minimum ${MIN_ACCOUNT_BALANCE}"
        return True, ""

    def _check_leverage(self, decision: dict) -> tuple[bool, str]:
        leverage = decision.get("leverage", 0)
        if leverage > MAX_LEVERAGE:
            return False, f"Leverage {leverage}x exceeds max {MAX_LEVERAGE}x"
        if leverage < 1:
            return False, f"Leverage must be at least 1x"
        return True, ""

    def _check_risk_per_trade(self, decision: dict) -> tuple[bool, str]:
        risk_pct = decision.get("risk_pct", 0)
        regime_mult = decision.get("regime_multiplier", 1.0)
        total_risk = risk_pct * regime_mult

        if total_risk > MAX_RISK_AFTER_REGIME:
            return False, f"Total risk {total_risk:.1%} exceeds max {MAX_RISK_AFTER_REGIME:.1%} (base {risk_pct:.1%} * regime {regime_mult}x)"
        return True, ""

    def _check_stop_distance(self, decision: dict) -> tuple[bool, str]:
        entry = decision.get("entry", 0)
        stop = decision.get("stop", 0)

        if entry == 0:
            return False, "Entry price is 0"

        stop_distance = abs(entry - stop) / entry
        if stop_distance < MIN_STOP_DISTANCE:
            return False, f"Stop distance {stop_distance:.2%} < minimum {MIN_STOP_DISTANCE:.2%}"
        return True, ""

    def _check_concurrent_positions(self, decision: dict) -> tuple[bool, str]:
        open_count = len(self.state.state["open_positions"])
        if open_count >= MAX_CONCURRENT_POSITIONS:
            return False, f"Already {open_count} positions (max {MAX_CONCURRENT_POSITIONS})"
        return True, ""

    def _check_margin_utilization(self, decision: dict) -> tuple[bool, str]:
        balance = self.state.state["current_balance"]
        if balance == 0:
            return False, "Account balance is 0"

        current_margin = self.state.get_position_margin_used()
        new_margin = self._calculate_margin(decision)
        total_margin = current_margin + new_margin

        if total_margin > balance * MAX_MARGIN_UTILIZATION:
            return False, f"Total margin ${total_margin:.2f} exceeds {MAX_MARGIN_UTILIZATION:.0%} of balance (${balance * MAX_MARGIN_UTILIZATION:.2f})"
        return True, ""

    def _check_single_position_margin(self, decision: dict) -> tuple[bool, str]:
        balance = self.state.state["current_balance"]
        if balance == 0:
            return False, "Account balance is 0"

        new_margin = self._calculate_margin(decision)
        if new_margin > balance * MAX_SINGLE_POSITION_MARGIN:
            return False, f"Position margin ${new_margin:.2f} exceeds {MAX_SINGLE_POSITION_MARGIN:.0%} of balance (${balance * MAX_SINGLE_POSITION_MARGIN:.2f})"
        return True, ""

    def _check_daily_trades(self, decision: dict) -> tuple[bool, str]:
        daily_tier = self.state.get_daily_loss_tier()
        if daily_tier == "halt_entries":
            return False, f"Daily loss exceeds {DAILY_LOSS_TIER_2:.0%}, entries halted"
        return True, ""

    def _check_cooldown(self, decision: dict) -> tuple[bool, str]:
        last_trade = self.state.state.get("last_trade_time")
        if last_trade:
            last_time = datetime.fromisoformat(last_trade)
            elapsed = (datetime.now() - last_time).seconds
            if elapsed < COOLDOWN_SECONDS:
                remaining = COOLDOWN_SECONDS - elapsed
                return False, f"Cooldown: {remaining}s remaining"
        return True, ""

    def _check_correlation(self, decision: dict) -> tuple[bool, str]:
        pair = decision.get("pair", "")
        existing_positions = self.state.state["open_positions"]

        # Update correlation if needed
        if self.correlation_manager.needs_update():
            symbols = list(set([pair] + [p.get("pair", "") for p in existing_positions]))
            self.correlation_manager.update(symbols)

        can_open, reason = self.correlation_manager.can_open_position(pair, existing_positions)
        if not can_open:
            return False, f"Correlation violation: {reason}"
        return True, ""

    def _check_min_notional(self, decision: dict) -> tuple[bool, str]:
        notional = self._calculate_notional(decision)
        if notional < MIN_NOTIONAL:
            return False, f"Notional ${notional:.2f} below minimum ${MIN_NOTIONAL}"
        return True, ""

    def _calculate_margin(self, decision: dict) -> float:
        notional = self._calculate_notional(decision)
        leverage = decision.get("leverage", 1)
        return notional / leverage

    def _calculate_notional(self, decision: dict) -> float:
        balance = self.state.state["current_balance"]
        risk_pct = decision.get("risk_pct", BASE_RISK_PER_TRADE)
        regime_mult = decision.get("regime_multiplier", 1.0)
        entry = decision.get("entry", 0)
        stop = decision.get("stop", 0)
        leverage = decision.get("leverage", 1)

        adjusted_risk = balance * risk_pct * regime_mult
        stop_distance = abs(entry - stop) / entry if entry > 0 else 0

        if stop_distance == 0:
            return 0

        notional = adjusted_risk / stop_distance

        max_margin = balance * MAX_SINGLE_POSITION_MARGIN
        max_notional = max_margin * leverage
        if notional > max_notional:
            notional = max_notional

        return notional

    def calculate_position_size(self, decision: dict) -> dict:
        """Calculate final position size with all caps applied."""
        balance = self.state.state["current_balance"]
        risk_pct = decision.get("risk_pct", BASE_RISK_PER_TRADE)
        regime_mult = decision.get("regime_multiplier", 1.0)
        entry = decision.get("entry", 0)
        stop = decision.get("stop", 0)
        leverage = decision.get("leverage", 3)

        adjusted_risk = balance * risk_pct * regime_mult
        stop_distance = abs(entry - stop) / entry if entry > 0 else 0

        if stop_distance == 0:
            return {"error": "Stop distance is 0"}

        notional = adjusted_risk / stop_distance
        margin = notional / leverage

        max_margin_single = balance * MAX_SINGLE_POSITION_MARGIN
        if margin > max_margin_single:
            margin = max_margin_single
            notional = margin * leverage

        current_margin = self.state.get_position_margin_used()
        max_margin_total = balance * MAX_MARGIN_UTILIZATION
        available_margin = max_margin_total - current_margin
        if margin > available_margin:
            margin = available_margin
            notional = margin * leverage

        actual_risk = notional * stop_distance

        return {
            "notional": round(notional, 2),
            "margin": round(margin, 2),
            "risk_amount": round(actual_risk, 2),
            "risk_pct": round(actual_risk / balance * 100, 2) if balance > 0 else 0,
            "leverage": leverage,
        }


# =============================================================================
# KILL SWITCH
# =============================================================================

class KillSwitch:
    """Emergency shutdown handler."""

    def __init__(self, state: TradingState):
        self.state = state

    def check(self) -> tuple[bool, str]:
        """Check if kill switch should activate."""
        drawdown = self.state.get_drawdown()
        if drawdown >= MAX_DRAWDOWN:
            return True, f"KILL SWITCH: Drawdown {drawdown:.1%} >= {MAX_DRAWDOWN:.1%}"

        daily_tier = self.state.get_daily_loss_tier()
        if daily_tier == "close_all_halt_24h":
            return True, f"KILL SWITCH: Daily loss > {DAILY_LOSS_TIER_3:.0%}"

        return False, ""

    def activate(self, reason: str):
        """Activate kill switch — halt all trading."""
        self.state.state["halt_until"] = (datetime.now() + timedelta(hours=24)).isoformat()
        self.state.save()
        return {
            "action": "kill_switch_activated",
            "reason": reason,
            "halt_until": self.state.state["halt_until"],
        }


# =============================================================================
# MAIN VALIDATOR INSTANCE
# =============================================================================

_validator: Optional[TradeValidator] = None
_state: Optional[TradingState] = None
_kill_switch: Optional[KillSwitch] = None


def init_engine(state_file: str = "trading_state.json") -> TradeValidator:
    global _state, _validator, _kill_switch
    _state = TradingState(state_file)
    _validator = TradeValidator(_state)
    _kill_switch = KillSwitch(_state)
    return _validator


def get_state() -> TradingState:
    global _state
    if _state is None:
        _state = TradingState()
    return _state


def get_validator() -> TradeValidator:
    global _validator
    if _validator is None:
        _validator = TradeValidator(get_state())
    return _validator


def get_kill_switch() -> KillSwitch:
    global _kill_switch
    if _kill_switch is None:
        _kill_switch = KillSwitch(get_state())
    return _kill_switch


def validate_trade(decision: dict) -> dict:
    """
    Full validation pipeline.

    Returns:
        {
            "valid": True/False,
            "reason": "...",
            "position_size": {...} (if valid),
            "kill_switch": True/False
        }
    """
    state = get_state()
    validator = get_validator()
    ks = get_kill_switch()

    state.check_daily_reset()

    kill_active, kill_reason = ks.check()
    if kill_active:
        ks.activate(kill_reason)
        return {
            "valid": False,
            "reason": kill_reason,
            "kill_switch": True,
        }

    is_valid, reason = validator.validate(decision)

    if not is_valid:
        return {
            "valid": False,
            "reason": reason,
            "kill_switch": False,
        }

    position_size = validator.calculate_position_size(decision)

    return {
        "valid": True,
        "reason": "All checks passed",
        "position_size": position_size,
        "kill_switch": False,
    }


if __name__ == "__main__":
    engine = init_engine()
    print("Trading Engine initialized")
    print(f"Max leverage: {MAX_LEVERAGE}x")
    print(f"Max risk: {MAX_RISK_AFTER_REGIME:.1%}")
    print(f"Max drawdown: {MAX_DRAWDOWN:.1%}")
    print(f"Max positions: {MAX_CONCURRENT_POSITIONS}")
    print(f"Min stop distance: {MIN_STOP_DISTANCE:.1%}")
