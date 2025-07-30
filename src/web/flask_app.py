from flask import Flask, render_template, request, jsonify, send_file, session
import json
import os
import sys
from datetime import datetime
import uuid
from pathlib import Path
import tempfile
import zipfile
import shutil

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from analyzer.codebase_analyzer import CodebaseAnalyzer
    from models.schemas import NodeLevel, NodeType, ComplexityLevel
    from utils.logger import get_logger
    from export.enhanced_exporter import EnhancedExporter
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative import paths...")
    
    # Try alternative import paths
    try:
        from src.analyzer.codebase_analyzer import CodebaseAnalyzer
        from src.models.schemas import NodeLevel, NodeType, ComplexityLevel
        from src.utils.logger import get_logger
        from src.export.enhanced_exporter import EnhancedExporter
    except ImportError as e2:
        print(f"Alternative import also failed: {e2}")
        raise

app = Flask(__name__)
app.secret_key = 'autograph-secret-key'

# Initialize logger
logger = get_logger(__name__)

# Store analysis results in memory (in production, use a proper database)
analysis_results = {}
analysis_sessions = {}

def convert_analysis_result_to_frontend_format(analysis_result):
    """Convert our backend analysis result to the frontend format"""
    if not analysis_result or 'graph' not in analysis_result or not analysis_result['graph']:
        return None
    
    graph = analysis_result['graph']
    
    # Convert nodes to frontend format
    nodes = []
    for node in graph.nodes:  # Graph object has .nodes attribute, not .get('nodes')
        frontend_node = {
            "id": node.id,
            "name": node.name,
            "type": node.type.value if hasattr(node.type, 'value') else str(node.type),
            "level": node.level.value if hasattr(node.level, 'value') else str(node.level),
            "files": node.files,  # Fixed: was file_paths, should be files
            "parent": node.parent,  # Fixed: was parent_id, should be parent
            "children": node.children,  # Fixed: was calculating from edges, should use children directly
            "metadata": {
                "purpose": node.metadata.purpose if node.metadata else '',
                "complexity": node.metadata.complexity.value if node.metadata and hasattr(node.metadata.complexity, 'value') else str(node.metadata.complexity) if node.metadata else 'low',
                "dependencies": node.metadata.dependencies if node.metadata else [],
                "line_count": node.metadata.line_count if node.metadata else 0,
                "file_size": node.metadata.file_size if node.metadata else 0,
                "language": node.metadata.language if node.metadata else 'unknown',
                "category": node.metadata.category if node.metadata else 'other'
            },
            "position": {"x": 0, "y": 0}  # Will be calculated by frontend
        }
        nodes.append(frontend_node)
    
    # Convert edges to frontend format
    edges = []
    for edge in graph.edges:  # Graph object has .edges attribute, not .get('edges')
        frontend_edge = {
            "id": f"{edge.from_node}_{edge.to_node}",  # Create ID from source and target
            "source": edge.from_node,  # Fixed: was source_id, should be from_node
            "target": edge.to_node,  # Fixed: was target_id, should be to_node
            "type": edge.type.value if hasattr(edge.type, 'value') else str(edge.type),
            "metadata": {
                "relationship_type": edge.metadata.get('relationship_type', 'dependency') if edge.metadata else 'dependency'
            }
        }
        edges.append(frontend_edge)
    
    # Create metadata
    metadata = {
        "codebase_path": analysis_result.get('codebase_path', ''),
        "analysis_timestamp": analysis_result.get('timestamp', datetime.now().isoformat()),
        "file_count": analysis_result.get('statistics', {}).get('total_files', 0),
        "coverage_percentage": analysis_result.get('statistics', {}).get('coverage_percentage', 0),
        "total_lines": analysis_result.get('statistics', {}).get('total_lines', 0),
        "languages": analysis_result.get('statistics', {}).get('languages', []),
        "categories": analysis_result.get('statistics', {}).get('categories', {})
    }
    
    return {
        "metadata": metadata,
        "nodes": nodes,
        "edges": edges
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analysis/upload', methods=['POST'])
def upload_analysis():
    """Handle file upload for analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Create temporary directory for uploaded files
        temp_dir = tempfile.mkdtemp()
        
        # Save uploaded file
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)
        
        # Extract if it's a zip file
        if file.filename.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            # Remove the zip file
            os.remove(file_path)
        
        # Initialize analysis session
        analysis_sessions[analysis_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Starting analysis...',
            'temp_dir': temp_dir,
            'logs': []
        }
        
        # Start analysis in background (for now, we'll do it synchronously)
        try:
            logger.info(f"Starting analysis for {analysis_id}")
            analysis_sessions[analysis_id]['message'] = 'Analyzing codebase...'
            analysis_sessions[analysis_id]['progress'] = 25
            
            # Use our existing analyzer
            analyzer = CodebaseAnalyzer()
            result = analyzer.analyze_codebase(temp_dir)
            
            # Convert to frontend format
            frontend_data = convert_analysis_result_to_frontend_format(result)
            
            if frontend_data:
                analysis_results[analysis_id] = frontend_data
                analysis_sessions[analysis_id]['status'] = 'completed'
                analysis_sessions[analysis_id]['progress'] = 100
                analysis_sessions[analysis_id]['message'] = 'Analysis completed successfully'
                logger.info(f"Analysis completed for {analysis_id}")
            else:
                analysis_sessions[analysis_id]['status'] = 'error'
                analysis_sessions[analysis_id]['message'] = 'Failed to process analysis result'
                logger.error(f"Analysis failed for {analysis_id}")
                
        except Exception as e:
            logger.error(f"Analysis error for {analysis_id}: {str(e)}")
            analysis_sessions[analysis_id]['status'] = 'error'
            analysis_sessions[analysis_id]['message'] = f'Analysis failed: {str(e)}'
        
        return jsonify({
            'success': True,
            'analysisId': analysis_id,
            'status': 'processing'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/analysis/github', methods=['POST'])
def github_analysis():
    """Handle GitHub repository analysis"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'GitHub URL required'}), 400
        
        github_url = data['url']
        branch = data.get('branch', 'main')
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Initialize analysis session
        analysis_sessions[analysis_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Cloning repository...',
            'logs': []
        }
        
        # For now, we'll simulate GitHub analysis
        # In a real implementation, you would clone the repo here
        analysis_sessions[analysis_id]['message'] = 'GitHub integration not implemented yet'
        analysis_sessions[analysis_id]['status'] = 'error'
        
        return jsonify({
            'analysis_id': analysis_id,
            'status': 'error',
            'message': 'GitHub integration not implemented yet'
        })
        
    except Exception as e:
        logger.error(f"GitHub analysis error: {str(e)}")
        return jsonify({'error': f'GitHub analysis failed: {str(e)}'}), 500

@app.route('/api/analysis/<analysis_id>/status')
def get_analysis_status(analysis_id):
    """Get analysis status"""
    if analysis_id not in analysis_sessions:
        return jsonify({'error': 'Analysis not found'}), 404
    
    session_data = analysis_sessions[analysis_id]
    return jsonify({
        'status': session_data['status'],
        'progress': session_data['progress'],
        'message': session_data['message']
    })

@app.route('/api/analysis/<analysis_id>/graph')
def get_graph_data(analysis_id):
    """Get graph data for completed analysis"""
    if analysis_id not in analysis_results:
        return jsonify({'error': 'Analysis not found or not completed'}), 404
    
    return jsonify(analysis_results[analysis_id])

@app.route('/api/analysis/<analysis_id>/logs')
def get_analysis_logs(analysis_id):
    """Get analysis logs"""
    if analysis_id not in analysis_sessions:
        return jsonify({'error': 'Analysis not found'}), 404
    
    session_data = analysis_sessions[analysis_id]
    return jsonify({
        'logs': session_data.get('logs', [])
    })

@app.route('/api/analysis/<analysis_id>/response')
def get_analysis_response(analysis_id):
    """Get complete analysis response"""
    if analysis_id not in analysis_sessions:
        return jsonify({'error': 'Analysis not found'}), 404
    
    session_data = analysis_sessions[analysis_id]
    
    response = {
        'analysis_id': analysis_id,
        'status': session_data['status'],
        'progress': session_data['progress'],
        'message': session_data['message']
    }
    
    if analysis_id in analysis_results:
        response['graph_data'] = analysis_results[analysis_id]
    
    return jsonify(response)

@app.route('/api/download/<format>')
def download_export(format):
    """Download analysis in specified format"""
    analysis_id = request.args.get('analysis_id')
    if not analysis_id or analysis_id not in analysis_results:
        return jsonify({'error': 'Analysis not found'}), 404
    
    try:
        # Get the analysis result
        result = analysis_results[analysis_id]
        
        # Create exporter
        exporter = EnhancedExporter()
        
        # Export in requested format
        if format == 'json':
            content = exporter.export_json(result)
            return jsonify(content)
        elif format == 'yaml':
            content = exporter.export_yaml(result)
            return content, 200, {'Content-Type': 'application/x-yaml'}
        elif format == 'csv':
            content = exporter.export_csv(result)
            return content, 200, {'Content-Type': 'text/csv'}
        elif format == 'dot':
            content = exporter.export_dot(result)
            return content, 200, {'Content-Type': 'text/plain'}
        elif format == 'html':
            content = exporter.export_html(result)
            return content, 200, {'Content-Type': 'text/html'}
        elif format == 'mermaid':
            content = exporter.export_mermaid(result)
            return content, 200, {'Content-Type': 'text/plain'}
        else:
            return jsonify({'error': f'Unsupported format: {format}'}), 400
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 