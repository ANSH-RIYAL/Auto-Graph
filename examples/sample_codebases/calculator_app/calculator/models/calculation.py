"""
Calculation model for representing calculation data.
"""

from typing import List, Union, Dict, Any, Optional
from datetime import datetime
import uuid


class Calculation:
    """Model representing a calculation."""
    
    def __init__(self, operation: str, operands: List[Union[int, float]], result: Union[int, float], 
                 calculation_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        self.id = calculation_id or str(uuid.uuid4())
        self.operation = operation
        self.operands = operands
        self.result = result
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert calculation to dictionary."""
        return {
            'id': self.id,
            'operation': self.operation,
            'operands': self.operands,
            'result': self.result,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Calculation':
        """Create calculation from dictionary."""
        timestamp = None
        if data.get('timestamp'):
            timestamp = datetime.fromisoformat(data['timestamp'])
        
        return cls(
            operation=data['operation'],
            operands=data['operands'],
            result=data['result'],
            calculation_id=data.get('id'),
            timestamp=timestamp
        )
    
    def __str__(self) -> str:
        """String representation of calculation."""
        operands_str = ', '.join(map(str, self.operands))
        return f"{self.operation}({operands_str}) = {self.result}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Calculation(id='{self.id}', operation='{self.operation}', operands={self.operands}, result={self.result})"
    
    def __eq__(self, other: object) -> bool:
        """Check equality with another calculation."""
        if not isinstance(other, Calculation):
            return False
        
        return (self.operation == other.operation and
                self.operands == other.operands and
                self.result == other.result)
    
    def __hash__(self) -> int:
        """Hash based on operation, operands, and result."""
        return hash((self.operation, tuple(self.operands), self.result)) 