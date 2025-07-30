"""
Main codebase analyzer for AutoGraph.
Coordinates the entire analysis pipeline and builds the hierarchical graph.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from ..utils.logger import get_logger
from ..utils.file_utils import FileUtils
from ..parser.file_parser import FileParser
from ..models.schemas import Graph, GraphMetadata, GraphNode, GraphEdge, NodeLevel, NodeType, EdgeType, ComplexityLevel
from ..models.graph_models import GraphBuilder, FileCategorizer
from ..graph_builder.enhanced_graph_builder import EnhancedGraphBuilder
from ..export.enhanced_exporter import EnhancedExporter

logger = get_logger(__name__)


class CodebaseAnalyzer:
    """Main analyzer that coordinates the entire analysis pipeline."""
    
    def __init__(self):
        self.file_parser = FileParser()
        self.graph_builder = GraphBuilder()
        self.enhanced_graph_builder = EnhancedGraphBuilder()
        self.enhanced_exporter = EnhancedExporter()
        self.analysis_results: Dict[str, Any] = {}
    
    def analyze_codebase(self, codebase_path: str) -> Dict[str, Any]:
        """Analyze a codebase and generate the hierarchical graph."""
        logger.log_analysis_start(codebase_path)
        
        # Validate codebase path
        if not FileUtils.validate_codebase_path(codebase_path):
            return self._create_error_result("Invalid codebase path")
        
        try:
            # Create output directories
            FileUtils.create_output_directories()
            
            # Step 1: Parse all files
            parsing_result = self.file_parser.parse_codebase(codebase_path)
            if not parsing_result['success']:
                return self._create_error_result("File parsing failed")
            
            # Step 2: Build enhanced graph structure with semantic analysis
            graph = self.enhanced_graph_builder.build_enhanced_graph(codebase_path, parsing_result)
            
            # Step 3: Validate graph
            validation_issues = self.graph_builder.validate_graph()
            if validation_issues:
                logger.log_graph_validation(validation_issues)
            
            # Step 4: Export graph in multiple formats
            export_results = self._export_analysis_results(graph, codebase_path)
            
            # Step 5: Generate final result with enhanced statistics
            result = self._create_enhanced_analysis_result(codebase_path, parsing_result, graph, validation_issues, export_results)
            
            logger.log_analysis_complete(result['statistics'])
            return result
            
        except Exception as e:
            error_msg = f"Analysis failed: {e}"
            logger.error(error_msg)
            return self._create_error_result(error_msg)
    
    def _build_graph_structure(self, codebase_path: str, parsing_result: Dict[str, Any]) -> Graph:
        """Build the hierarchical graph structure from parsing results."""
        logger.info("Building graph structure...")
        
        # Create graph metadata
        metadata = self._create_graph_metadata(codebase_path, parsing_result)
        
        # Create HLD nodes (modules, services, etc.)
        hld_nodes = self._create_hld_nodes(parsing_result)
        
        # Create LLD nodes (functions, classes, etc.)
        lld_nodes = self._create_lld_nodes(parsing_result)
        
        # Create edges between nodes
        edges = self._create_graph_edges(parsing_result, hld_nodes, lld_nodes)
        
        # Build the graph
        graph = Graph(
            metadata=metadata,
            nodes=list(hld_nodes.values()) + list(lld_nodes.values()),
            edges=edges
        )
        
        logger.info(f"Graph built: {len(hld_nodes)} HLD nodes, {len(lld_nodes)} LLD nodes, {len(edges)} edges")
        return graph
    
    def _create_graph_metadata(self, codebase_path: str, parsing_result: Dict[str, Any]) -> GraphMetadata:
        """Create metadata for the graph."""
        stats = parsing_result['parsing_stats']
        
        return GraphMetadata(
            codebase_path=codebase_path,
            analysis_timestamp=datetime.now(),
            file_count=stats['total_files'],
            coverage_percentage=stats['coverage_percentage'],
            total_lines=sum(file_data['file_info'].line_count for file_data in parsing_result['parsed_files'].values()),
            languages=list(stats['languages'].keys()),
            categories=stats['categories']
        )
    
    def _create_hld_nodes(self, parsing_result: Dict[str, Any]) -> Dict[str, GraphNode]:
        """Create High-Level Design nodes."""
        hld_nodes = {}
        
        # Group files by category to create HLD nodes
        category_files = {}
        for file_path, file_data in parsing_result['parsed_files'].items():
            category = file_data['file_info'].category
            if category not in category_files:
                category_files[category] = []
            category_files[category].append(file_path)
        
        # Create HLD nodes for each category
        for category, files in category_files.items():
            if category == 'backend':
                # Create separate nodes for different backend components
                self._create_backend_hld_nodes(files, parsing_result, hld_nodes)
            else:
                # Create single node for other categories
                node_id = f"module_{category}"
                hld_nodes[node_id] = GraphNode(
                    id=node_id,
                    name=f"{category.title()} Module",
                    type=NodeType.MODULE,
                    level=NodeLevel.HLD,
                    files=files,
                    metadata=self._create_node_metadata(files, parsing_result)
                )
        
        return hld_nodes
    
    def _create_backend_hld_nodes(self, files: List[str], parsing_result: Dict[str, Any], hld_nodes: Dict[str, GraphNode]) -> None:
        """Create specialized HLD nodes for backend components."""
        # Group backend files by their purpose
        api_files = []
        service_files = []
        model_files = []
        utility_files = []
        
        for file_path in files:
            file_name = Path(file_path).name.lower()
            if any(keyword in file_name for keyword in ['api', 'route', 'endpoint', 'controller']):
                api_files.append(file_path)
            elif any(keyword in file_name for keyword in ['service', 'business', 'logic']):
                service_files.append(file_path)
            elif any(keyword in file_name for keyword in ['model', 'entity', 'schema']):
                model_files.append(file_path)
            else:
                utility_files.append(file_path)
        
        # Create HLD nodes for each backend component type
        if api_files:
            hld_nodes['module_api'] = GraphNode(
                id='module_api',
                name='API Layer',
                type=NodeType.API,
                level=NodeLevel.HLD,
                files=api_files,
                metadata=self._create_node_metadata(api_files, parsing_result)
            )
        
        if service_files:
            hld_nodes['module_service'] = GraphNode(
                id='module_service',
                name='Service Layer',
                type=NodeType.SERVICE,
                level=NodeLevel.HLD,
                files=service_files,
                metadata=self._create_node_metadata(service_files, parsing_result)
            )
        
        if model_files:
            hld_nodes['module_model'] = GraphNode(
                id='module_model',
                name='Data Models',
                type=NodeType.MODEL,
                level=NodeLevel.HLD,
                files=model_files,
                metadata=self._create_node_metadata(model_files, parsing_result)
            )
        
        if utility_files:
            hld_nodes['module_utility'] = GraphNode(
                id='module_utility',
                name='Utilities',
                type=NodeType.UTILITY,
                level=NodeLevel.HLD,
                files=utility_files,
                metadata=self._create_node_metadata(utility_files, parsing_result)
            )
    
    def _create_lld_nodes(self, parsing_result: Dict[str, Any]) -> Dict[str, GraphNode]:
        """Create Low-Level Design nodes."""
        lld_nodes = {}
        
        for file_path, file_data in parsing_result['parsed_files'].items():
            # Create nodes for functions
            for func_name in file_data['functions']:
                node_id = f"function_{func_name}_{Path(file_path).stem}"
                lld_nodes[node_id] = GraphNode(
                    id=node_id,
                    name=func_name,
                    type=NodeType.FUNCTION,
                    level=NodeLevel.LLD,
                    files=[file_path],
                    functions=[func_name],
                    metadata=self._create_function_metadata(func_name, file_path, parsing_result)
                )
            
            # Create nodes for classes
            for class_name in file_data['classes']:
                node_id = f"class_{class_name}_{Path(file_path).stem}"
                lld_nodes[node_id] = GraphNode(
                    id=node_id,
                    name=class_name,
                    type=NodeType.CLASS,
                    level=NodeLevel.LLD,
                    files=[file_path],
                    classes=[class_name],
                    metadata=self._create_class_metadata(class_name, file_path, parsing_result)
                )
        
        return lld_nodes
    
    def _create_graph_edges(self, parsing_result: Dict[str, Any], hld_nodes: Dict[str, GraphNode], lld_nodes: Dict[str, GraphNode]) -> List[GraphEdge]:
        """Create edges between nodes."""
        edges = []
        
        # Create containment edges (HLD contains LLD)
        for lld_node in lld_nodes.values():
            for file_path in lld_node.files:
                # Find parent HLD node
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
        
        # Create import edges between LLD nodes
        import_edges = self._create_import_edges(parsing_result, lld_nodes)
        edges.extend(import_edges)
        
        return edges
    
    def _find_parent_hld_node(self, file_path: str, hld_nodes: Dict[str, GraphNode]) -> Optional[GraphNode]:
        """Find the HLD node that contains a given file."""
        for hld_node in hld_nodes.values():
            if file_path in hld_node.files:
                return hld_node
        return None
    
    def _create_import_edges(self, parsing_result: Dict[str, Any], lld_nodes: Dict[str, GraphNode]) -> List[GraphEdge]:
        """Create edges based on import relationships."""
        edges = []
        
        # This is a simplified implementation
        # In a full implementation, you would analyze import statements and create edges
        # between functions/classes that import each other
        
        return edges
    
    def _create_node_metadata(self, files: List[str], parsing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for a node."""
        total_lines = 0
        total_size = 0
        
        for file_path in files:
            if file_path in parsing_result['parsed_files']:
                file_info = parsing_result['parsed_files'][file_path]['file_info']
                total_lines += file_info.line_count
                total_size += file_info.size
        
        return {
            'purpose': f"Contains {len(files)} files",
            'complexity': ComplexityLevel.MEDIUM,
            'dependencies': [],
            'line_count': total_lines,
            'file_size': total_size,
            'language': 'python',
            'category': 'backend'
        }
    
    def _create_function_metadata(self, func_name: str, file_path: str, parsing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for a function node."""
        file_data = parsing_result['parsed_files'].get(file_path, {})
        file_info = file_data.get('file_info')
        
        if file_info:
            return {
                'purpose': f"Function: {func_name}",
                'complexity': ComplexityLevel.LOW,
                'dependencies': file_data.get('imports', []),
                'line_count': file_info.line_count,
                'file_size': file_info.size,
                'language': file_info.language,
                'category': file_info.category
            }
        else:
            return {
                'purpose': f"Function: {func_name}",
                'complexity': ComplexityLevel.LOW,
                'dependencies': file_data.get('imports', []),
                'line_count': 0,
                'file_size': 0,
                'language': 'python',
                'category': 'backend'
            }
    
    def _create_class_metadata(self, class_name: str, file_path: str, parsing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for a class node."""
        file_data = parsing_result['parsed_files'].get(file_path, {})
        file_info = file_data.get('file_info')
        
        if file_info:
            return {
                'purpose': f"Class: {class_name}",
                'complexity': ComplexityLevel.MEDIUM,
                'dependencies': file_data.get('imports', []),
                'line_count': file_info.line_count,
                'file_size': file_info.size,
                'language': file_info.language,
                'category': file_info.category
            }
        else:
            return {
                'purpose': f"Class: {class_name}",
                'complexity': ComplexityLevel.MEDIUM,
                'dependencies': file_data.get('imports', []),
                'line_count': 0,
                'file_size': 0,
                'language': 'python',
                'category': 'backend'
            }
    
    def _export_analysis_results(self, graph: Graph, codebase_path: str) -> Dict[str, str]:
        """Export analysis results in multiple formats."""
        logger.info("Exporting analysis results...")
        
        # Create export directory
        export_dir = Path("graph") / Path(codebase_path).name / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Export in all formats
        export_results = self.enhanced_exporter.export_graph(graph, str(export_dir))
        
        # Generate export report
        report_content = self.enhanced_exporter.generate_export_report(export_results)
        report_path = export_dir / "export_report.md"
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        export_results['report'] = str(report_path)
        logger.info(f"Export completed. Report: {report_path}")
        
        return export_results
    
    def _create_enhanced_analysis_result(self, codebase_path: str, parsing_result: Dict[str, Any], graph: Graph, validation_issues: List[str], export_results: Dict[str, str]) -> Dict[str, Any]:
        """Create the final enhanced analysis result with semantic analysis and exports."""
        # Get enhanced statistics
        enhanced_stats = self.enhanced_graph_builder.get_enhanced_statistics()
        
        return {
            'success': True,
            'codebase_path': codebase_path,
            'graph': graph,
            'parsing_result': parsing_result,
            'validation_issues': validation_issues,
            'export_results': export_results,
            'enhanced_features': {
                'semantic_analysis': True,
                'relationship_mapping': True,
                'complexity_analysis': True,
                'dependency_analysis': True,
                'visualization': True,
                'multi_format_export': True
            },
            'statistics': {
                'total_files': parsing_result['parsing_stats']['total_files'],
                'successful_parses': parsing_result['parsing_stats']['successful_parses'],
                'coverage_percentage': parsing_result['parsing_stats']['coverage_percentage'],
                'hld_nodes': len([n for n in graph.nodes if n.level == NodeLevel.HLD]),
                'lld_nodes': len([n for n in graph.nodes if n.level == NodeLevel.LLD]),
                'total_edges': len(graph.edges),
                'semantic_analysis': enhanced_stats['semantic_analysis'],
                'relationship_mapping': enhanced_stats['relationship_mapping'],
                'export_formats': len([k for k in export_results.keys() if not k.endswith('_error')])
            }
        }
    
    def _create_analysis_result(self, codebase_path: str, parsing_result: Dict[str, Any], graph: Graph, validation_issues: List[str]) -> Dict[str, Any]:
        """Create the final analysis result (legacy method)."""
        return self._create_enhanced_analysis_result(codebase_path, parsing_result, graph, validation_issues)
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result when analysis fails."""
        return {
            'success': False,
            'error': error_message,
            'codebase_path': '',
            'graph': None,
            'parsing_result': None,
            'validation_issues': [],
            'statistics': {}
        } 