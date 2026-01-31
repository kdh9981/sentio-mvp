"""
Sentio MVP - Logging Configuration

Sets up consistent logging across all modules with:
- File handler for persistent logs
- Console handler for real-time feedback
- Configurable log level from config.yaml
"""

import logging
import os
from pathlib import Path
import yaml


def setup_logging(config_path='config.yaml'):
    """
    Setup logging from configuration file.

    Args:
        config_path: Path to config.yaml (relative to project root)

    Returns:
        logging.Logger: Configured logger for 'sentio' namespace
    """
    # Find config file relative to this file's location
    project_root = Path(__file__).parent.parent
    config_file = project_root / config_path

    # Load config
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        log_config = config.get('logging', {})
    else:
        # Fallback defaults if no config
        log_config = {
            'level': 'INFO',
            'file': 'logs/sentio_analysis.log',
            'format': '%(asctime)s - %(levelname)s - %(message)s'
        }

    # Get configuration values
    log_level_str = log_config.get('level', 'INFO')
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    log_file = project_root / log_config.get('file', 'logs/sentio_analysis.log')
    log_format = log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s')

    # Create logs directory if needed
    log_dir = log_file.parent
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Get or create the sentio logger
    logger = logging.getLogger('sentio')
    logger.setLevel(log_level)

    # Clear any existing handlers
    logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    logger.info(f"Logging initialized: level={log_level_str}, file={log_file}")
    return logger


def get_logger(name='sentio'):
    """
    Get a logger instance.

    Args:
        name: Logger name (will be prefixed with 'sentio.' if not already)

    Returns:
        logging.Logger: Logger instance
    """
    if not name.startswith('sentio'):
        name = f'sentio.{name}'
    return logging.getLogger(name)
