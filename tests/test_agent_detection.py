"""
Tests for agent detection functionality.
"""

import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agent_detection.agent_detector import AgentDetector
from agent_detection.risk_assessor import RiskAssessor, RiskLevel
from agent_detection.context_extractor import ContextExtractor


class TestAgentDetector(unittest.TestCase):
    """Test agent detection functionality."""
    
    def setUp(self):
        self.detector = AgentDetector()
    
    def test_detect_openai_usage(self):
        """Test detection of OpenAI usage."""
        content = """
        import openai
        
        def analyze_text(text):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": text}]
            )
            return response.choices[0].message.content
        """
        
        result = self.detector.detect_agent_usage(content, "test.py")
        
        self.assertTrue(result['has_agent'])
        self.assertIn('openai', result['agent_types'])
        self.assertGreater(result['total_matches'], 0)
    
    def test_detect_langchain_usage(self):
        """Test detection of LangChain usage."""
        content = """
        from langchain import LLMChain, PromptTemplate
        
        def create_chain():
            template = PromptTemplate(input_variables=["question"], template="Answer: {question}")
            chain = LLMChain(llm=llm, prompt=template)
            return chain
        """
        
        result = self.detector.detect_agent_usage(content, "test.py")
        
        self.assertTrue(result['has_agent'])
        self.assertIn('langchain', result['agent_types'])
    
    def test_detect_anthropic_usage(self):
        """Test detection of Anthropic usage."""
        content = """
        from anthropic import Anthropic
        
        client = Anthropic(api_key="your-key")
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": "Hello"}]
        )
        """
        
        result = self.detector.detect_agent_usage(content, "test.py")
        
        self.assertTrue(result['has_agent'])
        self.assertIn('anthropic', result['agent_types'])
    
    def test_no_agent_usage(self):
        """Test detection when no agents are used."""
        content = """
        def calculate_sum(a, b):
            return a + b
        
        class Calculator:
            def multiply(self, x, y):
                return x * y
        """
        
        result = self.detector.detect_agent_usage(content, "test.py")
        
        self.assertFalse(result['has_agent'])
        self.assertEqual(result['total_matches'], 0)
    
    def test_analyze_agent_context(self):
        """Test agent context analysis."""
        content = """
        import openai
        
        def ai_classifier(data):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Classify: {data}"}]
            )
            return response.choices[0].message.content
        
        class DataProcessor:
            def process_with_ai(self, input_data):
                return ai_classifier(input_data)
        """
        
        symbols = {
            'functions': ['ai_classifier'],
            'classes': ['DataProcessor']
        }
        
        result = self.detector.analyze_agent_context(content, symbols)
        
        self.assertIn('ai_classifier', result['agent_functions'])
        self.assertIn('DataProcessor', result['agent_classes'])


class TestRiskAssessor(unittest.TestCase):
    """Test risk assessment functionality."""
    
    def setUp(self):
        self.assessor = RiskAssessor()
    
    def test_assess_high_risk(self):
        """Test assessment of high-risk component."""
        content = """
        def process_customer_payment(customer_data, payment_info):
            # Process customer payment using AI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Process payment: {payment_info}"}]
            )
            return response.choices[0].message.content
        """
        
        agent_info = {
            'has_agent': True,
            'agent_types': ['openai']
        }
        
        result = self.assessor.assess_risk(content, "payment_processor.py", agent_info)
        
        self.assertEqual(result['risk_level'], 'high')
        self.assertGreater(result['risk_score'], 5)
        self.assertIn('customer_data', result['risk_factors'])
        self.assertIn('financial_logic', result['risk_factors'])
    
    def test_assess_medium_risk(self):
        """Test assessment of medium-risk component."""
        content = """
        def analyze_user_preferences(user_data):
            # Analyze user preferences using AI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Analyze: {user_data}"}]
            )
            return response.choices[0].message.content
        """
        
        agent_info = {
            'has_agent': True,
            'agent_types': ['openai']
        }
        
        result = self.assessor.assess_risk(content, "preference_analyzer.py", agent_info)
        
        self.assertEqual(result['risk_level'], 'medium')
        self.assertIn('customer_data', result['risk_factors'])
    
    def test_assess_low_risk(self):
        """Test assessment of low-risk component."""
        content = """
        def generate_creative_content(topic):
            # Generate creative content using AI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Write about: {topic}"}]
            )
            return response.choices[0].message.content
        """
        
        agent_info = {
            'has_agent': True,
            'agent_types': ['openai']
        }
        
        result = self.assessor.assess_risk(content, "content_generator.py", agent_info)
        
        self.assertEqual(result['risk_level'], 'low')
        self.assertEqual(len(result['risk_factors']), 0)


class TestContextExtractor(unittest.TestCase):
    """Test context extraction functionality."""
    
    def setUp(self):
        self.extractor = ContextExtractor()
    
    @patch('agent_detection.context_extractor.LLMClient')
    def test_extract_basic_context(self, mock_llm_client):
        """Test basic context extraction."""
        content = """
        def classify_customer_risk(customer_data):
            # Classify customer risk using AI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Classify risk: {customer_data}"}]
            )
            return response.choices[0].message.content
        """
        
        agent_info = {
            'has_agent': True,
            'agent_types': ['openai']
        }
        
        result = self.extractor.extract_business_context(content, "risk_classifier.py", agent_info)
        
        self.assertIn('Classification', result['business_purpose'])
        self.assertIn('Customer data', result['data_processed'])
        self.assertIn('Customers', result['stakeholders'])


if __name__ == '__main__':
    unittest.main() 