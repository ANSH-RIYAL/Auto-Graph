"""
Main file parser for AutoGraph.
Coordinates parsing of different file types and manages the parsing pipeline.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from ..utils.logger import get_logger
from ..utils.file_utils import FileUtils
from ..models.graph_models import FileInfo, SymbolInfo
from .ast_parser import PythonASTParser

logger = get_logger(__name__)


class FileParser:
    """Main file parser that handles different file types."""
    
    def __init__(self):
        self.python_parser = PythonASTParser()
        self.parsed_files: Dict[str, Dict[str, Any]] = {}
        self.failed_files: List[str] = []
        self.total_files = 0
        self.successful_parses = 0
    
    def parse_codebase(self, codebase_path: str) -> Dict[str, Any]:
        """Parse all files in a codebase."""
        logger.info(f"Starting codebase parsing: {codebase_path}")
        
        # Discover files
        try:
            files = FileUtils.discover_files(codebase_path)
            self.total_files = len(files)
        except Exception as e:
            logger.error(f"Failed to discover files: {e}")
            return self._create_error_result(str(e))
        
        # Parse each file
        for file_path in files:
            self._parse_single_file(file_path, codebase_path)
        
        # Generate results
        return self._create_parsing_result(codebase_path)
    
    def _parse_single_file(self, file_path: Path, codebase_path: str) -> None:
        """Parse a single file based on its type."""
        try:
            file_info = FileUtils.get_file_info(file_path)
            relative_path = FileUtils.get_relative_path(file_path, Path(codebase_path))
            
            logger.debug(f"Parsing file: {relative_path}")
            
            # Parse based on file type
            if file_path.suffix.lower() == '.py':
                success = self._parse_python_file(file_path, file_info)
            else:
                # For non-Python files, just collect basic info
                success = self._parse_generic_file(file_path, file_info)
            
            if success:
                self.successful_parses += 1
                logger.log_file_processed(str(file_path), True)
            else:
                self.failed_files.append(str(file_path))
                logger.log_file_processed(str(file_path), False, "Parsing failed")
                
        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            logger.error(error_msg)
            self.failed_files.append(str(file_path))
            logger.log_file_processed(str(file_path), False, error_msg)
    
    def _parse_python_file(self, file_path: Path, file_info: FileInfo) -> bool:
        """Parse a Python file using AST parser."""
        try:
            success = self.python_parser.parse_file(file_path)
            
            if success:
                # Read file content for LLM analysis
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                except Exception as e:
                    logger.warning(f"Could not read file content for {file_path}: {e}")
                    file_content = ""
                
                # Collect parsing results
                symbols = self.python_parser.get_symbols()
                
                self.parsed_files[str(file_path)] = {
                    'file_info': file_info,
                    'symbols': symbols,
                    'file_content': file_content,
                    'imports': self.python_parser.get_imports(),
                    'functions': [f.name for f in self.python_parser.get_functions()],
                    'classes': [c.name for c in self.python_parser.get_classes()],
                    'errors': self.python_parser.get_errors()
                }
                
                return True
            else:
                return False
                
        except Exception as e:
            logger.log_parsing_error(str(file_path), str(e))
            return False
    
    def _parse_generic_file(self, file_path: Path, file_info: FileInfo) -> bool:
        """Parse a non-Python file (basic info only)."""
        try:
            # Read file content for LLM analysis
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            except Exception as e:
                logger.warning(f"Could not read file content for {file_path}: {e}")
                file_content = ""
            
            # For non-Python files, we just collect basic metadata
            self.parsed_files[str(file_path)] = {
                'file_info': file_info,
                'symbols': {
                    'imports': [],
                    'functions': [],
                    'classes': [],
                    'variables': []
                },
                'file_content': file_content,
                'imports': [],
                'functions': [],
                'classes': [],
                'errors': []
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error parsing generic file {file_path}: {e}")
            return False
    
    def _create_parsing_result(self, codebase_path: str) -> Dict[str, Any]:
        """Create the final parsing result."""
        coverage_percentage = (self.successful_parses / self.total_files * 100) if self.total_files > 0 else 100.0
        
        # Collect statistics
        stats = {
            'total_files': self.total_files,
            'successful_parses': self.successful_parses,
            'failed_parses': len(self.failed_files),
            'coverage_percentage': coverage_percentage,
            'languages': {},
            'categories': {}
        }
        
        # Aggregate language and category statistics
        for file_data in self.parsed_files.values():
            file_info = file_data['file_info']
            
            # Language stats
            lang = file_info.language
            stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
            
            # Category stats
            cat = file_info.category
            stats['categories'][cat] = stats['categories'].get(cat, 0) + 1
        
        return {
            'codebase_path': codebase_path,
            'parsing_stats': stats,
            'parsed_files': self.parsed_files,
            'failed_files': self.failed_files,
            'success': True  # Always successful if we can parse the codebase
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result when parsing fails."""
        return {
            'codebase_path': '',
            'parsing_stats': {
                'total_files': 0,
                'successful_parses': 0,
                'failed_parses': 0,
                'coverage_percentage': 0,
                'languages': {},
                'categories': {}
            },
            'parsed_files': {},
            'failed_files': [],
            'success': False,
            'error': error_message
        }
    
    def get_file_symbols(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get symbols for a specific file."""
        return self.parsed_files.get(file_path)
    
    def get_all_symbols(self) -> Dict[str, List[SymbolInfo]]:
        """Get all symbols from all parsed files."""
        all_symbols = {
            'imports': [],
            'functions': [],
            'classes': [],
            'variables': []
        }
        
        for file_data in self.parsed_files.values():
            symbols = file_data['symbols']
            for symbol_type, symbol_list in symbols.items():
                all_symbols[symbol_type].extend(symbol_list)
        
        return all_symbols
    
    def get_import_dependencies(self) -> Dict[str, List[str]]:
        """Get import dependencies between files."""
        dependencies = {}
        
        for file_path, file_data in self.parsed_files.items():
            if file_data['imports']:
                dependencies[file_path] = file_data['imports']
        
        return dependencies
    
    def get_file_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about parsed files."""
        stats = {
            'total_files': self.total_files,
            'successful_parses': self.successful_parses,
            'failed_parses': len(self.failed_files),
            'coverage_percentage': (self.successful_parses / self.total_files * 100) if self.total_files > 0 else 0,
            'languages': {},
            'categories': {},
            'total_functions': 0,
            'total_classes': 0,
            'total_imports': 0
        }
        
        for file_data in self.parsed_files.values():
            file_info = file_data['file_info']
            
            # Language and category stats
            lang = file_info.language
            stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
            
            cat = file_info.category
            stats['categories'][cat] = stats['categories'].get(cat, 0) + 1
            
            # Symbol counts
            stats['total_functions'] += len(file_data['functions'])
            stats['total_classes'] += len(file_data['classes'])
            stats['total_imports'] += len(file_data['imports'])
        
        return stats 