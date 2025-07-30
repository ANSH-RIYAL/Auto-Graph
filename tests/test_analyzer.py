"""
Tests for the codebase analyzer module.
"""

import pytest
from pathlib import Path
from src.analyzer.codebase_analyzer import CodebaseAnalyzer
from src.models.schemas import NodeLevel, NodeType


class TestCodebaseAnalyzer:
    """Test cases for CodebaseAnalyzer."""
    
    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly."""
        analyzer = CodebaseAnalyzer()
        assert analyzer is not None
        assert analyzer.file_parser is not None
        assert analyzer.graph_builder is not None
        assert len(analyzer.analysis_results) == 0
    
    def test_analyze_nonexistent_codebase(self):
        """Test analyzing a non-existent codebase."""
        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze_codebase("/nonexistent/path")
        
        assert not result['success']
        assert 'error' in result
        assert result['error'] == "Invalid codebase path"
    
    def test_analyze_empty_directory(self, tmp_path):
        """Test analyzing an empty directory."""
        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze_codebase(str(tmp_path))
        
        assert not result['success']
        assert 'error' in result
    
    def test_analyze_simple_python_codebase(self, tmp_path):
        """Test analyzing a simple Python codebase."""
        # Create a simple Python codebase
        app_file = tmp_path / "app.py"
        app_file.write_text("""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    app.run()
""")
        
        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze_codebase(str(tmp_path))
        
        assert result['success']
        assert result['codebase_path'] == str(tmp_path)
        assert result['graph'] is not None
        assert result['statistics']['total_files'] == 1
        assert result['statistics']['successful_parses'] == 1
        assert result['statistics']['coverage_percentage'] == 100.0
    
    def test_analyze_multi_file_codebase(self, tmp_path):
        """Test analyzing a multi-file codebase."""
        # Create main app file
        app_file = tmp_path / "app.py"
        app_file.write_text("""
from services.calculator import CalculatorService
from models.user import User

app = Flask(__name__)
calculator = CalculatorService()

@app.route('/calculate')
def calculate():
    return calculator.add(5, 3)
""")
        
        # Create services directory
        services_dir = tmp_path / "services"
        services_dir.mkdir()
        
        calculator_file = services_dir / "calculator.py"
        calculator_file.write_text("""
class CalculatorService:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
""")
        
        # Create models directory
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        
        user_file = models_dir / "user.py"
        user_file.write_text("""
class User:
    def __init__(self, name):
        self.name = name
    
    def get_name(self):
        return self.name
""")
        
        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze_codebase(str(tmp_path))
        
        assert result['success']
        assert result['statistics']['total_files'] == 3
        assert result['statistics']['successful_parses'] == 3
        assert result['statistics']['coverage_percentage'] == 100.0
        
        # Check that we have both HLD and LLD nodes
        graph = result['graph']
        hld_nodes = [n for n in graph.nodes if n.level == NodeLevel.HLD]
        lld_nodes = [n for n in graph.nodes if n.level == NodeLevel.LLD]
        
        assert len(hld_nodes) > 0
        assert len(lld_nodes) > 0
    
    def test_graph_structure_validation(self, tmp_path):
        """Test that generated graph has proper structure."""
        # Create a simple codebase
        app_file = tmp_path / "app.py"
        app_file.write_text("""
def main():
    print("Hello, World!")

if __name__ == '__main__':
    main()
""")
        
        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze_codebase(str(tmp_path))
        
        assert result['success']
        
        # Check graph metadata
        graph = result['graph']
        assert graph.metadata.codebase_path == str(tmp_path)
        assert graph.metadata.file_count == 1
        assert graph.metadata.coverage_percentage == 100.0
        
        # Check that all nodes have proper structure
        for node in graph.nodes:
            assert node.id is not None
            assert node.name is not None
            assert node.type is not None
            assert node.level is not None
            assert node.files is not None
            assert node.metadata is not None
    
    def test_node_relationships(self, tmp_path):
        """Test that nodes have proper relationships."""
        # Create a codebase with clear relationships
        app_file = tmp_path / "app.py"
        app_file.write_text("""
from services.math import MathService

service = MathService()

def calculate():
    return service.add(1, 2)
""")
        
        services_dir = tmp_path / "services"
        services_dir.mkdir()
        
        math_file = services_dir / "math.py"
        math_file.write_text("""
class MathService:
    def add(self, a, b):
        return a + b
""")
        
        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze_codebase(str(tmp_path))
        
        assert result['success']
        
        # Check that we have edges
        graph = result['graph']
        assert len(graph.edges) > 0
        
        # Check that LLD nodes have parent HLD nodes
        lld_nodes = [n for n in graph.nodes if n.level == NodeLevel.LLD]
        for lld_node in lld_nodes:
            assert lld_node.parent is not None 