"""
Pydantic schemas for AutoGraph data structures.
Defines the structure for nodes, edges, and metadata in the hierarchical graph.
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class NodeLevel(str, Enum):
    """Enumeration for node levels in the hierarchical graph."""
    HLD = "HLD"  # High-Level Design
    LLD = "LLD"  # Low-Level Design


class NodeType(str, Enum):
    """Enumeration for different types of nodes."""
    # HLD Types
    MODULE = "Module"
    API = "API"
    SERVICE = "Service"
    DATABASE = "Database"
    CLIENT = "Client"
    
    # LLD Types
    COMPONENT = "Component"
    FUNCTION = "Function"
    CLASS = "Class"
    FUNCTION_GROUP = "Function_Group"
    UTILITY = "Utility"
    CONTROLLER = "Controller"
    MODEL = "Model"


class EdgeType(str, Enum):
    """Enumeration for different types of relationships between nodes."""
    DEPENDS_ON = "depends_on"
    DEPENDS = "depends"  # Alias for DEPENDS_ON
    CONTAINS = "contains"
    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    COMMUNICATES = "communicates"
    DATA_FLOW = "data_flow"


class ComplexityLevel(str, Enum):
    """Enumeration for complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NodeMetadata(BaseModel):
    """Metadata associated with a graph node."""
    purpose: Optional[str] = Field(None, description="Purpose and responsibility of the node")
    complexity: ComplexityLevel = Field(ComplexityLevel.LOW, description="Complexity level")
    dependencies: List[str] = Field(default_factory=list, description="List of dependencies")
    line_count: Optional[int] = Field(None, description="Number of lines of code")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    last_modified: Optional[datetime] = Field(None, description="Last modification timestamp")
    language: Optional[str] = Field(None, description="Programming language")
    category: Optional[str] = Field(None, description="Category (frontend/backend/module/test/config)")


class GraphNode(BaseModel):
    """Represents a node in the hierarchical graph."""
    id: str = Field(..., description="Unique identifier for the node")
    name: str = Field(..., description="Human-readable name")
    type: NodeType = Field(..., description="Type of the node")
    level: NodeLevel = Field(..., description="Level in the hierarchy (HLD/LLD)")
    
    # File information
    files: List[str] = Field(default_factory=list, description="List of file paths")
    line_numbers: Dict[str, List[int]] = Field(default_factory=dict, description="Line numbers by file")
    
    # Relationships
    parent: Optional[str] = Field(None, description="Parent node ID")
    children: List[str] = Field(default_factory=list, description="Child node IDs")
    
    # Content
    functions: List[str] = Field(default_factory=list, description="List of function names")
    classes: List[str] = Field(default_factory=list, description="List of class names")
    imports: List[str] = Field(default_factory=list, description="List of imports")
    
    # Metadata
    metadata: NodeMetadata = Field(default_factory=NodeMetadata, description="Node metadata")


class GraphEdge(BaseModel):
    """Represents an edge (relationship) between nodes in the graph."""
    from_node: str = Field(..., description="Source node ID")
    to_node: str = Field(..., description="Target node ID")
    type: EdgeType = Field(..., description="Type of relationship")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Edge metadata")


class GraphMetadata(BaseModel):
    """Metadata about the entire graph."""
    codebase_path: str = Field(..., description="Path to the analyzed codebase")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    file_count: int = Field(0, description="Total number of files analyzed")
    coverage_percentage: float = Field(0.0, description="Percentage of files successfully parsed")
    total_lines: int = Field(0, description="Total lines of code")
    languages: List[str] = Field(default_factory=list, description="Programming languages found")
    categories: Dict[str, int] = Field(default_factory=dict, description="File categories and counts")


class Graph(BaseModel):
    """Complete hierarchical graph structure."""
    metadata: GraphMetadata = Field(..., description="Graph metadata")
    nodes: List[GraphNode] = Field(default_factory=list, description="List of all nodes")
    edges: List[GraphEdge] = Field(default_factory=list, description="List of all edges")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 