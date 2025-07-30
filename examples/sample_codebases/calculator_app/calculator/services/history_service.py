"""
History service for managing calculation history.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.calculation import Calculation


class HistoryService:
    """Service for managing calculation history."""
    
    def __init__(self):
        self.calculations: Dict[str, Calculation] = {}
        self.max_history_size = 1000
    
    def add_calculation(self, calculation: Calculation) -> str:
        """Add a calculation to history."""
        # Generate unique ID if not provided
        if not calculation.id:
            calculation.id = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if not calculation.timestamp:
            calculation.timestamp = datetime.now()
        
        # Store calculation
        self.calculations[calculation.id] = calculation
        
        # Maintain history size limit
        if len(self.calculations) > self.max_history_size:
            self._cleanup_old_calculations()
        
        return calculation.id
    
    def get_calculation(self, calculation_id: str) -> Optional[Calculation]:
        """Get a specific calculation by ID."""
        return self.calculations.get(calculation_id)
    
    def get_history(self, limit: int = 10) -> List[Calculation]:
        """Get recent calculation history."""
        # Sort by timestamp (newest first)
        sorted_calculations = sorted(
            self.calculations.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )
        
        return sorted_calculations[:limit]
    
    def get_history_by_operation(self, operation: str, limit: int = 10) -> List[Calculation]:
        """Get history filtered by operation type."""
        filtered_calculations = [
            calc for calc in self.calculations.values()
            if calc.operation == operation
        ]
        
        # Sort by timestamp (newest first)
        sorted_calculations = sorted(
            filtered_calculations,
            key=lambda x: x.timestamp,
            reverse=True
        )
        
        return sorted_calculations[:limit]
    
    def get_history_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Calculation]:
        """Get history within a date range."""
        filtered_calculations = [
            calc for calc in self.calculations.values()
            if start_date <= calc.timestamp <= end_date
        ]
        
        # Sort by timestamp (newest first)
        return sorted(
            filtered_calculations,
            key=lambda x: x.timestamp,
            reverse=True
        )
    
    def delete_calculation(self, calculation_id: str) -> bool:
        """Delete a specific calculation from history."""
        if calculation_id in self.calculations:
            del self.calculations[calculation_id]
            return True
        return False
    
    def clear_history(self) -> int:
        """Clear all calculation history."""
        count = len(self.calculations)
        self.calculations.clear()
        return count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the calculation history."""
        if not self.calculations:
            return {
                'total_calculations': 0,
                'operations_count': {},
                'date_range': None
            }
        
        # Count operations
        operations_count = {}
        for calc in self.calculations.values():
            operations_count[calc.operation] = operations_count.get(calc.operation, 0) + 1
        
        # Get date range
        timestamps = [calc.timestamp for calc in self.calculations.values()]
        date_range = {
            'earliest': min(timestamps),
            'latest': max(timestamps)
        }
        
        return {
            'total_calculations': len(self.calculations),
            'operations_count': operations_count,
            'date_range': date_range
        }
    
    def export_history(self, format: str = 'json') -> str:
        """Export history in specified format."""
        if format.lower() == 'json':
            return self._export_as_json()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_as_json(self) -> str:
        """Export history as JSON string."""
        import json
        
        history_data = {
            'calculations': [calc.to_dict() for calc in self.calculations.values()],
            'statistics': self.get_statistics()
        }
        
        return json.dumps(history_data, indent=2, default=str)
    
    def _cleanup_old_calculations(self) -> None:
        """Remove oldest calculations to maintain size limit."""
        # Sort by timestamp (oldest first)
        sorted_calculations = sorted(
            self.calculations.values(),
            key=lambda x: x.timestamp
        )
        
        # Remove oldest calculations
        to_remove = len(self.calculations) - self.max_history_size
        for calc in sorted_calculations[:to_remove]:
            del self.calculations[calc.id]
    
    def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        try:
            # Test basic operations
            test_calc = Calculation('add', [1, 2], 3)
            calc_id = self.add_calculation(test_calc)
            retrieved_calc = self.get_calculation(calc_id)
            
            return retrieved_calc is not None and retrieved_calc.id == calc_id
        except Exception:
            return False 