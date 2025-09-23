#!/usr/bin/env python3
"""
Centralized logging configuration for the Stock Data Fetcher application.

This module provides a unified logging setup that supports:
- Configurable log levels via environment variables
- Rotating log files
- Console and file handlers
- Web server log capture for the /logs endpoint
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional
from io import StringIO
import threading


class RotatingStringIOHandler(logging.Handler):
    """Custom handler that stores log records in a rotating string buffer."""
    
    def __init__(self, max_lines: int = 1000):
        super().__init__()
        self.max_lines = max_lines
        self.lines = []
        self.lock = threading.RLock()
    
    def emit(self, record):
        try:
            msg = self.format(record)
            with self.lock:
                self.lines.append(msg)
                if len(self.lines) > self.max_lines:
                    # Keep only the last max_lines entries
                    self.lines = self.lines[-self.max_lines:]
        except Exception:
            self.handleError(record)
    
    def get_logs(self) -> str:
        """Get all stored logs as a single string."""
        with self.lock:
            return '\n'.join(self.lines)
    
    def clear(self):
        """Clear all stored logs."""
        with self.lock:
            self.lines.clear()


# Global handler instance for web log capture
_web_log_handler: Optional[RotatingStringIOHandler] = None


def setup_logging(
    logger_name: str = 'stocks_app',
    log_level: Optional[str] = None,
    enable_file_logging: bool = True,
    log_file_path: str = 'stocks_app.log',
    enable_web_capture: bool = False
) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        logger_name: Name of the logger to create/configure
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If None, will use LOG_LEVEL environment variable, defaulting to INFO
        enable_file_logging: Whether to enable file logging
        log_file_path: Path to log file (only used if enable_file_logging=True)
        enable_web_capture: Whether to enable web log capture for /logs endpoint
    
    Returns:
        Configured logger instance
    """
    global _web_log_handler
    
    # Determine log level
    if log_level is None:
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Get or create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file_logging:
        try:
            # Create logs directory if it doesn't exist
            log_dir = os.path.dirname(log_file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails, just log to console
            logger.warning(f"Failed to setup file logging: {e}")
    
    # Web capture handler (for /logs endpoint)
    if enable_web_capture:
        _web_log_handler = RotatingStringIOHandler(max_lines=1000)
        _web_log_handler.setLevel(numeric_level)
        _web_log_handler.setFormatter(formatter)
        logger.addHandler(_web_log_handler)
    
    return logger


def get_web_logs() -> str:
    """Get captured logs for the web /logs endpoint."""
    if _web_log_handler:
        return _web_log_handler.get_logs()
    return "No logs available - web capture not enabled"


def clear_web_logs():
    """Clear captured web logs."""
    if _web_log_handler:
        _web_log_handler.clear()


def get_logger(name: str = 'stocks_app') -> logging.Logger:
    """
    Get a logger instance. If the main logger hasn't been set up yet,
    this will set it up with default configuration.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If no handlers have been set up, do basic setup
    if not logger.handlers:
        setup_logging(logger_name=name)
    
    return logger