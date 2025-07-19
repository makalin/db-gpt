"""
Logging utility for DB-GPT
"""

import logging
import logging.handlers
import os
from typing import Dict, Any


def setup_logging(config: Dict[str, Any]) -> None:
    """Setup logging configuration"""
    log_level = getattr(logging, config.get('level', 'INFO').upper())
    log_file = config.get('file', 'db_gpt.log')
    max_size = config.get('max_size', '10MB')
    backup_count = config.get('backup_count', 5)
    
    # Convert max_size to bytes
    if isinstance(max_size, str):
        if max_size.endswith('MB'):
            max_size = int(max_size[:-2]) * 1024 * 1024
        elif max_size.endswith('KB'):
            max_size = int(max_size[:-2]) * 1024
        else:
            max_size = int(max_size)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logging.info(f"Logging setup complete. Level: {log_level}, File: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name) 