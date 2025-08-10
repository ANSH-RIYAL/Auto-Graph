"""
Graph models and utilities for AutoGraph.
Provides additional models and helper functions for graph operations.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
from .schemas import GraphNode, GraphEdge, NodeLevel, NodeType, EdgeType


@dataclass
class FileInfo:
    """Information about a file in the codebase."""
    path: str
    size: int
    line_count: int
    language: str
    category: str
    last_modified: float


@dataclass
class SymbolInfo:
    """Information about a symbol (function, class, etc.) in a file."""
    name: str
    type: str  # 'function', 'class', 'import'
    line_number: int
    file_path: str
    parent: Optional[str] = None  # For nested functions/classes


class GraphBuilder:
    """Utility class for building and managing the hierarchical graph."""
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.file_to_nodes: Dict[str, List[str]] = {}
        self.symbol_to_node: Dict[str, str] = {}
    
    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        
        # Update file mappings
        for file_path in node.files:
            if file_path not in self.file_to_nodes:
                self.file_to_nodes[file_path] = []
            self.file_to_nodes[file_path].append(node.id)
        
        # Update symbol mappings
        for func in node.functions:
            self.symbol_to_node[func] = node.id
        for cls in node.classes:
            self.symbol_to_node[cls] = node.id
    
    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_nodes_by_level(self, level: NodeLevel) -> List[GraphNode]:
        """Get all nodes at a specific level."""
        return [node for node in self.nodes.values() if node.level == level]
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[GraphNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes.values() if node.type == node_type]
    
    def get_children(self, node_id: str) -> List[GraphNode]:
        """Get all child nodes of a given node."""
        node = self.get_node(node_id)
        if not node:
            return []
        return [self.nodes[child_id] for child_id in node.children if child_id in self.nodes]
    
    def get_parent(self, node_id: str) -> Optional[GraphNode]:
        """Get the parent node of a given node."""
        node = self.get_node(node_id)
        if not node or not node.parent:
            return None
        return self.get_node(node.parent)
    
    def get_related_nodes(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[Tuple[GraphNode, EdgeType]]:
        """Get all nodes related to a given node through edges."""
        related = []
        for edge in self.edges:
            if edge.from_node == node_id:
                if edge_type is None or edge.type == edge_type:
                    target_node = self.get_node(edge.to_node)
                    if target_node:
                        related.append((target_node, edge.type))
            elif edge.to_node == node_id:
                if edge_type is None or edge.type == edge_type:
                    source_node = self.get_node(edge.from_node)
                    if source_node:
                        related.append((source_node, edge.type))
        return related
    
    def validate_graph(self) -> List[str]:
        """Validate the graph structure and return any issues found."""
        issues = []
        
        # Check for orphaned nodes (nodes without any relationships)
        for node_id, node in self.nodes.items():
            has_relationships = False
            
            # Check if node has children
            if node.children:
                has_relationships = True
            
            # Check if node has parent
            if node.parent:
                has_relationships = True
            
            # Check if node has edges
            for edge in self.edges:
                if edge.from_node == node_id or edge.to_node == node_id:
                    has_relationships = True
                    break
            
            if not has_relationships:
                issues.append(f"Orphaned node: {node_id}")
        
        # Check for invalid parent-child relationships
        for node_id, node in self.nodes.items():
            if node.parent and node.parent not in self.nodes:
                issues.append(f"Invalid parent reference: {node_id} -> {node.parent}")
            
            for child_id in node.children:
                if child_id not in self.nodes:
                    issues.append(f"Invalid child reference: {node_id} -> {child_id}")
        
        # Check for invalid edge references
        for edge in self.edges:
            if edge.from_node not in self.nodes:
                issues.append(f"Invalid edge source: {edge.from_node}")
            if edge.to_node not in self.nodes:
                issues.append(f"Invalid edge target: {edge.to_node}")
        
        return issues
    
    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about the graph."""
        hld_nodes = self.get_nodes_by_level(NodeLevel.BUSINESS)
        lld_nodes = self.get_nodes_by_level(NodeLevel.IMPLEMENTATION)
        
        return {
            "total_nodes": len(self.nodes),
            "business_nodes": len(hld_nodes),
            "implementation_nodes": len(lld_nodes),
            "total_edges": len(self.edges),
            "node_types": {node_type.value: len(self.get_nodes_by_type(node_type)) 
                          for node_type in NodeType},
            "edge_types": {edge_type.value: len([e for e in self.edges if e.type == edge_type])
                          for edge_type in EdgeType}
        }


class FileCategorizer:
    """Utility for categorizing files in a codebase."""
    
    @staticmethod
    def categorize_file(file_path: str) -> str:
        """Categorize a file based on its path and name."""
        path = Path(file_path)
        
        # Test files
        if any(part.lower() in ['test', 'tests', 'spec', 'specs'] for part in path.parts):
            return "test"
        
        # Configuration files
        if any(part.lower() in ['config', 'conf', 'settings'] for part in path.parts):
            return "config"
        
        # Documentation
        if any(part.lower() in ['docs', 'documentation', 'readme'] for part in path.parts):
            return "docs"
        
        # Frontend files
        if path.suffix.lower() in ['.html', '.css', '.js', '.jsx', '.ts', '.tsx']:
            return "frontend"
        
        # Backend files
        if path.suffix.lower() in ['.py', '.java', '.go', '.rb', '.php']:
            return "backend"
        
        # Data files
        if path.suffix.lower() in ['.json', '.xml', '.yaml', '.yml', '.csv']:
            return "data"
        
        # Default
        return "other"
    
    @staticmethod
    def get_language(file_path: str) -> str:
        """Get the programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text'
        }
        
        return language_map.get(ext, 'unknown') 