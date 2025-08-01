#!/usr/bin/env python3
"""
Test script to verify enhanced JSON structure and LLM client fixes.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.analyzer.codebase_analyzer import CodebaseAnalyzer
from src.utils.logger import enable_logging_for_debug

def test_enhanced_structure():
    """Test the enhanced JSON structure with calculator app."""
    print("🧪 Testing Enhanced JSON Structure...")
    
    # Enable logging for debugging
    enable_logging_for_debug()
    
    # Test with calculator app
    test_codebase = "examples/sample_codebases/calculator_app"
    
    if not os.path.exists(test_codebase):
        print(f"❌ Test codebase not found: {test_codebase}")
        return False
    
    try:
        # Create analyzer
        analyzer = CodebaseAnalyzer()
        
        # Analyze codebase
        print(f"📊 Analyzing: {test_codebase}")
        result = analyzer.analyze_codebase(test_codebase)
        
        if result.get('error'):
            print(f"❌ Analysis failed: {result['error']}")
            return False
        
        print("✅ Analysis completed successfully")
        
        # Check enhanced structure
        graph = result.get('graph')
        if not graph:
            print("❌ No graph in result")
            return False
        
        # Check for enhanced metadata (Graph is a Pydantic object)
        metadata = graph.metadata
        statistics = metadata.statistics
        pm_metrics = metadata.pm_metrics
        
        print(f"📈 Graph Statistics:")
        print(f"   - Total Nodes: {statistics.total_nodes}")
        print(f"   - HLD Nodes: {statistics.hld_nodes}")
        print(f"   - LLD Nodes: {statistics.lld_nodes}")
        print(f"   - Total Edges: {statistics.total_edges}")
        print(f"   - Technical Depths: {statistics.technical_depths}")
        
        print(f"📊 PM Metrics:")
        if pm_metrics:
            print(f"   - Completion: {pm_metrics.completion_percentage}%")
            print(f"   - Risk Level: {pm_metrics.risk_level}")
            print(f"   - Active Dependencies: {pm_metrics.active_dependencies}")
        else:
            print("   - PM Metrics not available")
        
        # Check nodes for enhanced metadata
        nodes = graph.nodes
        if nodes:
            first_node = nodes[0]
            node_metadata = first_node.metadata
            
            print(f"🎯 Node Metadata Check:")
            print(f"   - Technical Depth: {node_metadata.technical_depth}")
            print(f"   - Color: {node_metadata.color}")
            print(f"   - Size: {node_metadata.size}")
            print(f"   - Agent Touched: {node_metadata.agent_touched}")
            print(f"   - Risk Level: {node_metadata.risk_level}")
        
        # Save enhanced JSON for inspection
        output_file = "test_enhanced_output.json"
        with open(output_file, 'w') as f:
            json.dump(graph.model_dump(), f, indent=2, default=str)
        
        print(f"💾 Enhanced JSON saved to: {output_file}")
        print("✅ Enhanced structure test passed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_structure()
    sys.exit(0 if success else 1) 