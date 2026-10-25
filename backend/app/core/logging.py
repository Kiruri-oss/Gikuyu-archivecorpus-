import logging
import sys


def configure_logging(debug: bool = False) -> None:
    """Configure application logging for development and production."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a standard-library logger for the requested module."""
    return logging.getLogger(name)
