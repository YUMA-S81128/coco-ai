import logging
import sys
from functools import lru_cache


@lru_cache
def setup_logging():
    """
    Configures the basic logging settings for the application.

    This function sets the logging level to INFO and formats log messages to
    include a timestamp, log level, logger name, and the message. It should be
    called once at application startup.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
        stream=sys.stdout,
    )


def get_logger(name: str) -> logging.Logger:
    """Retrieves a logger instance with the specified name."""
    return logging.getLogger(name)
