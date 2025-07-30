"""
Semantic analyzer for AutoGraph.
Prepares LLM prompts and handles semantic analysis of code components.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from ..utils.logger import get_logger
from ..models.schemas import NodeLevel, NodeType, ComplexityLevel
from ..models.graph_models import SymbolInfo

logger = get_logger(__name__)


class SemanticAnalyzer:
    """Semantic analyzer for understanding code purpose and relationships."""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.analysis_results: Dict[str, Dict[str, Any]] = {}
    
    def analyze_file_semantics(self, file_path: str, symbols: Dict[str, List[SymbolInfo]], 
                              file_content: str) -> Dict[str, Any]:
        """Analyze the semantic meaning of a file and its components."""
        logger.debug(f"Analyzing semantics for: {file_path}")
        
        # Check cache first
        cache_key = self._generate_cache_key(file_path, symbols)
        if cache_key in self.cache:
            logger.debug(f"Using cached analysis for: {file_path}")
            return self.cache[cache_key]
        
        # Prepare analysis data
        analysis_data = {
            'file_path': file_path,
            'file_name': Path(file_path).name,
            'functions': [s.name for s in symbols.get('functions', [])],
            'classes': [s.name for s in symbols.get('classes', [])],
            'imports': [s.name for s in symbols.get('imports', [])],
            'file_content_preview': self._get_content_preview(file_content),
            'file_size': len(file_content),
            'line_count': len(file_content.split('\n'))
        }
        
        # Generate semantic analysis (without LLM calls for now)
        semantic_analysis = self._generate_semantic_analysis(analysis_data)
        
        # Cache the result and store in analysis results
        self.cache[cache_key] = semantic_analysis
        self.analysis_results[file_path] = semantic_analysis
        
        return semantic_analysis
    
    def _generate_semantic_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate semantic analysis based on file characteristics."""
        file_name = analysis_data['file_name'].lower()
        functions = analysis_data['functions']
        classes = analysis_data['classes']
        imports = analysis_data['imports']
        
        # Determine file purpose based on naming patterns and content
        purpose = self._determine_file_purpose(file_name, functions, classes, imports)
        
        # Determine component level (HLD vs LLD)
        level = self._determine_component_level(file_name, functions, classes, imports)
        
        # Determine component type
        component_type = self._determine_component_type(file_name, functions, classes, imports)
        
        # Determine complexity
        complexity = self._determine_complexity(analysis_data)
        
        # Generate relationships
        relationships = self._identify_relationships(imports, functions, classes)
        
        return {
            'purpose': purpose,
            'level': level,
            'component_type': component_type,
            'complexity': complexity,
            'relationships': relationships,
            'confidence': 0.8,  # Placeholder confidence score
            'analysis_method': 'rule_based'  # Indicates this is rule-based, not LLM
        }
    
    def _determine_file_purpose(self, file_name: str, functions: List[str], 
                               classes: List[str], imports: List[str]) -> str:
        """Determine the primary purpose of a file."""
        
        # API/Controller files
        if any(keyword in file_name for keyword in ['api', 'route', 'endpoint', 'controller']):
            return "Handles HTTP requests and API endpoints"
        
        # Service files
        if any(keyword in file_name for keyword in ['service', 'business', 'logic']):
            return "Contains business logic and service operations"
        
        # Model files
        if any(keyword in file_name for keyword in ['model', 'entity', 'schema', 'dto']):
            return "Defines data models and entities"
        
        # Utility files
        if any(keyword in file_name for keyword in ['util', 'helper', 'tool', 'formatter']):
            return "Provides utility functions and helpers"
        
        # Configuration files
        if any(keyword in file_name for keyword in ['config', 'settings', 'conf']):
            return "Contains configuration and settings"
        
        # Test files
        if any(keyword in file_name for keyword in ['test', 'spec']):
            return "Contains test cases and specifications"
        
        # Main application files
        if file_name in ['app.py', 'main.py', '__init__.py']:
            return "Main application entry point or module initialization"
        
        # Default based on content analysis
        if classes:
            return f"Defines {len(classes)} class(es) for data modeling and business logic"
        elif functions:
            return f"Provides {len(functions)} function(s) for various operations"
        else:
            return "General purpose file with mixed functionality"
    
    def _determine_component_level(self, file_name: str, functions: List[str], 
                                  classes: List[str], imports: List[str]) -> NodeLevel:
        """Determine if a component is HLD or LLD."""
        
        # HLD indicators
        hld_indicators = [
            'api', 'route', 'endpoint', 'controller',  # API layer
            'service', 'business', 'logic',            # Service layer
            'model', 'entity', 'schema', 'dto',        # Data models
            'config', 'settings', 'conf',              # Configuration
            'main', 'app'                              # Main application
        ]
        
        # Check if file name suggests HLD
        if any(indicator in file_name for indicator in hld_indicators):
            return NodeLevel.HLD
        
        # Check if file has many functions/classes (suggests LLD)
        if len(functions) > 5 or len(classes) > 2:
            return NodeLevel.LLD
        
        # Check if file has utility functions (suggests LLD)
        if any('util' in func.lower() or 'helper' in func.lower() for func in functions):
            return NodeLevel.LLD
        
        # Default to LLD for most files
        return NodeLevel.LLD
    
    def _determine_component_type(self, file_name: str, functions: List[str], 
                                 classes: List[str], imports: List[str]) -> NodeType:
        """Determine the specific type of component."""
        
        # API/Controller
        if any(keyword in file_name for keyword in ['api', 'route', 'endpoint', 'controller']):
            return NodeType.API
        
        # Service
        if any(keyword in file_name for keyword in ['service', 'business', 'logic']):
            return NodeType.SERVICE
        
        # Model
        if any(keyword in file_name for keyword in ['model', 'entity', 'schema', 'dto']):
            return NodeType.MODEL
        
        # Utility
        if any(keyword in file_name for keyword in ['util', 'helper', 'tool', 'formatter']):
            return NodeType.UTILITY
        
        # Database
        if any(keyword in file_name for keyword in ['db', 'database', 'repo', 'dao']):
            return NodeType.DATABASE
        
        # Client
        if any(keyword in file_name for keyword in ['client', 'sdk', 'api_client']):
            return NodeType.CLIENT
        
        # Default based on content
        if classes:
            return NodeType.CLASS
        elif functions:
            return NodeType.FUNCTION
        else:
            return NodeType.MODULE
    
    def _determine_complexity(self, analysis_data: Dict[str, Any]) -> ComplexityLevel:
        """Determine the complexity level of a component."""
        line_count = analysis_data['line_count']
        function_count = len(analysis_data['functions'])
        class_count = len(analysis_data['classes'])
        
        # High complexity indicators
        if (line_count > 200 or function_count > 10 or class_count > 3 or
            any('complex' in func.lower() for func in analysis_data['functions'])):
            return ComplexityLevel.HIGH
        
        # Medium complexity indicators
        if (line_count > 50 or function_count > 3 or class_count > 1):
            return ComplexityLevel.MEDIUM
        
        # Low complexity
        return ComplexityLevel.LOW
    
    def _identify_relationships(self, imports: List[str], functions: List[str], 
                               classes: List[str]) -> Dict[str, List[str]]:
        """Identify relationships between components."""
        relationships = {
            'depends_on': [],
            'uses': [],
            'implements': [],
            'extends': []
        }
        
        # Analyze imports for dependencies
        for imp in imports:
            if '.' in imp:
                module = imp.split('.')[0]
                relationships['depends_on'].append(module)
        
        # Analyze function names for usage patterns
        for func in functions:
            if any(keyword in func.lower() for keyword in ['get', 'fetch', 'load']):
                relationships['uses'].append('data_access')
            elif any(keyword in func.lower() for keyword in ['save', 'store', 'persist']):
                relationships['uses'].append('data_storage')
            elif any(keyword in func.lower() for keyword in ['validate', 'check']):
                relationships['uses'].append('validation')
        
        return relationships
    
    def _get_content_preview(self, content: str, max_lines: int = 10) -> str:
        """Get a preview of file content for analysis."""
        lines = content.split('\n')
        preview_lines = lines[:max_lines]
        return '\n'.join(preview_lines)
    
    def _generate_cache_key(self, file_path: str, symbols: Dict[str, List[SymbolInfo]]) -> str:
        """Generate a cache key for the analysis."""
        import hashlib
        
        # Create a hash based on file path and symbol counts
        symbol_summary = f"{len(symbols.get('functions', []))}_{len(symbols.get('classes', []))}_{len(symbols.get('imports', []))}"
        content = f"{file_path}_{symbol_summary}"
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def prepare_llm_prompt(self, file_path: str, symbols: Dict[str, List[SymbolInfo]], 
                          file_content: str) -> str:
        """Prepare a prompt for LLM analysis (for future use)."""
        functions = [s.name for s in symbols.get('functions', [])]
        classes = [s.name for s in symbols.get('classes', [])]
        imports = [s.name for s in symbols.get('imports', [])]
        
        prompt = f"""
Given this file and its function list, analyze its role in the system:

1. What is the primary purpose of this file?
2. Is this a high-level module (HLD) or low-level component (LLD)?
3. What other modules/components does it interact with?
4. What is its complexity level (low/medium/high)?

File: {file_path}
Functions: {', '.join(functions) if functions else 'None'}
Classes: {', '.join(classes) if classes else 'None'}
Imports: {', '.join(imports) if imports else 'None'}

Content Preview:
{self._get_content_preview(file_content, 20)}
"""
        return prompt
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get statistics about the semantic analysis."""
        return {
            'total_files_analyzed': len(self.analysis_results),
            'cached_results': len(self.cache),
            'analysis_method': 'rule_based',
            'llm_integration_ready': True
        } 