"""
Enhanced graph builder for AutoGraph Phase 2.
Integrates semantic analysis and relationship mapping for better graph construction.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from ..utils.logger import get_logger
from ..utils.file_utils import FileUtils
from ..models.schemas import Graph, GraphMetadata, GraphNode, GraphEdge, NodeLevel, NodeType, EdgeType, ComplexityLevel
from ..models.graph_models import GraphBuilder
from ..llm_integration.semantic_analyzer import SemanticAnalyzer
from ..llm_integration.relationship_mapper import RelationshipMapper

logger = get_logger(__name__)


class EnhancedGraphBuilder:
    """Enhanced graph builder with semantic analysis and relationship mapping."""
    
    def __init__(self):
        self.semantic_analyzer = SemanticAnalyzer()
        self.relationship_mapper = RelationshipMapper()
        self.graph_builder = GraphBuilder()
        self.semantic_results: Dict[str, Dict[str, Any]] = {}
        self.relationship_results: Dict[str, List[Dict[str, Any]]] = {}
    
    def build_enhanced_graph(self, codebase_path: str, parsing_result: Dict[str, Any]) -> Graph:
        """Build an enhanced graph with semantic analysis and relationship mapping."""
        logger.info("Building enhanced graph with semantic analysis...")
        
        # Step 1: Perform semantic analysis
        self._perform_semantic_analysis(parsing_result)
        
        # Step 2: Map relationships
        self._map_relationships(parsing_result)
        
        # Step 3: Create enhanced graph structure
        graph = self._create_enhanced_graph_structure(codebase_path, parsing_result)
        
        # Step 4: Validate and enrich graph
        self._validate_and_enrich_graph(graph)
        
        logger.info(f"Enhanced graph built: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
        return graph
    
    def _perform_semantic_analysis(self, parsing_result: Dict[str, Any]) -> None:
        """Perform semantic analysis on all parsed files."""
        logger.info("Performing semantic analysis...")
        
        for file_path, file_data in parsing_result['parsed_files'].items():
            try:
                # Get file content for analysis
                file_content = FileUtils.get_file_content(Path(file_path))
                if file_content is None:
                    continue
                
                # Get symbols for analysis
                symbols = file_data.get('symbols', {})
                
                # Perform semantic analysis
                semantic_result = self.semantic_analyzer.analyze_file_semantics(
                    file_path, symbols, file_content
                )
                
                self.semantic_results[file_path] = semantic_result
                
            except Exception as e:
                logger.warning(f"Failed to analyze semantics for {file_path}: {e}")
                # Use default semantic analysis
                self.semantic_results[file_path] = self._get_default_semantic_analysis(file_path)
    
    def _map_relationships(self, parsing_result: Dict[str, Any]) -> None:
        """Map relationships between components."""
        logger.info("Mapping relationships between components...")
        
        try:
            self.relationship_results = self.relationship_mapper.map_relationships(
                parsing_result['parsed_files']
            )
        except Exception as e:
            logger.error(f"Failed to map relationships: {e}")
            self.relationship_results = {}
    
    def _create_enhanced_graph_structure(self, codebase_path: str, parsing_result: Dict[str, Any]) -> Graph:
        """Create enhanced graph structure with semantic analysis."""
        
        # Create graph metadata
        metadata = self._create_enhanced_graph_metadata(codebase_path, parsing_result)
        
        # Create HLD nodes with semantic analysis
        hld_nodes = self._create_enhanced_hld_nodes(parsing_result)
        
        # Create LLD nodes with semantic analysis
        lld_nodes = self._create_enhanced_lld_nodes(parsing_result)
        
        # Create enhanced edges with relationship mapping
        edges = self._create_enhanced_graph_edges(parsing_result, hld_nodes, lld_nodes)
        
        # Build the graph
        graph = Graph(
            metadata=metadata,
            nodes=list(hld_nodes.values()) + list(lld_nodes.values()),
            edges=edges
        )
        
        return graph
    
    def _create_enhanced_graph_metadata(self, codebase_path: str, parsing_result: Dict[str, Any]) -> GraphMetadata:
        """Create enhanced graph metadata with semantic analysis statistics."""
        stats = parsing_result['parsing_stats']
        
        # Get semantic analysis statistics
        semantic_stats = self.semantic_analyzer.get_analysis_statistics()
        
        # Get relationship metrics
        relationship_metrics = self.relationship_mapper.calculate_dependency_metrics(
            self.relationship_results
        )
        
        return GraphMetadata(
            codebase_path=codebase_path,
            analysis_timestamp=datetime.now(),
            file_count=stats['total_files'],
            coverage_percentage=stats['coverage_percentage'],
            total_lines=sum(file_data['file_info'].line_count for file_data in parsing_result['parsed_files'].values()),
            languages=list(stats['languages'].keys()),
            categories=stats['categories']
        )
    
    def _create_enhanced_hld_nodes(self, parsing_result: Dict[str, Any]) -> Dict[str, GraphNode]:
        """Create enhanced HLD nodes with semantic analysis."""
        hld_nodes = {}
        
        # Group files by semantic analysis results
        semantic_groups = self._group_files_by_semantics(parsing_result)
        
        for group_name, files in semantic_groups.items():
            if not files:
                continue
            
            # Get semantic analysis for the group
            group_semantics = self._get_group_semantics(files)
            
            node_id = f"module_{group_name.lower().replace(' ', '_')}"
            hld_nodes[node_id] = GraphNode(
                id=node_id,
                name=group_name,
                type=group_semantics.get('component_type', NodeType.MODULE),
                level=NodeLevel.HLD,
                files=files,
                metadata=self._create_enhanced_node_metadata(files, parsing_result, group_semantics)
            )
        
        return hld_nodes
    
    def _create_enhanced_lld_nodes(self, parsing_result: Dict[str, Any]) -> Dict[str, GraphNode]:
        """Create enhanced LLD nodes with semantic analysis."""
        lld_nodes = {}
        
        for file_path, file_data in parsing_result['parsed_files'].items():
            semantic_result = self.semantic_results.get(file_path, {})
            
            # Create nodes for functions with semantic analysis
            for func_name in file_data['functions']:
                node_id = f"function_{func_name}_{Path(file_path).stem}"
                lld_nodes[node_id] = GraphNode(
                    id=node_id,
                    name=func_name,
                    type=NodeType.FUNCTION,
                    level=NodeLevel.LLD,
                    files=[file_path],
                    functions=[func_name],
                    metadata=self._create_enhanced_function_metadata(func_name, file_path, parsing_result, semantic_result)
                )
            
            # Create nodes for classes with semantic analysis
            for class_name in file_data['classes']:
                node_id = f"class_{class_name}_{Path(file_path).stem}"
                lld_nodes[node_id] = GraphNode(
                    id=node_id,
                    name=class_name,
                    type=NodeType.CLASS,
                    level=NodeLevel.LLD,
                    files=[file_path],
                    classes=[class_name],
                    metadata=self._create_enhanced_class_metadata(class_name, file_path, parsing_result, semantic_result)
                )
        
        return lld_nodes
    
    def _create_enhanced_graph_edges(self, parsing_result: Dict[str, Any], 
                                   hld_nodes: Dict[str, GraphNode], 
                                   lld_nodes: Dict[str, GraphNode]) -> List[GraphEdge]:
        """Create enhanced graph edges with relationship mapping."""
        edges = []
        
        # Create containment edges (HLD contains LLD)
        for lld_node in lld_nodes.values():
            for file_path in lld_node.files:
                parent_hld = self._find_parent_hld_node(file_path, hld_nodes)
                if parent_hld:
                    edges.append(GraphEdge(
                        from_node=parent_hld.id,
                        to_node=lld_node.id,
                        type=EdgeType.CONTAINS,
                        metadata={'relationship_type': 'hierarchy'}
                    ))
                    lld_node.parent = parent_hld.id
                    parent_hld.children.append(lld_node.id)
        
        # Create relationship edges based on semantic analysis
        relationship_edges = self._create_relationship_edges(parsing_result, lld_nodes)
        edges.extend(relationship_edges)
        
        return edges
    
    def _group_files_by_semantics(self, parsing_result: Dict[str, Any]) -> Dict[str, List[str]]:
        """Group files by their semantic analysis results."""
        groups = {
            'API Layer': [],
            'Service Layer': [],
            'Data Models': [],
            'Utilities': [],
            'Configuration': [],
            'Other': []
        }
        
        for file_path, file_data in parsing_result['parsed_files'].items():
            semantic_result = self.semantic_results.get(file_path, {})
            component_type = semantic_result.get('component_type', NodeType.MODULE)
            
            if component_type == NodeType.API:
                groups['API Layer'].append(file_path)
            elif component_type == NodeType.SERVICE:
                groups['Service Layer'].append(file_path)
            elif component_type == NodeType.MODEL:
                groups['Data Models'].append(file_path)
            elif component_type == NodeType.UTILITY:
                groups['Utilities'].append(file_path)
            elif component_type in [NodeType.DATABASE, NodeType.CLIENT]:
                groups['Configuration'].append(file_path)
            else:
                groups['Other'].append(file_path)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _get_group_semantics(self, files: List[str]) -> Dict[str, Any]:
        """Get aggregated semantic analysis for a group of files."""
        if not files:
            return {}
        
        # Aggregate semantic results for the group
        purposes = []
        complexities = []
        component_types = []
        
        for file_path in files:
            semantic_result = self.semantic_results.get(file_path, {})
            purposes.append(semantic_result.get('purpose', ''))
            complexities.append(semantic_result.get('complexity', ComplexityLevel.LOW))
            component_types.append(semantic_result.get('component_type', NodeType.MODULE))
        
        # Determine dominant characteristics
        dominant_type = max(set(component_types), key=component_types.count) if component_types else NodeType.MODULE
        avg_complexity = self._calculate_average_complexity(complexities)
        
        return {
            'purpose': f"Group of {len(files)} files with {dominant_type.value} functionality",
            'component_type': dominant_type,
            'complexity': avg_complexity,
            'file_count': len(files)
        }
    
    def _create_enhanced_node_metadata(self, files: List[str], parsing_result: Dict[str, Any], 
                                     semantic_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced metadata for a node with semantic analysis."""
        total_lines = 0
        total_size = 0
        
        for file_path in files:
            if file_path in parsing_result['parsed_files']:
                file_info = parsing_result['parsed_files'][file_path]['file_info']
                total_lines += file_info.line_count
                total_size += file_info.size
        
        return {
            'purpose': semantic_result.get('purpose', f"Contains {len(files)} files"),
            'complexity': semantic_result.get('complexity', ComplexityLevel.MEDIUM),
            'dependencies': [],
            'line_count': total_lines,
            'file_size': total_size,
            'language': 'python',
            'category': 'backend',
            'semantic_analysis': semantic_result
        }
    
    def _create_enhanced_function_metadata(self, func_name: str, file_path: str, 
                                         parsing_result: Dict[str, Any], 
                                         semantic_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced metadata for a function with semantic analysis."""
        file_data = parsing_result['parsed_files'].get(file_path, {})
        file_info = file_data.get('file_info')
        
        # Get relationship summary for this file
        relationship_summary = self.relationship_mapper.get_relationship_summary(
            file_path, self.relationship_results
        )
        
        return {
            'purpose': f"Function: {func_name}",
            'complexity': semantic_result.get('complexity', ComplexityLevel.LOW),
            'dependencies': file_data.get('imports', []),
            'line_count': file_info.line_count if file_info else 0,
            'file_size': file_info.size if file_info else 0,
            'language': file_info.language if file_info else 'python',
            'category': file_info.category if file_info else 'backend',
            'semantic_analysis': semantic_result,
            'relationships': relationship_summary
        }
    
    def _create_enhanced_class_metadata(self, class_name: str, file_path: str, 
                                      parsing_result: Dict[str, Any], 
                                      semantic_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced metadata for a class with semantic analysis."""
        file_data = parsing_result['parsed_files'].get(file_path, {})
        file_info = file_data.get('file_info')
        
        # Get relationship summary for this file
        relationship_summary = self.relationship_mapper.get_relationship_summary(
            file_path, self.relationship_results
        )
        
        return {
            'purpose': f"Class: {class_name}",
            'complexity': semantic_result.get('complexity', ComplexityLevel.MEDIUM),
            'dependencies': file_data.get('imports', []),
            'line_count': file_info.line_count if file_info else 0,
            'file_size': file_info.size if file_info else 0,
            'language': file_info.language if file_info else 'python',
            'category': file_info.category if file_info else 'backend',
            'semantic_analysis': semantic_result,
            'relationships': relationship_summary
        }
    
    def _find_parent_hld_node(self, file_path: str, hld_nodes: Dict[str, GraphNode]) -> Optional[GraphNode]:
        """Find the HLD node that contains a given file."""
        for hld_node in hld_nodes.values():
            if file_path in hld_node.files:
                return hld_node
        return None
    
    def _create_relationship_edges(self, parsing_result: Dict[str, Any], 
                                 lld_nodes: Dict[str, GraphNode]) -> List[GraphEdge]:
        """Create edges based on relationship mapping."""
        edges = []
        
        for file_path, relationships in self.relationship_results.items():
            for rel in relationships:
                # Find the corresponding LLD nodes
                source_nodes = [n for n in lld_nodes.values() if file_path in n.files]
                target_nodes = [n for n in lld_nodes.values() if rel['target'] in n.files]
                
                # Create edges between the nodes
                for source_node in source_nodes:
                    for target_node in target_nodes:
                        if source_node.id != target_node.id:
                            edges.append(GraphEdge(
                                from_node=source_node.id,
                                to_node=target_node.id,
                                type=rel['type'],
                                metadata={
                                    'strength': rel['strength'],
                                    'description': rel['description'],
                                    'relationship_type': 'semantic'
                                }
                            ))
        
        return edges
    
    def _calculate_average_complexity(self, complexities: List[ComplexityLevel]) -> ComplexityLevel:
        """Calculate average complexity from a list of complexity levels."""
        if not complexities:
            return ComplexityLevel.LOW
        
        # Convert to numeric values for averaging
        complexity_values = {
            ComplexityLevel.LOW: 1,
            ComplexityLevel.MEDIUM: 2,
            ComplexityLevel.HIGH: 3
        }
        
        avg_value = sum(complexity_values.get(c, 1) for c in complexities) / len(complexities)
        
        if avg_value >= 2.5:
            return ComplexityLevel.HIGH
        elif avg_value >= 1.5:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.LOW
    
    def _get_default_semantic_analysis(self, file_path: str) -> Dict[str, Any]:
        """Get default semantic analysis when analysis fails."""
        return {
            'purpose': f"File: {Path(file_path).name}",
            'level': NodeLevel.LLD,
            'component_type': NodeType.MODULE,
            'complexity': ComplexityLevel.LOW,
            'relationships': {},
            'confidence': 0.5,
            'analysis_method': 'default'
        }
    
    def _validate_and_enrich_graph(self, graph: Graph) -> None:
        """Validate and enrich the graph with additional metadata."""
        logger.info("Validating and enriching graph...")
        
        # Validate graph structure
        validation_issues = self.graph_builder.validate_graph()
        if validation_issues:
            logger.warning(f"Graph validation found {len(validation_issues)} issues")
            for issue in validation_issues:
                logger.warning(f"  - {issue}")
        
        # Enrich with semantic analysis statistics
        semantic_stats = self.semantic_analyzer.get_analysis_statistics()
        relationship_metrics = self.relationship_mapper.calculate_dependency_metrics(
            self.relationship_results
        )
        
        logger.info(f"Semantic analysis: {semantic_stats}")
        logger.info(f"Relationship metrics: {relationship_metrics}")
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """Get enhanced statistics about the graph building process."""
        semantic_stats = self.semantic_analyzer.get_analysis_statistics()
        relationship_metrics = self.relationship_mapper.calculate_dependency_metrics(
            self.relationship_results
        )
        
        return {
            'semantic_analysis': semantic_stats,
            'relationship_mapping': relationship_metrics,
            'enhanced_features': {
                'semantic_classification': True,
                'relationship_mapping': True,
                'complexity_analysis': True,
                'dependency_analysis': True
            }
        } 