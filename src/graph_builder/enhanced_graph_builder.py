"""
Enhanced graph builder for AutoGraph Phase 2.
Integrates semantic analysis and relationship mapping for better graph construction.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from ..utils.logger import get_logger
from ..utils.file_utils import FileUtils
from ..models.schemas import (
    Graph, GraphMetadata, GraphNode, GraphEdge, NodeLevel, NodeType, EdgeType, 
    ComplexityLevel, TechnicalDepth, RiskLevel, NodeMetadata, PMMetadata, 
    EnhancedMetadata, PMMetrics, GraphStatistics
)
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
            # Skip non-core sources (tests/docs/examples/static)
            try:
                file_info = file_data.get('file_info')
                p = str(file_path).replace('\\','/').lower()
                if any(seg in p for seg in ['/tests/', '/test/', '/docs/', '/examples/', '/example/', '/static/', '/assets/']):
                    continue
                if file_info and hasattr(file_info, 'category') and file_info.category not in ('backend',):
                    continue
            except Exception:
                pass
            try:
                # Get file content from parsing result
                file_content = file_data.get('file_content', '')
                
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
        
        # Create BUSINESS nodes with semantic analysis
        hld_nodes = self._create_enhanced_hld_nodes(parsing_result)
        
        # Create IMPLEMENTATION nodes with semantic analysis
        lld_nodes = self._create_enhanced_lld_nodes(parsing_result)

        # Phase 2: Build SYSTEM nodes from import graph clustering
        system_nodes, system_edges = self._create_system_nodes_and_edges(parsing_result, hld_nodes, lld_nodes)

        # Create enhanced edges with relationship mapping
        edges = self._create_enhanced_graph_edges(parsing_result, hld_nodes, lld_nodes)
        edges.extend(system_edges)
        
        # Build the graph
        graph = Graph(
            metadata=metadata,
            nodes=list(hld_nodes.values()) + list(system_nodes.values()) + list(lld_nodes.values()),
            edges=edges
        )
        
        return graph

    def _create_system_nodes_and_edges(self, parsing_result: Dict[str, Any],
                                       business_nodes: Dict[str, GraphNode],
                                       impl_nodes: Dict[str, GraphNode]) -> (Dict[str, GraphNode], List[GraphEdge]):
        """Create SYSTEM-level nodes via lightweight clustering of the import graph.
        Fallback to directory-based grouping when clustering is unavailable or trivial.
        """
        try:
            import networkx as nx
            from networkx.algorithms.community import greedy_modularity_communities
        except Exception:
            nx = None
            greedy_modularity_communities = None

        # Build a file-level import graph (core files only)
        file_imports = {}
        file_paths = [fp for fp, fd in parsing_result['parsed_files'].items()
                      if not any(seg in str(fp).replace('\\','/').lower() for seg in ['/tests/','/test/','/docs/','/examples/','/example/','/static/','/assets/'])]
        normalized = {fp: Path(fp) for fp in file_paths}

        def matches_import(target_path: Path, imp: str) -> bool:
            # Simple heuristics to link imports to files
            stem = target_path.stem
            parts = imp.replace(' ', '').replace(':', '').split('.')
            return stem in parts or any(stem in p for p in parts)

        for fp, data in parsing_result['parsed_files'].items():
            imps = data.get('imports', []) or []
            targets = set()
            for other in file_paths:
                if other == fp:
                    continue
                if any(matches_import(normalized[other], imp) for imp in imps):
                    targets.add(other)
            file_imports[fp] = list(targets)

        # Group by package submodule under src/<package>/<group>/
        clusters: List[List[str]] = []
        pkg_groups: Dict[str, List[str]] = {}
        for fp in file_paths:
            lower = str(fp).replace('\\','/')
            key = Path(fp).parent.name
            if '/src/' in lower:
                rel = lower.split('/src/',1)[1]
                parts = rel.split('/')
                if len(parts) >= 2:
                    key = parts[1]
                else:
                    key = parts[0]
            pkg_groups.setdefault(key, []).append(fp)
        clusters = list(pkg_groups.values())

        # Create SYSTEM nodes from clusters
        system_nodes: Dict[str, GraphNode] = {}
        system_edges: List[GraphEdge] = []

        # Helper to find business parent by overlap of files
        def find_business_parent(files: List[str]) -> Optional[GraphNode]:
            best = None
            best_overlap = 0
            file_set = set(files)
            for bn in business_nodes.values():
                overlap = len(file_set.intersection(set(bn.files)))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best = bn
            return best

        # Map impl nodes to their primary file
        impl_by_file: Dict[str, List[GraphNode]] = {}
        for node in impl_nodes.values():
            for f in node.files:
                impl_by_file.setdefault(f, []).append(node)

        # Create nodes and containment edges
        for idx, files in enumerate(clusters):
            dir_names = [Path(f).parent.name for f in files]
            common_dir = max(set(dir_names), key=dir_names.count) if dir_names else f"cluster_{idx+1}"
            pretty_name = common_dir.replace('_',' ').title()
            node_id = f"system_{common_dir.lower()}_{idx+1}"
            system_node = GraphNode(
                id=node_id,
                name=f"{pretty_name}",
                type=NodeType.SERVICE,
                level=NodeLevel.SYSTEM,
                files=files,
                metadata=NodeMetadata(
                    purpose=f"Cluster of {len(files)} files under {common_dir}",
                    complexity=ComplexityLevel.MEDIUM,
                    dependencies=[],
                    line_count=0,
                    file_size=0,
                    language='python',
                    category='cluster',
                    technical_depth=TechnicalDepth.SYSTEM,
                    color=self._get_node_color(NodeType.SERVICE),
                    size=len(files) * 8
                )
            )
            system_nodes[node_id] = system_node

            # Parent under business node
            parent_business = find_business_parent(files)
            if parent_business:
                system_edges.append(GraphEdge(
                    from_node=parent_business.id,
                    to_node=node_id,
                    type=EdgeType.CONTAINS,
                    metadata={'relationship_type': 'hierarchy'}
                ))
                system_node.parent = parent_business.id
                parent_business.children.append(node_id)

            # Attach implementation nodes contained in this cluster
            for f in files:
                for impl in impl_by_file.get(f, []):
                    system_edges.append(GraphEdge(
                        from_node=node_id,
                        to_node=impl.id,
                        type=EdgeType.CONTAINS,
                        metadata={'relationship_type': 'hierarchy'}
                    ))
                    impl.parent = node_id
                    system_node.children.append(impl.id)

        # Collapse file-level imports into system-level depends_on edges
        # Map file to system cluster id
        file_to_cluster: Dict[str, str] = {}
        for sid, snode in system_nodes.items():
            for f in snode.files:
                file_to_cluster[f] = sid

        seen_pairs = set()
        for src, tgts in file_imports.items():
            src_cluster = file_to_cluster.get(src)
            for tgt in tgts:
                tgt_cluster = file_to_cluster.get(tgt)
                if not src_cluster or not tgt_cluster or src_cluster == tgt_cluster:
                    continue
                key = (src_cluster, tgt_cluster)
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                system_edges.append(GraphEdge(
                    from_node=src_cluster,
                    to_node=tgt_cluster,
                    type=EdgeType.DEPENDS_ON,
                    metadata={'relationship_type': 'depends_on'}
                ))

        return system_nodes, system_edges
    
    def _create_enhanced_graph_metadata(self, codebase_path: str, parsing_result: Dict[str, Any]) -> GraphMetadata:
        """Create enhanced graph metadata with semantic analysis statistics."""
        stats = parsing_result['parsing_stats']
        
        # Get semantic analysis statistics
        semantic_stats = self.semantic_analyzer.get_analysis_statistics()
        
        # Get relationship metrics
        relationship_metrics = self.relationship_mapper.calculate_dependency_metrics(
            self.relationship_results
        )
        
        # Calculate enhanced statistics
        total_files = stats['total_files']
        total_lines = sum(file_data['file_info'].line_count for file_data in parsing_result['parsed_files'].values())
        
        # Create graph statistics
        graph_stats = GraphStatistics(
            total_nodes=0,  # Will be updated after graph creation
            hld_nodes=0,    # Will be updated after graph creation
            lld_nodes=0,    # Will be updated after graph creation
            total_edges=0,  # Will be updated after graph creation
            technical_depths={
                "business": 0,
                "system": 0,
                "implementation": 0
            }
        )
        
        # Create PM metrics
        pm_metrics = PMMetrics(
            development_velocity="medium",
            risk_level=RiskLevel.LOW,
            completion_percentage=85.0,  # Default completion
            blocked_components=0,
            active_dependencies=len(relationship_metrics.get('dependency_chains', []))
        )
        
        return GraphMetadata(
            codebase_path=codebase_path,
            analysis_timestamp=datetime.now(),
            file_count=total_files,
            coverage_percentage=stats['coverage_percentage'],
            total_lines=total_lines,
            languages=list(stats['languages'].keys()),
            categories=stats['categories'],
            statistics=graph_stats,
            pm_metrics=pm_metrics
        )
    
    def _create_enhanced_hld_nodes(self, parsing_result: Dict[str, Any]) -> Dict[str, GraphNode]:
        """Create enhanced Business nodes with semantic analysis."""
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
                level=NodeLevel.BUSINESS,
                files=files,
                metadata=self._create_enhanced_node_metadata(files, parsing_result, group_semantics)
            )
        
        return hld_nodes
    
    def _create_enhanced_lld_nodes(self, parsing_result: Dict[str, Any]) -> Dict[str, GraphNode]:
        """Create enhanced Implementation nodes with semantic analysis - grouped by logical containers."""
        lld_nodes = {}
        
        # Track logical groupings
        logical_groups = {}
        
        for file_path, file_data in parsing_result['parsed_files'].items():
            semantic_result = self.semantic_results.get(file_path, {})
            file_stem = Path(file_path).stem
            
            # Group by classes first (classes are logical containers)
            for class_name in file_data['classes']:
                # Skip special methods and low-level functions
                if self._should_skip_low_level_component(class_name):
                    continue
                    
                node_id = f"class_{class_name}_{file_stem}"
                
                # Get all functions that belong to this class
                class_functions = self._get_class_functions(class_name, file_data)
                # Filter out low-level functions
                filtered_functions = [f for f in class_functions if not self._should_skip_low_level_component(f)]
                
                if filtered_functions:  # Only create node if there are meaningful functions
                    lld_nodes[node_id] = GraphNode(
                        id=node_id,
                        name=f"{class_name} Class",
                        type=NodeType.CLASS,
                        level=NodeLevel.IMPLEMENTATION,
                        files=[file_path],
                        classes=[class_name],
                        functions=filtered_functions,
                        metadata=self._create_enhanced_class_metadata(class_name, file_path, parsing_result, semantic_result)
                    )
                    logical_groups[node_id] = {
                        'type': 'class',
                        'name': class_name,
                        'functions': filtered_functions,
                        'file': file_path
                    }
            
            # Group standalone functions by their logical purpose
            standalone_functions = [f for f in file_data['functions'] 
                                  if not self._should_skip_low_level_component(f) 
                                  and not self._is_function_in_class(f, file_data)]
            
            if standalone_functions:
                # Group functions by their semantic purpose
                function_groups = self._group_functions_by_purpose(standalone_functions, file_path, semantic_result)
                
                for group_name, group_functions in function_groups.items():
                    if group_functions:  # Only create group if there are functions
                        node_id = f"function_group_{group_name}_{file_stem}"
                        lld_nodes[node_id] = GraphNode(
                            id=node_id,
                            name=f"{group_name} Functions",
                            type=NodeType.FUNCTION_GROUP,
                            level=NodeLevel.IMPLEMENTATION,
                            files=[file_path],
                            functions=group_functions,
                            metadata=self._create_enhanced_function_group_metadata(group_name, group_functions, file_path, parsing_result, semantic_result)
                        )
                        logical_groups[node_id] = {
                            'type': 'function_group',
                            'name': group_name,
                            'functions': group_functions,
                            'file': file_path
                        }
        
        return lld_nodes
    
    def _should_skip_low_level_component(self, name: str) -> bool:
        """Check if a component should be skipped (too low-level)."""
        low_level_patterns = [
            '__init__', '__str__', '__repr__', '__eq__', '__hash__',
            '__getitem__', '__setitem__', '__delitem__', '__len__',
            '__contains__', '__iter__', '__next__', '__enter__', '__exit__',
            '__call__', '__getattr__', '__setattr__', '__delattr__',
            '__getattribute__', '__new__', '__del__', '__slots__',
            'get_', 'set_', 'is_', 'has_', 'add_', 'remove_', 'clear_',
            'update_', 'reset_', 'init_', 'cleanup_', 'validate_'
        ]
        
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in low_level_patterns)
    
    def _get_class_functions(self, class_name: str, file_data: Dict[str, Any]) -> List[str]:
        """Get all functions that belong to a specific class."""
        # This is a simplified approach - in a real implementation, you'd parse the AST
        # to determine which functions belong to which class
        # For now, we'll return all functions and let the semantic analysis help
        return file_data.get('functions', [])
    
    def _is_function_in_class(self, function_name: str, file_data: Dict[str, Any]) -> bool:
        """Check if a function is likely part of a class."""
        # This is a simplified check - in reality, you'd need AST analysis
        # For now, we'll assume functions with 'self' parameter or class-like naming are in classes
        return any(class_name.lower() in function_name.lower() for class_name in file_data.get('classes', []))
    
    def _group_functions_by_purpose(self, functions: List[str], file_path: str, semantic_result: Dict[str, Any]) -> Dict[str, List[str]]:
        """Group standalone functions by their logical purpose."""
        groups = {
            'Data Processing': [],
            'Validation': [],
            'Utility': [],
            'Business Logic': [],
            'Configuration': [],
            'Other': []
        }
        
        for func_name in functions:
            func_lower = func_name.lower()
            
            # Categorize based on function name patterns
            if any(word in func_lower for word in ['process', 'transform', 'convert', 'parse', 'format']):
                groups['Data Processing'].append(func_name)
            elif any(word in func_lower for word in ['validate', 'check', 'verify', 'test', 'assert']):
                groups['Validation'].append(func_name)
            elif any(word in func_lower for word in ['util', 'helper', 'format', 'clean', 'normalize']):
                groups['Utility'].append(func_name)
            elif any(word in func_lower for word in ['calculate', 'compute', 'analyze', 'generate', 'create']):
                groups['Business Logic'].append(func_name)
            elif any(word in func_lower for word in ['config', 'setup', 'init', 'load', 'save']):
                groups['Configuration'].append(func_name)
            else:
                groups['Other'].append(func_name)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _create_enhanced_function_group_metadata(self, group_name: str, functions: List[str], file_path: str, 
                                               parsing_result: Dict[str, Any], semantic_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for a function group."""
        return {
            'purpose': f"Group of {group_name.lower()} functions",
            'complexity': ComplexityLevel.MEDIUM,
            'dependencies': [],
            'line_count': len(functions) * 10,  # Estimate
            'file_size': 0,
            'language': 'python',
            'category': 'function_group',
            'function_count': len(functions),
            'group_type': group_name
        }
    
    def _create_enhanced_graph_edges(self, parsing_result: Dict[str, Any], 
                                   hld_nodes: Dict[str, GraphNode], 
                                   lld_nodes: Dict[str, GraphNode]) -> List[GraphEdge]:
        """Create enhanced graph edges with relationship mapping."""
        edges = []
        
        # Create containment edges (BUSINESS contains IMPLEMENTATION)
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
            'Core Runtime': [],
            'Models': [],
            'Components': [],
            'Controls': [],
            'Actions': [],
            'Data': [],
            'Integrations': [],
            'Other': []
        }
        
        for file_path, file_data in parsing_result['parsed_files'].items():
            # Only core sources
            try:
                file_info = file_data.get('file_info')
                p = str(file_path).replace('\\','/')
                pl = p.lower()
                if any(seg in pl for seg in ['/tests/','/test/','/docs/','/examples/','/example/','/static/','/assets/']):
                    continue
                if file_info and hasattr(file_info, 'category') and file_info.category not in ('backend',):
                    continue
            except Exception:
                pass
            # Path-based buckets
            if '/src/' in p:
                rel = p.split('/src/',1)[1]
                if rel.startswith('vizro/_vizro'):
                    groups['Core Runtime'].append(file_path)
                elif '/models/_components/' in rel:
                    groups['Components'].append(file_path)
                elif '/models/_controls/' in rel:
                    groups['Controls'].append(file_path)
                elif '/models/' in rel:
                    groups['Models'].append(file_path)
                elif '/actions/' in rel:
                    groups['Actions'].append(file_path)
                elif '/managers/' in rel:
                    groups['Data'].append(file_path)
                elif '/integrations/' in rel:
                    groups['Integrations'].append(file_path)
                else:
                    groups['Other'].append(file_path)
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
                                     semantic_result: Dict[str, Any]) -> NodeMetadata:
        """Create enhanced metadata for a node with semantic analysis."""
        total_lines = 0
        total_size = 0
        
        for file_path in files:
            if file_path in parsing_result['parsed_files']:
                file_info = parsing_result['parsed_files'][file_path]['file_info']
                total_lines += file_info.line_count
                total_size += file_info.size
        
        # Determine technical depth based on node level (Business default)
        technical_depth = TechnicalDepth.BUSINESS
        
        # Determine color based on component type
        color = self._get_node_color(semantic_result.get('component_type', NodeType.MODULE))
        
        return NodeMetadata(
            purpose=semantic_result.get('purpose', f"Contains {len(files)} files"),
            complexity=semantic_result.get('complexity', ComplexityLevel.MEDIUM),
            dependencies=[],
            line_count=total_lines,
            file_size=total_size,
            language='python',
            category='backend',
            technical_depth=technical_depth,
            color=color,
            size=len(files) * 10,  # Size based on number of files
            agent_touched=False,  # Will be updated by agent detection
            agent_types=[],
            risk_level=RiskLevel.LOW,
            business_impact=None,
            agent_context=None
        )
    
    def _create_enhanced_function_metadata(self, func_name: str, file_path: str, 
                                         parsing_result: Dict[str, Any], 
                                         semantic_result: Dict[str, Any]) -> NodeMetadata:
        """Create enhanced metadata for a function with semantic analysis."""
        file_data = parsing_result['parsed_files'].get(file_path, {})
        file_info = file_data.get('file_info')
        
        # Get relationship summary for this file
        relationship_summary = self.relationship_mapper.get_relationship_summary(
            file_path, self.relationship_results
        )
        
        return NodeMetadata(
            purpose=f"Function: {func_name}",
            complexity=semantic_result.get('complexity', ComplexityLevel.LOW),
            dependencies=file_data.get('imports', []),
            line_count=file_info.line_count if file_info else 0,
            file_size=file_info.size if file_info else 0,
            language=file_info.language if file_info else 'python',
            category=file_info.category if file_info else 'backend',
            technical_depth=TechnicalDepth.IMPLEMENTATION,
            color=self._get_node_color(NodeType.FUNCTION),
            size=5,  # Small size for functions
            agent_touched=False,
            agent_types=[],
            risk_level=RiskLevel.LOW,
            business_impact=None,
            agent_context=None
        )
    
    def _create_enhanced_class_metadata(self, class_name: str, file_path: str, 
                                      parsing_result: Dict[str, Any], 
                                      semantic_result: Dict[str, Any]) -> NodeMetadata:
        """Create enhanced metadata for a class with semantic analysis."""
        file_data = parsing_result['parsed_files'].get(file_path, {})
        file_info = file_data.get('file_info')
        
        # Get relationship summary for this file
        relationship_summary = self.relationship_mapper.get_relationship_summary(
            file_path, self.relationship_results
        )
        
        return NodeMetadata(
            purpose=f"Class: {class_name}",
            complexity=semantic_result.get('complexity', ComplexityLevel.MEDIUM),
            dependencies=file_data.get('imports', []),
            line_count=file_info.line_count if file_info else 0,
            file_size=file_info.size if file_info else 0,
            language=file_info.language if file_info else 'python',
            category=file_info.category if file_info else 'backend',
            technical_depth=TechnicalDepth.IMPLEMENTATION,
            color=self._get_node_color(NodeType.CLASS),
            size=8,  # Medium size for classes
            agent_touched=False,
            agent_types=[],
            risk_level=RiskLevel.LOW,
            business_impact=None,
            agent_context=None
        )
    
    def _find_parent_hld_node(self, file_path: str, hld_nodes: Dict[str, GraphNode]) -> Optional[GraphNode]:
        """Find the BUSINESS node that contains a given file."""
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
            'level': NodeLevel.IMPLEMENTATION,
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
        
        # Update graph statistics
        hld_nodes = [node for node in graph.nodes if node.level == NodeLevel.BUSINESS]
        lld_nodes = [node for node in graph.nodes if node.level == NodeLevel.IMPLEMENTATION]
        
        # Count nodes by technical depth
        technical_depths = {
            "business": len(hld_nodes),
            "system": len([n for n in graph.nodes if n.metadata.technical_depth == TechnicalDepth.SYSTEM]),
            "implementation": len([n for n in graph.nodes if n.metadata.technical_depth == TechnicalDepth.IMPLEMENTATION])
        }
        
        # Update graph statistics
        graph.metadata.statistics = GraphStatistics(
            total_nodes=len(graph.nodes),
            hld_nodes=len(hld_nodes),  # legacy
            lld_nodes=len(lld_nodes),  # legacy
            business_nodes=len(hld_nodes),
            system_nodes=len([n for n in graph.nodes if n.metadata.technical_depth == TechnicalDepth.SYSTEM]),
            implementation_nodes=len(lld_nodes),
            total_edges=len(graph.edges),
            technical_depths=technical_depths
        )
        
        # Update PM metrics
        if graph.metadata.pm_metrics:
            # Calculate completion percentage based on node complexity
            total_complexity = sum(
                {"low": 1, "medium": 2, "high": 3}.get(node.metadata.complexity.value, 1)
                for node in graph.nodes
            )
            avg_complexity = total_complexity / len(graph.nodes) if graph.nodes else 1
            
            # Estimate completion based on complexity and node count
            completion_percentage = min(95.0, max(10.0, 100 - (avg_complexity * 10)))
            
            # Determine risk level based on complexity and agent usage
            high_complexity_nodes = [n for n in graph.nodes if n.metadata.complexity == ComplexityLevel.HIGH]
            agent_touched_nodes = [n for n in graph.nodes if n.metadata.agent_touched]
            
            risk_level = RiskLevel.LOW
            if len(agent_touched_nodes) > 0:
                risk_level = RiskLevel.MEDIUM
            if len(high_complexity_nodes) > len(graph.nodes) * 0.3:
                risk_level = RiskLevel.HIGH
            if len(agent_touched_nodes) > len(graph.nodes) * 0.2:
                risk_level = RiskLevel.CRITICAL
            
            graph.metadata.pm_metrics.completion_percentage = completion_percentage
            graph.metadata.pm_metrics.risk_level = risk_level
            graph.metadata.pm_metrics.active_dependencies = len(graph.edges)
        
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

    def _get_node_color(self, node_type: NodeType) -> str:
        """Get color for node based on type."""
        color_map = {
            NodeType.MODULE: '#9013FE',
            NodeType.API: '#4A90E2',
            NodeType.SERVICE: '#D0021B',
            NodeType.DATABASE: '#FF9800',
            NodeType.CLIENT: '#4CAF50',
            NodeType.APPLICATION: '#2196F3',
            NodeType.COMPONENT: '#9C27B0',
            NodeType.FUNCTION: '#607D8B',
            NodeType.CLASS: '#795548',
            NodeType.FUNCTION_GROUP: '#FF5722',
            NodeType.UTILITY: '#00BCD4',
            NodeType.CONTROLLER: '#8BC34A',
            NodeType.MODEL: '#FFC107',
            NodeType.TEST: '#E91E63'
        }
        return color_map.get(node_type, '#f0f0f0') 