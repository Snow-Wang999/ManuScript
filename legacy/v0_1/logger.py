# -*- coding: utf-8 -*-
"""
ManuScript v0.1 Logger Configuration
"""
import logging
import sys
from pathlib import Path
from config import config

# Log directory
LOG_DIR = Path(__file__).parent.parent / "logs" / "v0_1"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """Get configured logger"""
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))

    # Format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | v0.1 | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File output
    file_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
