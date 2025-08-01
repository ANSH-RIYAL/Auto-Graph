"""
Tests for observability functionality.
"""

import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from observability.audit_mode import AuditMode
from observability.compliance_reporter import ComplianceReporter
from observability.business_context import BusinessContextAnalyzer
from models.schemas import Graph, GraphNode, GraphMetadata


class TestAuditMode(unittest.TestCase):
    """Test audit mode functionality."""
    
    def setUp(self):
        self.audit_mode = AuditMode()
        
        # Create mock graph with agent and non-agent nodes
        self.mock_graph = Mock(spec=Graph)
        
        # Create agent node
        agent_metadata = Mock()
        agent_metadata.agent_touched = True
        agent_metadata.risk_level = 'high'
        agent_metadata.agent_types = ['openai']
        agent_metadata.business_impact = 'Customer credit decisions'
        
        agent_node = Mock(spec=GraphNode)
        agent_node.name = 'AI Risk Classifier'
        agent_node.type = 'Component'
        agent_node.level = 'LLD'
        agent_node.files = ['services/risk_classifier.py']
        agent_node.metadata = agent_metadata
        
        # Create regular node
        regular_metadata = Mock()
        regular_metadata.agent_touched = False
        
        regular_node = Mock(spec=GraphNode)
        regular_node.name = 'Data Validator'
        regular_node.type = 'Component'
        regular_node.level = 'LLD'
        regular_node.files = ['utils/validator.py']
        regular_node.metadata = regular_metadata
        
        self.mock_graph.nodes = [agent_node, regular_node]
    
    def test_enable_audit_mode(self):
        """Test enabling audit mode."""
        result = self.audit_mode.enable_audit_mode(self.mock_graph)
        
        self.assertTrue(result['audit_enabled'])
        self.assertEqual(len(result['agent_nodes']), 1)
        self.assertEqual(len(result['regular_nodes']), 1)
        self.assertIn('audit_statistics', result)
        self.assertIn('audit_summary', result)
    
    def test_generate_audit_report(self):
        """Test audit report generation."""
        audit_data = {
            'agent_nodes': self.mock_graph.nodes[:1],  # Only agent node
            'audit_statistics': {
                'total_components': 2,
                'agent_components': 1,
                'agent_percentage': 50.0,
                'high_risk_components': 1,
                'medium_risk_components': 0,
                'low_risk_components': 0,
                'total_files': 2
            }
        }
        
        report = self.audit_mode.generate_audit_report(self.mock_graph, audit_data)
        
        self.assertIn('AI System Audit Report', report)
        self.assertIn('AI Risk Classifier', report)
        self.assertIn('HIGH', report)
        self.assertIn('Customer credit decisions', report)
    
    def test_audit_statistics(self):
        """Test audit statistics generation."""
        agent_nodes = [self.mock_graph.nodes[0]]  # Only agent node
        
        stats = self.audit_mode._generate_audit_statistics(self.mock_graph, agent_nodes)
        
        self.assertEqual(stats['total_components'], 2)
        self.assertEqual(stats['agent_components'], 1)
        self.assertEqual(stats['agent_percentage'], 50.0)
        self.assertEqual(stats['high_risk_components'], 1)
        self.assertEqual(stats['total_files'], 2)


