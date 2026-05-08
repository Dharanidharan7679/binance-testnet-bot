"""
Order placement logic for PrimeTrade Bot.
Sits between the CLI layer and the raw API client, adding display/formatting.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .client import BinanceFuturesClient, BinanceAPIError, NetworkError
from .validators import validate_order_params, ValidationError
from .logging_config import setup_logger

logger = setup_logger("trading_bot.orders")


# ── Formatting helpers ────────────────────────────────────────────────────────

DIVIDER = "─" * 60


def _fmt_val(value: Any, default: str = "N/A") -> str:
    """Return a human-readable value or a default placeholder."""
    if value is None or value == "" or value == "0" or value == 0:
        return default
    return str(value)


def print_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
    stop_price: Optional[float],
) -> None:
    """Print a formatted summary of the order *before* it is sent."""
    print(f"\n{DIVIDER}")
    print("  📋  ORDER REQUEST SUMMARY")
    print(DIVIDER)
    print(f"  Symbol     : {symbol}")
    print(f"  Side       : {side}")
    print(f"  Type       : {order_type}")
    print(f"  Quantity   : {quantity}")
    print(f"  Price      : {_fmt_val(price, 'Market Price')}")
    if stop_price is not None:
        print(f"  Stop Price : {stop_price}")
    print(DIVIDER)


def print_order_response(response: Dict[str, Any]) -> None:
    """Print a formatted summary of the API response *after* the order is placed."""
    print(f"\n{DIVIDER}")
    print("  ✅  ORDER RESPONSE")
    print(DIVIDER)
    print(f"  Order ID     : {_fmt_val(response.get('orderId'))}")
    print(f"  Client OID   : {_fmt_val(response.get('clientOrderId'))}")
    print(f"  Symbol       : {_fmt_val(response.get('symbol'))}")
    print(f"  Side         : {_fmt_val(response.get('side'))}")
    print(f"  Type         : {_fmt_val(response.get('type'))}")
    print(f"  Status       : {_fmt_val(response.get('status'))}")
    print(f"  Quantity     : {_fmt_val(response.get('origQty'))}")
    print(f"  Executed Qty : {_fmt_val(response.get('executedQty'))}")
    print(f"  Avg Price    : {_fmt_val(response.get('avgPrice'))}")
    print(f"  Price        : {_fmt_val(response.get('price', None), 'Market')}")
    if response.get("stopPrice"):
        print(f"  Stop Price   : {_fmt_val(response.get('stopPrice'))}")
    print(f"  Time in Force: {_fmt_val(response.get('timeInForce'))}")
    print(f"  Created At   : {_fmt_val(response.get('updateTime'))}")
    print(DIVIDER)
    print("  🎉  Order placed successfully!\n")


def print_error(message: str) -> None:
    """Print a formatted error message."""
    print(f"\n{DIVIDER}")
    print("  ❌  ERROR")
    print(DIVIDER)
    print(f"  {message}")
    print(DIVIDER + "\n")


# ── Core order function ───────────────────────────────────────────────────────


def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
    time_in_force: str = "GTC",
    reduce_only: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Validate inputs, print a request summary, call the API, and display the result.

    Args:
        client:        An authenticated BinanceFuturesClient instance.
        symbol:        Trading pair (e.g. 'BTCUSDT').
        side:          'BUY' or 'SELL'.
        order_type:    'MARKET', 'LIMIT', 'STOP_MARKET', or 'STOP'.
        quantity:      Order quantity.
        price:         Limit / stop-limit price (optional for MARKET).
        stop_price:    Trigger price for STOP / STOP_MARKET orders.
        time_in_force: 'GTC' (default), 'IOC', or 'FOK'.
        reduce_only:   Only reduce an open position.

    Returns:
        The raw API response dict on success, or None on failure.
    """
    # ── 1. Validate inputs ──────────────────────────────────────────────────
    try:
        validated = validate_order_params(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        print_error(f"Validation Error: {exc}")
        return None

    sym = validated["symbol"]
    sid = validated["side"]
    otype = validated["order_type"]
    qty = validated["quantity"]
    prc = validated["price"]
    sprc = validated["stop_price"]

    # ── 2. Print request summary ────────────────────────────────────────────
    print_order_summary(sym, sid, otype, qty, prc, sprc)

    # ── 3. Call the API ─────────────────────────────────────────────────────
    try:
        response = client.place_order(
            symbol=sym,
            side=sid,
            order_type=otype,
            quantity=qty,
            price=prc,
            stop_price=sprc,
            time_in_force=time_in_force,
            reduce_only=reduce_only,
        )
    except ValidationError as exc:
        logger.error("Validation error during order placement: %s", exc)
        print_error(f"Validation Error: {exc}")
        return None
    except BinanceAPIError as exc:
        logger.error("Binance API error: code=%s msg=%s", exc.code, exc.message)
        print_error(f"Binance API Error [{exc.code}]: {exc.message}")
        return None
    except NetworkError as exc:
        logger.error("Network error: %s", exc)
        print_error(f"Network Error: {exc}")
        return None
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Unexpected error while placing order: %s", exc)
        print_error(f"Unexpected Error: {exc}")
        return None

    # ── 4. Print response ───────────────────────────────────────────────────
    print_order_response(response)
    logger.debug("Full API response: %s", response)
    return response
