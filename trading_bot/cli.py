"""
PrimeTrade Bot — CLI entry point.

Usage examples:
    # Market buy
    python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

    # Limit sell
    python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 95000

    # Stop-Limit buy
    python cli.py place-order --symbol BTCUSDT --side BUY --type STOP --quantity 0.01 --price 86000 --stop-price 85500

    # Stop-Market sell
    python cli.py place-order --symbol ETHUSDT --side SELL --type STOP_MARKET --quantity 0.1 --stop-price 2500

    # Check account balance
    python cli.py account

    # Check server connectivity
    python cli.py ping
"""

from __future__ import annotations

import os
import sys
import argparse
from typing import Optional

from dotenv import load_dotenv

from bot.client import BinanceFuturesClient, BinanceAPIError, NetworkError
from bot.orders import place_order, print_error, DIVIDER
from bot.validators import ValidationError
from bot.logging_config import setup_logger

logger = setup_logger("trading_bot.cli")

# ── Load environment variables from .env ─────────────────────────────────────
load_dotenv()


def _get_client() -> BinanceFuturesClient:
    """Read credentials from environment and return an authenticated client."""
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print_error(
            "API credentials not found.\n"
            "  Please set BINANCE_API_KEY and BINANCE_API_SECRET in your .env file\n"
            "  or as environment variables."
        )
        logger.critical("Missing API credentials. Exiting.")
        sys.exit(1)

    return BinanceFuturesClient(api_key=api_key, api_secret=api_secret)


# ── Subcommand handlers ───────────────────────────────────────────────────────


def cmd_ping(args: argparse.Namespace) -> None:
    """Ping the testnet to verify connectivity."""
    client = _get_client()
    print(f"\n{DIVIDER}")
    print("  🌐  CONNECTIVITY CHECK")
    print(DIVIDER)
    try:
        server_time = client.get_server_time()
        print(f"  Testnet URL  : {client.base_url}")
        print(f"  Server Time  : {server_time} ms")
        print(f"  Status       : ✅ Connected")
        logger.info("Ping successful. serverTime=%s", server_time)
    except (BinanceAPIError, NetworkError) as exc:
        print(f"  Status       : ❌ Failed — {exc}")
        logger.error("Ping failed: %s", exc)
    print(DIVIDER + "\n")


def cmd_account(args: argparse.Namespace) -> None:
    """Display futures account balance summary."""
    client = _get_client()
    print(f"\n{DIVIDER}")
    print("  💰  ACCOUNT SUMMARY")
    print(DIVIDER)
    try:
        info = client.get_account_info()
        print(f"  Total Wallet Balance  : {info.get('totalWalletBalance', 'N/A')} USDT")
        print(f"  Available Balance     : {info.get('availableBalance', 'N/A')} USDT")
        print(f"  Total Unrealised PnL  : {info.get('totalUnrealizedProfit', 'N/A')} USDT")
        print(f"  Total Margin Balance  : {info.get('totalMarginBalance', 'N/A')} USDT")
        print(f"  Can Trade             : {info.get('canTrade', False)}")
        logger.info("Account info fetched successfully.")
    except (BinanceAPIError, NetworkError) as exc:
        print(f"  Error: {exc}")
        logger.error("Account fetch failed: %s", exc)
    print(DIVIDER + "\n")


def cmd_place_order(args: argparse.Namespace) -> None:
    """Place a new futures order."""
    client = _get_client()
    place_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.type,
        quantity=args.quantity,
        price=args.price,
        stop_price=args.stop_price,
        time_in_force=args.time_in_force,
        reduce_only=args.reduce_only,
    )


def cmd_query_order(args: argparse.Namespace) -> None:
    """Query the status of an existing order."""
    client = _get_client()
    print(f"\n{DIVIDER}")
    print("  🔍  ORDER QUERY")
    print(DIVIDER)
    try:
        order = client.get_order(symbol=args.symbol, order_id=args.order_id)
        print(f"  Order ID     : {order.get('orderId')}")
        print(f"  Symbol       : {order.get('symbol')}")
        print(f"  Side         : {order.get('side')}")
        print(f"  Type         : {order.get('type')}")
        print(f"  Status       : {order.get('status')}")
        print(f"  Quantity     : {order.get('origQty')}")
        print(f"  Executed Qty : {order.get('executedQty')}")
        print(f"  Avg Price    : {order.get('avgPrice')}")
        logger.info("Order query successful. orderId=%s", args.order_id)
    except (BinanceAPIError, NetworkError) as exc:
        print(f"  Error: {exc}")
        logger.error("Order query failed: %s", exc)
    print(DIVIDER + "\n")


