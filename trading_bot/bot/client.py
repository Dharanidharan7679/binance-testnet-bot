"""
Binance Futures Testnet API client wrapper.
Handles authentication, request signing, and all HTTP communication.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .logging_config import setup_logger

logger = setup_logger("trading_bot.client")

# ── Constants ────────────────────────────────────────────────────────────────

BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000          # Milliseconds the request stays valid
REQUEST_TIMEOUT = 10        # Seconds before requests.get/post times out


# ── Custom Exceptions ────────────────────────────────────────────────────────


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error [{code}]: {message}")


class NetworkError(Exception):
    """Raised on network-level failures (timeouts, connection errors)."""


# ── Client ───────────────────────────────────────────────────────────────────


class BinanceFuturesClient:
    """
    Thin wrapper around the Binance Futures Testnet REST API.

    Responsibilities
    ----------------
    * HMAC-SHA256 request signing
    * Automatic timestamp injection
    * Centralised error handling and logging
    * Retry-free, fail-fast design (caller decides on retry logic)
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL) -> None:
        """
        Initialise the client.

        Args:
            api_key:    Your Binance Futures Testnet API key.
            api_secret: Your Binance Futures Testnet API secret.
            base_url:   Base URL (defaults to testnet).
        """
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")

        self._api_key = api_key
        self._api_secret = api_secret
        self.base_url = base_url.rstrip("/")

        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.info("BinanceFuturesClient initialised. Base URL: %s", self.base_url)

    # ── Private helpers ──────────────────────────────────────────────────────

    def _sign(self, params: Dict[str, Any]) -> str:
        """Generate HMAC-SHA256 signature for the given parameter dict."""
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _timestamp(self) -> int:
        """Return current UTC time in milliseconds."""
        return int(time.time() * 1000)

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse the HTTP response and raise on API or HTTP errors.

        Args:
            response: The raw requests.Response object.

        Returns:
            Parsed JSON dict.

        Raises:
            BinanceAPIError: On Binance-level errors (non-zero 'code').
            NetworkError: On unexpected HTTP status codes.
        """
        logger.debug(
            "HTTP %s  %s  body=%s",
            response.status_code,
            response.url,
            response.text[:500],
        )

        if response.status_code == 200:
            data = response.json()
            # Binance sometimes embeds errors in a 200 response
            if isinstance(data, dict) and data.get("code", 0) < 0:
                raise BinanceAPIError(data["code"], data.get("msg", "Unknown error"))
            return data

        # Try to decode a JSON error body
        try:
            err = response.json()
            raise BinanceAPIError(err.get("code", response.status_code), err.get("msg", response.text))
        except (ValueError, KeyError):
            raise NetworkError(
                f"Unexpected HTTP {response.status_code}: {response.text[:200]}"
            )

    # ── Public API methods ───────────────────────────────────────────────────

    def get_server_time(self) -> int:
        """
        Fetch Binance server time (useful for debugging clock skew).

        Returns:
            Server time in milliseconds.
        """
        url = f"{self.base_url}/fapi/v1/time"
        logger.debug("GET %s", url)
        try:
            resp = self._session.get(url, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout:
            raise NetworkError("Request timed out while fetching server time.")
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError(f"Connection error: {exc}") from exc

        data = self._handle_response(resp)
        return data["serverTime"]

    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve exchange information, optionally filtered by symbol.

        Args:
            symbol: Trading pair (e.g. 'BTCUSDT'). None returns all.

        Returns:
            Exchange info dict from the API.
        """
        url = f"{self.base_url}/fapi/v1/exchangeInfo"
        params: Dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol.upper()
        logger.debug("GET %s  params=%s", url, params)
        try:
            resp = self._session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout:
            raise NetworkError("Request timed out while fetching exchange info.")
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError(f"Connection error: {exc}") from exc

        return self._handle_response(resp)

    def get_account_info(self) -> Dict[str, Any]:
        """
        Retrieve futures account details (balance, positions, etc.).

        Returns:
            Account info dict.
        """
        url = f"{self.base_url}/fapi/v2/account"
        params: Dict[str, Any] = {
            "timestamp": self._timestamp(),
            "recvWindow": RECV_WINDOW,
        }
        params["signature"] = self._sign(params)

        logger.debug("GET %s  params=%s", url, {k: v for k, v in params.items() if k != "signature"})
        try:
            resp = self._session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout:
            raise NetworkError("Request timed out while fetching account info.")
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError(f"Connection error: {exc}") from exc

        return self._handle_response(resp)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Place a new futures order on the testnet.

        Args:
            symbol:        Trading pair (e.g. 'BTCUSDT').
            side:          'BUY' or 'SELL'.
            order_type:    'MARKET', 'LIMIT', 'STOP_MARKET', or 'STOP'.
            quantity:      Number of contracts / coin amount.
            price:         Limit price (required for LIMIT / STOP).
            stop_price:    Trigger price (required for STOP / STOP_MARKET).
            time_in_force: 'GTC', 'IOC', or 'FOK' (LIMIT orders only).
            reduce_only:   If True, only reduce an existing position.

        Returns:
            Order response dict from the API.

        Raises:
            BinanceAPIError: On API-level errors.
            NetworkError:    On connection / timeout failures.
        """
        url = f"{self.base_url}/fapi/v1/order"

        params: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
            "timestamp": self._timestamp(),
            "recvWindow": RECV_WINDOW,
        }

        if order_type.upper() == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        if order_type.upper() == "STOP":
            params["price"] = price
            params["stopPrice"] = stop_price
            params["timeInForce"] = time_in_force

        if order_type.upper() == "STOP_MARKET":
            params["stopPrice"] = stop_price

        if reduce_only:
            params["reduceOnly"] = "true"

        params["signature"] = self._sign(params)

        logger.info(
            "Placing order → symbol=%s side=%s type=%s qty=%s price=%s stopPrice=%s",
            symbol,
            side,
            order_type,
            quantity,
            price,
            stop_price,
        )
        logger.debug("POST %s  payload=%s", url, {k: v for k, v in params.items() if k != "signature"})

        try:
            resp = self._session.post(url, data=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout:
            raise NetworkError("Request timed out while placing order.")
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError(f"Connection error while placing order: {exc}") from exc

        result = self._handle_response(resp)
        logger.info("Order placed successfully. orderId=%s status=%s", result.get("orderId"), result.get("status"))
        return result

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Query a specific order by its ID.

        Args:
            symbol:   Trading pair.
            order_id: Binance-assigned order ID.

        Returns:
            Order detail dict.
        """
        url = f"{self.base_url}/fapi/v1/order"
        params: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "orderId": order_id,
            "timestamp": self._timestamp(),
            "recvWindow": RECV_WINDOW,
        }
        params["signature"] = self._sign(params)

        logger.debug("GET %s  orderId=%s", url, order_id)
        try:
            resp = self._session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout:
            raise NetworkError("Request timed out while fetching order.")
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError(f"Connection error: {exc}") from exc

        return self._handle_response(resp)

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel an open order.

        Args:
            symbol:   Trading pair.
            order_id: Binance-assigned order ID.

        Returns:
            Cancellation response dict.
        """
        url = f"{self.base_url}/fapi/v1/order"
        params: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "orderId": order_id,
            "timestamp": self._timestamp(),
            "recvWindow": RECV_WINDOW,
        }
        params["signature"] = self._sign(params)

        logger.info("Cancelling order → symbol=%s orderId=%s", symbol, order_id)
        try:
            resp = self._session.delete(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout:
            raise NetworkError("Request timed out while cancelling order.")
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError(f"Connection error: {exc}") from exc

        result = self._handle_response(resp)
        logger.info("Order cancelled. orderId=%s status=%s", result.get("orderId"), result.get("status"))
        return result
