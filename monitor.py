"""
monitor.py — Performance Tracking and Trade Journal

Tracks all trades, calculates metrics, and updates LEDGER.md and PERFORMANCE.md.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent
JOURNAL_DIR = Path.home() / "trading-journal"
LEDGER_FILE = JOURNAL_DIR / "LEDGER.md"
PERFORMANCE_FILE = JOURNAL_DIR / "PERFORMANCE.md"
TRADES_JSON = JOURNAL_DIR / "trades.json"
METRICS_JSON = JOURNAL_DIR / "metrics.json"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Trade:
    id: int
    pair: str
    side: str
    entry: float
    exit: Optional[float]
    stop: float
    tp: float
    leverage: int
    notional: float
    margin: float
    risk_amount: float
    risk_pct: float
    setup_grade: str
    pnl: Optional[float]
    pnl_pct: Optional[float]
    fees: float
    status: str  # "open", "closed", "stopped", "tp_hit"
    entry_time: str
    exit_time: Optional[str]
    notes: str = ""


# =============================================================================
# TRADE TRACKER
# =============================================================================

class TradeTracker:
    """Tracks all trades and maintains the journal."""

    def __init__(self):
        JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
        self.trades = self._load_trades()
        self._next_id = max((t["id"] for t in self.trades), default=0) + 1

    def _load_trades(self) -> list:
        if TRADES_JSON.exists():
            with open(TRADES_JSON) as f:
                return json.load(f)
        return []

    def _save_trades(self):
        with open(TRADES_JSON, "w") as f:
            json.dump(self.trades, f, indent=2)

    def record_entry(self, trade_data: dict) -> int:
        trade = {
            "id": self._next_id,
            "pair": trade_data["pair"],
            "side": trade_data["side"],
            "entry": trade_data["entry"],
            "exit": None,
            "stop": trade_data["stop"],
            "tp": trade_data["tp"],
            "leverage": trade_data["leverage"],
            "notional": trade_data["notional"],
            "margin": trade_data["margin"],
            "risk_amount": trade_data["risk_amount"],
            "risk_pct": trade_data["risk_pct"],
            "setup_grade": trade_data.get("setup_grade", "B"),
            "pnl": None,
            "pnl_pct": None,
            "fees": 0.0,
            "status": "open",
            "entry_time": datetime.now().isoformat(),
            "exit_time": None,
            "notes": "",
        }
        self.trades.append(trade)
        self._save_trades()
        self._next_id += 1
        return trade["id"]

    def record_exit(self, trade_id: int, exit_price: float, pnl: float, fees: float = 0.0):
        for trade in self.trades:
            if trade["id"] == trade_id:
                trade["exit"] = exit_price
                trade["pnl"] = pnl
                trade["pnl_pct"] = (pnl / trade["margin"]) * 100 if trade["margin"] > 0 else 0
                trade["fees"] = fees
                trade["status"] = "closed"
                trade["exit_time"] = datetime.now().isoformat()
                self._save_trades()
                self._update_ledger()
                self._update_performance()
                return
        print(f"Trade {trade_id} not found")

    def add_note(self, trade_id: int, note: str):
        for trade in self.trades:
            if trade["id"] == trade_id:
                trade["notes"] = note
                self._save_trades()
                return

    def get_open_trades(self) -> list:
        return [t for t in self.trades if t["status"] == "open"]

    def get_closed_trades(self) -> list:
        return [t for t in self.trades if t["status"] != "open"]

    def get_trades_since(self, since: datetime) -> list:
        return [
            t for t in self.trades
            if datetime.fromisoformat(t["entry_time"]) >= since
        ]

    # =========================================================================
    # METRICS CALCULATION
    # =========================================================================

    def calculate_metrics(self, period: Optional[timedelta] = None) -> dict:
        trades = self.trades
        if period:
            since = datetime.now() - period
            trades = [t for t in trades if t["status"] == "closed"
                     and datetime.fromisoformat(t["exit_time"]) >= since]

        closed = [t for t in trades if t["status"] == "closed"]
        if not closed:
            return self._empty_metrics()

        wins = [t for t in closed if (t.get("pnl") or 0) > 0]
        losses = [t for t in closed if (t.get("pnl") or 0) <= 0]

        total_pnl = sum(t.get("pnl", 0) for t in closed)
        total_fees = sum(t.get("fees", 0) for t in closed)
        gross_profit = sum(t["pnl"] for t in wins) if wins else 0
        gross_loss = abs(sum(t["pnl"] for t in losses)) if losses else 0

        win_rate = len(wins) / len(closed) if closed else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        avg_win = gross_profit / len(wins) if wins else 0
        avg_loss = gross_loss / len(losses) if losses else 0
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        pnls = [t.get("pnl", 0) for t in closed]
        max_dd = self._calculate_max_drawdown(pnls)

        by_grade = {}
        for t in closed:
            grade = t.get("setup_grade", "B")
            if grade not in by_grade:
                by_grade[grade] = {"count": 0, "wins": 0, "pnl": 0}
            by_grade[grade]["count"] += 1
            if (t.get("pnl") or 0) > 0:
                by_grade[grade]["wins"] += 1
            by_grade[grade]["pnl"] += t.get("pnl", 0)

        return {
            "total_trades": len(closed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate * 100, 1),
            "total_pnl": round(total_pnl, 2),
            "total_fees": round(total_fees, 2),
            "net_pnl": round(total_pnl - total_fees, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "expectancy": round(expectancy, 2),
            "max_drawdown_pct": round(max_dd, 1),
            "by_grade": by_grade,
            "consecutive_wins": self._max_consecutive(closed, True),
            "consecutive_losses": self._max_consecutive(closed, False),
        }

    def _empty_metrics(self) -> dict:
        return {
            "total_trades": 0, "wins": 0, "losses": 0, "win_rate": 0,
            "total_pnl": 0, "total_fees": 0, "net_pnl": 0,
            "gross_profit": 0, "gross_loss": 0, "profit_factor": 0,
            "avg_win": 0, "avg_loss": 0, "expectancy": 0,
            "max_drawdown_pct": 0, "by_grade": {},
            "consecutive_wins": 0, "consecutive_losses": 0,
        }

    def _calculate_max_drawdown(self, pnls: list) -> float:
        if not pnls:
            return 0.0
        peak = 0
        balance = 0
        max_dd = 0
        for pnl in pnls:
            balance += pnl
            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak * 100 if peak > 0 else 0
            max_dd = max(max_dd, dd)
        return max_dd

    def _max_consecutive(self, trades: list, is_win: bool) -> int:
        max_count = 0
        count = 0
        for t in trades:
            won = (t.get("pnl", 0) or 0) > 0
            if won == is_win:
                count += 1
                max_count = max(max_count, count)
            else:
                count = 0
        return max_count

    # =========================================================================
    # LEDGER GENERATION
    # =========================================================================

    def _update_ledger(self):
        closed = self.get_closed_trades()
        metrics = self.calculate_metrics()

        lines = [
            "# Trading Ledger\n",
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            "\n## Summary\n",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Trades | {metrics['total_trades']} |",
            f"| Win Rate | {metrics['win_rate']}% |",
            f"| Net P&L | ${metrics['net_pnl']:.2f} |",
            f"| Profit Factor | {metrics['profit_factor']} |",
            f"| Max Drawdown | {metrics['max_drawdown_pct']}% |",
            f"| Avg Win | ${metrics['avg_win']:.2f} |",
            f"| Avg Loss | ${metrics['avg_loss']:.2f} |",
            f"| Expectancy | ${metrics['expectancy']:.2f} |",
            "\n## Trade Log\n",
            "| # | Date | Pair | Side | Entry | Exit | Lev | P&L | Grade | Notes |",
            "|---|------|------|------|-------|------|-----|-----|-------|-------|",
        ]

        for t in reversed(closed[-50:]):
            date = t["entry_time"][:10]
            pnl_str = f"${t['pnl']:.2f}" if t.get("pnl") is not None else "OPEN"
            notes = t.get("notes", "")[:50]
            lines.append(
                f"| {t['id']} | {date} | {t['pair']} | {t['side']} | "
                f"${t['entry']:.2f} | ${t.get('exit', 0):.2f} | "
                f"{t['leverage']}x | {pnl_str} | {t['setup_grade']} | {notes} |"
            )

        lines.append("\n## By Setup Grade\n")
        lines.append("| Grade | Trades | Win Rate | Total P&L |")
        lines.append("|-------|--------|----------|-----------|")
        for grade, data in sorted(metrics.get("by_grade", {}).items()):
            wr = round(data["wins"] / data["count"] * 100, 1) if data["count"] > 0 else 0
            lines.append(f"| {grade} | {data['count']} | {wr}% | ${data['pnl']:.2f} |")

        with open(LEDGER_FILE, "w") as f:
            f.write("\n".join(lines))

    # =========================================================================
    # PERFORMANCE GENERATION
    # =========================================================================

    def _update_performance(self):
        metrics_daily = self.calculate_metrics(timedelta(days=1))
        metrics_weekly = self.calculate_metrics(timedelta(days=7))
        metrics_all = self.calculate_metrics()

        lines = [
            "# Performance Report\n",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            "\n## Today\n",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Trades | {metrics_daily['total_trades']} |",
            f"| Win Rate | {metrics_daily['win_rate']}% |",
            f"| Net P&L | ${metrics_daily['net_pnl']:.2f} |",
            f"| Profit Factor | {metrics_daily['profit_factor']} |",
            "\n## This Week\n",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Trades | {metrics_weekly['total_trades']} |",
            f"| Win Rate | {metrics_weekly['win_rate']}% |",
            f"| Net P&L | ${metrics_weekly['net_pnl']:.2f} |",
            f"| Profit Factor | {metrics_weekly['profit_factor']} |",
            "\n## All Time\n",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Trades | {metrics_all['total_trades']} |",
            f"| Win Rate | {metrics_all['win_rate']}% |",
            f"| Net P&L | ${metrics_all['net_pnl']:.2f} |",
            f"| Profit Factor | {metrics_all['profit_factor']} |",
            f"| Max Drawdown | {metrics_all['max_drawdown_pct']}% |",
            f"| Expectancy | ${metrics_all['expectancy']:.2f} |",
            f"| Best Trade | ${max((t.get('pnl', 0) or 0) for t in self.get_closed_trades() or [0]):.2f} |",
            f"| Worst Trade | ${min((t.get('pnl', 0) or 0) for t in self.get_closed_trades() or [0]):.2f} |",
            f"| Consecutive Wins | {metrics_all['consecutive_wins']} |",
            f"| Consecutive Losses | {metrics_all['consecutive_losses']} |",
        ]

        with open(PERFORMANCE_FILE, "w") as f:
            f.write("\n".join(lines))

        with open(METRICS_JSON, "w") as f:
            json.dump({
                "daily": metrics_daily,
                "weekly": metrics_weekly,
                "all_time": metrics_all,
                "updated": datetime.now().isoformat(),
            }, f, indent=2)


# =============================================================================
# STATE FILE GENERATOR
# =============================================================================

class StateGenerator:
    """Generates STATE.md with current account state."""

    def __init__(self, tracker: TradeTracker):
        self.tracker = tracker
        self.state_file = BASE_DIR / "STATE.md"

    def generate(self, balance: float, positions: list):
        metrics = self.tracker.calculate_metrics()
        open_trades = self.tracker.get_open_trades()

        lines = [
            "# Trading State",
            f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "<!-- ENGINE_DATA_START -->",
            f"Balance: ${balance:.2f}",
            f"Open Positions: {len(positions)}",
            f"Drawdown: {metrics['max_drawdown_pct']}%",
            f"Daily Trades: {len(self.tracker.get_trades_since(datetime.now().replace(hour=0, minute=0, second=0)))}",
            "",
            "## Open Positions",
        ]

        if positions:
            lines.append("| Pair | Side | Entry | Current | P&L | Leverage |")
            lines.append("|------|------|-------|---------|-----|----------|")
            for p in positions:
                pnl = p.get("unrealized_pnl", 0)
                lines.append(
                    f"| {p['pair']} | {p['side']} | ${p['entry_price']:.2f} | "
                    f"${p['mark_price']:.2f} | ${pnl:.2f} | {p['leverage']}x |"
                )
        else:
            lines.append("No open positions.")

        lines.extend([
            "",
            "## Recent Trades (Last 10)",
            "| # | Pair | Side | Entry | Exit | P&L | Grade |",
            "|---|------|------|-------|------|-----|-------|",
        ])

        recent = self.tracker.get_closed_trades()[-10:]
        for t in reversed(recent):
            pnl = t.get("pnl", 0) or 0
            lines.append(
                f"| {t['id']} | {t['pair']} | {t['side']} | ${t['entry']:.2f} | "
                f"${t.get('exit', 0):.2f} | ${pnl:.2f} | {t['setup_grade']} |"
            )

        lines.extend([
            "",
            "<!-- ENGINE_DATA_END -->",
            "",
            "<!-- AI_ANALYSIS_START -->",
            "(AI writes analysis here)",
            "<!-- AI_ANALYSIS_END -->",
        ])

        with open(self.state_file, "w") as f:
            f.write("\n".join(lines))


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    tracker = TradeTracker()
    generator = StateGenerator(tracker)
    print("Monitor initialized")
    print(f"Journal dir: {JOURNAL_DIR}")
    print(f"Trades tracked: {len(tracker.trades)}")
    metrics = tracker.calculate_metrics()
    print(f"Win rate: {metrics['win_rate']}%")
    print(f"Profit factor: {metrics['profit_factor']}")
