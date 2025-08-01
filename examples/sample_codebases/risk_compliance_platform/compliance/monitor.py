"""
Compliance Monitor
Real-time monitoring of regulatory compliance requirements and automated reporting.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .regulatory_rules import RegulatoryRulesEngine
from .audit_trail import AuditTrailManager
from .reporting_engine import ComplianceReportingEngine

class ComplianceMonitor:
    """
    Main compliance monitoring system for regulatory requirements.
    Handles FINRA, SEC, Basel III, and other regulatory compliance.
    """
    
    def __init__(self):
        self.rules_engine = RegulatoryRulesEngine()
        self.audit_manager = AuditTrailManager()
        self.reporting_engine = ComplianceReportingEngine()
        self.monitoring_active = False
        self.compliance_status = {
            "overall_compliance": 0.0,
            "regulatory_breaches": [],
            "audit_readiness": 0.0,
            "last_assessment": None
        }
        
        # Regulatory frameworks
        self.frameworks = {
            "finra": "Financial Industry Regulatory Authority",
            "sec": "Securities and Exchange Commission", 
            "basel_iii": "Basel III Capital Requirements",
            "sox": "Sarbanes-Oxley Act",
            "gdpr": "General Data Protection Regulation"
        }
    
    def start_monitoring(self):
        """Start real-time compliance monitoring."""
        self.monitoring_active = True
        print("🔄 Compliance monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time compliance monitoring."""
        self.monitoring_active = False
        print("⏹️ Compliance monitoring stopped")
    
    def get_compliance_status(self) -> Dict:
        """Get current compliance status across all regulatory frameworks."""
        try:
            # Check each regulatory framework
            framework_status = {}
            total_compliance = 0.0
            breach_count = 0
            
            for framework, description in self.frameworks.items():
                status = self._check_framework_compliance(framework)
                framework_status[framework] = status
                total_compliance += status.get("compliance_score", 0)
                breach_count += len(status.get("breaches", []))
            
            # Calculate overall compliance
            overall_compliance = total_compliance / len(self.frameworks)
            
            # Update compliance status
            self.compliance_status.update({
                "overall_compliance": overall_compliance,
                "framework_status": framework_status,
                "regulatory_breaches": breach_count,
                "audit_readiness": self._calculate_audit_readiness(),
                "last_assessment": datetime.now().isoformat()
            })
            
            return self.compliance_status
            
        except Exception as e:
            return {
                "error": f"Compliance assessment failed: {str(e)}",
                "overall_compliance": 0.0,
                "risk_level": "CRITICAL"
            }
    
    def _check_framework_compliance(self, framework: str) -> Dict:
        """Check compliance for a specific regulatory framework."""
        try:
            rules = self.rules_engine.get_framework_rules(framework)
            compliance_score = 0.0
            breaches = []
            
            # Check each rule in the framework
            for rule in rules:
                rule_status = self._evaluate_rule(rule)
                if rule_status["compliant"]:
                    compliance_score += rule_status["weight"]
                else:
                    breaches.append({
                        "rule_id": rule["id"],
                        "description": rule["description"],
                        "severity": rule["severity"],
                        "breach_details": rule_status["details"]
                    })
            
            # Normalize compliance score
            compliance_score = min(compliance_score, 100.0)
            
            return {
                "framework": framework,
                "compliance_score": compliance_score,
                "breaches": breaches,
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "framework": framework,
                "compliance_score": 0.0,
                "breaches": [{"error": str(e)}],
                "last_checked": datetime.now().isoformat()
            }
    
    def _evaluate_rule(self, rule: Dict) -> Dict:
        """Evaluate compliance for a specific rule."""
        try:
            rule_type = rule.get("type", "generic")
            
            if rule_type == "data_retention":
                return self._evaluate_data_retention_rule(rule)
            elif rule_type == "risk_limits":
                return self._evaluate_risk_limits_rule(rule)
            elif rule_type == "reporting_frequency":
                return self._evaluate_reporting_rule(rule)
            elif rule_type == "audit_trail":
                return self._evaluate_audit_rule(rule)
            else:
                return self._evaluate_generic_rule(rule)
                
        except Exception as e:
            return {
                "compliant": False,
                "weight": 0.0,
                "details": f"Rule evaluation failed: {str(e)}"
            }
    
    def _evaluate_data_retention_rule(self, rule: Dict) -> Dict:
        """Evaluate data retention compliance."""
        retention_period = rule.get("retention_period_days", 7)
        current_data_age = 5  # Simulated data age in days
        
        compliant = current_data_age <= retention_period
        return {
            "compliant": compliant,
            "weight": rule.get("weight", 10.0),
            "details": f"Data retention: {current_data_age} days (max: {retention_period})"
        }
    
    def _evaluate_risk_limits_rule(self, rule: Dict) -> Dict:
        """Evaluate risk limits compliance."""
        max_risk_threshold = rule.get("max_risk_threshold", 0.05)
        current_risk = 0.023  # Simulated current risk level
        
        compliant = current_risk <= max_risk_threshold
        return {
            "compliant": compliant,
            "weight": rule.get("weight", 15.0),
            "details": f"Risk level: {current_risk:.3f} (max: {max_risk_threshold})"
        }
    
    def _evaluate_reporting_rule(self, rule: Dict) -> Dict:
        """Evaluate reporting frequency compliance."""
        required_frequency = rule.get("frequency_hours", 24)
        last_report_age = 12  # Simulated hours since last report
        
        compliant = last_report_age <= required_frequency
        return {
            "compliant": compliant,
            "weight": rule.get("weight", 12.0),
            "details": f"Last report: {last_report_age} hours ago (max: {required_frequency})"
        }
    
    def _evaluate_audit_rule(self, rule: Dict) -> Dict:
        """Evaluate audit trail compliance."""
        audit_completeness = 0.98  # Simulated audit trail completeness
        
        compliant = audit_completeness >= 0.95
        return {
            "compliant": compliant,
            "weight": rule.get("weight", 20.0),
            "details": f"Audit trail completeness: {audit_completeness:.1%}"
        }
    
    def _evaluate_generic_rule(self, rule: Dict) -> Dict:
        """Evaluate generic compliance rule."""
        # Simulate 95% compliance for generic rules
        compliant = True  # Simulated compliance
        return {
            "compliant": compliant,
            "weight": rule.get("weight", 8.0),
            "details": "Generic rule compliance check passed"
        }
    
    def _calculate_audit_readiness(self) -> float:
        """Calculate audit readiness score."""
        try:
            # Simulate audit readiness factors
            data_completeness = 0.99
            documentation_quality = 0.95
            system_accessibility = 0.98
            compliance_history = 0.97
            
            # Weighted average
            readiness_score = (
                data_completeness * 0.3 +
                documentation_quality * 0.25 +
                system_accessibility * 0.25 +
                compliance_history * 0.2
            )
            
            return readiness_score * 100
            
        except Exception:
            return 0.0
    
    def generate_compliance_report(self, framework: str = "all") -> Dict:
        """Generate detailed compliance report."""
        try:
            if framework == "all":
                status = self.get_compliance_status()
            else:
                status = self._check_framework_compliance(framework)
            
            report = self.reporting_engine.generate_report(
                framework=framework,
                status=status,
                timestamp=datetime.now()
            )
            
            # Log report generation
            self.audit_manager.log_compliance_report(framework, report["id"])
            
            return report
            
        except Exception as e:
            return {
                "error": f"Report generation failed: {str(e)}",
                "framework": framework,
                "timestamp": datetime.now().isoformat()
            } 