"""
Compliance reporter for AutoGraph.
Generates compliance reports for enterprise use.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ComplianceReporter:
    """Generates compliance reports for enterprise use."""
    
    def __init__(self):
        self.compliance_frameworks = {
            'soc2': self._generate_soc2_report,
            'hipaa': self._generate_hipaa_report,
            'gdpr': self._generate_gdpr_report,
            'sox': self._generate_sox_report,
            'pci': self._generate_pci_report
        }
    
    def generate_compliance_report(self, audit_data: Dict[str, Any], 
                                 framework: str = 'general') -> str:
        """Generate a compliance report for the specified framework."""
        logger.info(f"Generating {framework.upper()} compliance report")
        
        if framework.lower() in self.compliance_frameworks:
            return self.compliance_frameworks[framework.lower()](audit_data)
        else:
            return self._generate_general_compliance_report(audit_data)
    
    def _generate_general_compliance_report(self, audit_data: Dict[str, Any]) -> str:
        """Generate a general compliance report."""
        agent_nodes = audit_data.get('agent_nodes', [])
        audit_stats = audit_data.get('audit_statistics', {})
        
        report = f"""
# General Compliance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Compliance Overview
This report provides a general compliance assessment of AI components in the codebase.

## Key Findings
- **Total Components**: {audit_stats.get('total_components', 0)}
- **AI Components**: {audit_stats.get('agent_components', 0)}
- **High Risk Components**: {audit_stats.get('high_risk_components', 0)}
- **Compliance Status**: {'⚠️ Requires Attention' if audit_stats.get('high_risk_components', 0) > 0 else '✅ Compliant'}

## AI Component Analysis
"""
        
        for node in agent_nodes:
            metadata = node.metadata if hasattr(node, 'metadata') else {}
            risk_level = metadata.get('risk_level', 'unknown')
            business_impact = metadata.get('business_impact', 'Not specified')
            
            report += f"""
### {node.name}
- **Risk Level**: {risk_level.upper()}
- **Business Impact**: {business_impact}
- **Compliance Notes**: {self._get_compliance_notes(risk_level)}
"""
        
        report += """
## Compliance Recommendations
1. **Documentation**: Ensure all AI components have documented decision logic
2. **Testing**: Implement comprehensive testing for high-risk components
3. **Monitoring**: Establish monitoring and alerting for critical AI systems
4. **Review Process**: Implement regular compliance reviews
5. **Training**: Provide training on AI compliance requirements

## Next Steps
- Review high-risk components immediately
- Implement recommended controls
- Schedule regular compliance audits
- Update documentation as needed
"""
        
        return report
    
    def _generate_soc2_report(self, audit_data: Dict[str, Any]) -> str:
        """Generate SOC2 compliance report."""
        return f"""
# SOC2 Compliance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## SOC2 Trust Service Criteria Assessment

### Security
- AI components must have proper access controls
- Implement monitoring for AI system access
- Document security measures for AI components

### Availability
- AI systems must have defined availability requirements
- Implement monitoring for AI system availability
- Document recovery procedures for AI components

### Processing Integrity
- AI decision logic must be documented and tested
- Implement validation for AI outputs
- Monitor AI system performance and accuracy

### Confidentiality
- AI systems processing sensitive data must be protected
- Implement data encryption for AI components
- Document data handling procedures

### Privacy
- AI systems must comply with privacy requirements
- Implement data minimization for AI components
- Document privacy controls and procedures

## Compliance Status: {'⚠️ Requires Attention' if audit_data.get('audit_statistics', {}).get('high_risk_components', 0) > 0 else '✅ Compliant'}
"""
    
    def _generate_hipaa_report(self, audit_data: Dict[str, Any]) -> str:
        """Generate HIPAA compliance report."""
        return f"""
# HIPAA Compliance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## HIPAA Requirements Assessment

### Administrative Safeguards
- AI systems must have documented policies and procedures
- Implement workforce training for AI systems
- Establish incident response procedures for AI components

### Physical Safeguards
- AI systems must have appropriate physical security
- Implement facility access controls for AI infrastructure
- Document physical security measures

### Technical Safeguards
- AI systems must have access controls
- Implement audit controls for AI components
- Ensure data integrity for AI systems
- Implement transmission security for AI data

## Compliance Status: {'⚠️ Requires Attention' if audit_data.get('audit_statistics', {}).get('high_risk_components', 0) > 0 else '✅ Compliant'}
"""
    
    def _generate_gdpr_report(self, audit_data: Dict[str, Any]) -> str:
        """Generate GDPR compliance report."""
        return f"""
# GDPR Compliance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## GDPR Requirements Assessment

### Data Protection Principles
- AI systems must process data lawfully, fairly, and transparently
- Implement data minimization for AI components
- Ensure data accuracy in AI systems
- Implement appropriate data retention for AI components

### Individual Rights
- AI systems must support data subject rights
- Implement data portability for AI-processed data
- Ensure right to erasure for AI components
- Support right to object to AI processing

### Accountability
- AI systems must have documented compliance measures
- Implement data protection impact assessments for AI
- Establish data protection officer oversight for AI systems

## Compliance Status: {'⚠️ Requires Attention' if audit_data.get('audit_statistics', {}).get('high_risk_components', 0) > 0 else '✅ Compliant'}
"""
    
    def _generate_sox_report(self, audit_data: Dict[str, Any]) -> str:
        """Generate SOX compliance report."""
        return f"""
# SOX Compliance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## SOX Requirements Assessment

### Internal Controls
- AI systems affecting financial reporting must have controls
- Implement monitoring for AI financial systems
- Document control procedures for AI components

### Audit Trail
- AI systems must maintain audit trails
- Implement logging for AI decision processes
- Ensure audit trail integrity for AI components

### Management Assessment
- Management must assess AI system controls
- Implement regular control testing for AI systems
- Document management oversight of AI components

## Compliance Status: {'⚠️ Requires Attention' if audit_data.get('audit_statistics', {}).get('high_risk_components', 0) > 0 else '✅ Compliant'}
"""
    
    def _generate_pci_report(self, audit_data: Dict[str, Any]) -> str:
        """Generate PCI compliance report."""
        return f"""
# PCI Compliance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## PCI Requirements Assessment

### Data Security
- AI systems processing card data must be secured
- Implement encryption for AI-processed card data
- Document security measures for AI components

### Access Control
- AI systems must have appropriate access controls
- Implement monitoring for AI system access
- Document access control procedures

### Monitoring and Testing
- AI systems must be monitored and tested
- Implement regular security testing for AI components
- Document monitoring and testing procedures

## Compliance Status: {'⚠️ Requires Attention' if audit_data.get('audit_statistics', {}).get('high_risk_components', 0) > 0 else '✅ Compliant'}
"""
    
    def _get_compliance_notes(self, risk_level: str) -> str:
        """Get compliance notes based on risk level."""
        if risk_level == 'high':
            return "Requires immediate attention and comprehensive controls"
        elif risk_level == 'medium':
            return "Requires periodic review and standard controls"
        else:
            return "Standard controls sufficient" 