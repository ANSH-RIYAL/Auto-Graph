"""
Graph visualizer for AutoGraph.
Generates visual representations of HLD/LLD graphs.
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from ..utils.logger import get_logger
from ..models.schemas import Graph, GraphNode, GraphEdge, NodeLevel, NodeType, EdgeType
from ..models.graph_models import GraphBuilder

logger = get_logger(__name__)


class GraphVisualizer:
    """Visualizes AutoGraph graphs in various formats."""
    
    def __init__(self):
        self.graph_builder = GraphBuilder()
        self.visualization_config = {
            'hld_color': '#4A90E2',  # Blue for HLD
            'lld_color': '#F5A623',  # Orange for LLD
            'api_color': '#7ED321',  # Green for APIs
            'service_color': '#9013FE',  # Purple for Services
            'model_color': '#50E3C2',  # Teal for Models
            'utility_color': '#D0021B',  # Red for Utilities
            'edge_color': '#9B9B9B',  # Gray for edges
            'font_family': 'Arial, sans-serif',
            'font_size': 12
        }
    
    def generate_dot_visualization(self, graph: Graph, output_path: str) -> str:
        """Generate DOT format visualization for Graphviz."""
        logger.info("Generating DOT visualization...")
        
        dot_content = [
            "digraph AutoGraph {",
            "  rankdir=TB;",
            "  node [shape=box, style=filled, fontname=\"Arial\"];",
            "  edge [fontname=\"Arial\", fontsize=10];",
            "",
            "  // Subgraph for HLD nodes",
            "  subgraph cluster_hld {",
            "    label=\"High-Level Design (HLD)\";",
            "    style=filled;",
            "    color=lightblue;",
            "    node [style=filled, fillcolor=lightblue];"
        ]
        
        # Add HLD nodes
        hld_nodes = [n for n in graph.nodes if n.level == NodeLevel.HLD]
        for node in hld_nodes:
            color = self._get_node_color(node.type)
            dot_content.append(f"    \"{node.id}\" [label=\"{node.name}\", fillcolor=\"{color}\"];")
        
        dot_content.append("  }")
        dot_content.append("")
        dot_content.append("  // Subgraph for LLD nodes")
        dot_content.append("  subgraph cluster_lld {")
        dot_content.append("    label=\"Low-Level Design (LLD)\";")
        dot_content.append("    style=filled;")
        dot_content.append("    color=lightyellow;")
        dot_content.append("    node [style=filled, fillcolor=lightyellow];")
        
        # Add LLD nodes
        lld_nodes = [n for n in graph.nodes if n.level == NodeLevel.LLD]
        for node in lld_nodes:
            color = self._get_node_color(node.type)
            dot_content.append(f"    \"{node.id}\" [label=\"{node.name}\", fillcolor=\"{color}\"];")
        
        dot_content.append("  }")
        dot_content.append("")
        dot_content.append("  // Edges")
        
        # Add edges
        for edge in graph.edges:
            edge_style = self._get_edge_style(edge.type)
            dot_content.append(f"  \"{edge.from_node}\" -> \"{edge.to_node}\" [label=\"{edge.type.value}\", {edge_style}];")
        
        dot_content.append("}")
        
        dot_content = "\n".join(dot_content)
        
        # Save to file
        with open(output_path, 'w') as f:
            f.write(dot_content)
        
        logger.info(f"DOT visualization saved to: {output_path}")
        return dot_content
    
    def generate_json_visualization(self, graph: Graph, output_path: str) -> Dict[str, Any]:
        """Generate JSON format visualization for web-based tools."""
        logger.info("Generating JSON visualization...")
        
        visualization_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_nodes': len(graph.nodes),
                'total_edges': len(graph.edges),
                'hld_nodes': len([n for n in graph.nodes if n.level == NodeLevel.HLD]),
                'lld_nodes': len([n for n in graph.nodes if n.level == NodeLevel.LLD])
            },
            'nodes': [],
            'edges': []
        }
        
        # Convert nodes to visualization format
        for node in graph.nodes:
            node_data = {
                'id': node.id,
                'name': node.name,
                'type': node.type.value,
                'level': node.level.value,
                'color': self._get_node_color(node.type),
                'size': self._get_node_size(node),
                'metadata': node.metadata.model_dump() if hasattr(node.metadata, 'model_dump') else {},
                'files': node.files,
                'functions': node.functions,
                'classes': node.classes
            }
            visualization_data['nodes'].append(node_data)
        
        # Convert edges to visualization format
        for edge in graph.edges:
            edge_data = {
                'from': edge.from_node,
                'to': edge.to_node,
                'type': edge.type.value,
                'color': self._get_edge_color(edge.type),
                'width': self._get_edge_width(edge.type),
                'metadata': edge.metadata
            }
            visualization_data['edges'].append(edge_data)
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(visualization_data, f, indent=2, default=str)
        
        logger.info(f"JSON visualization saved to: {output_path}")
        return visualization_data
    
    def generate_html_visualization(self, graph: Graph, output_path: str) -> str:
        """Generate interactive HTML visualization using D3.js."""
        logger.info("Generating HTML visualization...")
        
        # Generate JSON data first
        json_data = self.generate_json_visualization(graph, output_path.replace('.html', '.json'))
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AutoGraph Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: {self.visualization_config['font_family']};
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}
        .graph-container {{
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }}
        .node {{
            cursor: pointer;
        }}
        .node:hover {{
            stroke: #333;
            stroke-width: 2px;
        }}
        .link {{
            stroke: #999;
            stroke-opacity: 0.6;
        }}
        .link:hover {{
            stroke-opacity: 1;
        }}
        .tooltip {{
            position: absolute;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            pointer-events: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AutoGraph Visualization</h1>
            <p>High-Level Design (HLD) and Low-Level Design (LLD) Graph</p>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background-color: {self.visualization_config['hld_color']}"></div>
                <span>HLD Nodes</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: {self.visualization_config['lld_color']}"></div>
                <span>LLD Nodes</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: {self.visualization_config['api_color']}"></div>
                <span>API</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: {self.visualization_config['service_color']}"></div>
                <span>Service</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: {self.visualization_config['model_color']}"></div>
                <span>Model</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: {self.visualization_config['utility_color']}"></div>
                <span>Utility</span>
            </div>
        </div>
        
        <div class="graph-container">
            <div id="graph"></div>
        </div>
    </div>

    <script>
        // Graph data
        const graphData = {json.dumps(json_data)};
        
        // Set up the visualization
        const width = 1000;
        const height = 600;
        
        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
        
        // Create force simulation
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(30));
        
        // Create links
        const link = svg.append("g")
            .selectAll("line")
            .data(graphData.edges)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke-width", d => d.width || 1);
        
        // Create nodes
        const node = svg.append("g")
            .selectAll("circle")
            .data(graphData.nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", d => d.size || 8)
            .attr("fill", d => d.color)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        // Add labels
        const label = svg.append("g")
            .selectAll("text")
            .data(graphData.nodes)
            .enter().append("text")
            .text(d => d.name)
            .attr("x", 12)
            .attr("dy", ".35em")
            .attr("font-size", "10px");
        
        // Tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);
        
        node.on("mouseover", function(event, d) {{
            tooltip.transition()
                .duration(200)
                .style("opacity", .9);
            tooltip.html(`
                <strong>${{d.name}}</strong><br/>
                Type: ${{d.type}}<br/>
                Level: ${{d.level}}<br/>
                Files: ${{d.files.length}}<br/>
                Functions: ${{d.functions.length}}<br/>
                Classes: ${{d.classes.length}}
            `)
                .style("left", (event.pageX + 5) + "px")
                .style("top", (event.pageY - 28) + "px");
        }})
        .on("mouseout", function(d) {{
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
        }});
        
        // Update positions on simulation tick
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
            
            label
                .attr("x", d => d.x + 12)
                .attr("y", d => d.y);
        }});
        
        // Drag functions
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
    </script>
</body>
</html>
"""
        
        # Save to file
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML visualization saved to: {output_path}")
        return html_content
    
    def generate_mermaid_visualization(self, graph: Graph, output_path: str) -> str:
        """Generate Mermaid format visualization."""
        logger.info("Generating Mermaid visualization...")
        
        mermaid_content = ["graph TB"]
        
        # Add nodes
        for node in graph.nodes:
            node_id = node.id.replace('-', '_').replace(' ', '_')
            color = self._get_mermaid_color(node.type)
            mermaid_content.append(f"    {node_id}[{node.name}]:::node_{node.type.value}")
        
        # Add edges
        for edge in graph.edges:
            from_id = edge.from_node.replace('-', '_').replace(' ', '_')
            to_id = edge.to_node.replace('-', '_').replace(' ', '_')
            mermaid_content.append(f"    {from_id} -->|{edge.type.value}| {to_id}")
        
        # Add styling
        mermaid_content.append("")
        mermaid_content.append("    classDef node_API fill:#7ED321")
        mermaid_content.append("    classDef node_SERVICE fill:#9013FE")
        mermaid_content.append("    classDef node_MODEL fill:#50E3C2")
        mermaid_content.append("    classDef node_UTILITY fill:#D0021B")
        mermaid_content.append("    classDef node_CLASS fill:#F5A623")
        mermaid_content.append("    classDef node_FUNCTION fill:#4A90E2")
        mermaid_content.append("    classDef node_MODULE fill:#9B9B9B")
        
        mermaid_content = "\n".join(mermaid_content)
        
        # Save to file
        with open(output_path, 'w') as f:
            f.write(mermaid_content)
        
        logger.info(f"Mermaid visualization saved to: {output_path}")
        return mermaid_content
    
    def _get_node_color(self, node_type: NodeType) -> str:
        """Get color for a node type."""
        color_map = {
            NodeType.API: self.visualization_config['api_color'],
            NodeType.SERVICE: self.visualization_config['service_color'],
            NodeType.MODEL: self.visualization_config['model_color'],
            NodeType.UTILITY: self.visualization_config['utility_color'],
            NodeType.CLASS: self.visualization_config['lld_color'],
            NodeType.FUNCTION: self.visualization_config['lld_color'],
            NodeType.MODULE: self.visualization_config['hld_color'],
            NodeType.DATABASE: '#8B4513',  # Brown
            NodeType.CLIENT: '#FF69B4'     # Pink
        }
        return color_map.get(node_type, self.visualization_config['hld_color'])
    
    def _get_node_size(self, node: GraphNode) -> int:
        """Get size for a node based on its complexity."""
        base_size = 8
        if node.metadata and 'complexity' in node.metadata:
            complexity = node.metadata['complexity']
            if complexity.value == 'high':
                return base_size + 6
            elif complexity.value == 'medium':
                return base_size + 3
        return base_size
    
    def _get_edge_color(self, edge_type: EdgeType) -> str:
        """Get color for an edge type."""
        color_map = {
            EdgeType.CONTAINS: '#4A90E2',
            EdgeType.IMPORTS: '#7ED321',
            EdgeType.CALLS: '#F5A623',
            EdgeType.INHERITS: '#9013FE',
            EdgeType.DEPENDS: '#D0021B'
        }
        return color_map.get(edge_type, self.visualization_config['edge_color'])
    
    def _get_edge_width(self, edge_type: EdgeType) -> int:
        """Get width for an edge type."""
        width_map = {
            EdgeType.CONTAINS: 3,
            EdgeType.IMPORTS: 2,
            EdgeType.CALLS: 1,
            EdgeType.INHERITS: 2,
            EdgeType.DEPENDS: 1
        }
        return width_map.get(edge_type, 1)
    
    def _get_edge_style(self, edge_type: EdgeType) -> str:
        """Get style for an edge type."""
        style_map = {
            EdgeType.CONTAINS: 'style=bold,color=blue',
            EdgeType.IMPORTS: 'style=dashed,color=green',
            EdgeType.CALLS: 'style=solid,color=orange',
            EdgeType.INHERITS: 'style=bold,color=purple',
            EdgeType.DEPENDS: 'style=dotted,color=red'
        }
        return style_map.get(edge_type, 'style=solid,color=gray')
    
    def _get_mermaid_color(self, node_type: NodeType) -> str:
        """Get Mermaid color for a node type."""
        color_map = {
            NodeType.API: '#7ED321',
            NodeType.SERVICE: '#9013FE',
            NodeType.MODEL: '#50E3C2',
            NodeType.UTILITY: '#D0021B',
            NodeType.CLASS: '#F5A623',
            NodeType.FUNCTION: '#4A90E2',
            NodeType.MODULE: '#9B9B9B'
        }
        return color_map.get(node_type, '#9B9B9B') 