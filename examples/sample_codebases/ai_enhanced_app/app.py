"""
AI-Enhanced Application Example
Main application demonstrating AI agent usage for testing AutoGraph's agent detection.
"""

from ai_services.classifier import CustomerRiskClassifier
from ai_services.analyzer import SentimentAnalyzer
from services.business_logic import BusinessLogicService


class AIEnhancedApp:
    """Main application class demonstrating AI agent usage."""
    
    def __init__(self):
        self.risk_classifier = CustomerRiskClassifier()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.business_logic = BusinessLogicService()
    
    def process_customer_data(self, customer_data):
        """Process customer data using AI agents."""
        # Use AI to classify customer risk
        risk_score = self.risk_classifier.classify_risk(customer_data)
        
        # Use AI to analyze customer sentiment
        sentiment = self.sentiment_analyzer.analyze_sentiment(customer_data.get('feedback', ''))
        
        # Apply business logic
        result = self.business_logic.process_results(risk_score, sentiment)
        
        return {
            'risk_score': risk_score,
            'sentiment': sentiment,
            'business_decision': result
        }
    
    def generate_customer_report(self, customer_id):
        """Generate comprehensive customer report using AI."""
        # This would typically fetch customer data from database
        customer_data = self._fetch_customer_data(customer_id)
        
        # Process with AI agents
        processed_data = self.process_customer_data(customer_data)
        
        return {
            'customer_id': customer_id,
            'analysis': processed_data,
            'recommendations': self._generate_recommendations(processed_data)
        }
    
    def _fetch_customer_data(self, customer_id):
        """Fetch customer data from database."""
        # Mock implementation
        return {
            'id': customer_id,
            'name': 'John Doe',
            'email': 'john@example.com',
            'transaction_history': [
                {'amount': 100, 'type': 'purchase'},
                {'amount': 50, 'type': 'refund'}
            ],
            'feedback': 'Great service, very satisfied with the product.'
        }
    
    def _generate_recommendations(self, processed_data):
        """Generate business recommendations based on AI analysis."""
        risk_score = processed_data['risk_score']
        sentiment = processed_data['sentiment']
        
        recommendations = []
        
        if risk_score > 0.7:
            recommendations.append('High risk customer - implement additional monitoring')
        
        if sentiment < 0.3:
            recommendations.append('Negative sentiment detected - consider outreach')
        
        return recommendations


def main():
    """Main application entry point."""
    app = AIEnhancedApp()
    
    # Example usage
    customer_id = "CUST123"
    report = app.generate_customer_report(customer_id)
    
    print("AI-Enhanced Customer Report")
    print("=" * 40)
    print(f"Customer ID: {report['customer_id']}")
    print(f"Risk Score: {report['analysis']['risk_score']}")
    print(f"Sentiment: {report['analysis']['sentiment']}")
    print(f"Business Decision: {report['analysis']['business_decision']}")
    print("Recommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")


if __name__ == "__main__":
    main() 