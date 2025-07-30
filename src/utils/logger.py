"""
Logging configuration for AutoGraph.
Provides structured logging with different levels and output formats.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class AutoGraphLogger:
    """Custom logger for AutoGraph with structured logging capabilities."""
    
    def __init__(self, name: str = "autograph", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Add handlers
        self._setup_console_handler()
        self._setup_file_handler()
        self._setup_error_handler()
    
    def _setup_console_handler(self):
        """Setup console handler for INFO and above."""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """Setup file handler for all levels with rotation."""
        log_file = self.log_dir / f"{self.name}.log"
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(file_handler)
    
    def _setup_error_handler(self):
        """Setup separate error file handler."""
        error_file = self.log_dir / f"{self.name}_errors.log"
        
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        
        # Create formatter
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
            'Exception: %(exc_info)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)
    
    def log_analysis_start(self, codebase_path: str):
        """Log the start of codebase analysis."""
        self.info(f"Starting analysis of codebase: {codebase_path}")
    
    def log_analysis_complete(self, stats: dict):
        """Log the completion of codebase analysis."""
        self.info(f"Analysis complete. Statistics: {stats}")
    
    def log_file_processed(self, file_path: str, success: bool, error: Optional[str] = None):
        """Log file processing result."""
        if success:
            self.debug(f"Successfully processed: {file_path}")
        else:
            self.warning(f"Failed to process: {file_path} - {error}")
    
    def log_parsing_error(self, file_path: str, error: str):
        """Log parsing errors."""
        self.error(f"Parsing error in {file_path}: {error}")
    
    def log_graph_validation(self, issues: list):
        """Log graph validation results."""
        if issues:
            self.warning(f"Graph validation found {len(issues)} issues:")
            for issue in issues:
                self.warning(f"  - {issue}")
        else:
            self.info("Graph validation passed - no issues found")


# Global logger instance
logger = AutoGraphLogger()


def get_logger(name: str = None) -> AutoGraphLogger:
    """Get a logger instance."""
    if name:
        return AutoGraphLogger(name)
    return logger 