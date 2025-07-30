"""
Tests for the semantic analyzer module.
"""

import pytest
from pathlib import Path
from src.llm_integration.semantic_analyzer import SemanticAnalyzer
from src.models.schemas import NodeLevel, NodeType, ComplexityLevel
from src.models.graph_models import SymbolInfo


class TestSemanticAnalyzer:
    """Test cases for SemanticAnalyzer."""
    
    def test_analyzer_initialization(self):
        """Test that semantic analyzer initializes correctly."""
        analyzer = SemanticAnalyzer()
        assert analyzer is not None
        assert len(analyzer.cache) == 0
        assert len(analyzer.analysis_results) == 0
    
    def test_analyze_api_file_semantics(self):
        """Test semantic analysis of an API file."""
        analyzer = SemanticAnalyzer()
        
        # Mock API file data
        file_path = "api/user_controller.py"
        symbols = {
            'functions': [
                SymbolInfo('get_user', 'function', 10, file_path),
                SymbolInfo('create_user', 'function', 20, file_path),
                SymbolInfo('update_user', 'function', 30, file_path)
            ],
            'classes': [
                SymbolInfo('UserController', 'class', 5, file_path)
            ],
            'imports': [
                SymbolInfo('flask', 'import', 1, file_path),
                SymbolInfo('models.user', 'import', 2, file_path)
            ]
        }
        file_content = """
from flask import Flask, request
from models.user import User

class UserController:
    def get_user(self, user_id):
        return User.find_by_id(user_id)

    def create_user(self, user_data):
        return User.create(user_data)

    def update_user(self, user_id, user_data):
        return User.update(user_id, user_data)
"""
        
        result = analyzer.analyze_file_semantics(file_path, symbols, file_content)
        
        # Check that purpose contains relevant keywords
        assert 'user' in result['purpose'].lower() or 'api' in result['purpose'].lower() or 'controller' in result['purpose'].lower()
        assert result['level'] in ['HLD', 'LLD']
        assert result['component_type'] in ['API', 'Controller', 'Module']
        assert result['complexity'] in ['low', 'medium', 'high']
        assert 'analysis_method' in result
    
    def test_analyze_service_file_semantics(self):
        """Test semantic analysis of a service file."""
        analyzer = SemanticAnalyzer()
        
        # Mock service file data
        file_path = "services/user_service.py"
        symbols = {
            'functions': [
                SymbolInfo('validate_user_data', 'function', 15, file_path),
                SymbolInfo('process_user_registration', 'function', 25, file_path)
            ],
            'classes': [
                SymbolInfo('UserService', 'class', 10, file_path)
            ],
            'imports': [
                SymbolInfo('models.user', 'import', 1, file_path),
                SymbolInfo('utils.validators', 'import', 2, file_path)
            ]
        }
        file_content = """
from models.user import User
from utils.validators import validate_email

class UserService:
    def validate_user_data(self, user_data):
        return validate_email(user_data['email'])
    
    def process_user_registration(self, user_data):
        # Business logic here
        pass
"""
        
        result = analyzer.analyze_file_semantics(file_path, symbols, file_content)
        
        # Check that purpose contains relevant keywords
        assert 'user' in result['purpose'].lower() or 'service' in result['purpose'].lower() or 'business' in result['purpose'].lower()
        assert result['level'] in ['HLD', 'LLD']
        assert result['component_type'] in ['Service', 'Module']
        assert result['complexity'] in ['low', 'medium', 'high']
        assert 'analysis_method' in result
    
    def test_analyze_utility_file_semantics(self):
        """Test semantic analysis of a utility file."""
        analyzer = SemanticAnalyzer()
        
        # Mock utility file data
        file_path = "utils/formatters.py"
        symbols = {
            'functions': [
                SymbolInfo('format_date', 'function', 5, file_path),
                SymbolInfo('format_currency', 'function', 10, file_path),
                SymbolInfo('format_phone', 'function', 8, file_path),
                SymbolInfo('format_address', 'function', 12, file_path),
                SymbolInfo('format_name', 'function', 6, file_path)
            ],
            'classes': [],
            'imports': [
                SymbolInfo('datetime', 'import', 1, file_path),
                SymbolInfo('locale', 'import', 2, file_path)
            ]
        }
        file_content = """
import datetime
import locale

def format_date(date_obj):
    return date_obj.strftime('%Y-%m-%d')

def format_currency(amount):
    return f"${amount:.2f}"

def format_phone(phone):
    return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"

def format_address(address):
    return address.replace('\\n', ', ')

def format_name(first, last):
    return f"{first} {last}"
"""
        
        result = analyzer.analyze_file_semantics(file_path, symbols, file_content)
        
        # Check that purpose contains relevant keywords
        assert 'format' in result['purpose'].lower() or 'utility' in result['purpose'].lower()
        assert result['level'] in ['HLD', 'LLD']
        assert result['component_type'] in ['Utility', 'Function', 'Module']
        assert result['complexity'] in ['low', 'medium', 'high']
        assert 'analysis_method' in result
    
    def test_analyze_model_file_semantics(self):
        """Test semantic analysis of a model file."""
        analyzer = SemanticAnalyzer()
        
        # Mock model file data
        file_path = "models/user.py"
        symbols = {
            'functions': [
                SymbolInfo('__init__', 'function', 10, file_path),
                SymbolInfo('to_dict', 'function', 15, file_path),
                SymbolInfo('from_dict', 'function', 20, file_path)
            ],
            'classes': [
                SymbolInfo('User', 'class', 5, file_path)
            ],
            'imports': [
                SymbolInfo('datetime', 'import', 1, file_path),
                SymbolInfo('uuid', 'import', 2, file_path)
            ]
        }
        file_content = """
import datetime
import uuid

class User:
    def __init__(self, name, email):
        self.id = str(uuid.uuid4())
        self.name = name
        self.email = email
        self.created_at = datetime.datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        user = cls(data['name'], data['email'])
        user.id = data['id']
        user.created_at = datetime.datetime.fromisoformat(data['created_at'])
        return user
"""
        
        result = analyzer.analyze_file_semantics(file_path, symbols, file_content)
        
        # Check that purpose contains relevant keywords
        assert 'user' in result['purpose'].lower() or 'model' in result['purpose'].lower() or 'entity' in result['purpose'].lower()
        assert result['level'] in ['HLD', 'LLD']
        assert result['component_type'] in ['Model', 'Class', 'Module']
        assert result['complexity'] in ['low', 'medium', 'high']
        assert 'analysis_method' in result
    
    def test_cache_functionality(self):
        """Test that semantic analysis results are cached."""
        analyzer = SemanticAnalyzer()
        
        file_path = "test_file.py"
        symbols = {
            'functions': [SymbolInfo('test_func', 'function', 10, file_path)],
            'classes': [],
            'imports': []
        }
        file_content = "def test_func(): pass"
        
        # First analysis
        result1 = analyzer.analyze_file_semantics(file_path, symbols, file_content)
        
        # Second analysis (should use cache)
        result2 = analyzer.analyze_file_semantics(file_path, symbols, file_content)
        
        assert result1 == result2
        assert len(analyzer.cache) == 1
    
    def test_prepare_llm_prompt(self):
        """Test LLM prompt preparation."""
        analyzer = SemanticAnalyzer()
        
        file_path = "test_file.py"
        symbols = {
            'functions': [SymbolInfo('test_func', 'function', 10, file_path)],
            'classes': [SymbolInfo('TestClass', 'class', 5, file_path)],
            'imports': [SymbolInfo('os', 'import', 1, file_path)]
        }
        file_content = "import os\ndef test_func(): pass\nclass TestClass: pass"
        
        prompt = analyzer.prepare_llm_prompt(file_path, symbols, file_content)
        
        assert "test_file.py" in prompt
        assert "test_func" in prompt
        assert "TestClass" in prompt
        assert "os" in prompt
        assert "Content Preview:" in prompt
    
    def test_get_analysis_statistics(self):
        """Test getting analysis statistics."""
        analyzer = SemanticAnalyzer()
        
        # Perform some analysis first
        file_path = "test_file.py"
        symbols = {'functions': [], 'classes': [], 'imports': []}
        file_content = "pass"
        
        analyzer.analyze_file_semantics(file_path, symbols, file_content)
        
        stats = analyzer.get_analysis_statistics()
        
        assert stats['total_files_analyzed'] == 1
        assert stats['cached_results'] == 1
        assert stats['analysis_method'] in ['llm', 'rule_based']  # Can be either depending on LLM availability
        assert stats['llm_integration_ready'] == True 