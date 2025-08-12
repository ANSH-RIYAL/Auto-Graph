from flask import Flask, render_template, request, jsonify, send_file, session
import json
import os
import sys
from datetime import datetime
import uuid
from collections import defaultdict
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

TOP_N_DEPENDS = 5

import re
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def _extract_flask_routes(codebase_dir: str):
    routes = []
    pat = re.compile(r"@app\.route\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*methods=\[([^\]]+)\])?\)")
    def_pat = re.compile(r"def\s+([a-zA-Z0-9_]+)\s*\(")
    for root, _, files in os.walk(codebase_dir or "."):
        for f in files:
            if not f.endswith('.py'):
                continue
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read()
                for m in pat.finditer(content):
                    path = m.group(1)
                    methods_raw = m.group(2) or ''
                    methods = []
                    for token in methods_raw.split(','):
                        t = token.strip().strip('\'"').upper()
                        if t in {'GET','POST','PUT','PATCH','DELETE'}:
                            methods.append(t)
                    # naive: find next def name
                    dm = def_pat.search(content, m.end())
                    handler = dm.group(1) if dm else 'handler'
                    routes.append({"method": methods[0] if methods else 'GET', "path": path, "handler": handler})
            except Exception:
                continue
    return routes


def _build_viz_from_frontend(frontend: dict, codebase_dir: str = "") -> dict:
    nodes = list(frontend.get('nodes', []))
    edges = list(frontend.get('edges', []))

    # Indexes
    by_id = {n['id']: n for n in nodes}
    parent_of = {e['to_node']: e['from_node'] for e in edges if str(e.get('type','')).lower() == 'contains'}

    def system_ancestor(nid: str):
        cur = nid
        while cur in parent_of:
            cur = parent_of[cur]
            n = by_id.get(cur)
            if n and n.get('level') == 'SYSTEM':
                return cur
        return None

    # depends_on rollup from calls
    weights = {}
    for e in edges:
        if str(e.get('type','')).lower() != 'calls':
            continue
        a = e.get('from_node')
        b = e.get('to_node')
        sa = system_ancestor(a)
        sb = system_ancestor(b)
        if sa and sb and sa != sb:
            weights[(sa, sb)] = weights.get((sa, sb), 0) + 1

    per_src = {}
    for (sa, sb), w in weights.items():
        per_src.setdefault(sa, []).append((sb, w))
    dep_edges = []
    for sa, lst in per_src.items():
        lst.sort(key=lambda x: (-x[1], x[0]))
        for sb, w in lst[:TOP_N_DEPENDS]:
            dep_edges.append({
                'id': f'{sa}->{sb}#dep',
                'from_node': sa,
                'to_node': sb,
                'type': 'depends_on',
                'metadata': {'weight': int(w)}
            })

    # Merge edges (keep contains, add pruned depends_on, and raw calls for implementation-level toggling)
    call_edges = [
        {
            'id': f"{e.get('from_node')}->{e.get('to_node')}#call",
            'from_node': e.get('from_node'),
            'to_node': e.get('to_node'),
            'type': 'calls',
            'metadata': e.get('metadata', {})
        }
        for e in edges if str(e.get('type','')).lower() == 'calls'
    ]
    merged_edges = [e for e in edges if str(e.get('type','')).lower() == 'contains'] + dep_edges + call_edges

    # Layout: six rows, degree-centered ordering
    business = [n for n in nodes if n.get('level') == 'BUSINESS']
    system = [n for n in nodes if n.get('level') == 'SYSTEM']
    impl = [n for n in nodes if n.get('level') == 'IMPLEMENTATION']

    def degree_map(es):
        d = {n['id']:0 for n in nodes}
        for e in es:
            d[e['from_node']] = d.get(e['from_node'],0)+1
            d[e['to_node']] = d.get(e['to_node'],0)+1
        return d

    deg = degree_map(merged_edges)
    business.sort(key=lambda n: n.get('name',''))
    col = 350
    # 12 vertical layers to improve readability
    # 12 rows total: Business 1, System 3, Implementation 8
    rowvals = [120, 200, 280, 360, 440, 520, 600, 680, 760, 840, 920, 1000]
    row = {i+1: y for i, y in enumerate(rowvals)}
    bx = {}
    for i, bn in enumerate(business):
        x = 200 + i*col
        y = row[1]  # single business band
        bn['position'] = {'x':x,'y':y}
        bx[bn['id']] = x

    # group systems by business parent
    sys_by_parent = {}
    for sn in system:
        p = parent_of.get(sn['id'])
        sys_by_parent.setdefault(p, []).append(sn)
    sx = {}
    for p, group in sys_by_parent.items():
        group.sort(key=lambda n: (-deg.get(n['id'],0), n.get('name','')))
        cx = bx.get(p, 200)
        for j, sn in enumerate(group):
            off = (j-(len(group)-1)/2.0)*180
            # place over 3 rows (2..4)
            y = row[2 + (j % 3)]
            sn['position'] = {'x': cx+off, 'y': y}
            sx[sn['id']] = cx+off

    # implementations under system ancestor
    impl_groups = {}
    for inn in impl:
        sp = system_ancestor(inn['id'])
        impl_groups.setdefault(sp, []).append(inn)
    for sp, group in impl_groups.items():
        cx = sx.get(sp, 200)
        group.sort(key=lambda n: (-deg.get(n['id'],0), n.get('name','')))
        for k, inn in enumerate(group):
            off = (k-(len(group)-1)/2.0)*140
            # place over 8 rows (5..12)
            y_index = 5 + (k % 8)
            y = row[y_index]
            inn['position'] = {'x': cx+off, 'y': y}

    # Ensure no blank summaries (placeholder)
    for n in nodes:
        md = n.get('metadata') or {}
        if not md.get('purpose'):
            md['purpose'] = 'information missing'
            n['metadata'] = md

    # External/User stubs and API routes
    sys_api = next((n for n in nodes if n.get('level')=='SYSTEM' and 'api' in n.get('name','').lower()), None)
    if sys_api:
        # user actor
        user_id = 'actor_user'
        if not any(nn.get('id')==user_id for nn in nodes):
            nodes.append({"id":user_id,"name":"User","type":"Actor","level":"BUSINESS","metadata":{"purpose":"external actor"},"position":{"x":0,"y":150}})
        merged_edges.append({'id':f'{user_id}->{sys_api["id"]}#dep','from_node':user_id,'to_node':sys_api['id'],'type':'depends_on','metadata':{'weight':1}})
        # routes
        routes = _extract_flask_routes(codebase_dir)
        api_md = sys_api.get('metadata') or {}
        api_md['routes'] = routes
        sys_api['metadata'] = api_md

    # Scan codebase for externals
    try:
        code = ''
        for root,_,files in os.walk(codebase_dir or "."):
            for f in files:
                if f.endswith('.py'):
                    with open(os.path.join(root,f),'r',encoding='utf-8',errors='ignore') as fh:
                        code += fh.read()[:20000]
        if 'openai' in code and sys_api:
            stub='external_llm_service'
            if not any(nn.get('id')==stub for nn in nodes):
                nodes.append({"id":stub,"name":"LLM Service","type":"External","level":"SYSTEM","metadata":{"purpose":"external dependency"},"position":{"x":0,"y":390}})
            merged_edges.append({'id':f'{sys_api["id"]}->{stub}#dep','from_node':sys_api['id'],'to_node':stub,'type':'depends_on','metadata':{'weight':1}})
        if ('jwt' in code or 'oidc' in code) and sys_api:
            stub='external_auth_provider'
            if not any(nn.get('id')==stub for nn in nodes):
                nodes.append({"id":stub,"name":"Auth Provider","type":"External","level":"SYSTEM","metadata":{"purpose":"external dependency"},"position":{"x":0,"y":390}})
            merged_edges.append({'id':f'{sys_api["id"]}->{stub}#dep','from_node':sys_api['id'],'to_node':stub,'type':'depends_on','metadata':{'weight':1}})
    except Exception:
        pass

    # Deterministic module descriptions (fallback when LLM absent)
    name_map = {n['id']: n.get('name') for n in nodes}
    out_edges = defaultdict(list)
    in_edges = defaultdict(list)
    for e in merged_edges:
        out_edges[e['from_node']].append(e)
        in_edges[e['to_node']].append(e)
    for n in nodes:
        lvl = n.get('level')
        if lvl in ('BUSINESS','SYSTEM'):
            outs = out_edges.get(n['id'], [])
            ins = in_edges.get(n['id'], [])
            def summarize(es):
                t = defaultdict(int)
                for ed in es:
                    t[ed.get('type','')] += 1
                return ', '.join(f"{k}: {v}" for k,v in t.items() if k)
            desc = f"{n.get('name','Module')} handles {n.get('type','component').lower()} duties. Incoming: {summarize(ins)}. Outgoing: {summarize(outs)}. Neighbors: "
            neigh = sorted({ name_map.get(e['from_node']) for e in ins } | { name_map.get(e['to_node']) for e in outs } - {n.get('name')})
            desc += ', '.join([x for x in neigh if x]) or 'none'
            md = n.get('metadata') or {}
            if not md.get('purpose') or md.get('purpose') == 'information missing':
                md['purpose'] = desc
            n['metadata'] = md

    return {
        'metadata': frontend.get('metadata', {}),
        'nodes': nodes,
        'edges': merged_edges,
    }

