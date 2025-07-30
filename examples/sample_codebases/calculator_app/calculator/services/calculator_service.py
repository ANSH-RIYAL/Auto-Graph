"""
Calculator service for performing mathematical operations.
"""

import math
from typing import List, Union, Optional
from ..utils.exceptions import CalculationError


class CalculatorService:
    """Service for performing mathematical calculations."""
    
    def __init__(self):
        self.supported_operations = {
            'add': self._add,
            'subtract': self._subtract,
            'multiply': self._multiply,
            'divide': self._divide,
            'power': self._power,
            'sqrt': self._sqrt,
            'log': self._log,
            'sin': self._sin,
            'cos': self._cos,
            'tan': self._tan
        }
    
    def calculate(self, operation: str, operands: List[Union[int, float]]) -> Union[int, float]:
        """Perform a calculation based on operation and operands."""
        if operation not in self.supported_operations:
            raise CalculationError(f"Unsupported operation: {operation}")
        
        try:
            return self.supported_operations[operation](operands)
        except Exception as e:
            raise CalculationError(f"Calculation failed: {str(e)}")
    
    def _add(self, operands: List[Union[int, float]]) -> Union[int, float]:
        """Add multiple numbers."""
        if len(operands) < 2:
            raise CalculationError("Addition requires at least 2 operands")
        
        result = operands[0]
        for operand in operands[1:]:
            result += operand
        return result
    
    def _subtract(self, operands: List[Union[int, float]]) -> Union[int, float]:
        """Subtract numbers from the first operand."""
        if len(operands) < 2:
            raise CalculationError("Subtraction requires at least 2 operands")
        
        result = operands[0]
        for operand in operands[1:]:
            result -= operand
        return result
    
    def _multiply(self, operands: List[Union[int, float]]) -> Union[int, float]:
        """Multiply multiple numbers."""
        if len(operands) < 2:
            raise CalculationError("Multiplication requires at least 2 operands")
        
        result = operands[0]
        for operand in operands[1:]:
            result *= operand
        return result
    
    def _divide(self, operands: List[Union[int, float]]) -> float:
        """Divide the first operand by subsequent operands."""
        if len(operands) < 2:
            raise CalculationError("Division requires at least 2 operands")
        
        result = float(operands[0])
        for operand in operands[1:]:
            if operand == 0:
                raise CalculationError("Division by zero")
            result /= operand
        return result
    
    def _power(self, operands: List[Union[int, float]]) -> Union[int, float]:
        """Raise the first operand to the power of the second."""
        if len(operands) != 2:
            raise CalculationError("Power operation requires exactly 2 operands")
        
        return math.pow(operands[0], operands[1])
    
    def _sqrt(self, operands: List[Union[int, float]]) -> float:
        """Calculate square root of the operand."""
        if len(operands) != 1:
            raise CalculationError("Square root requires exactly 1 operand")
        
        if operands[0] < 0:
            raise CalculationError("Cannot calculate square root of negative number")
        
        return math.sqrt(operands[0])
    
    def _log(self, operands: List[Union[int, float]]) -> float:
        """Calculate natural logarithm of the operand."""
        if len(operands) != 1:
            raise CalculationError("Logarithm requires exactly 1 operand")
        
        if operands[0] <= 0:
            raise CalculationError("Cannot calculate logarithm of non-positive number")
        
        return math.log(operands[0])
    
    def _sin(self, operands: List[Union[int, float]]) -> float:
        """Calculate sine of the operand (in radians)."""
        if len(operands) != 1:
            raise CalculationError("Sine requires exactly 1 operand")
        
        return math.sin(operands[0])
    
    def _cos(self, operands: List[Union[int, float]]) -> float:
        """Calculate cosine of the operand (in radians)."""
        if len(operands) != 1:
            raise CalculationError("Cosine requires exactly 1 operand")
        
        return math.cos(operands[0])
    
    def _tan(self, operands: List[Union[int, float]]) -> float:
        """Calculate tangent of the operand (in radians)."""
        if len(operands) != 1:
            raise CalculationError("Tangent requires exactly 1 operand")
        
        return math.tan(operands[0])
    
    def get_supported_operations(self) -> List[str]:
        """Get list of supported operations."""
        return list(self.supported_operations.keys())
    
    def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        try:
            # Test a simple calculation
            test_result = self.calculate('add', [1, 2])
            return test_result == 3
        except Exception:
            return False 