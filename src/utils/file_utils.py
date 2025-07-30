"""
File utilities for AutoGraph.
Provides functions for file system operations, codebase traversal, and metadata extraction.
"""

import os
import stat
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime
from .logger import get_logger
from ..models.graph_models import FileInfo, FileCategorizer

logger = get_logger(__name__)


class FileUtils:
    """Utility class for file system operations."""
    
    # File extensions to include in analysis
    SUPPORTED_EXTENSIONS = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rb', '.php',
        '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.md', '.txt'
    }
    
    # Directories to exclude from analysis
    EXCLUDE_DIRS = {
        '.git', '.svn', '.hg', '__pycache__', 'node_modules', '.venv', 'venv',
        'env', '.env', 'build', 'dist', 'target', 'bin', 'obj', '.pytest_cache',
        '.coverage', '.mypy_cache', '.tox', '.eggs', '*.egg-info'
    }
    
    # Files to exclude from analysis
    EXCLUDE_FILES = {
        '.DS_Store', 'Thumbs.db', '.gitignore', '.gitattributes',
        '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.dylib'
    }
    
    @staticmethod
    def should_include_file(file_path: Path) -> bool:
        """Check if a file should be included in analysis."""
        # Check if file has supported extension
        if file_path.suffix.lower() not in FileUtils.SUPPORTED_EXTENSIONS:
            return False
        
        # Check if file is in excluded directory
        for part in file_path.parts:
            if part in FileUtils.EXCLUDE_DIRS:
                return False
        
        # Check if file name matches exclude patterns
        for pattern in FileUtils.EXCLUDE_FILES:
            if pattern.startswith('*'):
                if file_path.name.endswith(pattern[1:]):
                    return False
            elif file_path.name == pattern:
                return False
        
        return True
    
    @staticmethod
    def discover_files(codebase_path: str) -> List[Path]:
        """Discover all relevant files in a codebase."""
        codebase = Path(codebase_path)
        if not codebase.exists():
            raise FileNotFoundError(f"Codebase path does not exist: {codebase_path}")
        
        if not codebase.is_dir():
            raise ValueError(f"Codebase path must be a directory: {codebase_path}")
        
        files = []
        logger.info(f"Discovering files in: {codebase_path}")
        
        for file_path in codebase.rglob('*'):
            if file_path.is_file() and FileUtils.should_include_file(file_path):
                files.append(file_path)
        
        logger.info(f"Discovered {len(files)} files for analysis")
        return files
    
    @staticmethod
    def get_file_info(file_path: Path) -> FileInfo:
        """Extract metadata from a file."""
        try:
            stat_info = file_path.stat()
            
            # Count lines
            line_count = 0
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    line_count = sum(1 for _ in f)
            except Exception as e:
                logger.warning(f"Could not count lines in {file_path}: {e}")
            
            # Get language and category
            language = FileCategorizer.get_language(str(file_path))
            category = FileCategorizer.categorize_file(str(file_path))
            
            return FileInfo(
                path=str(file_path),
                size=stat_info.st_size,
                line_count=line_count,
                language=language,
                category=category,
                last_modified=stat_info.st_mtime
            )
        
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            raise
    
    @staticmethod
    def get_file_content(file_path: Path) -> Optional[str]:
        """Read file content with proper encoding handling."""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Try with error handling
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Could not read file {file_path}: {e}")
                return None
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    @staticmethod
    def get_relative_path(file_path: Path, base_path: Path) -> str:
        """Get relative path from base path."""
        try:
            return str(file_path.relative_to(base_path))
        except ValueError:
            return str(file_path)
    
    @staticmethod
    def create_output_directories() -> None:
        """Create necessary output directories."""
        directories = ['graph', 'logs', 'cache']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    @staticmethod
    def get_codebase_stats(files: List[Path]) -> Dict[str, any]:
        """Get statistics about the codebase."""
        stats = {
            'total_files': len(files),
            'languages': {},
            'categories': {},
            'total_size': 0,
            'total_lines': 0
        }
        
        for file_path in files:
            try:
                file_info = FileUtils.get_file_info(file_path)
                
                # Language stats
                lang = file_info.language
                stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
                
                # Category stats
                cat = file_info.category
                stats['categories'][cat] = stats['categories'].get(cat, 0) + 1
                
                # Size and line stats
                stats['total_size'] += file_info.size
                stats['total_lines'] += file_info.line_count
                
            except Exception as e:
                logger.warning(f"Could not get stats for {file_path}: {e}")
        
        return stats
    
    @staticmethod
    def validate_codebase_path(codebase_path: str) -> bool:
        """Validate that the codebase path is accessible and contains code."""
        try:
            path = Path(codebase_path)
            
            if not path.exists():
                logger.error(f"Codebase path does not exist: {codebase_path}")
                return False
            
            if not path.is_dir():
                logger.error(f"Codebase path is not a directory: {codebase_path}")
                return False
            
            # Check if directory contains any files
            files = list(path.rglob('*'))
            if not files:
                logger.error(f"Codebase directory is empty: {codebase_path}")
                return False
            
            # Check if directory contains any supported files
            supported_files = [f for f in files if f.is_file() and FileUtils.should_include_file(f)]
            if not supported_files:
                logger.error(f"No supported files found in codebase: {codebase_path}")
                return False
            
            logger.info(f"Codebase validation passed: {len(supported_files)} supported files found")
            return True
            
        except Exception as e:
            logger.error(f"Error validating codebase path {codebase_path}: {e}")
            return False
    
    @staticmethod
    def get_file_hash(file_path: Path) -> str:
        """Get a hash of the file content for caching purposes."""
        import hashlib
        
        try:
            content = FileUtils.get_file_content(file_path)
            if content is None:
                return ""
            
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Error getting file hash for {file_path}: {e}")
            return "" 