def convert_analysis_result_to_frontend_format(analysis_result):
    """Convert our backend analysis result to the frontend format with enhanced metadata"""
    if not analysis_result or 'graph' not in analysis_result or not analysis_result['graph']:
        return None
    
    graph = analysis_result['graph']
    
    # Convert nodes to frontend format with enhanced metadata
    nodes = []
    for node in graph.nodes:
        # Get enhanced metadata
        node_metadata = node.metadata if node.metadata else {}
        
        frontend_node = {
            "id": node.id,
            "name": node.name,
            "type": node.type.value if hasattr(node.type, 'value') else str(node.type),
            "level": node.level.value if hasattr(node.level, 'value') else str(node.level),
            "files": node.files,
            "parent": node.parent,
            "children": node.children,
            "functions": node.functions,
            "classes": node.classes,
            "imports": node.imports,
            "metadata": {
                "purpose": node_metadata.purpose if node_metadata else '',
                "complexity": node_metadata.complexity.value if node_metadata and hasattr(node_metadata.complexity, 'value') else str(node_metadata.complexity) if node_metadata else 'low',
                "dependencies": node_metadata.dependencies if node_metadata else [],
                "line_count": node_metadata.line_count if node_metadata else 0,
                "file_size": node_metadata.file_size if node_metadata else 0,
                "language": node_metadata.language if node_metadata else 'unknown',
                "category": node_metadata.category if node_metadata else 'other',
                # Enhanced metadata
                "technical_depth": node_metadata.technical_depth if node_metadata else (1 if node.level.value == 'BUSINESS' else (2 if node.level.value == 'SYSTEM' else 3)),
                "color": node_metadata.color if node_metadata else None,
                "size": node_metadata.size if node_metadata else None,
                "agent_touched": node_metadata.agent_touched if node_metadata else False,
                "agent_types": node_metadata.agent_types if node_metadata else [],
                "risk_level": node_metadata.risk_level.value if node_metadata and hasattr(node_metadata.risk_level, 'value') else str(node_metadata.risk_level) if node_metadata else 'low',
                "business_impact": node_metadata.business_impact if node_metadata else None,
                "agent_context": node_metadata.agent_context if node_metadata else None
            },
            "pm_metadata": {
                "business_value": node.pm_metadata.business_value if node.pm_metadata else None,
                "development_status": node.pm_metadata.development_status if node.pm_metadata else "Active",
                "completion_percentage": node.pm_metadata.completion_percentage if node.pm_metadata else 0.0,
                "team_size": node.pm_metadata.team_size if node.pm_metadata else None,
                "estimated_completion": node.pm_metadata.estimated_completion if node.pm_metadata else None,
                "risk_factors": node.pm_metadata.risk_factors if node.pm_metadata else [],
                "stakeholder_priority": node.pm_metadata.stakeholder_priority if node.pm_metadata else "medium"
            } if node.pm_metadata else None,
            "enhanced_metadata": {
                "total_symbols": node.enhanced_metadata.total_symbols if node.enhanced_metadata else 0,
                "has_parent": node.enhanced_metadata.has_parent if node.enhanced_metadata else False,
                "has_children": node.enhanced_metadata.has_children if node.enhanced_metadata else False,
                "child_count": node.enhanced_metadata.child_count if node.enhanced_metadata else 0,
                "file_diversity": node.enhanced_metadata.file_diversity if node.enhanced_metadata else 0,
                "complexity_score": node.enhanced_metadata.complexity_score if node.enhanced_metadata else 1
            } if node.enhanced_metadata else None,
            "position": {"x": 0, "y": 0}  # Will be calculated by frontend
        }
        nodes.append(frontend_node)
    
    # Convert edges to frontend format
    edges = []
    for edge in graph.edges:
        frontend_edge = {
            "id": f"{edge.from_node}_{edge.to_node}",
            "from_node": edge.from_node,  # Use from_node for consistency
            "to_node": edge.to_node,      # Use to_node for consistency
            "type": edge.type.value if hasattr(edge.type, 'value') else str(edge.type),
            "metadata": {
                "relationship_type": edge.metadata.get('relationship_type', 'dependency') if edge.metadata else 'dependency',
                "communication_type": edge.metadata.get('communication_type', '') if edge.metadata else '',
                "bidirectional": edge.metadata.get('bidirectional', False) if edge.metadata else False,
                # Optional examples for edge payloads (requests/queries) to show in details panel
                "examples": edge.metadata.get('examples', []) if edge.metadata else []
            }
        }
        edges.append(frontend_edge)
    
    # Create enhanced metadata with statistics and PM metrics
    graph_metadata = graph.metadata if graph.metadata else {}
    
    metadata = {
        "codebase_path": analysis_result.get('codebase_path', ''),
        "analysis_timestamp": analysis_result.get('timestamp', datetime.now().isoformat()),
        "file_count": graph_metadata.file_count if graph_metadata else 0,
        "coverage_percentage": graph_metadata.coverage_percentage if graph_metadata else 0,
        "total_lines": graph_metadata.total_lines if graph_metadata else 0,
        "languages": graph_metadata.languages if graph_metadata else [],
        "categories": graph_metadata.categories if graph_metadata else {},
        # Enhanced statistics
            "statistics": {
                "total_nodes": graph_metadata.statistics.total_nodes if graph_metadata and graph_metadata.statistics else len(nodes),
                "business_nodes": getattr(graph_metadata.statistics, 'business_nodes', 0) or len([n for n in nodes if n['level'] == 'BUSINESS']),
                "system_nodes": getattr(graph_metadata.statistics, 'system_nodes', 0) or len([n for n in nodes if n['level'] == 'SYSTEM']),
                "implementation_nodes": getattr(graph_metadata.statistics, 'implementation_nodes', 0) or len([n for n in nodes if n['level'] == 'IMPLEMENTATION']),
                "total_edges": graph_metadata.statistics.total_edges if graph_metadata and graph_metadata.statistics else len(edges),
                "technical_depths": graph_metadata.statistics.technical_depths if graph_metadata and graph_metadata.statistics else {
                    "business": len([n for n in nodes if n['metadata']['technical_depth'] == 1]),
                    "system": len([n for n in nodes if n['metadata']['technical_depth'] == 2]),
                    "implementation": len([n for n in nodes if n['metadata']['technical_depth'] == 3])
                }
            },
        # PM metrics
        "pm_metrics": {
            "development_velocity": graph_metadata.pm_metrics.development_velocity if graph_metadata and graph_metadata.pm_metrics else "medium",
            "risk_level": graph_metadata.pm_metrics.risk_level.value if graph_metadata and graph_metadata.pm_metrics and hasattr(graph_metadata.pm_metrics.risk_level, 'value') else str(graph_metadata.pm_metrics.risk_level) if graph_metadata and graph_metadata.pm_metrics else "low",
            "completion_percentage": graph_metadata.pm_metrics.completion_percentage if graph_metadata and graph_metadata.pm_metrics else 85.0,
            "blocked_components": graph_metadata.pm_metrics.blocked_components if graph_metadata and graph_metadata.pm_metrics else 0,
            "active_dependencies": graph_metadata.pm_metrics.active_dependencies if graph_metadata and graph_metadata.pm_metrics else len(edges)
        } if graph_metadata and graph_metadata.pm_metrics else None
    }
    
    # Compute stable positions (zoned layout) on the server for deterministic views
    try:
        # Organize nodes by level
        business_nodes = [n for n in nodes if n['level'] == 'BUSINESS']
        system_nodes = [n for n in nodes if n['level'] == 'SYSTEM']
        impl_nodes = [n for n in nodes if n['level'] == 'IMPLEMENTATION']

        # Map of parent relationships from edges
        parent_of = {e['to_node']: e['from_node'] for e in edges if e['type'].lower() == 'contains'}

        # Sort business nodes for deterministic ordering
        business_nodes.sort(key=lambda n: n['name'])
        column_spacing = 350
        # 6-layer zoning: L1-L2 business, L3-L4 system, L5-L6 implementation
        row_y = {1: 150, 2: 230, 3: 310, 4: 390, 5: 470, 6: 550}

        # Assign positions for business nodes
        business_x = {}
        for idx, bn in enumerate(business_nodes):
            x = 200 + idx * column_spacing
            y = row_y[1 if (idx % 2) == 0 else 2]
            bn['position'] = {"x": x, "y": y}
            business_x[bn['id']] = x

        # Group system nodes under business parents
        sys_by_parent = {}
        for sn in system_nodes:
            parent = parent_of.get(sn['id'])
            sys_by_parent.setdefault(parent, []).append(sn)

        for parent, group in sys_by_parent.items():
            group.sort(key=lambda n: n['name'])
            px = business_x.get(parent, 200)
            count = len(group)
            for j, sn in enumerate(group):
                offset = (j - (count - 1) / 2.0) * 180
                y = row_y[3 if (j % 2) == 0 else 4]
                sn['position'] = {"x": px + offset, "y": y}

        # Group implementation nodes under system (fallback to business if no system parent)
        impl_by_parent = {}
        for inn in impl_nodes:
            parent = parent_of.get(inn['id'])
            impl_by_parent.setdefault(parent, []).append(inn)

        system_x = {n['id']: n['position']['x'] for n in system_nodes if 'position' in n}
        for parent, group in impl_by_parent.items():
            group.sort(key=lambda n: n['name'] if n['name'] else n['id'])
            px = system_x.get(parent, business_x.get(parent, 200))
            count = len(group)
            for k, inn in enumerate(group):
                offset = (k - (count - 1) / 2.0) * 140
                y = row_y[5 if (k % 2) == 0 else 6]
                inn['position'] = {"x": px + offset, "y": y}
    except Exception as _:
        # If anything fails, keep zero positions and let client layout fallback
        pass

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
        # Accept either a single 'file' (zip) or multiple 'files' (folder upload)
        upload_files = []
        if 'file' in request.files and request.files['file'].filename:
            upload_files = [request.files['file']]
        elif 'files' in request.files:
            upload_files = request.files.getlist('files')
            if not upload_files:
                return jsonify({'error': 'No files provided'}), 400
        else:
            return jsonify({'error': 'No file(s) provided'}), 400
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Create temporary directory for uploaded files
        temp_dir = tempfile.mkdtemp()
        
        # Save uploaded files
        for f in upload_files:
            dst_path = os.path.join(temp_dir, f.filename)
            # Ensure parent directory exists for folder uploads
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            f.save(dst_path)
            # Extract zip archives
            if f.filename.endswith('.zip'):
                with zipfile.ZipFile(dst_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                os.remove(dst_path)
        
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
            
            # Convert to frontend format (AST-level)
            frontend_data = convert_analysis_result_to_frontend_format(result)
            # Bake visualization-draft (contains + pruned depends_on + positions)
            if frontend_data:
                frontend_data = _build_viz_from_frontend(frontend_data, temp_dir)
            
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

@app.route('/api/analysis/<analysis_id>/hld_graph')
def get_hld_graph_data(analysis_id):
    """Get HLD/LLD-adapted graph data (reuses canonical positions and core edge types)."""
    if analysis_id not in analysis_results:
        return jsonify({'error': 'Analysis not found or not completed'}), 404

    try:
        base = analysis_results[analysis_id]

        # Shallow copy nodes/edges; preserve server-side positions and canonical edge types
        nodes = list(base.get('nodes', []))
        edges = [e for e in base.get('edges', []) if str(e.get('type', '')).lower() in {'contains','depends_on','depends','calls'}]

        # Normalize depends alias
        for e in edges:
            t = str(e.get('type','')).lower()
            if t == 'depends':
                e['type'] = 'depends_on'

        # Collect kinds/types for UI filters (use type names as HLDBuilder does)
        kinds = sorted({ str(n.get('type') or 'Module') for n in nodes })

        metadata = dict(base.get('metadata', {}))
        metadata['kinds'] = kinds
        # Carry over statistics if present
        out = {
            'metadata': metadata,
            'nodes': nodes,
            'edges': edges
        }
        return jsonify(out)
    except Exception as e:
        logger.error(f"HLD graph build error for {analysis_id}: {str(e)}")
        return jsonify({'error': f'HLD graph build failed: {str(e)}'}), 500

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