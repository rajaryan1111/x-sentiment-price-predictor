"""Minimal structured logging setup; never log credential values or full secret headers."""
import logging


def get_logger(component: str) -> logging.Logger:
    return logging.getLogger(f"xsentiment.{component}")
