"""
Customer Risk Classifier
Uses OpenAI to classify customer risk based on transaction data.
"""

import openai
from typing import Dict, Any


class CustomerRiskClassifier:
    """AI-powered customer risk classification using OpenAI."""
    
    def __init__(self, api_key: str = None):
        """Initialize the classifier with OpenAI API key."""
        if api_key:
            openai.api_key = api_key
        # In production, this would be loaded from environment variables
    
    def classify_risk(self, customer_data: Dict[str, Any]) -> float:
        """Classify customer risk using OpenAI GPT-4."""
        try:
            # Prepare the prompt for risk classification
            prompt = self._create_risk_prompt(customer_data)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial risk assessment expert. Analyze customer data and provide a risk score between 0 and 1, where 0 is low risk and 1 is high risk."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            # Extract and parse the risk score
            risk_score_text = response.choices[0].message.content.strip()
            risk_score = self._parse_risk_score(risk_score_text)
            
            return risk_score
            
        except Exception as e:
            print(f"Error in risk classification: {e}")
            return 0.5  # Default to medium risk on error
    
    def _create_risk_prompt(self, customer_data: Dict[str, Any]) -> str:
        """Create a prompt for risk classification."""
        transaction_history = customer_data.get('transaction_history', [])
        
        prompt = f"""
        Analyze the following customer data and provide a risk score:
        
        Customer Information:
        - Name: {customer_data.get('name', 'Unknown')}
        - Email: {customer_data.get('email', 'Unknown')}
        
        Transaction History:
        {self._format_transactions(transaction_history)}
        
        Please provide only a number between 0 and 1 representing the risk score.
        """
        
        return prompt
    
    def _format_transactions(self, transactions: list) -> str:
        """Format transaction history for the prompt."""
        if not transactions:
            return "No transaction history available."
        
        formatted = []
        for tx in transactions:
            formatted.append(f"- {tx.get('type', 'unknown')}: ${tx.get('amount', 0)}")
        
        return "\n".join(formatted)
    
    def _parse_risk_score(self, score_text: str) -> float:
        """Parse risk score from OpenAI response."""
        try:
            # Extract numeric value from response
            import re
            numbers = re.findall(r'\d+\.?\d*', score_text)
            if numbers:
                score = float(numbers[0])
                return max(0.0, min(1.0, score))  # Clamp between 0 and 1
            else:
                return 0.5  # Default to medium risk
        except (ValueError, IndexError):
            return 0.5  # Default to medium risk
    
    def get_risk_explanation(self, customer_data: Dict[str, Any]) -> str:
        """Get explanation for risk classification."""
        try:
            prompt = f"""
            Explain why the following customer has the given risk level:
            
            Customer Data: {customer_data}
            
            Provide a brief explanation of the risk factors.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial risk assessment expert. Provide clear, concise explanations of risk factors."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Unable to generate risk explanation: {e}" 