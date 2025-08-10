"""
Pydantic schemas for AutoGraph data structures.
Defines the structure for nodes, edges, and metadata in the hierarchical graph.
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class NodeLevel(str, Enum):
    """Enumeration for node levels in the hierarchical graph (BSI)."""
    BUSINESS = "BUSINESS"
    SYSTEM = "SYSTEM"
    IMPLEMENTATION = "IMPLEMENTATION"


class NodeType(str, Enum):
    """Enumeration for different types of nodes."""
    # HLD Types
    MODULE = "Module"
    API = "API"
    SERVICE = "Service"
    DATABASE = "Database"
    CLIENT = "Client"
    APPLICATION = "Application"
    
    # LLD Types
    COMPONENT = "Component"
    FUNCTION = "Function"
    CLASS = "Class"
    FUNCTION_GROUP = "Function_Group"
    UTILITY = "Utility"
    CONTROLLER = "Controller"
    MODEL = "Model"
    TEST = "Test"


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


class TechnicalDepth(int, Enum):
    """Enumeration for technical depth levels (1=Business, 2=System, 3=Implementation)."""
    BUSINESS = 1
    SYSTEM = 2
    IMPLEMENTATION = 3


class RiskLevel(str, Enum):
    """Enumeration for risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


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
    
    # Enhanced metadata for visualization
    technical_depth: TechnicalDepth = Field(TechnicalDepth.IMPLEMENTATION, description="Technical depth level")
    color: Optional[str] = Field(None, description="Node color for visualization")
    size: Optional[int] = Field(None, description="Node size for visualization")
    
    # Agent detection metadata
    agent_touched: bool = Field(False, description="Whether this component uses AI agents")
    agent_types: List[str] = Field(default_factory=list, description="Types of AI agents used")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="Business risk level")
    business_impact: Optional[str] = Field(None, description="Business impact description")
    agent_context: Optional[str] = Field(None, description="Context of AI agent usage")


class PMMetadata(BaseModel):
    """Project management metadata for nodes."""
    business_value: Optional[str] = Field(None, description="Business value of the component")
    development_status: str = Field("Active", description="Development status")
    completion_percentage: float = Field(0.0, description="Completion percentage (0-100)")
    team_size: Optional[int] = Field(None, description="Team size working on this component")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion date")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    stakeholder_priority: str = Field("medium", description="Stakeholder priority")


class EnhancedMetadata(BaseModel):
    """Enhanced metadata for detailed analysis."""
    total_symbols: int = Field(0, description="Total number of symbols")
    has_parent: bool = Field(False, description="Whether node has a parent")
    has_children: bool = Field(False, description="Whether node has children")
    child_count: int = Field(0, description="Number of children")
    file_diversity: int = Field(0, description="Number of different files")
    complexity_score: int = Field(1, description="Complexity score (1-5)")


class GraphNode(BaseModel):
    """Represents a node in the hierarchical graph."""
    id: str = Field(..., description="Unique identifier for the node")
    name: str = Field(..., description="Human-readable name")
    type: NodeType = Field(..., description="Type of the node")
    level: NodeLevel = Field(..., description="Level in the hierarchy (BUSINESS/SYSTEM/IMPLEMENTATION)")
    
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
    pm_metadata: Optional[PMMetadata] = Field(None, description="Project management metadata")
    enhanced_metadata: Optional[EnhancedMetadata] = Field(None, description="Enhanced analysis metadata")


class GraphEdge(BaseModel):
    """Represents an edge (relationship) between nodes in the graph."""
    from_node: str = Field(..., description="Source node ID")
    to_node: str = Field(..., description="Target node ID")
    type: EdgeType = Field(..., description="Type of relationship")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Edge metadata")


class PMMetrics(BaseModel):
    """Project management metrics for the entire graph."""
    development_velocity: str = Field("medium", description="Development velocity")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="Overall risk level")
    completion_percentage: float = Field(0.0, description="Overall completion percentage")
    blocked_components: int = Field(0, description="Number of blocked components")
    active_dependencies: int = Field(0, description="Number of active dependencies")


class GraphStatistics(BaseModel):
    """Statistics about the graph."""
    total_nodes: int = Field(0, description="Total number of nodes")
    # Backward-compat fields (kept but not primary)
    hld_nodes: int = Field(0, description="Legacy: Number of HLD nodes")
    lld_nodes: int = Field(0, description="Legacy: Number of LLD nodes")
    # BSI counts
    business_nodes: int = Field(0, description="Number of BUSINESS nodes")
    system_nodes: int = Field(0, description="Number of SYSTEM nodes")
    implementation_nodes: int = Field(0, description="Number of IMPLEMENTATION nodes")
    total_edges: int = Field(0, description="Total number of edges")
    technical_depths: Dict[str, int] = Field(default_factory=dict, description="Nodes by technical depth")


class GraphMetadata(BaseModel):
    """Metadata about the entire graph."""
    codebase_path: str = Field(..., description="Path to the analyzed codebase")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    file_count: int = Field(0, description="Total number of files analyzed")
    coverage_percentage: float = Field(0.0, description="Percentage of files successfully parsed")
    total_lines: int = Field(0, description="Total lines of code")
    languages: List[str] = Field(default_factory=list, description="Programming languages found")
    categories: Dict[str, int] = Field(default_factory=dict, description="File categories and counts")
    
    # Enhanced metadata
    statistics: GraphStatistics = Field(default_factory=GraphStatistics, description="Graph statistics")
    pm_metrics: Optional[PMMetrics] = Field(None, description="Project management metrics")


class Graph(BaseModel):
    """Complete hierarchical graph structure."""
    metadata: GraphMetadata = Field(..., description="Graph metadata")
    nodes: List[GraphNode] = Field(default_factory=list, description="List of all nodes")
    edges: List[GraphEdge] = Field(default_factory=list, description="List of all edges")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 