"""
Input validation for PrimeTrade Bot.
Validates all user-supplied CLI parameters before any API call is made.
"""

from __future__ import annotations

from typing import Optional

from .logging_config import setup_logger

logger = setup_logger("trading_bot.validators")

# ── Constants ───────────────────────────────────────────────────────────────

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET", "STOP"}
MIN_QUANTITY = 0.001
MIN_PRICE = 0.01


class ValidationError(ValueError):
    """Raised when input validation fails."""


# ── Individual validators ────────────────────────────────────────────────────


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalise the trading symbol.

    Args:
        symbol: e.g. 'btcusdt' or 'BTCUSDT'

    Returns:
        Upper-cased symbol string.

    Raises:
        ValidationError: If symbol is empty or contains invalid characters.
    """
    if not symbol or not symbol.strip():
        raise ValidationError("Symbol cannot be empty.")

    cleaned = symbol.strip().upper()

    if not cleaned.isalpha():
        raise ValidationError(
            f"Symbol '{cleaned}' must contain only alphabetic characters (e.g. BTCUSDT)."
        )

    if len(cleaned) < 5:
        raise ValidationError(
            f"Symbol '{cleaned}' looks too short. Expected something like 'BTCUSDT'."
        )

    logger.debug("Symbol validated: %s", cleaned)
    return cleaned


def validate_side(side: str) -> str:
    """
    Validate the order side.

    Args:
        side: 'BUY' or 'SELL' (case-insensitive)

    Returns:
        Upper-cased side string.

    Raises:
        ValidationError: If side is not BUY or SELL.
    """
    cleaned = side.strip().upper()
    if cleaned not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{cleaned}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    logger.debug("Side validated: %s", cleaned)
    return cleaned


def validate_order_type(order_type: str) -> str:
    """
    Validate the order type.

    Args:
        order_type: e.g. 'MARKET', 'LIMIT', 'STOP_MARKET', 'STOP'

    Returns:
        Upper-cased order type string.

    Raises:
        ValidationError: If order_type is not recognised.
    """
    cleaned = order_type.strip().upper()
    if cleaned not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{cleaned}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    logger.debug("Order type validated: %s", cleaned)
    return cleaned


def validate_quantity(quantity: float) -> float:
    """
    Validate the order quantity.

    Args:
        quantity: Positive numeric quantity.

    Returns:
        Validated quantity as float.

    Raises:
        ValidationError: If quantity is not positive.
    """
    if quantity <= 0:
        raise ValidationError(f"Quantity must be positive. Got: {quantity}.")
    if quantity < MIN_QUANTITY:
        raise ValidationError(
            f"Quantity {quantity} is below the minimum allowed ({MIN_QUANTITY})."
        )
    logger.debug("Quantity validated: %s", quantity)
    return float(quantity)


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    """
    Validate the price parameter against the order type.

    Args:
        price: Price value (may be None for MARKET orders).
        order_type: The validated order type string.

    Returns:
        Validated price as float, or None for MARKET orders.

    Raises:
        ValidationError: If price rules are violated.
    """
    if order_type in {"LIMIT", "STOP"}:
        if price is None:
            raise ValidationError(
                f"Price is required for {order_type} orders."
            )
        if price < MIN_PRICE:
            raise ValidationError(
                f"Price {price} is below the minimum allowed ({MIN_PRICE})."
            )
        logger.debug("Price validated: %s", price)
        return float(price)

    # MARKET / STOP_MARKET — price should not be supplied
    if price is not None:
        logger.warning(
            "Price was provided for a %s order and will be ignored.", order_type
        )
    return None


def validate_stop_price(stop_price: Optional[float], order_type: str) -> Optional[float]:
    """
    Validate stop price for STOP / STOP_MARKET orders.

    Args:
        stop_price: Trigger price value.
        order_type: The validated order type string.

    Returns:
        Validated stop price as float, or None if not applicable.

    Raises:
        ValidationError: If stop_price is required but missing.
    """
    if order_type in {"STOP", "STOP_MARKET"}:
        if stop_price is None:
            raise ValidationError(
                f"--stop-price is required for {order_type} orders."
            )
        if stop_price < MIN_PRICE:
            raise ValidationError(
                f"Stop price {stop_price} is below the minimum allowed ({MIN_PRICE})."
            )
        logger.debug("Stop price validated: %s", stop_price)
        return float(stop_price)
    return None


# ── Composite validator (validates a full order payload) ─────────────────────


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> dict:
    """
    Validate all order parameters together and return a clean dict.

    Returns:
        Dictionary with validated, normalised values.

    Raises:
        ValidationError: On any invalid input.
    """
    validated = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
    }
    validated["quantity"] = validate_quantity(quantity)
    validated["price"] = validate_price(price, validated["order_type"])
    validated["stop_price"] = validate_stop_price(stop_price, validated["order_type"])

    logger.info(
        "Order params validated: symbol=%s side=%s type=%s qty=%s price=%s stop_price=%s",
        validated["symbol"],
        validated["side"],
        validated["order_type"],
        validated["quantity"],
        validated["price"],
        validated["stop_price"],
    )
    return validated
