import logging
import sys

# Global logger instance
_logger = None

def configure_logging(verbose=False):
    """Configure the application logger."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger('aws_inventory_scan')
    logger.setLevel(log_level)

    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Store the configured logger
    global _logger
    _logger = logger

    return logger

def get_logger():
    """Get the configured logger."""
    global _logger
    if _logger is None:
        _logger = configure_logging(False)
    return _logger