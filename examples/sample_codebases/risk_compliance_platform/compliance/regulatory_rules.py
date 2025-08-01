"""
Regulatory Rules Engine
Manages regulatory compliance rules for different frameworks.
"""

from typing import Dict, List

class RegulatoryRulesEngine:
    """Manages regulatory compliance rules and requirements."""
    
    def __init__(self):
        self.rules = self._initialize_rules()
    
    def get_framework_rules(self, framework: str) -> List[Dict]:
        """Get all rules for a specific regulatory framework."""
        return self.rules.get(framework, [])
    
    def _initialize_rules(self) -> Dict:
        """Initialize regulatory rules for different frameworks."""
        return {
            "finra": [
                {
                    "id": "FINRA_001",
                    "type": "data_retention",
                    "description": "Trade data retention for 6 years",
                    "retention_period_days": 2190,
                    "severity": "HIGH",
                    "weight": 15.0
                },
                {
                    "id": "FINRA_002", 
                    "type": "risk_limits",
                    "description": "Position concentration limits",
                    "max_risk_threshold": 0.25,
                    "severity": "HIGH",
                    "weight": 20.0
                }
            ],
            "sec": [
                {
                    "id": "SEC_001",
                    "type": "reporting_frequency",
                    "description": "Form PF filing requirements",
                    "frequency_hours": 24,
                    "severity": "HIGH",
                    "weight": 25.0
                },
                {
                    "id": "SEC_002",
                    "type": "audit_trail",
                    "description": "Complete transaction audit trail",
                    "severity": "MEDIUM",
                    "weight": 18.0
                }
            ],
            "basel_iii": [
                {
                    "id": "BASEL_001",
                    "type": "risk_limits",
                    "description": "Capital adequacy requirements",
                    "max_risk_threshold": 0.08,
                    "severity": "CRITICAL",
                    "weight": 30.0
                }
            ]
        } 