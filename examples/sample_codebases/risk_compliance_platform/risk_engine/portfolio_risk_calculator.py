"""
Portfolio Risk Calculator
Core risk assessment engine for portfolio analysis and real-time monitoring.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .var_calculator import VaRCalculator
from .stress_testing import StressTestEngine
from .risk_metrics import RiskMetricsCalculator

class PortfolioRiskCalculator:
    """
    Main portfolio risk calculation engine.
    Handles real-time risk assessment, VaR calculations, and stress testing.
    """
    
    def __init__(self):
        self.var_calculator = VaRCalculator()
        self.stress_engine = StressTestEngine()
        self.metrics_calculator = RiskMetricsCalculator()
        self.monitoring_active = False
        self.risk_thresholds = {
            "var_95": 0.02,  # 2% VaR threshold
            "var_99": 0.05,  # 5% VaR threshold
            "max_drawdown": 0.15,  # 15% max drawdown
            "concentration": 0.25  # 25% max concentration
        }
    
    def calculate_risk_metrics(self, portfolio_data: Dict) -> Dict:
        """
        Calculate comprehensive risk metrics for portfolio assessment.
        
        Args:
            portfolio_data: Portfolio holdings and market data
            
        Returns:
            Dictionary containing all risk metrics
        """
        try:
            # Extract portfolio components
            positions = portfolio_data.get("positions", [])
            market_data = portfolio_data.get("market_data", {})
            
            # Calculate VaR metrics
            var_metrics = self.var_calculator.calculate_var(
                positions=positions,
                market_data=market_data,
                confidence_levels=[0.95, 0.99]
            )
            
            # Calculate stress test scenarios
            stress_results = self.stress_engine.run_stress_tests(
                positions=positions,
                scenarios=["market_crash", "interest_rate_shock", "liquidity_crisis"]
            )
            
            # Calculate additional risk metrics
            risk_metrics = self.metrics_calculator.calculate_metrics(
                positions=positions,
                market_data=market_data
            )
            
            # Combine all metrics
            overall_risk_score = self._calculate_overall_risk_score(
                var_metrics, stress_results, risk_metrics
            )
            
            return {
                "overall_risk_score": overall_risk_score,
                "var_metrics": var_metrics,
                "stress_test_results": stress_results,
                "risk_metrics": risk_metrics,
                "risk_level": self._determine_risk_level(overall_risk_score),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Risk calculation failed: {str(e)}",
                "overall_risk_score": 10.0,  # High risk on error
                "risk_level": "CRITICAL"
            }
    
    def start_monitoring(self):
        """Start real-time risk monitoring."""
        self.monitoring_active = True
        print("🔄 Portfolio risk monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time risk monitoring."""
        self.monitoring_active = False
        print("⏹️ Portfolio risk monitoring stopped")
    
    def _calculate_overall_risk_score(self, var_metrics: Dict, 
                                    stress_results: Dict, 
                                    risk_metrics: Dict) -> float:
        """Calculate overall risk score from all metrics."""
        try:
            # Weighted average of different risk factors
            var_score = var_metrics.get("var_95_percentile", 0) * 0.3
            stress_score = stress_results.get("worst_case_loss", 0) * 0.25
            volatility_score = risk_metrics.get("portfolio_volatility", 0) * 0.2
            concentration_score = risk_metrics.get("concentration_risk", 0) * 0.15
            liquidity_score = risk_metrics.get("liquidity_risk", 0) * 0.1
            
            overall_score = (var_score + stress_score + volatility_score + 
                           concentration_score + liquidity_score)
            
            # Normalize to 0-10 scale
            return min(max(overall_score * 10, 0), 10)
            
        except Exception:
            return 5.0  # Medium risk as fallback
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score."""
        if risk_score <= 2.0:
            return "LOW"
        elif risk_score <= 5.0:
            return "MEDIUM"
        elif risk_score <= 8.0:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def check_risk_thresholds(self, risk_metrics: Dict) -> List[Dict]:
        """Check if any risk thresholds have been breached."""
        alerts = []
        
        var_95 = risk_metrics.get("var_metrics", {}).get("var_95_percentile", 0)
        if var_95 > self.risk_thresholds["var_95"]:
            alerts.append({
                "type": "VAR_BREACH",
                "severity": "HIGH",
                "message": f"VaR 95% threshold breached: {var_95:.2%}",
                "threshold": self.risk_thresholds["var_95"]
            })
        
        concentration = risk_metrics.get("risk_metrics", {}).get("concentration_risk", 0)
        if concentration > self.risk_thresholds["concentration"]:
            alerts.append({
                "type": "CONCENTRATION_BREACH",
                "severity": "MEDIUM",
                "message": f"Concentration risk threshold breached: {concentration:.2%}",
                "threshold": self.risk_thresholds["concentration"]
            })
        
        return alerts 