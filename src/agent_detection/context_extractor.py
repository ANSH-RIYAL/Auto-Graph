"""
Context extractor for AutoGraph.
Extracts business context of AI agent usage.
"""

from typing import Dict, List, Any, Optional
from ..utils.logger import get_logger
from ..llm_integration.llm_client import LLMClient

logger = get_logger(__name__)


class ContextExtractor:
    """Extracts business context of AI agent usage."""
    
    def __init__(self):
        self.llm_client = LLMClient()
    
    def extract_business_context(self, file_content: str, file_path: str, 
                                agent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract business context of agent usage in a file."""
        logger.debug(f"Extracting business context for: {file_path}")
        
        # Extract basic context without LLM
        basic_context = self._extract_basic_context(file_content, agent_info)
        
        # Try to get enhanced context from LLM
        enhanced_context = self._extract_enhanced_context(file_content, file_path, agent_info)
        
        return {
            'business_purpose': enhanced_context.get('business_purpose', basic_context['business_purpose']),
            'business_impact': enhanced_context.get('business_impact', basic_context['business_impact']),
            'data_processed': enhanced_context.get('data_processed', basic_context['data_processed']),
            'decisions_made': enhanced_context.get('decisions_made', basic_context['decisions_made']),
            'stakeholders': enhanced_context.get('stakeholders', basic_context['stakeholders']),
            'compliance_implications': enhanced_context.get('compliance_implications', basic_context['compliance_implications']),
            'extraction_method': enhanced_context.get('extraction_method', 'rule_based')
        }
    
    def _extract_basic_context(self, file_content: str, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic business context using rule-based analysis."""
        content_lower = file_content.lower()
        
        # Identify business purpose based on keywords
        business_purpose = self._identify_business_purpose(content_lower)
        
        # Identify business impact
        business_impact = self._identify_business_impact(content_lower)
        
        # Identify data being processed
        data_processed = self._identify_data_processed(content_lower)
        
        # Identify decisions being made
        decisions_made = self._identify_decisions_made(content_lower)
        
        # Identify stakeholders
        stakeholders = self._identify_stakeholders(content_lower)
        
        # Identify compliance implications
        compliance_implications = self._identify_compliance_implications(content_lower)
        
        return {
            'business_purpose': business_purpose,
            'business_impact': business_impact,
            'data_processed': data_processed,
            'decisions_made': decisions_made,
            'stakeholders': stakeholders,
            'compliance_implications': compliance_implications
        }
    
    def _extract_enhanced_context(self, file_content: str, file_path: str, 
                                 agent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract enhanced business context using LLM."""
        try:
            # Create prompt for LLM analysis
            prompt = self._create_context_prompt(file_content, file_path, agent_info)
            
            # Get LLM analysis
            result = self.llm_client.analyze_component(file_path, file_content, {'prompt': prompt})
            
            if result and 'business_context' in result:
                return {
                    **result['business_context'],
                    'extraction_method': 'llm_enhanced'
                }
            
        except Exception as e:
            logger.warning(f"Failed to extract enhanced context for {file_path}: {e}")
        
        return {'extraction_method': 'rule_based'}
    
    def _create_context_prompt(self, file_content: str, file_path: str, 
                              agent_info: Dict[str, Any]) -> str:
        """Create prompt for LLM context extraction."""
        agent_types = agent_info.get('agent_types', [])
        
        return f"""
        Analyze this code file for business context of AI agent usage:
        
        File: {file_path}
        AI Agents Used: {', '.join(agent_types)}
        
        Code:
        {file_content[:2000]}  # Limit content for token efficiency
        
        Please provide business context analysis in JSON format:
        {{
            "business_context": {{
                "business_purpose": "What business purpose does this AI component serve?",
                "business_impact": "What is the business impact if this AI fails?",
                "data_processed": "What type of data does this AI process?",
                "decisions_made": "What business decisions does this AI make?",
                "stakeholders": "Who are the stakeholders affected by this AI?",
                "compliance_implications": "What compliance implications does this AI have?"
            }}
        }}
        
        Focus on business value and risk, not technical implementation.
        """
    
    def _identify_business_purpose(self, content: str) -> str:
        """Identify business purpose based on keywords."""
        purposes = []
        
        if any(word in content for word in ['classify', 'categorize', 'sort']):
            purposes.append('Classification')
        if any(word in content for word in ['recommend', 'suggest', 'recommendation']):
            purposes.append('Recommendation')
        if any(word in content for word in ['analyze', 'analysis', 'insight']):
            purposes.append('Analysis')
        if any(word in content for word in ['predict', 'forecast', 'prediction']):
            purposes.append('Prediction')
        if any(word in content for word in ['generate', 'create', 'produce']):
            purposes.append('Content Generation')
        if any(word in content for word in ['translate', 'language', 'text']):
            purposes.append('Language Processing')
        
        return ', '.join(purposes) if purposes else 'AI-powered processing'
    
    def _identify_business_impact(self, content: str) -> str:
        """Identify business impact of AI failure."""
        if any(word in content for word in ['customer', 'user', 'client']):
            return 'Customer experience and satisfaction'
        if any(word in content for word in ['revenue', 'sales', 'profit']):
            return 'Revenue and financial performance'
        if any(word in content for word in ['security', 'compliance', 'legal']):
            return 'Security and compliance risks'
        if any(word in content for word in ['operation', 'process', 'workflow']):
            return 'Operational efficiency'
        
        return 'General business operations'
    
    def _identify_data_processed(self, content: str) -> str:
        """Identify data being processed."""
        data_types = []
        
        if any(word in content for word in ['customer', 'user', 'personal']):
            data_types.append('Customer data')
        if any(word in content for word in ['financial', 'payment', 'transaction']):
            data_types.append('Financial data')
        if any(word in content for word in ['text', 'document', 'content']):
            data_types.append('Text content')
        if any(word in content for word in ['image', 'photo', 'visual']):
            data_types.append('Image data')
        if any(word in content for word in ['log', 'event', 'activity']):
            data_types.append('Log data')
        
        return ', '.join(data_types) if data_types else 'General data'
    
    def _identify_decisions_made(self, content: str) -> str:
        """Identify decisions being made by AI."""
        decisions = []
        
        if any(word in content for word in ['approve', 'reject', 'decision']):
            decisions.append('Approval/Rejection decisions')
        if any(word in content for word in ['classify', 'categorize', 'label']):
            decisions.append('Classification decisions')
        if any(word in content for word in ['recommend', 'suggest', 'advise']):
            decisions.append('Recommendation decisions')
        if any(word in content for word in ['route', 'direct', 'assign']):
            decisions.append('Routing decisions')
        
        return ', '.join(decisions) if decisions else 'AI-powered decisions'
    
    def _identify_stakeholders(self, content: str) -> str:
        """Identify stakeholders affected by AI."""
        stakeholders = []
        
        if any(word in content for word in ['customer', 'user', 'client']):
            stakeholders.append('Customers')
        if any(word in content for word in ['employee', 'staff', 'team']):
            stakeholders.append('Employees')
        if any(word in content for word in ['manager', 'executive', 'leadership']):
            stakeholders.append('Management')
        if any(word in content for word in ['regulator', 'compliance', 'auditor']):
            stakeholders.append('Regulators')
        
        return ', '.join(stakeholders) if stakeholders else 'Business stakeholders'
    
    def _identify_compliance_implications(self, content: str) -> str:
        """Identify compliance implications."""
        implications = []
        
        if any(word in content for word in ['gdpr', 'privacy', 'personal']):
            implications.append('GDPR/Privacy compliance')
        if any(word in content for word in ['hipaa', 'health', 'medical']):
            implications.append('HIPAA compliance')
        if any(word in content for word in ['sox', 'financial', 'audit']):
            implications.append('SOX compliance')
        if any(word in content for word in ['pci', 'payment', 'card']):
            implications.append('PCI compliance')
        
        return ', '.join(implications) if implications else 'General compliance requirements' 