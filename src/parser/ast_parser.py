"""
AST-based parser for Python files.
Extracts functions, classes, imports, and other symbols from Python source code.
"""

import ast
import ast_comments
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from ..utils.logger import get_logger
from ..models.graph_models import SymbolInfo

logger = get_logger(__name__)


class PythonASTParser:
    """AST parser for Python files."""
    
    def __init__(self):
        self.imports: List[str] = []
        self.functions: List[SymbolInfo] = []
        self.classes: List[SymbolInfo] = []
        self.variables: List[SymbolInfo] = []
        self.errors: List[str] = []
    
    def parse_file(self, file_path: Path) -> bool:
        """Parse a Python file and extract symbols."""
        try:
            content = self._read_file(file_path)
            if content is None:
                return False
            
            # Parse with ast_comments to handle comments
            tree = ast_comments.parse(content)
            
            # Reset state
            self.imports.clear()
            self.functions.clear()
            self.classes.clear()
            self.variables.clear()
            self.errors.clear()
            
            # Visit all nodes
            visitor = PythonSymbolVisitor(file_path)
            visitor.visit(tree)
            
            # Collect results
            self.imports = visitor.imports
            self.functions = visitor.functions
            self.classes = visitor.classes
            self.variables = visitor.variables
            
            logger.debug(f"Parsed {file_path}: {len(self.functions)} functions, {len(self.classes)} classes, {len(self.imports)} imports")
            return True
            
        except SyntaxError as e:
            error_msg = f"Syntax error in {file_path}: {e}"
            logger.warning(error_msg)
            self.errors.append(error_msg)
            return False
        except Exception as e:
            error_msg = f"Error parsing {file_path}: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def _read_file(self, file_path: Path) -> Optional[str]:
        """Read file content with proper encoding."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Could not read file {file_path}: {e}")
                return None
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def get_symbols(self) -> Dict[str, List[SymbolInfo]]:
        """Get all extracted symbols."""
        return {
            'imports': [SymbolInfo(name=imp, type='import', line_number=0, file_path='') for imp in self.imports],
            'functions': self.functions,
            'classes': self.classes,
            'variables': self.variables
        }
    
    def get_imports(self) -> List[str]:
        """Get list of imports."""
        return self.imports
    
    def get_functions(self) -> List[SymbolInfo]:
        """Get list of functions."""
        return self.functions
    
    def get_classes(self) -> List[SymbolInfo]:
        """Get list of classes."""
        return self.classes
    
    def get_errors(self) -> List[str]:
        """Get list of parsing errors."""
        return self.errors


class PythonSymbolVisitor(ast.NodeVisitor):
    """AST visitor for extracting symbols from Python code."""
    
    def __init__(self, file_path: Path):
        self.file_path = str(file_path)
        self.imports: List[str] = []
        self.functions: List[SymbolInfo] = []
        self.classes: List[SymbolInfo] = []
        self.variables: List[SymbolInfo] = []
        self.current_class: Optional[str] = None
    
    def visit_Import(self, node: ast.Import):
        """Visit import statements."""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from-import statements."""
        module = node.module or ""
        for alias in node.names:
            if module:
                self.imports.append(f"{module}.{alias.name}")
            else:
                self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions."""
        symbol = SymbolInfo(
            name=node.name,
            type='function',
            line_number=node.lineno,
            file_path=self.file_path,
            parent=self.current_class
        )
        self.functions.append(symbol)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definitions."""
        symbol = SymbolInfo(
            name=node.name,
            type='async_function',
            line_number=node.lineno,
            file_path=self.file_path,
            parent=self.current_class
        )
        self.functions.append(symbol)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions."""
        symbol = SymbolInfo(
            name=node.name,
            type='class',
            line_number=node.lineno,
            file_path=self.file_path,
            parent=None
        )
        self.classes.append(symbol)
        
        # Track current class for nested functions
        previous_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = previous_class
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment statements (for variable tracking)."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                symbol = SymbolInfo(
                    name=target.id,
                    type='variable',
                    line_number=node.lineno,
                    file_path=self.file_path,
                    parent=self.current_class
                )
                self.variables.append(symbol)
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Visit annotated assignment statements."""
        if isinstance(node.target, ast.Name):
            symbol = SymbolInfo(
                name=node.target.id,
                type='variable',
                line_number=node.lineno,
                file_path=self.file_path,
                parent=self.current_class
            )
            self.variables.append(symbol)
        self.generic_visit(node)


class ASTAnalyzer:
    """Advanced AST analysis utilities."""
    
    @staticmethod
    def get_function_complexity(func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    @staticmethod
    def get_class_methods(class_node: ast.ClassDef) -> List[str]:
        """Get all method names in a class."""
        methods = []
        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(node.name)
        return methods
    
    @staticmethod
    def get_class_bases(class_node: ast.ClassDef) -> List[str]:
        """Get base class names for a class."""
        bases = []
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                # Handle cases like 'module.Class'
                bases.append(ASTAnalyzer._get_attribute_name(base))
        return bases
    
    @staticmethod
    def _get_attribute_name(node: ast.Attribute) -> str:
        """Get full attribute name (e.g., 'module.Class')."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{ASTAnalyzer._get_attribute_name(node.value)}.{node.attr}"
        else:
            return node.attr
    
    @staticmethod
    def get_function_parameters(func_node: ast.FunctionDef) -> List[str]:
        """Get parameter names for a function."""
        params = []
        for arg in func_node.args.args:
            params.append(arg.arg)
        return params
    
    @staticmethod
    def get_decorators(node: ast.FunctionDef) -> List[str]:
        """Get decorator names for a function or class."""
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(ASTAnalyzer._get_attribute_name(decorator))
        return decorators 