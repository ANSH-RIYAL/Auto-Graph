"""
VaR Calculator
Value at Risk calculations for portfolio risk assessment.
"""

import numpy as np
from typing import Dict, List

class VaRCalculator:
    """Calculate Value at Risk metrics for portfolio analysis."""
    
    def calculate_var(self, positions: List[Dict], market_data: Dict, 
                     confidence_levels: List[float] = [0.95, 0.99]) -> Dict:
        """Calculate VaR for given confidence levels."""
        try:
            var_results = {}
            
            for confidence in confidence_levels:
                var_value = self._calculate_historical_var(positions, confidence)
                var_results[f"var_{int(confidence*100)}_percentile"] = var_value
            
            return var_results
            
        except Exception as e:
            return {"error": f"VaR calculation failed: {str(e)}"}
    
    def _calculate_historical_var(self, positions: List[Dict], confidence: float) -> float:
        """Calculate historical VaR using Monte Carlo simulation."""
        # Simulated VaR calculation
        portfolio_value = sum(pos.get("market_value", 0) for pos in positions)
        volatility = 0.15  # 15% annual volatility
        time_horizon = 1/252  # Daily horizon
        
        # Monte Carlo simulation (simplified)
        returns = np.random.normal(0, volatility * np.sqrt(time_horizon), 10000)
        portfolio_returns = [portfolio_value * ret for ret in returns]
        
        # Calculate VaR
        var_percentile = np.percentile(portfolio_returns, (1 - confidence) * 100)
        
        return abs(var_percentile) / portfolio_value  # Return as percentage 