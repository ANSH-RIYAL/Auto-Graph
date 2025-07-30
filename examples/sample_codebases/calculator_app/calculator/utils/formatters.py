"""
Result formatting utilities for the calculator app.
"""

from typing import Union, Dict, Any
import math


def format_result(result: Union[int, float]) -> Union[int, float]:
    """Format calculation result for display."""
    if isinstance(result, int):
        return result
    
    # Handle special float values
    if math.isnan(result):
        return "NaN"
    
    if math.isinf(result):
        return "Infinity" if result > 0 else "-Infinity"
    
    # Round to reasonable precision
    if abs(result) < 1e-10:
        return 0.0
    
    # For very large or very small numbers, use scientific notation
    if abs(result) >= 1e6 or (abs(result) < 1e-6 and result != 0):
        return round(result, 6)
    
    # For regular numbers, round to 6 decimal places
    return round(result, 6)


def format_calculation_display(operation: str, operands: list, result: Union[int, float]) -> str:
    """Format a complete calculation for display."""
    operands_str = ', '.join(map(str, operands))
    formatted_result = format_result(result)
    
    return f"{operation}({operands_str}) = {formatted_result}"


def format_error_message(error: str) -> str:
    """Format error messages for display."""
    return f"Error: {error}"


def format_history_entry(calculation: Dict[str, Any]) -> str:
    """Format a history entry for display."""
    operation = calculation.get('operation', 'unknown')
    operands = calculation.get('operands', [])
    result = calculation.get('result', 'unknown')
    timestamp = calculation.get('timestamp', 'unknown')
    
    operands_str = ', '.join(map(str, operands))
    formatted_result = format_result(result)
    
    return f"[{timestamp}] {operation}({operands_str}) = {formatted_result}"


def format_statistics(stats: Dict[str, Any]) -> str:
    """Format statistics for display."""
    lines = []
    lines.append("Calculation Statistics:")
    lines.append(f"  Total calculations: {stats.get('total_calculations', 0)}")
    
    operations_count = stats.get('operations_count', {})
    if operations_count:
        lines.append("  Operations breakdown:")
        for operation, count in sorted(operations_count.items()):
            lines.append(f"    {operation}: {count}")
    
    date_range = stats.get('date_range')
    if date_range:
        earliest = date_range.get('earliest')
        latest = date_range.get('latest')
        if earliest and latest:
            lines.append(f"  Date range: {earliest} to {latest}")
    
    return '\n'.join(lines) 