class TestComplianceReporter(unittest.TestCase):
    """Test compliance reporter functionality."""
    
    def setUp(self):
        self.reporter = ComplianceReporter()
        
        self.mock_audit_data = {
            'agent_nodes': [],
            'audit_statistics': {
                'total_components': 5,
                'agent_components': 2,
                'high_risk_components': 1,
                'medium_risk_components': 1,
                'low_risk_components': 0
            }
        }
    
    def test_generate_general_compliance_report(self):
        """Test general compliance report generation."""
        report = self.reporter.generate_compliance_report(self.mock_audit_data, 'general')
        
        self.assertIn('General Compliance Report', report)
        self.assertIn('Total Components: 5', report)
        self.assertIn('AI Components: 2', report)
        self.assertIn('High Risk Components: 1', report)
    
    def test_generate_soc2_report(self):
        """Test SOC2 compliance report generation."""
        report = self.reporter.generate_compliance_report(self.mock_audit_data, 'soc2')
        
        self.assertIn('SOC2 Compliance Report', report)
        self.assertIn('Trust Service Criteria', report)
        self.assertIn('Security', report)
        self.assertIn('Availability', report)
    
    def test_generate_hipaa_report(self):
        """Test HIPAA compliance report generation."""
        report = self.reporter.generate_compliance_report(self.mock_audit_data, 'hipaa')
        
        self.assertIn('HIPAA Compliance Report', report)
        self.assertIn('Administrative Safeguards', report)
        self.assertIn('Physical Safeguards', report)
        self.assertIn('Technical Safeguards', report)
    
    def test_generate_gdpr_report(self):
        """Test GDPR compliance report generation."""
        report = self.reporter.generate_compliance_report(self.mock_audit_data, 'gdpr')
        
        self.assertIn('GDPR Compliance Report', report)
        self.assertIn('Data Protection Principles', report)
        self.assertIn('Individual Rights', report)
        self.assertIn('Accountability', report)
    
    def test_get_compliance_notes(self):
        """Test compliance notes generation."""
        high_notes = self.reporter._get_compliance_notes('high')
        medium_notes = self.reporter._get_compliance_notes('medium')
        low_notes = self.reporter._get_compliance_notes('low')
        
        self.assertIn('immediate attention', high_notes)
        self.assertIn('periodic review', medium_notes)
        self.assertIn('Standard controls', low_notes)


class TestBusinessContextAnalyzer(unittest.TestCase):
    """Test business context analyzer functionality."""
    
    def setUp(self):
        self.analyzer = BusinessContextAnalyzer()
        
        # Create mock agent nodes
        self.mock_agent_nodes = []
        
        # Finance domain node
        finance_metadata = Mock()
        finance_metadata.purpose = 'Process payment transactions'
        finance_metadata.business_impact = 'Revenue and financial performance'
        finance_metadata.risk_level = 'high'
        finance_metadata.stakeholders = 'Customers and management'
        
        finance_node = Mock()
        finance_node.name = 'Payment Processor'
        finance_node.metadata = finance_metadata
        self.mock_agent_nodes.append(finance_node)
        
        # Customer service domain node
        service_metadata = Mock()
        service_metadata.purpose = 'Analyze customer support tickets'
        service_metadata.business_impact = 'Customer experience and satisfaction'
        service_metadata.risk_level = 'medium'
        service_metadata.stakeholders = 'Customers and employees'
        
        service_node = Mock()
        service_node.name = 'Support Analyzer'
        service_node.metadata = service_metadata
        self.mock_agent_nodes.append(service_node)
    
    def test_analyze_business_domains(self):
        """Test business domain analysis."""
        result = self.analyzer._analyze_business_domains(self.mock_agent_nodes)
        
        self.assertIn('finance', result['domain_counts'])
        self.assertIn('customer_service', result['domain_counts'])
        self.assertEqual(result['domain_counts']['finance'], 1)
        self.assertEqual(result['domain_counts']['customer_service'], 1)
        self.assertEqual(result['total_domains_affected'], 2)
    
    def test_analyze_business_impact(self):
        """Test business impact analysis."""
        result = self.analyzer._analyze_business_impact(self.mock_agent_nodes)
        
        self.assertEqual(result['impact_levels']['high'], 1)
        self.assertEqual(result['impact_levels']['medium'], 1)
        self.assertIn('revenue', result['impact_areas'])
        self.assertIn('customer_experience', result['impact_areas'])
    
    def test_analyze_stakeholder_impact(self):
        """Test stakeholder impact analysis."""
        result = self.analyzer._analyze_stakeholder_impact(self.mock_agent_nodes)
        
        self.assertIn('customers', result['stakeholder_counts'])
        self.assertIn('management', result['stakeholder_counts'])
        self.assertIn('employees', result['stakeholder_counts'])
    
    def test_generate_business_summary(self):
        """Test business summary generation."""
        domain_analysis = {
            'primary_domain': 'finance',
            'total_domains_affected': 2
        }
        impact_analysis = {
            'impact_levels': {'high': 1, 'medium': 1, 'low': 0},
            'primary_impact_area': 'revenue'
        }
        stakeholder_analysis = {
            'primary_stakeholder': 'customers'
        }
        
        summary = self.analyzer._generate_business_summary(
            domain_analysis, impact_analysis, stakeholder_analysis
        )
        
        self.assertIn('finance', summary)
        self.assertIn('revenue', summary)
        self.assertIn('customers', summary)
        self.assertIn('high-impact', summary)
        self.assertIn('cross-functional', summary)


if __name__ == '__main__':
    unittest.main() 