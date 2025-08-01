"""
Sentiment Analyzer
Uses LangChain to analyze customer sentiment from feedback.
"""

from langchain import LLMChain, PromptTemplate
from langchain.llms import OpenAI
from typing import Dict, Any


class SentimentAnalyzer:
    """AI-powered sentiment analysis using LangChain."""
    
    def __init__(self, api_key: str = None):
        """Initialize the sentiment analyzer with LangChain."""
        if api_key:
            self.llm = OpenAI(openai_api_key=api_key, temperature=0.1)
        else:
            # In production, this would be loaded from environment variables
            self.llm = OpenAI(temperature=0.1)
        
        # Create the sentiment analysis chain
        self.sentiment_chain = self._create_sentiment_chain()
    
    def _create_sentiment_chain(self) -> LLMChain:
        """Create the LangChain for sentiment analysis."""
        template = """
        Analyze the sentiment of the following customer feedback and provide a sentiment score between -1 and 1, where:
        -1 = Very negative
        0 = Neutral
        1 = Very positive
        
        Customer Feedback: {feedback}
        
        Provide only the sentiment score as a number.
        """
        
        prompt = PromptTemplate(
            input_variables=["feedback"],
            template=template
        )
        
        return LLMChain(llm=self.llm, prompt=prompt)
    
    def analyze_sentiment(self, feedback: str) -> float:
        """Analyze sentiment of customer feedback."""
        try:
            if not feedback or feedback.strip() == "":
                return 0.0  # Neutral for empty feedback
            
            # Run the sentiment analysis chain
            result = self.sentiment_chain.run(feedback=feedback)
            
            # Parse the sentiment score
            sentiment_score = self._parse_sentiment_score(result)
            
            return sentiment_score
            
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return 0.0  # Default to neutral on error
    
    def _parse_sentiment_score(self, result: str) -> float:
        """Parse sentiment score from LangChain response."""
        try:
            import re
            # Extract numeric value from response
            numbers = re.findall(r'-?\d+\.?\d*', result)
            if numbers:
                score = float(numbers[0])
                return max(-1.0, min(1.0, score))  # Clamp between -1 and 1
            else:
                return 0.0  # Default to neutral
        except (ValueError, IndexError):
            return 0.0  # Default to neutral
    
    def get_sentiment_explanation(self, feedback: str) -> str:
        """Get explanation for sentiment analysis."""
        try:
            template = """
            Analyze the sentiment of the following customer feedback and explain why:
            
            Feedback: {feedback}
            
            Provide a brief explanation of the sentiment analysis.
            """
            
            prompt = PromptTemplate(
                input_variables=["feedback"],
                template=template
            )
            
            explanation_chain = LLMChain(llm=self.llm, prompt=prompt)
            result = explanation_chain.run(feedback=feedback)
            
            return result.strip()
            
        except Exception as e:
            return f"Unable to generate sentiment explanation: {e}"
    
    def analyze_batch_sentiment(self, feedback_list: list) -> list:
        """Analyze sentiment for multiple feedback items."""
        results = []
        
        for feedback in feedback_list:
            sentiment_score = self.analyze_sentiment(feedback)
            results.append({
                'feedback': feedback,
                'sentiment_score': sentiment_score,
                'sentiment_label': self._get_sentiment_label(sentiment_score)
            })
        
        return results
    
    def _get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label."""
        if score >= 0.7:
            return "Very Positive"
        elif score >= 0.3:
            return "Positive"
        elif score >= -0.3:
            return "Neutral"
        elif score >= -0.7:
            return "Negative"
        else:
            return "Very Negative"
    
    def get_sentiment_summary(self, feedback_list: list) -> Dict[str, Any]:
        """Get summary statistics for sentiment analysis."""
        if not feedback_list:
            return {
                'average_sentiment': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'total_count': 0
            }
        
        batch_results = self.analyze_batch_sentiment(feedback_list)
        
        scores = [result['sentiment_score'] for result in batch_results]
        average_sentiment = sum(scores) / len(scores)
        
        positive_count = sum(1 for score in scores if score > 0.3)
        negative_count = sum(1 for score in scores if score < -0.3)
        neutral_count = len(scores) - positive_count - negative_count
        
        return {
            'average_sentiment': average_sentiment,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'total_count': len(scores)
        } 