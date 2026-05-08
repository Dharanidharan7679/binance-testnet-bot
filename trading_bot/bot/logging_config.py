"""
Logging configuration for PrimeTrade Bot.
Sets up both file and console handlers with structured formatting.
"""

import logging
import os
from datetime import datetime


LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"trading_bot_{datetime.now().strftime('%Y%m%d')}.log")


def setup_logger(name: str = "trading_bot") -> logging.Logger:
    """
    Set up and return a configured logger.

    Args:
        name: Logger name (default: 'trading_bot')

    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── File handler (DEBUG level, full detail) ─────────────────────────────
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    # ── Console handler (WARNING and above, clean output) ───────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(
        fmt="[%(levelname)s] %(message)s",
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Module-level logger instance
logger = setup_logger()
