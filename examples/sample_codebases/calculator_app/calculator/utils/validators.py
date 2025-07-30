"""
Input validation utilities for the calculator app.
"""

from typing import List, Union, Dict, Any
from .exceptions import ValidationError


def validate_input(data: Dict[str, Any]) -> bool:
    """Validate input data for calculations."""
    if not isinstance(data, dict):
        raise ValidationError("Input must be a dictionary")
    
    # Check required fields
    if 'operation' not in data:
        raise ValidationError("Missing required field: operation")
    
    if 'operands' not in data:
        raise ValidationError("Missing required field: operands")
    
    # Validate operation
    operation = data['operation']
    if not isinstance(operation, str):
        raise ValidationError("Operation must be a string")
    
    if not operation.strip():
        raise ValidationError("Operation cannot be empty")
    
    # Validate operands
    operands = data['operands']
    if not isinstance(operands, list):
        raise ValidationError("Operands must be a list")
    
    if not operands:
        raise ValidationError("Operands list cannot be empty")
    
    # Validate each operand
    for i, operand in enumerate(operands):
        if not isinstance(operand, (int, float)):
            raise ValidationError(f"Operand {i} must be a number")
        
        if isinstance(operand, float) and (operand == float('inf') or operand == float('-inf')):
            raise ValidationError(f"Operand {i} cannot be infinite")
    
    return True


def validate_operation(operation: str) -> bool:
    """Validate a specific operation."""
    valid_operations = {
        'add', 'subtract', 'multiply', 'divide',
        'power', 'sqrt', 'log', 'sin', 'cos', 'tan'
    }
    
    if operation not in valid_operations:
        raise ValidationError(f"Invalid operation: {operation}")
    
    return True


def validate_operands_for_operation(operation: str, operands: List[Union[int, float]]) -> bool:
    """Validate operands for a specific operation."""
    if operation in ['add', 'subtract', 'multiply', 'divide']:
        if len(operands) < 2:
            raise ValidationError(f"{operation} requires at least 2 operands")
    
    elif operation in ['power']:
        if len(operands) != 2:
            raise ValidationError(f"{operation} requires exactly 2 operands")
    
    elif operation in ['sqrt', 'log', 'sin', 'cos', 'tan']:
        if len(operands) != 1:
            raise ValidationError(f"{operation} requires exactly 1 operand")
    
    return True


def validate_numeric_range(value: Union[int, float], min_value: float = None, max_value: float = None) -> bool:
    """Validate that a numeric value is within a specified range."""
    if min_value is not None and value < min_value:
        raise ValidationError(f"Value {value} is below minimum {min_value}")
    
    if max_value is not None and value > max_value:
        raise ValidationError(f"Value {value} is above maximum {max_value}")
    
    return True


def validate_calculation_id(calculation_id: str) -> bool:
    """Validate a calculation ID."""
    if not isinstance(calculation_id, str):
        raise ValidationError("Calculation ID must be a string")
    
    if not calculation_id.strip():
        raise ValidationError("Calculation ID cannot be empty")
    
    # Basic UUID format validation
    if len(calculation_id) != 36:
        raise ValidationError("Invalid calculation ID format")
    
    return True 