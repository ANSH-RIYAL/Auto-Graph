#!/usr/bin/env python3
"""
Simple test to verify Flask integration works.
"""

import sys
from pathlib import Path
import tempfile
import zipfile
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_flask_integration():
    """Test that Flask app can import and analyze a codebase."""
    try:
        # Test import
        from web.flask_app import app, convert_analysis_result_to_frontend_format
        print("✅ Flask app imports successfully")
        
        # Test with a simple codebase
        test_dir = tempfile.mkdtemp()
        
        # Create a simple test file
        test_file = os.path.join(test_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("""
def hello_world():
    return "Hello, World!"

class TestClass:
    def __init__(self):
        self.name = "test"
""")
        
        # Test analysis using the same import strategy as Flask app
        try:
            from analyzer.codebase_analyzer import CodebaseAnalyzer
        except ImportError:
            from src.analyzer.codebase_analyzer import CodebaseAnalyzer
            
        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze_codebase(test_dir)
        
        if result and result.get('success'):
            print("✅ Analysis completed successfully")
            
            # Test conversion
            frontend_data = convert_analysis_result_to_frontend_format(result)
            if frontend_data:
                print("✅ Frontend conversion successful")
                print(f"   - Nodes: {len(frontend_data['nodes'])}")
                print(f"   - Edges: {len(frontend_data['edges'])}")
                print(f"   - Metadata: {frontend_data['metadata']['file_count']} files")
            else:
                print("❌ Frontend conversion failed")
        else:
            print("❌ Analysis failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🧪 Testing Flask Integration...")
    test_flask_integration()
    print("✅ Test completed!") 