"""Logging helpers."""

from logging.config import dictConfig


def setup_logging(log_level: str) -> None:
    """Configure application logging."""
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": log_level,
                },
            },
            "root": {
                "handlers": ["default"],
                "level": log_level,
            },
        }
    )