def cmd_cancel_order(args: argparse.Namespace) -> None:
    """Cancel an open order."""
    client = _get_client()
    print(f"\n{DIVIDER}")
    print("  🗑️   CANCEL ORDER")
    print(DIVIDER)
    try:
        result = client.cancel_order(symbol=args.symbol, order_id=args.order_id)
        print(f"  Order ID : {result.get('orderId')}")
        print(f"  Status   : {result.get('status')}")
        print(f"  ✅  Order cancelled successfully.")
        logger.info("Order cancelled. orderId=%s", args.order_id)
    except (BinanceAPIError, NetworkError) as exc:
        print(f"  Error: {exc}")
        logger.error("Order cancel failed: %s", exc)
    print(DIVIDER + "\n")


# ── Argument parser ───────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="primetrade",
        description=(
            "PrimeTrade Bot — Binance Futures Testnet CLI\n"
            "Place, query, and cancel futures orders on the USDT-M testnet."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python cli.py ping\n"
            "  python cli.py account\n"
            "  python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01\n"
            "  python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 95000\n"
            "  python cli.py place-order --symbol BTCUSDT --side BUY --type STOP --quantity 0.01 --price 86000 --stop-price 85500\n"
            "  python cli.py query-order --symbol BTCUSDT --order-id 123456789\n"
            "  python cli.py cancel-order --symbol BTCUSDT --order-id 123456789\n"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # ── ping ──────────────────────────────────────────────────────────────
    subparsers.add_parser(
        "ping",
        help="Check connectivity to the Binance Futures Testnet.",
    )

    # ── account ───────────────────────────────────────────────────────────
    subparsers.add_parser(
        "account",
        help="Display your futures account balance and margin info.",
    )

    # ── place-order ───────────────────────────────────────────────────────
    po = subparsers.add_parser(
        "place-order",
        help="Place a new futures order (MARKET, LIMIT, STOP_MARKET, STOP).",
    )
    po.add_argument(
        "--symbol", "-s",
        required=True,
        metavar="SYMBOL",
        help="Trading pair, e.g. BTCUSDT",
    )
    po.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        metavar="SIDE",
        help="Order side: BUY or SELL",
    )
    po.add_argument(
        "--type", "-t",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET", "STOP"],
        metavar="TYPE",
        dest="type",
        help="Order type: MARKET | LIMIT | STOP_MARKET | STOP",
    )
    po.add_argument(
        "--quantity", "-q",
        required=True,
        type=float,
        metavar="QTY",
        help="Order quantity (number of contracts/coins)",
    )
    po.add_argument(
        "--price", "-p",
        type=float,
        default=None,
        metavar="PRICE",
        help="Limit price (required for LIMIT and STOP order types)",
    )
    po.add_argument(
        "--stop-price",
        type=float,
        default=None,
        metavar="STOP_PRICE",
        dest="stop_price",
        help="Stop/trigger price (required for STOP and STOP_MARKET)",
    )
    po.add_argument(
        "--time-in-force",
        default="GTC",
        choices=["GTC", "IOC", "FOK"],
        dest="time_in_force",
        help="Time in force for LIMIT orders (default: GTC)",
    )
    po.add_argument(
        "--reduce-only",
        action="store_true",
        default=False,
        dest="reduce_only",
        help="Mark order as reduce-only (will only reduce open position)",
    )

    # ── query-order ───────────────────────────────────────────────────────
    qo = subparsers.add_parser(
        "query-order",
        help="Query the status of an existing order by ID.",
    )
    qo.add_argument("--symbol", "-s", required=True, metavar="SYMBOL")
    qo.add_argument("--order-id", required=True, type=int, dest="order_id", metavar="ORDER_ID")

    # ── cancel-order ──────────────────────────────────────────────────────
    co = subparsers.add_parser(
        "cancel-order",
        help="Cancel an open order by ID.",
    )
    co.add_argument("--symbol", "-s", required=True, metavar="SYMBOL")
    co.add_argument("--order-id", required=True, type=int, dest="order_id", metavar="ORDER_ID")

    return parser


# ── Dispatch ──────────────────────────────────────────────────────────────────

COMMAND_HANDLERS = {
    "ping": cmd_ping,
    "account": cmd_account,
    "place-order": cmd_place_order,
    "query-order": cmd_query_order,
    "cancel-order": cmd_cancel_order,
}


def main() -> None:
    """Main entry point — parse args and dispatch to the appropriate handler."""
    parser = build_parser()
    args = parser.parse_args()
    logger.info("Command received: %s", args.command)

    handler = COMMAND_HANDLERS.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
