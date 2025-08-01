"""
Risk Management & Compliance Platform
Main application entry point for fintech risk assessment and regulatory compliance.
"""

from risk_engine.portfolio_risk_calculator import PortfolioRiskCalculator
from compliance.monitor import ComplianceMonitor
from data_pipeline.market_data_ingestion import MarketDataIngestion
from reporting.regulatory_reports import RegulatoryReportGenerator
from alerts.risk_alert_system import RiskAlertSystem
from audit.transaction_logger import TransactionLogger
from utils.config import Config
from utils.logger import setup_logger

class RiskCompliancePlatform:
    """
    Main platform orchestrator for risk management and compliance operations.
    Handles real-time risk assessment, regulatory monitoring, and automated reporting.
    """
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger()
        
        # Core components
        self.risk_calculator = PortfolioRiskCalculator()
        self.compliance_monitor = ComplianceMonitor()
        self.data_pipeline = MarketDataIngestion()
        self.report_generator = RegulatoryReportGenerator()
        self.alert_system = RiskAlertSystem()
        self.audit_logger = TransactionLogger()
        
        self.logger.info("Risk Management & Compliance Platform initialized")
    
    def start_monitoring(self):
        """Start real-time monitoring of portfolio risk and compliance status."""
        try:
            # Initialize data pipeline
            self.data_pipeline.start_ingestion()
            
            # Start risk monitoring
            self.risk_calculator.start_monitoring()
            
            # Start compliance monitoring
            self.compliance_monitor.start_monitoring()
            
            # Start alert system
            self.alert_system.start_monitoring()
            
            self.logger.info("All monitoring systems started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            return False
    
    def generate_compliance_report(self, report_type="monthly"):
        """Generate regulatory compliance reports for SEC, FINRA, or Basel III."""
        try:
            portfolio_data = self.data_pipeline.get_portfolio_data()
            risk_metrics = self.risk_calculator.calculate_risk_metrics(portfolio_data)
            compliance_status = self.compliance_monitor.get_compliance_status()
            
            report = self.report_generator.generate_report(
                report_type=report_type,
                portfolio_data=portfolio_data,
                risk_metrics=risk_metrics,
                compliance_status=compliance_status
            )
            
            # Log report generation for audit trail
            self.audit_logger.log_report_generation(report_type, report.id)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate compliance report: {e}")
            return None
    
    def get_executive_dashboard_data(self):
        """Get executive dashboard KPIs and metrics."""
        try:
            portfolio_data = self.data_pipeline.get_portfolio_data()
            risk_metrics = self.risk_calculator.calculate_risk_metrics(portfolio_data)
            compliance_status = self.compliance_monitor.get_compliance_status()
            alert_summary = self.alert_system.get_alert_summary()
            
            return {
                "portfolio_risk_score": risk_metrics.get("overall_risk_score", 0),
                "compliance_status": compliance_status.get("overall_compliance", 0),
                "audit_readiness": compliance_status.get("audit_readiness", 0),
                "system_uptime": self.data_pipeline.get_uptime(),
                "regulatory_breaches": alert_summary.get("breach_count", 0),
                "total_portfolio_value": portfolio_data.get("total_value", 0),
                "active_alerts": alert_summary.get("active_alerts", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get executive dashboard data: {e}")
            return {}

def main():
    """Main application entry point."""
    platform = RiskCompliancePlatform()
    
    # Start monitoring
    if platform.start_monitoring():
        print("✅ Risk Management & Compliance Platform started successfully")
        print("📊 Monitoring portfolio risk and compliance in real-time")
        print("📈 Executive dashboard available at /dashboard")
        print("📋 Compliance reports available at /reports")
    else:
        print("❌ Failed to start platform")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 