#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
Logging configuration for AWS inventory scan.
"""

import logging
import sys
import os
import json
from typing import Optional, Dict, Any, Union
from datetime import datetime

# Global logger instance
_logger = None

# Log levels mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

class StructuredLogFormatter(logging.Formatter):
    """Formatter for structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

def configure_logging(verbose: bool = False, log_file: Optional[str] = None, 
                     log_format: Optional[str] = None, structured: bool = False,
                     log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure the application logger.
    
    Args:
        verbose: Whether to enable verbose logging (DEBUG level)
        log_file: Path to log file (None for console logging)
        log_format: Format string for log messages
        structured: Whether to use structured JSON logging
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger
    """
    # Determine log level
    if log_level and log_level.upper() in LOG_LEVELS:
        level = LOG_LEVELS[log_level.upper()]
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    # Create logger
    logger = logging.getLogger('aws_inventory_scan')
    logger.setLevel(level)
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Default format
    if not log_format:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create formatter
    if structured:
        formatter = StructuredLogFormatter()
    else:
        formatter = logging.Formatter(log_format)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Store the configured logger
    global _logger
    _logger = logger
    
    return logger

def get_logger() -> logging.Logger:
    """
    Get the configured logger.
    
    Returns:
        Configured logger
    """
    global _logger
    if _logger is None:
        # Try to get configuration from config module
        try:
            from config import get_logging_config
            config = get_logging_config()
            return configure_logging(
                verbose=False,
                log_file=config.get("log_file", ""),
                log_format=config.get("log_format", None),
                structured=config.get("structured", False),
                log_level=config.get("log_level", "INFO")
            )
        except ImportError:
            # Fall back to default configuration
            _logger = configure_logging(False)
    
    return _logger

def log_with_context(level: str, message: str, **context: Any) -> None:
    """
    Log a message with additional context.
    
    Args:
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **context: Additional context fields to include in the log
    """
    logger = get_logger()
    
    # Get the log method based on level
    log_method = getattr(logger, level.lower(), logger.info)
    
    # Create a log record with extra context
    extra = {"extra": context}
    log_method(message, extra=extra)
