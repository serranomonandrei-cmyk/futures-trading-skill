"""
executor.py — Binance Futures Order Execution

Handles order placement, position monitoring, and error handling.
Uses ccxt for Binance USDT-M perpetual futures.
"""

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

try:
    import ccxt
except ImportError:
    ccxt = None
    print("WARNING: ccxt not installed. Run: pip install ccxt")

from engine import (
    get_state,
    get_validator,
    get_kill_switch,
    validate_trade,
    MIN_NOTIONAL,
    COOLDOWN_SECONDS,
)

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("trading_executor.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("executor")


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ExchangeConfig:
    api_key: str = ""
    api_secret: str = ""
    testnet: bool = False
    max_retries: int = 3
    retry_backoff: list = None
    spread_threshold: float = 0.0005  # 0.05% — use limit below, market above

    def __post_init__(self):
        if self.retry_backoff is None:
            self.retry_backoff = [1, 3, 10]


def load_config() -> ExchangeConfig:
    config = ExchangeConfig()
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key == "BINANCE_API_KEY":
                        config.api_key = value
                    elif key == "BINANCE_API_SECRET":
                        config.api_secret = value
                    elif key == "BINANCE_TESTNET":
                        config.testnet = value.lower() == "true"
    return config


# =============================================================================
# EXCHANGE WRAPPER
# =============================================================================

class BinanceExecutor:
    """Handles order execution on Binance USDT-M perpetual futures."""

    def __init__(self, config: Optional[ExchangeConfig] = None):
        self.config = config or load_config()
        self.exchange = None
        self._init_exchange()

    def _init_exchange(self):
        if ccxt is None:
            raise ImportError("ccxt not installed. Run: pip install ccxt")

        self.exchange = ccxt.binanceusdm({
            "apiKey": self.config.api_key,
            "secret": self.config.api_secret,
            "enableRateLimit": True,
            "options": {
                "defaultType": "future",
            },
        })

        if self.config.testnet:
            self.exchange.set_sandbox_mode(True)
            logger.info("Sandbox mode enabled (testnet)")

        logger.info("Exchange initialized")

    # =========================================================================
    # ORDER PLACEMENT
    # =========================================================================

    def place_entry(self, decision: dict, position_size: dict) -> dict:
        """
        Place entry order (limit or market based on spread).

        Args:
            decision: AI's trade decision
            position_size: Calculated position size from engine

        Returns:
            {"success": True/False, "order": {...}, "error": "..."}
        """
        pair = decision["pair"]
        side = decision["side"]
        entry = decision["entry"]
        leverage = decision["leverage"]

        notional = position_size["notional"]
        if notional < MIN_NOTIONAL:
            return {"success": False, "error": f"Notional ${notional:.2f} below minimum ${MIN_NOTIONAL}"}

        try:
            self.exchange.set_leverage(leverage, pair)
        except Exception as e:
            logger.warning(f"Could not set leverage for {pair}: {e}")

        order_type = self._choose_order_type(pair, entry)

        try:
            symbol = pair
            amount = notional / entry

            if order_type == "limit":
                order = self._place_limit_order(symbol, side, entry, amount)
            else:
                order = self._place_market_order(symbol, side, amount)

            if order and order.get("id"):
                logger.info(f"Entry placed: {order_type.upper()} {side} {pair} @ {entry} | notional: ${notional:.2f} | leverage: {leverage}x")
                return {"success": True, "order": order, "order_type": order_type}
            else:
                return {"success": False, "error": f"Order returned no ID: {order}"}

        except ccxt.InsufficientFunds as e:
            logger.error(f"Insufficient funds for {pair}: {e}")
            return {"success": False, "error": f"Insufficient funds: {e}"}
        except ccxt.InvalidOrder as e:
            logger.error(f"Invalid order for {pair}: {e}")
            return {"success": False, "error": f"Invalid order: {e}"}
        except ccxt.NetworkError as e:
            logger.error(f"Network error for {pair}: {e}")
            return self._retry_entry(decision, position_size, "network")
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error for {pair}: {e}")
            return {"success": False, "error": f"Exchange error: {e}"}
        except Exception as e:
            logger.error(f"Unexpected error for {pair}: {e}")
            return {"success": False, "error": f"Unexpected error: {e}"}

    def _place_limit_order(self, symbol: str, side: str, price: float, amount: float) -> dict:
        order_side = "buy" if side == "long" else "sell"
        return self.exchange.create_limit_order(
            symbol, order_side, amount, price,
            {"timeInForce": "GTC"}
        )

    def _place_market_order(self, symbol: str, side: str, amount: float) -> dict:
        order_side = "buy" if side == "long" else "sell"
        return self.exchange.create_market_order(symbol, order_side, amount)

    def _retry_entry(self, decision: dict, position_size: dict, error_type: str) -> dict:
        for attempt, delay in enumerate(self.config.retry_backoff):
            logger.info(f"Retry {attempt + 1}/{len(self.config.retry_backoff)} after {delay}s")
            time.sleep(delay)
            result = self.place_entry(decision, position_size)
            if result["success"]:
                return result
        return {"success": False, "error": f"Max retries exceeded for {error_type}"}

    def _choose_order_type(self, pair: str, entry: float) -> str:
        try:
            ticker = self.exchange.fetch_ticker(pair)
            spread_pct = ticker.get("ask", 0) - ticker.get("bid", 0)
            if ticker.get("bid", 0) > 0:
                spread_pct = spread_pct / ticker["bid"]
            else:
                spread_pct = 999

            if spread_pct < self.config.spread_threshold:
                return "limit"
            else:
                return "market"
        except Exception:
            return "market"

    # =========================================================================
    # EXIT ORDERS
    # =========================================================================

    def place_stop_loss(self, pair: str, side: str, stop_price: float, amount: float) -> dict:
        try:
            order_side = "sell" if side == "long" else "buy"
            order = self.exchange.create_order(
                pair,
                "STOP_MARKET",
                order_side,
                amount,
                None,
                {"stopPrice": stop_price, "closePosition": "false"}
            )
            logger.info(f"Stop loss placed: {pair} @ {stop_price}")
            return {"success": True, "order": order}
        except Exception as e:
            logger.error(f"Failed to place stop loss for {pair}: {e}")
            return {"success": False, "error": str(e)}

    def place_take_profit(self, pair: str, side: str, tp_price: float, amount: float) -> dict:
        try:
            order_side = "sell" if side == "long" else "buy"
            order = self.exchange.create_order(
                pair,
                "TAKE_PROFIT_MARKET",
                order_side,
                amount,
                None,
                {"stopPrice": tp_price, "closePosition": "false"}
            )
            logger.info(f"Take profit placed: {pair} @ {tp_price}")
            return {"success": True, "order": order}
        except Exception as e:
            logger.error(f"Failed to place take profit for {pair}: {e}")
            return {"success": False, "error": str(e)}

    def close_position(self, pair: str, side: str, amount: float) -> dict:
        try:
            order_side = "sell" if side == "long" else "buy"
            order = self.exchange.create_market_order(pair, order_side, amount)
            logger.info(f"Position closed: {pair}")
            return {"success": True, "order": order}
        except Exception as e:
            logger.error(f"Failed to close position for {pair}: {e}")
            return {"success": False, "error": str(e)}

    def close_all_positions(self) -> list:
        results = []
        try:
            positions = self.exchange.fetch_positions()
            for pos in positions:
                if pos["contracts"] and float(pos["contracts"]) > 0:
                    pair = pos["symbol"]
                    side = "long" if pos["side"] == "long" else "short"
                    amount = float(pos["contracts"])
                    result = self.close_position(pair, side, amount)
                    results.append({"pair": pair, "result": result})
        except Exception as e:
            logger.error(f"Failed to close all positions: {e}")
        return results

    # =========================================================================
    # POSITION MONITORING
    # =========================================================================

    def fetch_positions(self) -> list:
        try:
            positions = self.exchange.fetch_positions()
            return [
                {
                    "pair": p["symbol"],
                    "side": p["side"],
                    "contracts": float(p["contracts"]) if p["contracts"] else 0,
                    "entry_price": float(p["entryPrice"]) if p["entryPrice"] else 0,
                    "mark_price": float(p["markPrice"]) if p["markPrice"] else 0,
                    "unrealized_pnl": float(p["unrealizedPnl"]) if p["unrealizedPnl"] else 0,
                    "margin": float(p["initialMargin"]) if p["initialMargin"] else 0,
                    "leverage": int(p["leverage"]) if p["leverage"] else 1,
                    "liquidation_price": float(p["liquidationPrice"]) if p["liquidationPrice"] else 0,
                }
                for p in positions
                if p["contracts"] and float(p["contracts"]) > 0
            ]
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            return []

    def fetch_balance(self) -> float:
        try:
            balance = self.exchange.fetch_balance()
            return float(balance.get("total", {}).get("USDT", 0))
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            return 0.0

    def fetch_ticker(self, pair: str) -> dict:
        try:
            return self.exchange.fetch_ticker(pair)
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {pair}: {e}")
            return {}

    def fetch_ohlcv(self, pair: str, timeframe: str = "1h", limit: int = 100) -> list:
        try:
            return self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {pair}: {e}")
            return []

    # =========================================================================
    # FUNDING RATE
    # =========================================================================

    def fetch_funding_rate(self, pair: str) -> float:
        try:
            info = self.exchange.fetch_funding_rate(pair)
            return float(info.get("fundingRate", 0))
        except Exception as e:
            logger.error(f"Failed to fetch funding rate for {pair}: {e}")
            return 0.0

    # =========================================================================
    # EXCHANGE INFO
    # =========================================================================

    def fetch_exchange_info(self) -> dict:
        try:
            return self.exchange.load_markets()
        except Exception as e:
            logger.error(f"Failed to fetch exchange info: {e}")
            return {}

    def get_min_notional(self, pair: str) -> float:
        try:
            market = self.exchange.market(pair)
            limits = market.get("limits", {}).get("cost", {})
            return float(limits.get("min", MIN_NOTIONAL))
        except Exception:
            return MIN_NOTIONAL

    # =========================================================================
    # FULL TRADE EXECUTION PIPELINE
    # =========================================================================

    def execute_trade(self, decision: dict) -> dict:
        """
        Full pipeline: validate → calculate size → place order → set SL/TP.

        Args:
            decision: AI's trade decision

        Returns:
            {"success": True/False, "trade": {...}, "error": "..."}
        """
        state = get_state()
        validator = get_validator()
        ks = get_kill_switch()

        state.check_daily_reset()

        kill_active, kill_reason = ks.check()
        if kill_active:
            ks.activate(kill_reason)
            return {"success": False, "error": kill_reason, "kill_switch": True}

        validation = validate_trade(decision)
        if not validation["valid"]:
            return {"success": False, "error": validation["reason"]}

        position_size = validation["position_size"]

        entry_result = self.place_entry(decision, position_size)
        if not entry_result["success"]:
            return {"success": False, "error": entry_result["error"]}

        sl_result = self.place_stop_loss(
            decision["pair"],
            decision["side"],
            decision["stop"],
            position_size["notional"] / decision["entry"],
        )

        tp_result = self.place_take_profit(
            decision["pair"],
            decision["side"],
            decision["tp"],
            position_size["notional"] / decision["entry"],
        )

        trade_record = {
            "pair": decision["pair"],
            "side": decision["side"],
            "entry": decision["entry"],
            "stop": decision["stop"],
            "tp": decision["tp"],
            "leverage": decision["leverage"],
            "notional": position_size["notional"],
            "margin": position_size["margin"],
            "risk_amount": position_size["risk_amount"],
            "risk_pct": position_size["risk_pct"],
            "setup_grade": decision.get("setup_grade", "B"),
            "entry_order": entry_result.get("order", {}).get("id"),
            "sl_order": sl_result.get("order", {}).get("id"),
            "tp_order": tp_result.get("order", {}).get("id"),
            "timestamp": datetime.now().isoformat(),
        }

        state.state["open_positions"].append(trade_record)
        state.save()

        logger.info(f"Trade executed: {decision['side']} {decision['pair']} @ {decision['entry']}")
        return {"success": True, "trade": trade_record}


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    executor = BinanceExecutor()
    balance = executor.fetch_balance()
    print(f"Account balance: ${balance:.2f}")
    positions = executor.fetch_positions()
    print(f"Open positions: {len(positions)}")
    for pos in positions:
        print(f"  {pos['pair']} {pos['side']} | Entry: {pos['entry_price']} | PnL: ${pos['unrealized_pnl']:.2f}")
