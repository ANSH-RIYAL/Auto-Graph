"""
Risk assessor for AutoGraph.
Assesses business risk of AI agent components.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RiskLevel(Enum):
    """Risk levels for agent components."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskAssessor:
    """Assesses business risk of AI agent components."""
    
    def __init__(self):
        # Risk factors and their weights
        self.risk_factors = {
            'customer_data': 3,
            'financial_logic': 3,
            'security_decisions': 3,
            'regulatory_compliance': 3,
            'high_volume': 2,
            'real_time': 2,
            'automated_decisions': 2,
            'sensitive_business_logic': 2,
            'external_api_dependency': 1,
            'complex_ai_model': 1
        }
        
        # Keywords that indicate high-risk areas
        self.high_risk_keywords = {
            'customer_data': [
                'customer', 'user', 'personal', 'private', 'sensitive',
                'credit_card', 'ssn', 'password', 'email', 'address'
            ],
            'financial_logic': [
                'payment', 'transaction', 'money', 'currency', 'price',
                'cost', 'revenue', 'profit', 'loss', 'financial'
            ],
            'security_decisions': [
                'auth', 'authentication', 'authorization', 'security',
                'permission', 'access', 'login', 'password'
            ],
            'regulatory_compliance': [
                'compliance', 'regulation', 'legal', 'law', 'policy',
                'gdpr', 'hipaa', 'sox', 'pci'
            ],
            'high_volume': [
                'batch', 'bulk', 'mass', 'scale', 'high_volume',
                'thousands', 'millions', 'stream'
            ],
            'real_time': [
                'real_time', 'realtime', 'live', 'instant', 'immediate',
                'synchronous', 'blocking'
            ],
            'automated_decisions': [
                'decision', 'choice', 'select', 'approve', 'reject',
                'classify', 'categorize', 'recommend'
            ],
            'sensitive_business_logic': [
                'business_logic', 'core_logic', 'critical', 'essential',
                'mission_critical', 'key_process'
            ],
            'external_api_dependency': [
                'api', 'external', 'third_party', 'dependency', 'service'
            ],
            'complex_ai_model': [
                'model', 'neural', 'deep_learning', 'ml', 'ai_model',
                'complex', 'sophisticated'
            ]
        }
    
    def assess_risk(self, file_content: str, file_path: str, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the business risk of an agent component."""
        logger.debug(f"Assessing risk for: {file_path}")
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(file_content, agent_info)
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(file_content)
        
        # Generate risk summary
        risk_summary = self._generate_risk_summary(risk_level, risk_factors, agent_info)
        
        return {
            'risk_level': risk_level.value,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'risk_summary': risk_summary,
            'file_path': file_path
        }
    
    def _calculate_risk_score(self, file_content: str, agent_info: Dict[str, Any]) -> int:
        """Calculate risk score based on content and agent usage."""
        score = 0
        
        # Base score for agent usage
        if agent_info.get('has_agent'):
            score += 1
        
        # Add score for each risk factor found
        for factor, weight in self.risk_factors.items():
            if self._contains_risk_factor(file_content, factor):
                score += weight
        
        # Additional score for multiple agent types
        agent_types = agent_info.get('agent_types', [])
        if len(agent_types) > 1:
            score += 1
        
        return score
    
    def _determine_risk_level(self, risk_score: int) -> RiskLevel:
        """Determine risk level based on score."""
        if risk_score >= 6:
            return RiskLevel.HIGH
        elif risk_score >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _identify_risk_factors(self, file_content: str) -> List[str]:
        """Identify risk factors present in the file."""
        factors = []
        
        for factor, keywords in self.high_risk_keywords.items():
            for keyword in keywords:
                if keyword.lower() in file_content.lower():
                    factors.append(factor)
                    break
        
        return list(set(factors))  # Remove duplicates
    
    def _contains_risk_factor(self, file_content: str, factor: str) -> bool:
        """Check if file contains a specific risk factor."""
        keywords = self.high_risk_keywords.get(factor, [])
        return any(keyword.lower() in file_content.lower() for keyword in keywords)
    
    def _generate_risk_summary(self, risk_level: RiskLevel, risk_factors: List[str], 
                              agent_info: Dict[str, Any]) -> str:
        """Generate a human-readable risk summary."""
        agent_types = agent_info.get('agent_types', [])
        
        summary = f"This component uses {', '.join(agent_types)} AI agents "
        
        if risk_level == RiskLevel.HIGH:
            summary += "and poses HIGH business risk due to "
        elif risk_level == RiskLevel.MEDIUM:
            summary += "and poses MEDIUM business risk due to "
        else:
            summary += "and poses LOW business risk."
            return summary
        
        if risk_factors:
            summary += f"involvement in {', '.join(risk_factors)}."
        else:
            summary += "its AI agent usage."
        
        return summary 