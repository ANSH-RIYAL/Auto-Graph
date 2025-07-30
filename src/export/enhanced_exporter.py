"""
Enhanced exporter for AutoGraph Phase 3.
Provides multiple export formats and metadata enrichment.
"""

import json
import yaml
import csv
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from ..utils.logger import get_logger
from ..models.schemas import Graph, GraphNode, GraphEdge, NodeLevel, NodeType, EdgeType
from ..visualization.graph_visualizer import GraphVisualizer

logger = get_logger(__name__)


class EnhancedExporter:
    """Enhanced exporter with multiple formats and metadata enrichment."""
    
    def __init__(self):
        self.visualizer = GraphVisualizer()
        self.export_formats = ['json', 'yaml', 'csv', 'dot', 'html', 'mermaid']
    
    def export_graph(self, graph: Graph, output_dir: str, formats: List[str] = None) -> Dict[str, str]:
        """Export graph in multiple formats."""
        logger.info(f"Exporting graph to {output_dir}")
        
        if formats is None:
            formats = self.export_formats
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        export_results = {}
        
        # Generate timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for format_type in formats:
            if format_type not in self.export_formats:
                logger.warning(f"Unsupported export format: {format_type}")
                continue
            
            try:
                if format_type == 'json':
                    output_path = output_dir / f"autograph_graph_{timestamp}.json"
                    result = self._export_json(graph, str(output_path))
                    export_results['json'] = str(output_path)
                
                elif format_type == 'yaml':
                    output_path = output_dir / f"autograph_graph_{timestamp}.yaml"
                    result = self._export_yaml(graph, str(output_path))
                    export_results['yaml'] = str(output_path)
                
                elif format_type == 'csv':
                    output_path = output_dir / f"autograph_graph_{timestamp}.csv"
                    result = self._export_csv(graph, str(output_path))
                    export_results['csv'] = str(output_path)
                
                elif format_type == 'dot':
                    output_path = output_dir / f"autograph_graph_{timestamp}.dot"
                    result = self.visualizer.generate_dot_visualization(graph, str(output_path))
                    export_results['dot'] = str(output_path)
                
                elif format_type == 'html':
                    output_path = output_dir / f"autograph_graph_{timestamp}.html"
                    result = self.visualizer.generate_html_visualization(graph, str(output_path))
                    export_results['html'] = str(output_path)
                
                elif format_type == 'mermaid':
                    output_path = output_dir / f"autograph_graph_{timestamp}.mmd"
                    result = self.visualizer.generate_mermaid_visualization(graph, str(output_path))
                    export_results['mermaid'] = str(output_path)
                
                logger.info(f"Successfully exported {format_type} to {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to export {format_type}: {e}")
                export_results[f"{format_type}_error"] = str(e)
        
        return export_results
    
    def _export_json(self, graph: Graph, output_path: str) -> Dict[str, Any]:
        """Export graph as enhanced JSON with metadata."""
        enhanced_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'export_format': 'enhanced_json',
                'version': '1.0',
                'graph_metadata': graph.metadata.dict() if graph.metadata else {},
                'statistics': self._generate_graph_statistics(graph)
            },
            'nodes': [],
            'edges': [],
            'hierarchical_structure': self._generate_hierarchical_structure(graph),
            'dependency_analysis': self._generate_dependency_analysis(graph),
            'complexity_analysis': self._generate_complexity_analysis(graph)
        }
        
        # Enhanced node data
        for node in graph.nodes:
            node_data = {
                'id': node.id,
                'name': node.name,
                'type': node.type.value,
                'level': node.level.value,
                'metadata': node.metadata,
                'files': node.files,
                'functions': node.functions,
                'classes': node.classes,
                'parent': node.parent,
                'children': node.children,
                'enhanced_metadata': self._enrich_node_metadata(node)
            }
            enhanced_data['nodes'].append(node_data)
        
        # Enhanced edge data
        for edge in graph.edges:
            edge_data = {
                'from_node': edge.from_node,
                'to_node': edge.to_node,
                'type': edge.type.value,
                'metadata': edge.metadata,
                'enhanced_metadata': self._enrich_edge_metadata(edge)
            }
            enhanced_data['edges'].append(edge_data)
        
        with open(output_path, 'w') as f:
            json.dump(enhanced_data, f, indent=2, default=str)
        
        return enhanced_data
    
    def _export_yaml(self, graph: Graph, output_path: str) -> Dict[str, Any]:
        """Export graph as YAML with enhanced metadata."""
        yaml_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'export_format': 'enhanced_yaml',
                'version': '1.0',
                'graph_metadata': graph.metadata.dict() if graph.metadata else {},
                'statistics': self._generate_graph_statistics(graph)
            },
            'nodes': [],
            'edges': [],
            'hierarchical_structure': self._generate_hierarchical_structure(graph)
        }
        
        # Node data
        for node in graph.nodes:
            node_data = {
                'id': node.id,
                'name': node.name,
                'type': node.type.value,
                'level': node.level.value,
                'files': node.files,
                'functions': node.functions,
                'classes': node.classes,
                'metadata': node.metadata
            }
            yaml_data['nodes'].append(node_data)
        
        # Edge data
        for edge in graph.edges:
            edge_data = {
                'from_node': edge.from_node,
                'to_node': edge.to_node,
                'type': edge.type.value,
                'metadata': edge.metadata
            }
            yaml_data['edges'].append(edge_data)
        
        with open(output_path, 'w') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
        
        return yaml_data
    
    def _export_csv(self, graph: Graph, output_path: str) -> List[Dict[str, Any]]:
        """Export graph as CSV with node and edge information."""
        csv_data = []
        
        # Add nodes
        for node in graph.nodes:
            node_row = {
                'type': 'node',
                'id': node.id,
                'name': node.name,
                'node_type': node.type.value,
                'level': node.level.value,
                'file_count': len(node.files),
                'function_count': len(node.functions),
                'class_count': len(node.classes),
                'parent': node.parent or '',
                'child_count': len(node.children),
                'complexity': node.metadata.complexity.value if hasattr(node.metadata, 'complexity') and node.metadata.complexity else '',
                'purpose': node.metadata.purpose if hasattr(node.metadata, 'purpose') and node.metadata.purpose else ''
            }
            csv_data.append(node_row)
        
        # Add edges
        for edge in graph.edges:
            edge_row = {
                'type': 'edge',
                'from_node': edge.from_node,
                'to_node': edge.to_node,
                'edge_type': edge.type.value,
                'description': edge.metadata.get('description', '') if edge.metadata else ''
            }
            csv_data.append(edge_row)
        
        # Write CSV
        if csv_data:
            # Get all possible fieldnames from both nodes and edges
            all_fieldnames = set()
            for row in csv_data:
                all_fieldnames.update(row.keys())
            
            fieldnames = sorted(list(all_fieldnames))
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
        
        return csv_data
    
    def _generate_graph_statistics(self, graph: Graph) -> Dict[str, Any]:
        """Generate comprehensive graph statistics."""
        hld_nodes = [n for n in graph.nodes if n.level == NodeLevel.HLD]
        lld_nodes = [n for n in graph.nodes if n.level == NodeLevel.LLD]
        
        # Node type distribution
        node_types = {}
        for node in graph.nodes:
            node_type = node.type.value
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        # Edge type distribution
        edge_types = {}
        for edge in graph.edges:
            edge_type = edge.type.value
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        # Complexity distribution
        complexity_dist = {'low': 0, 'medium': 0, 'high': 0}
        for node in graph.nodes:
            if node.metadata and hasattr(node.metadata, 'complexity') and node.metadata.complexity:
                complexity = node.metadata.complexity.value
                complexity_dist[complexity] = complexity_dist.get(complexity, 0) + 1
        
        return {
            'total_nodes': len(graph.nodes),
            'hld_nodes': len(hld_nodes),
            'lld_nodes': len(lld_nodes),
            'total_edges': len(graph.edges),
            'node_type_distribution': node_types,
            'edge_type_distribution': edge_types,
            'complexity_distribution': complexity_dist,
            'average_children_per_node': sum(len(n.children) for n in graph.nodes) / len(graph.nodes) if graph.nodes else 0,
            'nodes_without_parents': len([n for n in graph.nodes if not n.parent]),
            'nodes_without_children': len([n for n in graph.nodes if not n.children])
        }
    
    def _generate_hierarchical_structure(self, graph: Graph) -> Dict[str, Any]:
        """Generate hierarchical structure analysis."""
        hld_nodes = [n for n in graph.nodes if n.level == NodeLevel.HLD]
        lld_nodes = [n for n in graph.nodes if n.level == NodeLevel.LLD]
        
        hierarchy = {
            'hld_modules': [],
            'lld_components': [],
            'containment_relationships': []
        }
        
        # HLD modules
        for node in hld_nodes:
            module_info = {
                'id': node.id,
                'name': node.name,
                'type': node.type.value,
                'child_count': len(node.children),
                'children': node.children
            }
            hierarchy['hld_modules'].append(module_info)
        
        # LLD components
        for node in lld_nodes:
            component_info = {
                'id': node.id,
                'name': node.name,
                'type': node.type.value,
                'parent': node.parent,
                'files': node.files,
                'function_count': len(node.functions),
                'class_count': len(node.classes)
            }
            hierarchy['lld_components'].append(component_info)
        
        # Containment relationships
        containment_edges = [e for e in graph.edges if e.type == EdgeType.CONTAINS]
        for edge in containment_edges:
            containment_info = {
                'parent': edge.from_node,
                'child': edge.to_node,
                'metadata': edge.metadata
            }
            hierarchy['containment_relationships'].append(containment_info)
        
        return hierarchy
    
    def _generate_dependency_analysis(self, graph: Graph) -> Dict[str, Any]:
        """Generate dependency analysis."""
        dependency_edges = [e for e in graph.edges if e.type in [EdgeType.IMPORTS, EdgeType.CALLS, EdgeType.DEPENDS]]
        
        dependencies = {
            'import_dependencies': [],
            'function_calls': [],
            'general_dependencies': [],
            'circular_dependencies': self._detect_circular_dependencies(graph)
        }
        
        for edge in dependency_edges:
            dep_info = {
                'from': edge.from_node,
                'to': edge.to_node,
                'type': edge.type.value,
                'metadata': edge.metadata
            }
            
            if edge.type == EdgeType.IMPORTS:
                dependencies['import_dependencies'].append(dep_info)
            elif edge.type == EdgeType.CALLS:
                dependencies['function_calls'].append(dep_info)
            else:
                dependencies['general_dependencies'].append(dep_info)
        
        return dependencies
    
    def _generate_complexity_analysis(self, graph: Graph) -> Dict[str, Any]:
        """Generate complexity analysis."""
        complexity_data = {
            'by_node_type': {},
            'by_level': {'HLD': [], 'LLD': []},
            'most_complex_nodes': [],
            'complexity_trends': {}
        }
        
        # Analyze by node type
        for node in graph.nodes:
            node_type = node.type.value
            if node_type not in complexity_data['by_node_type']:
                complexity_data['by_node_type'][node_type] = []
            
            complexity_info = {
                'id': node.id,
                'name': node.name,
                'complexity': node.metadata.get('complexity', '').value if node.metadata and 'complexity' in node.metadata else 'unknown',
                'file_count': len(node.files),
                'function_count': len(node.functions),
                'class_count': len(node.classes)
            }
            
            complexity_data['by_node_type'][node_type].append(complexity_info)
            
            # By level
            level = node.level.value
            complexity_data['by_level'][level].append(complexity_info)
        
        # Find most complex nodes
        all_nodes_with_complexity = []
        for node in graph.nodes:
            if node.metadata and hasattr(node.metadata, 'complexity') and node.metadata.complexity:
                complexity_score = {'low': 1, 'medium': 2, 'high': 3}.get(node.metadata.complexity.value, 0)
                all_nodes_with_complexity.append((node, complexity_score))
        
        most_complex = sorted(all_nodes_with_complexity, key=lambda x: x[1], reverse=True)[:5]
        complexity_data['most_complex_nodes'] = [
            {
                'id': node.id,
                'name': node.name,
                'complexity': node.metadata.complexity.value if hasattr(node.metadata, 'complexity') and node.metadata.complexity else 'unknown',
                'type': node.type.value,
                'level': node.level.value
            }
            for node, _ in most_complex
        ]
        
        return complexity_data
    
    def _detect_circular_dependencies(self, graph: Graph) -> List[List[str]]:
        """Detect circular dependencies in the graph."""
        # Simple circular dependency detection
        # In a full implementation, this would use a more sophisticated algorithm
        circular_deps = []
        
        # This is a simplified implementation
        # For now, we'll return an empty list
        # A proper implementation would use DFS to detect cycles
        
        return circular_deps
    
    def _enrich_node_metadata(self, node: GraphNode) -> Dict[str, Any]:
        """Enrich node metadata with additional analysis."""
        enriched = {
            'total_symbols': len(node.functions) + len(node.classes),
            'has_parent': bool(node.parent),
            'has_children': bool(node.children),
            'child_count': len(node.children),
            'file_diversity': len(set(Path(f).suffix for f in node.files)) if node.files else 0
        }
        
        if node.metadata and 'complexity' in node.metadata:
            enriched['complexity_score'] = {'low': 1, 'medium': 2, 'high': 3}.get(node.metadata['complexity'].value, 0)
        
        return enriched
    
    def _enrich_edge_metadata(self, edge: GraphEdge) -> Dict[str, Any]:
        """Enrich edge metadata with additional analysis."""
        enriched = {
            'edge_strength': self._calculate_edge_strength(edge),
            'is_hierarchical': edge.type == EdgeType.CONTAINS,
            'is_dependency': edge.type in [EdgeType.IMPORTS, EdgeType.CALLS, EdgeType.DEPENDS]
        }
        
        return enriched
    
    def _calculate_edge_strength(self, edge: GraphEdge) -> str:
        """Calculate the strength of an edge relationship."""
        if edge.type == EdgeType.CONTAINS:
            return 'strong'
        elif edge.type == EdgeType.INHERITS:
            return 'strong'
        elif edge.type == EdgeType.IMPORTS:
            return 'medium'
        elif edge.type == EdgeType.CALLS:
            return 'weak'
        else:
            return 'medium'
    
    def generate_export_report(self, export_results: Dict[str, str]) -> str:
        """Generate a summary report of the export process."""
        report_lines = [
            "# AutoGraph Export Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Export Summary",
            f"Total formats attempted: {len(export_results)}",
            ""
        ]
        
        successful_exports = [k for k in export_results.keys() if not k.endswith('_error')]
        failed_exports = [k for k in export_results.keys() if k.endswith('_error')]
        
        report_lines.extend([
            f"Successful exports: {len(successful_exports)}",
            f"Failed exports: {len(failed_exports)}",
            ""
        ])
        
        if successful_exports:
            report_lines.append("## Successful Exports")
            for format_type in successful_exports:
                report_lines.append(f"- {format_type}: {export_results[format_type]}")
            report_lines.append("")
        
        if failed_exports:
            report_lines.append("## Failed Exports")
            for format_type in failed_exports:
                original_format = format_type.replace('_error', '')
                report_lines.append(f"- {original_format}: {export_results[format_type]}")
            report_lines.append("")
        
        report_lines.append("## Next Steps")
        report_lines.append("1. Open HTML file in a web browser for interactive visualization")
        report_lines.append("2. Use DOT file with Graphviz for static diagrams")
        report_lines.append("3. Import JSON/YAML files into other tools for further analysis")
        report_lines.append("4. Use CSV file for spreadsheet analysis")
        
        return "\n".join(report_lines) 