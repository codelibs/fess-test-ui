"""
Logging configuration for Fess UI test suite.

Environment Variables:
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FILE: Enable file logging (true/false)
    LOG_DIR: Directory for log files (default: logs)
"""

import logging
import os
from datetime import datetime
from typing import Optional


def setup_logging(
    log_level: Optional[str] = None,
    enable_file_logging: Optional[bool] = None,
    log_dir: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the test suite.

    Args:
        log_level: Override LOG_LEVEL env var
        enable_file_logging: Override LOG_FILE env var
        log_dir: Override LOG_DIR env var

    Returns:
        Root logger instance
    """
    # Get configuration from environment with fallbacks
    level_str = log_level or os.environ.get('LOG_LEVEL', 'INFO').upper()
    file_logging = enable_file_logging if enable_file_logging is not None \
        else os.environ.get('LOG_FILE', 'false').lower() == 'true'
    log_directory = log_dir or os.environ.get('LOG_DIR', 'logs')

    # Map string to logging level
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    level = level_map.get(level_str, logging.INFO)

    # Create formatters
    console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    file_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

    console_formatter = logging.Formatter(console_format)
    file_formatter = logging.Formatter(file_format)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    log_file_path = None
    if file_logging:
        os.makedirs(log_directory, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file_path = os.path.join(log_directory, f'test_run_{timestamp}.log')

        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always DEBUG for file
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        root_logger.info(f"File logging enabled: {log_file_path}")

    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)

    # Log configuration summary
    root_logger.debug(f"Logging configured: level={level_str}, file_logging={file_logging}")

    return root_logger


def get_module_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module with consistent naming.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
