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
import hashlib
import shutil

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from analyzer.codebase_analyzer import CodebaseAnalyzer
    from models.schemas import NodeLevel, NodeType, ComplexityLevel
    from utils.logger import get_logger
    from export.enhanced_exporter import EnhancedExporter
    # Optional: LangGraph workflow orchestrator
    try:
        from workflows.langgraph_pipeline import create_workflow
    except Exception:
        create_workflow = None
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative import paths...")
    
    # Try alternative import paths
    try:
        from src.analyzer.codebase_analyzer import CodebaseAnalyzer
        from src.models.schemas import NodeLevel, NodeType, ComplexityLevel
        from src.utils.logger import get_logger
        from src.export.enhanced_exporter import EnhancedExporter
        try:
            from src.workflows.langgraph_pipeline import create_workflow
        except Exception:
            create_workflow = None
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
MIN_DEPENDS_WEIGHT = 3
TOP_IMPL_REPRESENTATIVES = 3

import re
from dotenv import load_dotenv
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# Load environment variables (e.g., OPENAI_API_KEY) from .env if present
load_dotenv()

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
            if int(w) < MIN_DEPENDS_WEIGHT:
                continue
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
    # Keep a copy of the original contains edges for mapping parents and pre-cluster calculations
    contains_edges = [e for e in edges if str(e.get('type','')).lower() == 'contains']
    merged_edges = [e for e in edges if str(e.get('type','')).lower() == 'contains'] + dep_edges + call_edges

    # Layout: preset with 12 rows (1/3/8 bands) and degree-centered ordering
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
    # 12 vertical layers: Business top (1), Systems (2..6), Implementation/Clusters (7..12)
    # Increased spacing for clearer separation between levels
    rowvals = [140, 420, 560, 700, 840, 980, 1180, 1320, 1460, 1600, 1740, 1880]
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
            # place over 5 rows (2..6)
            y = row[2 + (j % 5)]
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
        # Grid columns under each system to avoid overlap
        col_w = 140
        start_x = cx - (len(group)-1)/2.0 * col_w
        for k, inn in enumerate(group):
            x_pos = start_x + k*col_w
            # place over 6 rows (7..12)
            y_index = 7 + (k % 6)
            y = row[y_index]
            inn['position'] = {'x': x_pos, 'y': y}

    # Implementation clustering (post-generation visual grouping)
    def slug(s: str) -> str:
        return ''.join(c.lower() if c.isalnum() else '_' for c in (s or 'cluster')).strip('_')[:40]

    cluster_nodes = []
    impl_to_cluster = {}
    # Skip clustering if too few system nodes overall
    do_cluster = len(system) > 5
    # For each system, group implementations by nearest directory token in their primary file path
    if do_cluster:
      def cluster_color(cid: str) -> str:
          h = int(hashlib.md5(cid.encode('utf-8')).hexdigest()[:6], 16) % 360
          return f"hsla({h}, 70%, 60%, 0.10)"
      sys_index = 0
      for sid, group in impl_groups.items():
        buckets = {}
        for n in group or []:
            fp = (n.get('files') or [''])[0]
            parts = Path(fp).parts
            key = None
            # Prefer last directory before filename
            if len(parts) >= 2:
                key = parts[-2]
            key = key or 'misc'
            buckets.setdefault(key, []).append(n)
        # If too many tiny buckets, merge smallest into 'other'
        if len(buckets) > 20:
            # keep top 15 by size, merge rest
            items = sorted(buckets.items(), key=lambda kv: -len(kv[1]))
            keep = dict(items[:15])
            other = []
            for k, v in items[15:]:
                other.extend(v)
            if other:
                keep['other'] = other
            buckets = keep
        # Create cluster nodes (only if at least 2 members); skip creating cluster when the bucket corresponds to a SYSTEM node (we never wrap systems)
        for k, members in buckets.items():
            if len(members) < 2:
                continue
            cid = f"cluster_{sid}_{slug(k)}"
            member_ids = [m['id'] for m in members]
            # compute translucent color and description
            purpose_text = f"Group of {len(member_ids)} closely related implementation elements in '{k}'."
            cluster_nodes.append({
                'id': cid,
                'name': f"{k.title()} Cluster",
                'type': 'Cluster',
                'level': 'IMPLEMENTATION',
                'metadata': {
                    'cluster': True,
                    'members': member_ids,
                    'counts': {'members': len(member_ids)},
                    'purpose': purpose_text,
                    'description': purpose_text
                },
                'position': {'x': sx.get(sid, 200), 'y': row[9]},  # place lower band
                'color': cluster_color(cid)
            })
            for mid in member_ids:
                impl_to_cluster[mid] = cid
        sys_index += 1
    # assign parent for impl nodes to enable compound bounding boxes on frontend
    if do_cluster:
      # Assign parents and compute tight grid placement per cluster
      clusters_map = { c['id']: c for c in cluster_nodes }
      members_by_cluster = defaultdict(list)
      for n in impl:
          cid = impl_to_cluster.get(n['id'])
          if cid:
              n['parent'] = cid
              members_by_cluster[cid].append(n)
      # Arrange clusters: keep clusters of the same system adjacent; within each system order by size desc
      grouped = defaultdict(list)
      for cid, members in members_by_cluster.items():
          parts = cid.split('_'); sid = parts[1] if len(parts) > 2 else 'sys'
          grouped[sid].append((cid, members))
      for sid in grouped:
          grouped[sid].sort(key=lambda item: -len(item[1]))
      ordered = []
      for sid, items in grouped.items():
          ordered.extend(items)
      line_y = row[11]
      cursor_x = 200.0
      gap = 80.0
      layers = [row[9], row[10], row[11]]
      layer_index = 0
      for cid, members in ordered:
          count = len(members)
          cols = int(max(2, round(count ** 0.5)))
          rows = int((count + cols - 1) // cols)
          spacing_x = 120.0
          spacing_y = 90.0
          width = (cols - 1) * spacing_x + 2 * 80.0
          center_x = cursor_x + width / 2.0
          line_y = layers[layer_index % len(layers)]
          clusters_map[cid]['position'] = {'x': center_x, 'y': line_y}
          cursor_x += width + gap
          layer_index += 1

          # Start grid centered inside cluster
          start_x = center_x - (cols - 1) * spacing_x / 2.0
          start_y = line_y - (rows - 1) * spacing_y / 2.0
          for idx, child in enumerate(sorted(members, key=lambda n: n.get('name') or n['id'])):
              r = idx // cols; c = idx % cols
              child['position'] = {'x': start_x + c * spacing_x, 'y': start_y + r * spacing_y}

      # Re-anchor systems and business nodes to the midpoints of their cluster ranges
      if members_by_cluster:
          sys_to_minmax = defaultdict(lambda: [float('inf'), float('-inf')])
          for cid, mems in members_by_cluster.items():
              # cluster id format cluster_<systemId>_...
              parts = cid.split('_')
              sid = parts[1] if len(parts) > 2 else None
              if sid and cid in clusters_map:
                  x = clusters_map[cid]['position']['x']
                  w = 0  # if we expand later to include width
                  lo, hi = sys_to_minmax[sid]
                  sys_to_minmax[sid] = [min(lo, x), max(hi, x)]

          sys_center_x = {}
          for sn in system:
              lo, hi = sys_to_minmax.get(sn['id'], [None, None])
              if lo is not None and hi is not None and lo != float('inf') and hi != float('-inf'):
                  sn['position']['x'] = (lo + hi) / 2.0
                  sys_center_x[sn['id']] = sn['position']['x']

          # Business x is average of its system children x (use original contains edges; clusters handled later)
          sys_parent = { e['to_node']: e['from_node'] for e in contains_edges if by_id.get(e['from_node'],{}).get('level')=='BUSINESS' and by_id.get(e['to_node'],{}).get('level')=='SYSTEM' }
          bus_to_sys = defaultdict(list)
          for sid, bid in sys_parent.items():
              bus_to_sys[bid].append(sid)
          for bn in business:
              xs = [sys_center_x[s] for s in bus_to_sys.get(bn['id'], []) if s in sys_center_x]
              if xs:
                  bn['position']['x'] = sum(xs) / len(xs)

    # Keep original system→implementation contains; add cluster→impl contains for drill-down
    new_contains = list(contains_edges)
    if do_cluster:
        for mid, cid in impl_to_cluster.items():
            new_contains.append({'id': f"{cid}->{mid}#contains","from_node": cid, "to_node": mid, "type": 'contains', 'metadata': {}})

    # Roll up implementation calls into cluster-level depends_on
    cluster_weights = defaultdict(int)
    cluster_dep_edges = []
    if do_cluster:
      for ce in call_edges:
          a = ce['from_node']; b = ce['to_node']
          ca = impl_to_cluster.get(a); cb = impl_to_cluster.get(b)
          if ca and cb and ca != cb:
              cluster_weights[(ca, cb)] += 1
      for (ca, cb), w in cluster_weights.items():
          cluster_dep_edges.append({'id': f"{ca}->{cb}#cdep", 'from_node': ca, 'to_node': cb, 'type': 'depends_on', 'metadata': {'weight': int(w)}})

    # Aggregate system members, representatives, and provenance
    sys_members = {sn['id']: { 'files': [], 'classes': [], 'functions': [], 'counts': {'files':0,'classes':0,'functions':0}, 'ast_ids': [] } for sn in system}
    # Heuristic fallback mapping when contains links are missing
    def fallback_system_for_impl(impl_node):
        name = (impl_node.get('name') or impl_node.get('id','')).lower()
        files = impl_node.get('files', []) or []
        joined = ' '.join(files).lower()
        best_id = None; best_score = -1
        for sysn in system:
            nm = (sysn.get('name') or sysn.get('id','')).lower()
            score = 0
            if any(k in joined or k in name for k in ['model','schema']):
                score += 3 if ('schema' in nm or 'model' in nm) else 0
            if any(k in joined or k in name for k in ['control']):
                score += 3 if 'control' in nm else 0
            if any(k in joined or k in name for k in ['component','ui']):
                score += 3 if ('component' in nm or 'ui' in nm) else 0
            if any(k in joined or k in name for k in ['actions','action','/actions/']):
                score += 3 if 'action' in nm else 0
            if any(k in joined for k in ['/data/','/io/','io.py']):
                score += 2 if ('data' in nm or 'io' in nm) else 0
            if 'integrations' in joined:
                score += 3 if 'integration' in nm else 0
            if 'manager' in joined:
                score += 1 if 'manager' in nm else 0
            if score > best_score:
                best_score = score; best_id = sysn['id']
        return best_id if best_score > 0 else None

    for inn in impl:
        sid = system_ancestor(inn['id']) or fallback_system_for_impl(inn)
        if not sid or sid not in sys_members:
            continue
        memb = sys_members[sid]
        memb['files'].extend(inn.get('files', []) or [])
        memb['classes'].extend(inn.get('classes', []) or [])
        memb['functions'].extend(inn.get('functions', []) or [])
        memb['ast_ids'].append(inn['id'])
    for sid, memb in sys_members.items():
        memb['counts'] = {
            'files': len(memb['files']),
            'classes': len(memb['classes']),
            'functions': len(memb['functions'])
        }
    # Representatives: top-K implementation children by degree
    sys_children = {sn['id']: [] for sn in system}
    for inn in impl:
        sid = system_ancestor(inn['id'])
        if sid in sys_children:
            sys_children[sid].append(inn)
    sys_reps = {}
    for sid, childs in sys_children.items():
        childs.sort(key=lambda n: (-deg.get(n['id'],0), n.get('name','')))
        sys_reps[sid] = [c['id'] for c in childs[:TOP_IMPL_REPRESENTATIVES]]
    # Attach to system nodes
    for sn in system:
        md = sn.get('metadata') or {}
        md['members'] = {
            'files': sys_members[sn['id']]['files'][:50],
            'classes': sys_members[sn['id']]['classes'][:50],
            'functions': sys_members[sn['id']]['functions'][:50],
            'counts': sys_members[sn['id']]['counts']
        }
        md['representatives'] = sys_reps.get(sn['id'], [])
        md['provenance'] = { 'ast_ids': sys_members[sn['id']]['ast_ids'][:200] }
        # Module facts placeholders
        facts = md.get('facts') or {
            'routes': [], 'io_ops': [], 'db_ops': [], 'http_calls': [],
            'cache_ops': [], 'queue_ops': [], 'pubsub_ops': [],
            'external_calls': [], 'entrypoints': []
        }
        md['facts'] = facts
        sn['metadata'] = md

    # Visual styling metadata: size factors and colors
    level_to_factor = { 'BUSINESS': 8, 'SYSTEM': 4, 'IMPLEMENTATION': 1 }
    # Diverse but sober palette; keyed by type fallback to level colors
    type_palette = {
        'API': '#3B82F6',
        'Service': '#EF4444',
        'Module': '#6366F1',
        'Database': '#14B8A6',
        'Cache': '#22C55E',
        'Message_Bus': '#F59E0B',
        'Queue': '#F97316',
        'Scheduler': '#EAB308',
        'Storage': '#8B5CF6',
        'Search': '#06B6D4',
        'External': '#64748B',
        'Actor': '#0EA5E9'
    }
    level_palette = { 'BUSINESS': '#0EA5E9', 'SYSTEM': '#3B82F6', 'IMPLEMENTATION': '#94A3B8' }
    # Palette seeds: 10 business, 20 system (paired 2 per business), 200 implementation
    business_palette = ['#1E3A8A','#B91C1C','#0F766E','#7C2D12','#6D28D9','#0B5ED7','#065F46','#7E22CE','#BE185D','#365314']
    system_palette = [
        '#3B82F6','#60A5FA', '#EF4444','#F87171', '#14B8A6','#2DD4BF', '#F59E0B','#FBBF24', '#8B5CF6','#A78BFA',
        '#10B981','#34D399', '#F97316','#FB923C', '#06B6D4','#22D3EE', '#84CC16','#A3E635', '#D946EF','#E879F9'
    ]
    impl_palette = [
        '#CBD5E1','#D1D5DB','#E5E7EB','#F3F4F6','#E2E8F0','#F1F5F9','#E4E4E7','#F4F4F5','#EDE9FE','#FAE8FF',
    ] * 20  # repeat to reach ~200
    for n in nodes:
        md = n.get('metadata') or {}
        lvl = n.get('level', 'IMPLEMENTATION')
        md['size_factor'] = level_to_factor.get(lvl, 1)
        # assign hierarchical colors deterministically
        if lvl == 'BUSINESS':
            idx = sum(ord(c) for c in (n.get('id') or '')) % len(business_palette)
            md['color'] = business_palette[idx]
        elif lvl == 'SYSTEM':
            # pick based on business parent bucket
            p = parent_of.get(n.get('id'))
            base_index = sum(ord(c) for c in (p or '')) % (len(business_palette))
            pair = system_palette[(base_index*2) % len(system_palette):(base_index*2+2) % len(system_palette)]
            if not pair:
                pair = [system_palette[0]]
            idx = sum(ord(c) for c in (n.get('id') or '')) % len(pair)
            md['color'] = pair[idx]
        elif n.get('type') == 'Cluster':
            # translucent shade derived from its system parent color
            sid = None
            for e in contains_edges:
                if e.get('to_node') == n.get('id'):
                    sid = e.get('from_node'); break
            sys_color = level_palette['SYSTEM']
            if sid:
                sp = next((sn for sn in system if sn['id']==sid), None)
                sys_color = (sp.get('metadata') or {}).get('color', sys_color) if sp else sys_color
            md['color'] = sys_color
        else:
            # implementation symbols
            idx = sum(ord(c) for c in (n.get('id') or '')) % len(impl_palette)
            md['color'] = impl_palette[idx]
        # Add paths alias for UI/exports
        if (n.get('files') or []) and 'paths' not in md:
            md['paths'] = list(n.get('files') or [])
        n['metadata'] = md

    # Ensure no blank summaries (placeholder) and one-line English for impl reps
    rep_ids = set()
    for rlist in sys_reps.values():
        rep_ids.update(rlist)
    for n in nodes:
        md = n.get('metadata') or {}
        if not md.get('purpose'):
            md['purpose'] = 'information missing'
        if n.get('level') == 'IMPLEMENTATION' and n.get('id') in rep_ids:
            # simple one-line description
            desc = md.get('purpose')
            if not desc or desc == 'information missing':
                kind = n.get('type') or 'Symbol'
                path = (n.get('files') or [''])[0]
                md['purpose'] = f"{kind} implemented at {path}"
        n['metadata'] = md

    # Prune Business->Implementation 'contains' when Business->System->Implementation exists
    try:
        node_by_id = { n['id']: n for n in nodes }
        contains = [e for e in merged_edges if e['type'] == 'contains']
        children_of = defaultdict(set)
        for e in contains:
            children_of[e['from_node']].add(e['to_node'])
        prune_pairs = set()
        for e in contains:
            f = e['from_node']; t = e['to_node']
            if node_by_id.get(f,{}).get('level') == 'BUSINESS' and node_by_id.get(t,{}).get('level') == 'IMPLEMENTATION':
                for s in children_of.get(f, set()):
                    if node_by_id.get(s,{}).get('level') == 'SYSTEM' and t in children_of.get(s, set()):
                        prune_pairs.add((f,t)); break
        if prune_pairs:
            merged_edges = [e for e in merged_edges if not (e['type']=='contains' and (e['from_node'], e['to_node']) in prune_pairs)]
    except Exception:
        pass

    # Append cluster nodes and edges (from previous step)
    if do_cluster and cluster_nodes:
        nodes.extend(cluster_nodes)
        # Replace contains set
        non_contains = [e for e in merged_edges if e['type'] != 'contains']
        merged_edges = new_contains + non_contains + cluster_dep_edges

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

    # Populate module facts by scanning files of implementation nodes and attributing to system parents
    try:
        # Quick maps
        sys_meta = { sn['id']: (sn.get('metadata') or {}) for sn in system }
        # Initialize facts structures
        for sid, md in sys_meta.items():
            md.setdefault('facts', {
                'routes': md.get('routes', []),
                'io_ops': [], 'db_ops': [], 'http_calls': [],
                'cache_ops': [], 'queue_ops': [], 'pubsub_ops': [],
                'external_calls': [], 'entrypoints': []
            })
        # Helper to append unique (bounded)
        def add_fact(sid, key, item, cap=50):
            if not sid or sid not in sys_meta: return
            arr = sys_meta[sid]['facts'].setdefault(key, [])
            if item not in arr:
                if len(arr) < cap:
                    arr.append(item)
        # Iterate impl nodes
        for inn in impl:
            sid = system_ancestor(inn['id']) or fallback_system_for_impl(inn)
            if not sid: continue
            for fp in (inn.get('files') or []):
                p = os.path.join(codebase_dir or '.', fp)
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
                        txt = fh.read(20000)
                except Exception:
                    continue
                low = txt.lower()
                # IO ops
                if 'read_csv' in low: add_fact(sid, 'io_ops', {'read_csv': fp})
                if 'to_csv' in low or 'write' in low: add_fact(sid, 'io_ops', {'write': fp})
                # DB ops
                if 'sqlite3' in low or 'sqlalchemy' in low or 'session.query' in low:
                    add_fact(sid, 'db_ops', {'op': 'query', 'file': fp})
                # HTTP calls
                if 'requests.' in low:
                    add_fact(sid, 'http_calls', {'lib': 'requests', 'file': fp})
                # Cache
                if 'redis' in low:
                    add_fact(sid, 'cache_ops', {'lib': 'redis', 'file': fp})
                # Queue / PubSub
                if 'rq.' in low or 'celery' in low:
                    add_fact(sid, 'queue_ops', {'lib': 'rq/celery', 'file': fp})
                if 'pika' in low:
                    add_fact(sid, 'pubsub_ops', {'lib': 'pika', 'file': fp})
                # External SDKs
                if 'openai' in low:
                    add_fact(sid, 'external_calls', {'sdk': 'openai', 'file': fp})
                if 'plotly' in low or 'px.' in low:
                    add_fact(sid, 'external_calls', {'sdk': 'plotly', 'file': fp})
                # Entrypoints
                if '__main__' in low:
                    add_fact(sid, 'entrypoints', fp)
        # Write back
        for sn in system:
            sn['metadata'] = sys_meta[sn['id']]
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

    # Compulsory: LLM-based naming for Business/System and cluster descriptions (if OPENAI_API_KEY is set)
    try:
        targets = [n for n in nodes if n.get('level') in ('BUSINESS','SYSTEM')]
        # Also prepare clusters missing description
        clusters_to_describe = [n for n in nodes if n.get('type')=='Cluster' and not ((n.get('metadata') or {}).get('description'))]
        if OpenAI and os.environ.get('OPENAI_API_KEY'):
            client = OpenAI()
            for n in targets:
                brief = {
                    'id': n.get('id'),
                    'level': n.get('level'),
                    'type': n.get('type'),
                    'files': n.get('files', [])[:5],
                    'neighbors': sorted({ by_id.get(e['to_node'],{}).get('name') for e in out_edges.get(n['id'],[]) } | { by_id.get(e['from_node'],{}).get('name') for e in in_edges.get(n['id'],[]) })
                }
                prompt = (
                    'Propose a concise, human-friendly name (3-5 words) for this software module. '
                    'Only return the name as plain text.\n' + json.dumps(brief)
                )
                try:
                    resp = client.chat.completions.create(model=os.environ.get('OPENAI_MODEL','gpt-4o-mini'),
                                                          messages=[{'role':'system','content':'You name software modules clearly without adding extra text.'},
                                                                    {'role':'user','content':prompt}],
                                                          temperature=0.1, max_tokens=24)
                    suggestion = (resp.choices[0].message.content or '').strip()
                    if suggestion:
                        n['name'] = suggestion
                except Exception:
                    pass
            # Cluster descriptions (2 lines max)
            for n in clusters_to_describe:
                members = (n.get('metadata') or {}).get('members', [])
                context = {
                    'id': n.get('id'),
                    'member_count': len(members),
                    'sample_members': members[:5]
                }
                prompt = (
                    'Write a clear two-line English description of this implementation cluster for a PM. '
                    'Line 1: what the group represents; Line 2: examples (by id). Return text only.\n' + json.dumps(context)
                )
                try:
                    resp = client.chat.completions.create(model=os.environ.get('OPENAI_MODEL','gpt-4o-mini'),
                                                          messages=[{'role':'system','content':'You describe software modules briefly for PMs.'},
                                                                    {'role':'user','content':prompt}],
                                                          temperature=0.1, max_tokens=80)
                    desc = (resp.choices[0].message.content or '').strip()
                    md = n.get('metadata') or {}
                    if desc:
                        md['description'] = desc
                        # also upgrade generic cluster name if very mechanical
                        base_name = (n.get('name') or '')
                        if base_name.lower().startswith('cluster_') or 'cluster' in base_name.lower():
                            # Derive a concise name from first sentence
                            short = desc.split('\n')[0].strip('.')
                            n['name'] = short[:60]
                        n['metadata'] = md
                except Exception:
                    pass
        else:
            logger.error('OpenAI client unavailable despite required LLM step. Ensure openai package is installed.')
    except Exception:
        pass

    # Enrich depends_on intents and top_calls
    # Build quick name lookup
    sys_name = { n['id']: (n.get('name') or '') for n in system }
    # Index call edges by system pair
    calls_by_pair = defaultdict(list)
    for ce in call_edges:
        a = ce['from_node']; b = ce['to_node']
        sa = system_ancestor(a); sb = system_ancestor(b)
        if sa and sb and sa != sb:
            calls_by_pair[(sa,sb)].append(ce)
    def infer_intent(sa_id: str, sb_id: str, sa_name: str, sb_name: str):
        s = sa_name.lower(); t = sb_name.lower(); intents = []
        # Use facts to drive mapping
        sa_md = (by_id.get(sa_id, {}) or {}).get('metadata') or {}
        sb_md = (by_id.get(sb_id, {}) or {}).get('metadata') or {}
        sa_f = sa_md.get('facts') or {}; sb_f = sb_md.get('facts') or {}
        if (sa_f.get('routes') or []) and (sb_f.get('http_calls') or []):
            intents.append('http_request')
        if sa_f.get('io_ops') or sb_f.get('io_ops'):
            intents.append('read/write')
        if sa_f.get('db_ops') or sb_f.get('db_ops'):
            intents.append('db_access')
        if sa_f.get('cache_ops') or sb_f.get('cache_ops'):
            intents.append('cache_access')
        if sa_f.get('queue_ops') or sb_f.get('queue_ops'):
            intents.append('enqueue')
        if sa_f.get('pubsub_ops') or sb_f.get('pubsub_ops'):
            intents.append('publish/subscribe')
        if sa_f.get('external_calls') or sb_f.get('external_calls'):
            intents.append('external_integration')
        # Name-based fallbacks
        if 'control' in s and 'action' in t: intents.append('emit_events')
        if 'component' in s and 'action' in t: intents.append('invoke_handlers')
        if 'action' in s and ('data' in t or 'io' in t or 'schema' in t): intents.append('read/write')
        if 'action' in s and 'component' in t: intents.append('update_ui')
        if not intents: intents.append('depends')
        return list(dict.fromkeys(intents))
    for e in dep_edges:
        sa = e['from_node']; sb = e['to_node']
        e_md = e.get('metadata') or {}
        pair_calls = calls_by_pair.get((sa,sb), [])
        # sample top calls
        samples = []
        for ce in pair_calls[:3]:
            src = by_id.get(ce['from_node'], {})
            dst = by_id.get(ce['to_node'], {})
            samples.append({
                'from': src.get('name') or src.get('id'),
                'to': dst.get('name') or dst.get('id')
            })
        if samples:
            e_md['top_calls'] = samples
        e_md['intent'] = infer_intent(sa, sb, sys_name.get(sa,''), sys_name.get(sb,''))
        e['metadata'] = e_md

    viz = {
        'metadata': { **frontend.get('metadata', {}), 'layout': { 'rows': 12, 'bands': { 'business':[1], 'system':[2,3,4], 'implementation':[5,6,7,8,9,10,11,12] }, 'anchors_px': rowvals } },
        'nodes': nodes,
        'edges': merged_edges,
    }

    # Also emit split artifacts: viz_core (no positions/colors), viz_layout, and viz_meta
    try:
        project = Path(codebase_dir).parts[-1] or 'project'
        out_dir = Path('graph') / project / 'exports'
        out_dir.mkdir(parents=True, exist_ok=True)
        # Core
        core_nodes = []
        layout_nodes = []
        meta_nodes = []
        for n in nodes:
            nd = dict(n)
            vis = (nd.get('metadata') or {}).get('color')
            pos = nd.pop('position', None)
            # strip visual-only from core
            core_nodes.append(nd)
            layout_nodes.append({'id': n['id'], 'position': pos or {'x':0,'y':0}, 'visual': {
                'size_factor': (n.get('metadata') or {}).get('size_factor', 1),
                'color': (n.get('metadata') or {}).get('color')
            }})
            md = n.get('metadata') or {}
            meta_nodes.append({'id': n['id'], 'name': n.get('name'), 'level': n.get('level'), 'type': n.get('type'), 'description': md.get('description') or md.get('purpose')})
        viz_core = {'metadata': {'project': project}, 'nodes': core_nodes, 'edges': merged_edges}
        viz_layout = {'metadata': viz['metadata']['layout'], 'nodes': layout_nodes}
        viz_meta = {'metadata': {'project': project}, 'nodes': meta_nodes}
        (out_dir / 'viz_core.json').write_text(json.dumps(viz_core, indent=2), encoding='utf-8')
        (out_dir / 'viz_layout.json').write_text(json.dumps(viz_layout, indent=2), encoding='utf-8')
        (out_dir / 'viz_meta.json').write_text(json.dumps(viz_meta, indent=2), encoding='utf-8')
    except Exception:
        pass

    return viz

def convert_analysis_result_to_frontend_format(analysis_result):
    """Convert our backend analysis result to the frontend format with enhanced metadata"""
    if not analysis_result or 'graph' not in analysis_result or not analysis_result['graph']:
        return None
    
    graph = analysis_result['graph']

    # Emit AST split artifacts (core + meta)
    try:
        codebase_path = analysis_result.get('codebase_path') or ''
        project = Path(codebase_path).name or 'project'
        out_dir = Path('graph') / project / 'exports'
        out_dir.mkdir(parents=True, exist_ok=True)
        # Core: implementation symbols and call/import edges
        ast_nodes = []
        for n in getattr(graph, 'nodes', []):
            lvl = (n.level.value if hasattr(n.level,'value') else str(n.level))
            if lvl != 'IMPLEMENTATION':
                continue
            ast_nodes.append({
                'id': n.id,
                'name': n.name,
                'level': lvl,
                'type': (n.type.value if hasattr(n.type,'value') else str(n.type)),
                'files': list(n.files or []),
                'classes': list(n.classes or []),
                'functions': list(n.functions or [])
            })
        ast_edges = []
        for e in getattr(graph, 'edges', []):
            t = (e.type.value if hasattr(e.type,'value') else str(e.type))
            if t in ('calls','imports'):
                ast_edges.append({'from': e.from_node, 'to': e.to_node, 'type': t})
        (out_dir / 'ast_core.json').write_text(json.dumps({'nodes': ast_nodes, 'edges': ast_edges}, indent=2), encoding='utf-8')
        # Meta: per-symbol metrics
        ast_meta = []
        for n in getattr(graph, 'nodes', []):
            lvl = (n.level.value if hasattr(n.level,'value') else str(n.level))
            if lvl != 'IMPLEMENTATION':
                continue
            md = n.metadata or None
            ast_meta.append({
                'id': n.id,
                'paths': list(n.files or []),
                'line_count': getattr(md,'line_count', None) if md else None,
                'file_size': getattr(md,'file_size', None) if md else None,
                'language': getattr(md,'language', None) if md else None,
                'complexity': (md.complexity.value if md and hasattr(md,'complexity') and hasattr(md.complexity,'value') else (str(md.complexity) if md and hasattr(md,'complexity') else None))
            })
        (out_dir / 'ast_meta.json').write_text(json.dumps({'nodes': ast_meta}, indent=2), encoding='utf-8')
    except Exception:
        pass
    
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
        
        # Start analysis (synchronously). Feature flag to route via LangGraph.
        try:
            engine = (request.form.get('engine') or request.args.get('engine') or os.getenv('AUTOGRAPH_PIPELINE') or '').strip().lower()
            use_langgraph = engine == 'langgraph'
            logger.info(f"Engine selection for {analysis_id}: {'langgraph' if use_langgraph else 'legacy'}")
            analysis_sessions[analysis_id]['message'] = 'Analyzing codebase...'
            analysis_sessions[analysis_id]['progress'] = 25

            if use_langgraph and create_workflow is not None:
                # LangGraph path: identical inner steps but orchestrated as a workflow
                try:
                    project_name = Path(temp_dir).name
                    runs_dir = Path('graph') / project_name / 'runs'
                    runs_dir.mkdir(parents=True, exist_ok=True)
                    checkpointer = str(runs_dir / 'checkpoints.sqlite')
                except Exception:
                    project_name = 'project'
                    checkpointer = None

                app = create_workflow(project_name=project_name, analysis_id=analysis_id, checkpointer_path=checkpointer)
                initial_state = {
                    'upload_temp_dir': temp_dir,
                    'analysis_id': analysis_id,
                    'flags': {
                        'deterministic': True,
                        'use_llm': bool(os.getenv('OPENAI_API_KEY')) and (os.getenv('USE_LLM', '0') in {'1','true','yes'}),
                        'engine': 'langgraph'
                    },
                    'logs': [],
                    'progress': 10,
                    'message': 'Initialized'
                }
                result_state = app.invoke(initial_state, config={'configurable': {'thread_id': analysis_id}})
                frontend_data = result_state.get('viz_graph')
            else:
                # Legacy path: keep existing behavior exactly
                analyzer = CodebaseAnalyzer()
                result = analyzer.analyze_codebase(temp_dir)
                frontend_data = convert_analysis_result_to_frontend_format(result)
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