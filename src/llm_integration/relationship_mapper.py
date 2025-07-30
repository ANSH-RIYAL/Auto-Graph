"""
Relationship mapper for AutoGraph.
Identifies dependencies and connections between code components.
"""

from typing import Dict, List, Set, Tuple, Any
from pathlib import Path
from ..utils.logger import get_logger
from ..models.schemas import EdgeType, NodeType
from ..models.graph_models import SymbolInfo

logger = get_logger(__name__)


class RelationshipMapper:
    """Maps relationships between code components."""
    
    def __init__(self):
        self.relationships: Dict[str, List[Dict[str, Any]]] = {}
        self.import_graph: Dict[str, Set[str]] = {}
        self.function_calls: Dict[str, Set[str]] = {}
        self.class_inheritance: Dict[str, List[str]] = {}
    
    def map_relationships(self, parsed_files: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Map all relationships in the codebase."""
        logger.info("Mapping relationships between components...")
        
        # Build import graph
        self._build_import_graph(parsed_files)
        
        # Build function call graph
        self._build_function_call_graph(parsed_files)
        
        # Build class inheritance graph
        self._build_class_inheritance_graph(parsed_files)
        
        # Generate relationship edges
        relationships = self._generate_relationship_edges(parsed_files)
        
        logger.info(f"Mapped {len(relationships)} relationships")
        return relationships
    
    def _build_import_graph(self, parsed_files: Dict[str, Any]) -> None:
        """Build a graph of import dependencies."""
        for file_path, file_data in parsed_files.items():
            imports = file_data.get('imports', [])
            self.import_graph[file_path] = set()
            
            for imp in imports:
                # Find the file that provides this import
                source_file = self._find_import_source(imp, parsed_files)
                if source_file and source_file != file_path:
                    self.import_graph[file_path].add(source_file)
    
    def _build_function_call_graph(self, parsed_files: Dict[str, Any]) -> None:
        """Build a graph of function calls (simplified analysis)."""
        for file_path, file_data in parsed_files.items():
            functions = file_data.get('functions', [])
            self.function_calls[file_path] = set()
            
            # This is a simplified analysis - in a full implementation,
            # you would analyze the actual function calls in the code
            for func in functions:
                # Look for potential calls to other functions
                for other_file, other_data in parsed_files.items():
                    if other_file != file_path:
                        other_functions = other_data.get('functions', [])
                        # Simple heuristic: if function names match, assume a call
                        for other_func in other_functions:
                            if func == other_func:
                                self.function_calls[file_path].add(other_file)
    
    def _build_class_inheritance_graph(self, parsed_files: Dict[str, Any]) -> None:
        """Build a graph of class inheritance relationships."""
        for file_path, file_data in parsed_files.items():
            classes = file_data.get('classes', [])
            self.class_inheritance[file_path] = []
            
            # This would require deeper AST analysis to find actual inheritance
            # For now, we'll use a simplified approach
            for class_name in classes:
                # Look for potential base classes in other files
                for other_file, other_data in parsed_files.items():
                    if other_file != file_path:
                        other_classes = other_data.get('classes', [])
                        # Simple heuristic: if class names are similar, assume inheritance
                        for other_class in other_classes:
                            if class_name.lower().endswith(other_class.lower()):
                                self.class_inheritance[file_path].append(other_file)
    
    def _find_import_source(self, import_name: str, parsed_files: Dict[str, Any]) -> str:
        """Find the file that provides a given import."""
        # Simple heuristic: look for files that might provide this import
        for file_path, file_data in parsed_files.items():
            file_name = Path(file_path).stem
            
            # Check if the file name matches the import
            if import_name.startswith(file_name):
                return file_path
            
            # Check if any class in the file matches the import
            classes = file_data.get('classes', [])
            if import_name in classes:
                return file_path
        
        return None
    
    def _generate_relationship_edges(self, parsed_files: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate relationship edges between components."""
        relationships = {}
        
        for file_path in parsed_files.keys():
            relationships[file_path] = []
            
            # Import relationships
            for imported_file in self.import_graph.get(file_path, []):
                relationships[file_path].append({
                    'type': EdgeType.IMPORTS,
                    'target': imported_file,
                    'strength': 'strong',
                    'description': f'Imports from {Path(imported_file).name}'
                })
            
            # Function call relationships
            for called_file in self.function_calls.get(file_path, []):
                relationships[file_path].append({
                    'type': EdgeType.CALLS,
                    'target': called_file,
                    'strength': 'medium',
                    'description': f'Calls functions in {Path(called_file).name}'
                })
            
            # Inheritance relationships
            for base_file in self.class_inheritance.get(file_path, []):
                relationships[file_path].append({
                    'type': EdgeType.INHERITS,
                    'target': base_file,
                    'strength': 'strong',
                    'description': f'Inherits from {Path(base_file).name}'
                })
        
        return relationships
    
    def analyze_dependency_cycles(self, relationships: Dict[str, List[Dict[str, Any]]]) -> List[List[str]]:
        """Analyze for circular dependencies."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for rel in relationships.get(node, []):
                target = rel['target']
                dfs(target, path.copy())
            
            rec_stack.remove(node)
            path.pop()
        
        for node in relationships.keys():
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def calculate_dependency_metrics(self, relationships: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Calculate dependency metrics for the codebase."""
        total_relationships = sum(len(rels) for rels in relationships.values())
        avg_relationships = total_relationships / len(relationships) if relationships else 0
        
        # Count relationship types
        relationship_types = {}
        for rels in relationships.values():
            for rel in rels:
                rel_type = rel['type']
                relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        
        # Find most dependent files
        dependency_counts = {}
        for file_path, rels in relationships.items():
            dependency_counts[file_path] = len(rels)
        
        most_dependent = sorted(dependency_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_relationships': total_relationships,
            'average_relationships_per_file': avg_relationships,
            'relationship_types': relationship_types,
            'most_dependent_files': most_dependent,
            'files_with_no_dependencies': len([f for f, count in dependency_counts.items() if count == 0])
        }
    
    def get_relationship_summary(self, file_path: str, relationships: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Get a summary of relationships for a specific file."""
        file_relationships = relationships.get(file_path, [])
        
        summary = {
            'file_path': file_path,
            'total_relationships': len(file_relationships),
            'relationship_types': {},
            'dependencies': [],
            'dependents': []
        }
        
        for rel in file_relationships:
            rel_type = rel['type']
            summary['relationship_types'][rel_type] = summary['relationship_types'].get(rel_type, 0) + 1
            summary['dependencies'].append(rel['target'])
        
        # Find files that depend on this file
        for other_file, other_rels in relationships.items():
            if other_file != file_path:
                for rel in other_rels:
                    if rel['target'] == file_path:
                        summary['dependents'].append(other_file)
        
        return summary 