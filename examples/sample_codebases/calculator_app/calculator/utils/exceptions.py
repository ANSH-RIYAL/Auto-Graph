"""
Custom exceptions for the calculator app.
"""


class CalculationError(Exception):
    """Base exception for calculation errors."""
    pass


class ValidationError(Exception):
    """Exception for validation errors."""
    pass


class HistoryError(Exception):
    """Exception for history-related errors."""
    pass 