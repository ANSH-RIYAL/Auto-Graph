"""
Tests for the file parser module.
"""

import pytest
from pathlib import Path
from src.parser.file_parser import FileParser
from src.parser.ast_parser import PythonASTParser


class TestFileParser:
    """Test cases for FileParser."""
    
    def test_parser_initialization(self):
        """Test that parser initializes correctly."""
        parser = FileParser()
        assert parser is not None
        assert parser.total_files == 0
        assert parser.successful_parses == 0
        assert len(parser.parsed_files) == 0
        assert len(parser.failed_files) == 0
    
    def test_parse_nonexistent_codebase(self):
        """Test parsing a non-existent codebase."""
        parser = FileParser()
        result = parser.parse_codebase("/nonexistent/path")
        
        assert not result['success']
        assert 'error' in result
        assert result['parsing_stats']['total_files'] == 0
    
    def test_parse_empty_directory(self, tmp_path):
        """Test parsing an empty directory."""
        parser = FileParser()
        result = parser.parse_codebase(str(tmp_path))
        
        assert result['success']
        assert result['parsing_stats']['total_files'] == 0
        assert result['parsing_stats']['coverage_percentage'] == 100.0


class TestPythonASTParser:
    """Test cases for PythonASTParser."""
    
    def test_parser_initialization(self):
        """Test that AST parser initializes correctly."""
        parser = PythonASTParser()
        assert parser is not None
        assert len(parser.imports) == 0
        assert len(parser.functions) == 0
        assert len(parser.classes) == 0
        assert len(parser.variables) == 0
        assert len(parser.errors) == 0
    
    def test_parse_simple_python_file(self, tmp_path):
        """Test parsing a simple Python file."""
        # Create a simple Python file
        python_file = tmp_path / "test.py"
        python_file.write_text("""
import os
import sys

def hello_world():
    print("Hello, World!")

class TestClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value

x = 10
""")
        
        parser = PythonASTParser()
        success = parser.parse_file(python_file)
        
        assert success
        assert len(parser.imports) == 2
        assert 'os' in parser.imports
        assert 'sys' in parser.imports
        assert len(parser.functions) == 3  # hello_world, __init__, get_value
        assert len(parser.classes) == 1
        assert len(parser.variables) == 1
    
    def test_parse_invalid_python_file(self, tmp_path):
        """Test parsing an invalid Python file."""
        # Create an invalid Python file
        python_file = tmp_path / "invalid.py"
        python_file.write_text("""
def invalid_function(
    # Missing closing parenthesis
""")
        
        parser = PythonASTParser()
        success = parser.parse_file(python_file)
        
        assert not success
        assert len(parser.errors) > 0
    
    def test_parse_nonexistent_file(self, tmp_path):
        """Test parsing a non-existent file."""
        parser = PythonASTParser()
        nonexistent_file = tmp_path / "nonexistent.py"
        
        success = parser.parse_file(nonexistent_file)
        
        assert not success
    
    def test_get_symbols(self, tmp_path):
        """Test getting symbols from parsed file."""
        # Create a Python file with various symbols
        python_file = tmp_path / "symbols.py"
        python_file.write_text("""
import math
from typing import List

def calculate_area(radius: float) -> float:
    return math.pi * radius ** 2

class Circle:
    def __init__(self, radius: float):
        self.radius = radius
    
    def area(self) -> float:
        return calculate_area(self.radius)

PI = 3.14159
""")
        
        parser = PythonASTParser()
        parser.parse_file(python_file)
        
        symbols = parser.get_symbols()
        
        assert 'imports' in symbols
        assert 'functions' in symbols
        assert 'classes' in symbols
        assert 'variables' in symbols
        
        assert len(symbols['imports']) == 2
        assert len(symbols['functions']) == 3  # calculate_area, __init__, area
        assert len(symbols['classes']) == 1
        assert len(symbols['variables']) == 1 