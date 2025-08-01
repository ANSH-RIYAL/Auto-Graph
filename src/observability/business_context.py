"""
Business context analysis for AutoGraph.
Provides business context analysis for AI components.
"""

from typing import Dict, List, Any, Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BusinessContextAnalyzer:
    """Analyzes business context of AI components."""
    
    def __init__(self):
        self.business_domains = {
            'finance': ['payment', 'transaction', 'money', 'financial', 'banking', 'credit'],
            'healthcare': ['medical', 'health', 'patient', 'diagnosis', 'treatment', 'clinical'],
            'ecommerce': ['product', 'order', 'shopping', 'cart', 'inventory', 'sales'],
            'customer_service': ['support', 'ticket', 'inquiry', 'chat', 'help', 'service'],
            'marketing': ['campaign', 'advertisement', 'promotion', 'analytics', 'conversion'],
            'security': ['authentication', 'authorization', 'security', 'compliance', 'audit'],
            'operations': ['workflow', 'process', 'automation', 'efficiency', 'optimization']
        }
    
    def analyze_business_context(self, agent_nodes: List[Any]) -> Dict[str, Any]:
        """Analyze business context of agent components."""
        logger.info("Analyzing business context of agent components")
        
        # Analyze business domains
        domain_analysis = self._analyze_business_domains(agent_nodes)
        
        # Analyze business impact
        impact_analysis = self._analyze_business_impact(agent_nodes)
        
        # Analyze stakeholder impact
        stakeholder_analysis = self._analyze_stakeholder_impact(agent_nodes)
        
        # Generate business summary
        business_summary = self._generate_business_summary(domain_analysis, impact_analysis, stakeholder_analysis)
        
        return {
            'business_domains': domain_analysis,
            'business_impact': impact_analysis,
            'stakeholder_impact': stakeholder_analysis,
            'business_summary': business_summary
        }
    
    def _analyze_business_domains(self, agent_nodes: List[Any]) -> Dict[str, Any]:
        """Analyze which business domains are affected by AI components."""
        domain_counts = {domain: 0 for domain in self.business_domains.keys()}
        domain_components = {domain: [] for domain in self.business_domains.keys()}
        
        for node in agent_nodes:
            if hasattr(node, 'metadata') and node.metadata:
                content = node.metadata.get('purpose', '') + ' ' + node.metadata.get('business_impact', '')
                
                for domain, keywords in self.business_domains.items():
                    if any(keyword.lower() in content.lower() for keyword in keywords):
                        domain_counts[domain] += 1
                        domain_components[domain].append(node.name)
        
        # Find primary domain
        primary_domain = max(domain_counts.items(), key=lambda x: x[1])[0] if any(domain_counts.values()) else 'general'
        
        return {
            'domain_counts': domain_counts,
            'domain_components': domain_components,
            'primary_domain': primary_domain,
            'total_domains_affected': len([count for count in domain_counts.values() if count > 0])
        }
    
    def _analyze_business_impact(self, agent_nodes: List[Any]) -> Dict[str, Any]:
        """Analyze business impact of AI components."""
        impact_levels = {'high': 0, 'medium': 0, 'low': 0}
        impact_areas = {
            'revenue': 0,
            'customer_experience': 0,
            'operational_efficiency': 0,
            'compliance': 0,
            'security': 0,
            'innovation': 0
        }
        
        for node in agent_nodes:
            if hasattr(node, 'metadata') and node.metadata:
                risk_level = node.metadata.get('risk_level', 'low')
                impact_levels[risk_level] += 1
                
                # Analyze impact areas based on metadata
                content = node.metadata.get('business_impact', '').lower()
                
                if any(word in content for word in ['revenue', 'sales', 'profit', 'financial']):
                    impact_areas['revenue'] += 1
                if any(word in content for word in ['customer', 'user', 'experience', 'satisfaction']):
                    impact_areas['customer_experience'] += 1
                if any(word in content for word in ['efficiency', 'automation', 'process', 'workflow']):
                    impact_areas['operational_efficiency'] += 1
                if any(word in content for word in ['compliance', 'regulation', 'legal', 'audit']):
                    impact_areas['compliance'] += 1
                if any(word in content for word in ['security', 'authentication', 'authorization']):
                    impact_areas['security'] += 1
                if any(word in content for word in ['innovation', 'ai', 'machine_learning', 'automation']):
                    impact_areas['innovation'] += 1
        
        return {
            'impact_levels': impact_levels,
            'impact_areas': impact_areas,
            'primary_impact_area': max(impact_areas.items(), key=lambda x: x[1])[0] if any(impact_areas.values()) else 'general'
        }
    
    def _analyze_stakeholder_impact(self, agent_nodes: List[Any]) -> Dict[str, Any]:
        """Analyze stakeholder impact of AI components."""
        stakeholders = {
            'customers': 0,
            'employees': 0,
            'management': 0,
            'regulators': 0,
            'partners': 0,
            'investors': 0
        }
        
        for node in agent_nodes:
            if hasattr(node, 'metadata') and node.metadata:
                content = node.metadata.get('stakeholders', '').lower()
                
                if 'customer' in content or 'user' in content or 'client' in content:
                    stakeholders['customers'] += 1
                if 'employee' in content or 'staff' in content or 'team' in content:
                    stakeholders['employees'] += 1
                if 'management' in content or 'executive' in content or 'leadership' in content:
                    stakeholders['management'] += 1
                if 'regulator' in content or 'compliance' in content or 'auditor' in content:
                    stakeholders['regulators'] += 1
                if 'partner' in content or 'vendor' in content or 'supplier' in content:
                    stakeholders['partners'] += 1
                if 'investor' in content or 'shareholder' in content or 'board' in content:
                    stakeholders['investors'] += 1
        
        return {
            'stakeholder_counts': stakeholders,
            'primary_stakeholder': max(stakeholders.items(), key=lambda x: x[1])[0] if any(stakeholders.values()) else 'general'
        }
    
    def _generate_business_summary(self, domain_analysis: Dict[str, Any], 
                                  impact_analysis: Dict[str, Any], 
                                  stakeholder_analysis: Dict[str, Any]) -> str:
        """Generate a business summary of AI component impact."""
        primary_domain = domain_analysis.get('primary_domain', 'general')
        primary_impact = impact_analysis.get('primary_impact_area', 'general')
        primary_stakeholder = stakeholder_analysis.get('primary_stakeholder', 'general')
        
        high_impact = impact_analysis.get('impact_levels', {}).get('high', 0)
        total_domains = domain_analysis.get('total_domains_affected', 0)
        
        summary = f"AI components primarily serve the {primary_domain} business domain, "
        summary += f"with {primary_impact.replace('_', ' ')} as the main impact area. "
        summary += f"Primary stakeholders are {primary_stakeholder}. "
        
        if high_impact > 0:
            summary += f"⚠️ {high_impact} high-impact components require executive attention. "
        
        if total_domains > 1:
            summary += f"AI systems span {total_domains} business domains, indicating cross-functional impact. "
        
        summary += "Regular business review recommended for strategic alignment."
        
        return summary 