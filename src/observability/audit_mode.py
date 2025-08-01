"""
Audit mode for AutoGraph.
Provides audit mode functionality for agent-aware analysis.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from ..utils.logger import get_logger
from ..models.schemas import Graph, GraphNode

logger = get_logger(__name__)


class AuditMode:
    """Audit mode functionality for agent-aware analysis."""
    
    def __init__(self):
        self.audit_results = {}
    
    def enable_audit_mode(self, graph: Graph) -> Dict[str, Any]:
        """Enable audit mode and filter for agent-touched components."""
        logger.info("Enabling audit mode")
        
        # Filter nodes to only include agent-touched components
        agent_nodes = []
        regular_nodes = []
        
        for node in graph.nodes:
            if self._is_agent_touched(node):
                agent_nodes.append(node)
            else:
                regular_nodes.append(node)
        
        # Generate audit statistics
        audit_stats = self._generate_audit_statistics(graph, agent_nodes)
        
        # Create audit summary
        audit_summary = self._create_audit_summary(audit_stats, agent_nodes)
        
        return {
            'audit_enabled': True,
            'agent_nodes': agent_nodes,
            'regular_nodes': regular_nodes,
            'audit_statistics': audit_stats,
            'audit_summary': audit_summary,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_audit_report(self, graph: Graph, audit_data: Dict[str, Any]) -> str:
        """Generate a comprehensive audit report."""
        logger.info("Generating audit report")
        
        agent_nodes = audit_data.get('agent_nodes', [])
        audit_stats = audit_data.get('audit_statistics', {})
        
        report = f"""
# AI System Audit Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- Total Components: {audit_stats.get('total_components', 0)}
- AI-Controlled Components: {audit_stats.get('agent_components', 0)} ({audit_stats.get('agent_percentage', 0):.1f}%)
- High Risk Components: {audit_stats.get('high_risk_components', 0)}
- Medium Risk Components: {audit_stats.get('medium_risk_components', 0)}
- Low Risk Components: {audit_stats.get('low_risk_components', 0)}

## AI Component Inventory
"""
        
        # Add details for each agent component
        for node in agent_nodes:
            metadata = node.metadata if hasattr(node, 'metadata') else {}
            agent_types = metadata.get('agent_types', [])
            risk_level = metadata.get('risk_level', 'unknown')
            business_impact = metadata.get('business_impact', 'Not specified')
            
            report += f"""
### {node.name}
- **Type**: {node.type}
- **Level**: {node.level}
- **Files**: {', '.join(node.files)}
- **AI Agents**: {', '.join(agent_types)}
- **Risk Level**: {risk_level.upper()}
- **Business Impact**: {business_impact}
"""
        
        # Add risk assessment
        report += f"""
## Risk Assessment
- **High Risk Components**: {audit_stats.get('high_risk_components', 0)}
- **Medium Risk Components**: {audit_stats.get('medium_risk_components', 0)}
- **Low Risk Components**: {audit_stats.get('low_risk_components', 0)}

## Compliance Recommendations
"""
        
        # Add compliance recommendations based on risk levels
        if audit_stats.get('high_risk_components', 0) > 0:
            report += """
### High Risk Components Require:
- Regular security audits
- Comprehensive testing
- Documentation of decision logic
- Monitoring and alerting
- Compliance review
"""
        
        if audit_stats.get('medium_risk_components', 0) > 0:
            report += """
### Medium Risk Components Require:
- Periodic reviews
- Testing procedures
- Basic monitoring
- Documentation
"""
        
        report += f"""
## Technical Details
- **Analysis Timestamp**: {datetime.now().isoformat()}
- **Total Files Analyzed**: {audit_stats.get('total_files', 0)}
- **Agent Detection Method**: Pattern-based + LLM validation
- **Risk Assessment Method**: Keyword-based + business context analysis

## Next Steps
1. Review high-risk components for compliance requirements
2. Implement monitoring for critical AI components
3. Document decision logic for audit purposes
4. Establish regular review cycles
5. Consider additional testing for high-risk components
"""
        
        return report
    
    def _is_agent_touched(self, node: GraphNode) -> bool:
        """Check if a node is agent-touched."""
        if not hasattr(node, 'metadata') or not node.metadata:
            return False
        
        return node.metadata.get('agent_touched', False)
    
    def _generate_audit_statistics(self, graph: Graph, agent_nodes: List[GraphNode]) -> Dict[str, Any]:
        """Generate audit statistics."""
        total_components = len(graph.nodes)
        agent_components = len(agent_nodes)
        
        # Count risk levels
        risk_counts = {'high': 0, 'medium': 0, 'low': 0}
        
        for node in agent_nodes:
            if hasattr(node, 'metadata') and node.metadata:
                risk_level = node.metadata.get('risk_level', 'low')
                risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        return {
            'total_components': total_components,
            'agent_components': agent_components,
            'agent_percentage': (agent_components / total_components * 100) if total_components > 0 else 0,
            'high_risk_components': risk_counts['high'],
            'medium_risk_components': risk_counts['medium'],
            'low_risk_components': risk_counts['low'],
            'total_files': len(set([file for node in graph.nodes for file in node.files]))
        }
    
    def _create_audit_summary(self, audit_stats: Dict[str, Any], agent_nodes: List[GraphNode]) -> str:
        """Create a human-readable audit summary."""
        total = audit_stats.get('total_components', 0)
        agent = audit_stats.get('agent_components', 0)
        high_risk = audit_stats.get('high_risk_components', 0)
        
        summary = f"Audit analysis found {agent} AI-controlled components out of {total} total components "
        summary += f"({audit_stats.get('agent_percentage', 0):.1f}% AI coverage). "
        
        if high_risk > 0:
            summary += f"⚠️ {high_risk} high-risk components identified requiring immediate attention. "
        else:
            summary += "✅ No high-risk components identified. "
        
        summary += "Review recommended for compliance and security purposes."
        
        return summary 