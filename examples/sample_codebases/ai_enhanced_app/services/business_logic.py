"""
Business Logic Service
Contains business logic for processing AI analysis results.
"""

from typing import Dict, Any


class BusinessLogicService:
    """Business logic service for processing AI analysis results."""
    
    def __init__(self):
        """Initialize the business logic service."""
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.7,
            'high': 0.9
        }
        
        self.sentiment_thresholds = {
            'positive': 0.3,
            'negative': -0.3
        }
    
    def process_results(self, risk_score: float, sentiment_score: float) -> Dict[str, Any]:
        """Process AI analysis results and make business decisions."""
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        # Determine sentiment level
        sentiment_level = self._determine_sentiment_level(sentiment_score)
        
        # Make business decisions based on risk and sentiment
        decisions = self._make_business_decisions(risk_level, sentiment_level)
        
        return {
            'risk_level': risk_level,
            'sentiment_level': sentiment_level,
            'decisions': decisions,
            'priority': self._calculate_priority(risk_score, sentiment_score)
        }
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score."""
        if risk_score >= self.risk_thresholds['high']:
            return 'high'
        elif risk_score >= self.risk_thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _determine_sentiment_level(self, sentiment_score: float) -> str:
        """Determine sentiment level based on score."""
        if sentiment_score >= self.sentiment_thresholds['positive']:
            return 'positive'
        elif sentiment_score <= self.sentiment_thresholds['negative']:
            return 'negative'
        else:
            return 'neutral'
    
    def _make_business_decisions(self, risk_level: str, sentiment_level: str) -> list:
        """Make business decisions based on risk and sentiment levels."""
        decisions = []
        
        # Risk-based decisions
        if risk_level == 'high':
            decisions.append('Implement enhanced monitoring')
            decisions.append('Require manual review')
            decisions.append('Set up alerts for unusual activity')
        elif risk_level == 'medium':
            decisions.append('Schedule periodic review')
            decisions.append('Monitor for changes')
        
        # Sentiment-based decisions
        if sentiment_level == 'negative':
            decisions.append('Initiate customer outreach')
            decisions.append('Review customer service interactions')
            decisions.append('Consider retention strategies')
        elif sentiment_level == 'positive':
            decisions.append('Consider upselling opportunities')
            decisions.append('Request testimonials')
        
        # Combined decisions
        if risk_level == 'high' and sentiment_level == 'negative':
            decisions.append('URGENT: High-risk customer with negative sentiment')
            decisions.append('Escalate to senior management')
        
        return decisions
    
    def _calculate_priority(self, risk_score: float, sentiment_score: float) -> str:
        """Calculate priority level based on risk and sentiment."""
        # High priority for high risk or very negative sentiment
        if risk_score >= self.risk_thresholds['high'] or sentiment_score <= -0.7:
            return 'high'
        # Medium priority for medium risk or negative sentiment
        elif risk_score >= self.risk_thresholds['medium'] or sentiment_score <= self.sentiment_thresholds['negative']:
            return 'medium'
        else:
            return 'low'
    
    def generate_action_plan(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an action plan based on analysis results."""
        risk_level = analysis_results.get('risk_level', 'low')
        sentiment_level = analysis_results.get('sentiment_level', 'neutral')
        priority = analysis_results.get('priority', 'low')
        
        action_plan = {
            'immediate_actions': [],
            'short_term_actions': [],
            'long_term_actions': [],
            'monitoring_requirements': [],
            'escalation_path': []
        }
        
        # Immediate actions (within 24 hours)
        if priority == 'high':
            action_plan['immediate_actions'].extend([
                'Review customer account immediately',
                'Contact customer service team',
                'Implement account restrictions if necessary'
            ])
        
        if risk_level == 'high':
            action_plan['immediate_actions'].append('Freeze account pending review')
        
        if sentiment_level == 'negative':
            action_plan['immediate_actions'].append('Initiate customer outreach')
        
        # Short-term actions (within 1 week)
        if risk_level in ['medium', 'high']:
            action_plan['short_term_actions'].extend([
                'Schedule detailed account review',
                'Update risk assessment',
                'Implement additional monitoring'
            ])
        
        # Long-term actions (within 1 month)
        action_plan['long_term_actions'].extend([
            'Review and update risk models',
            'Analyze patterns for similar customers',
            'Update business processes if needed'
        ])
        
        # Monitoring requirements
        if risk_level == 'high':
            action_plan['monitoring_requirements'].extend([
                'Daily account activity monitoring',
                'Real-time transaction alerts',
                'Weekly risk assessment reviews'
            ])
        elif risk_level == 'medium':
            action_plan['monitoring_requirements'].extend([
                'Weekly account activity monitoring',
                'Monthly risk assessment reviews'
            ])
        
        # Escalation path
        if priority == 'high':
            action_plan['escalation_path'] = [
                'Customer Service Manager',
                'Risk Management Team',
                'Senior Management'
            ]
        elif priority == 'medium':
            action_plan['escalation_path'] = [
                'Customer Service Team Lead',
                'Risk Management Team'
            ]
        
        return action_plan
    
    def calculate_business_impact(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate potential business impact of the analysis."""
        risk_level = analysis_results.get('risk_level', 'low')
        sentiment_level = analysis_results.get('sentiment_level', 'neutral')
        
        impact = {
            'financial_risk': 'low',
            'reputation_risk': 'low',
            'operational_impact': 'low',
            'customer_impact': 'low',
            'recommended_budget': 0
        }
        
        # Financial risk assessment
        if risk_level == 'high':
            impact['financial_risk'] = 'high'
            impact['recommended_budget'] = 10000  # $10k for high-risk mitigation
        elif risk_level == 'medium':
            impact['financial_risk'] = 'medium'
            impact['recommended_budget'] = 5000   # $5k for medium-risk mitigation
        
        # Reputation risk assessment
        if sentiment_level == 'negative':
            impact['reputation_risk'] = 'medium'
            if risk_level == 'high':
                impact['reputation_risk'] = 'high'
        
        # Operational impact
        if risk_level == 'high':
            impact['operational_impact'] = 'high'
        elif risk_level == 'medium':
            impact['operational_impact'] = 'medium'
        
        # Customer impact
        if sentiment_level == 'negative':
            impact['customer_impact'] = 'high'
        elif sentiment_level == 'positive':
            impact['customer_impact'] = 'low'
        
        return impact 