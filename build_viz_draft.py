import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import re

Y_LAYERS = [150, 230, 310, 390, 470, 550]
LEVEL_ROWS = {
    "BUSINESS": [Y_LAYERS[0], Y_LAYERS[1]],
    "SYSTEM": [Y_LAYERS[2], Y_LAYERS[3]],
    "IMPLEMENTATION": [Y_LAYERS[4], Y_LAYERS[5]],
}
TOP_N_DEPENDS = 5
MIN_WEIGHT = 1


def load_latest_ast() -> Path:
    candidates = list(Path("graph").glob("**/autograph_graph_*.json"))
    if not candidates:
        raise SystemExit("No AST graphs found under graph/*")
    return max(candidates, key=lambda p: p.stat().st_mtime)


essential_node_fields = [
    "id",
    "name",
    "level",
]


CANON_KINDS = {
    "Domain","Actor","API","Service","Module","Database","Message_Bus","Queue","Cache","Storage","Search","Scheduler","External_API","LLM_Service","Auth_Provider","File","Class","Function_Group"
}


def build_parent_maps(ast_edges):
    parent_of = {}
    children_of = defaultdict(list)
    for e in ast_edges:
        t = e.get("type") or e.get("edge_type") or ""
        if t.lower() == "contains":
            p = e["from_node"] if "from_node" in e else e.get("from")
            c = e["to_node"] if "to_node" in e else e.get("to")
            parent_of[c] = p
            children_of[p].append(c)
    return parent_of, children_of


def find_ancestor_level(node_id: str, level_name: str, nodes_by_id: dict, parent_of: dict):
    cur = node_id
    while cur in parent_of:
        cur = parent_of[cur]
        n = nodes_by_id.get(cur)
        if n and n.get("level") == level_name:
            return cur
    return None


def degree_center_order(ids, graph_edges):
    deg = defaultdict(int)
    idset = set(ids)
    for e in graph_edges:
        a = e.get("from") or e.get("from_node")
        b = e.get("to") or e.get("to_node")
        if a in idset:
            deg[a] += 1
        if b in idset:
            deg[b] += 1
    return sorted(ids, key=lambda i: (-deg[i], i))


def guess_kind(name: str, ast_type: str) -> str:
    nm = (name or "").lower()
    if "api" in nm or "app.py" in nm:
        return "API"
    if "service" in nm:
        return "Service"
    if "repo" in nm or "database" in nm or "db" in nm:
        return "Database"
    if "messagebus" in nm or nm == "bus":
        return "Message_Bus"
    if "queue" in nm or "taskqueue" in nm:
        return "Queue"
    if "cache" in nm:
        return "Cache"
    if "objectstore" in nm or "storage" in nm:
        return "Storage"
    if "index" in nm or "search" in nm:
        return "Search"
    if "schedule" in nm or "job" in nm:
        return "Scheduler"
    if "auth" in nm:
        return "Auth_Provider"
    if "externalapi" in nm:
        return "External_API"
    if "llm" in nm:
        return "LLM_Service"
    if ast_type.title() in CANON_KINDS:
        return ast_type.title()
    return "Module"


def ensure_placeholders(node: dict) -> None:
    if not node.get("summary"):
        node["summary"] = "information missing"
    if "interfaces" not in node:
        node["interfaces"] = {"inputs": [], "outputs": []}


def add_external_stub(viz_nodes: dict, edges: list, src_system: str, stub_id: str, name: str, kind: str):
    if stub_id not in viz_nodes:
        viz_nodes[stub_id] = {
            "id": stub_id,
            "name": name,
            "level": "SYSTEM",
            "kind": kind,
            "technical_depth": 2,
            "external": True,
            "summary": "external dependency",
            "domain_tags": ["external"],
            "members": {"ast_nodes": [], "files": [], "classes": [], "functions": []},
            "interfaces": {"inputs": [], "outputs": []},
            "kind_specific": {},
            "position": {"x": 0, "y": LEVEL_ROWS["SYSTEM"][1]},
            "stats": {"degree": 0},
            "provenance": {"from_ast": False},
            "completeness": {"coverage_pct": 0, "stub": True},
        }
    edges.append({
        "id": f"{src_system}->{stub_id}#dep",
        "from": src_system,
        "to": stub_id,
        "type": "depends_on",
        "weight": 1,
        "examples": [],
        "label_visibility": "highlight_only",
        "evidence": [],
        "rollup_from_ast": ["external_stub"],
        "provenance": {"from_ast": False},
    })


def build_viz(ast_graph: dict) -> dict:
    ast_nodes = ast_graph.get("nodes", [])
    ast_edges = ast_graph.get("edges", [])
    nodes_by_id = {n["id"]: n for n in ast_nodes if all(k in n for k in essential_node_fields)}

    parent_of, children_of = build_parent_maps(ast_edges)

    # Collect ids by level
    business_ids = [n["id"] for n in ast_nodes if n.get("level") == "BUSINESS"]
    system_ids = [n["id"] for n in ast_nodes if n.get("level") == "SYSTEM"]
    impl_ids = [n["id"] for n in ast_nodes if n.get("level") == "IMPLEMENTATION"]

    # Build node skeletons with kind guess and placeholders
    viz_nodes = {}
    for nid in business_ids + system_ids + impl_ids:
        src = nodes_by_id[nid]
        level = src.get("level")
        kind = guess_kind(src.get("name", nid), src.get("type", ""))
        node = {
            "id": nid,
            "name": src.get("name", nid),
            "level": level,
            "kind": kind,
            "technical_depth": 1 if level == "BUSINESS" else (2 if level == "SYSTEM" else 3),
            "external": False,
            "summary": "",
            "domain_tags": [],
            "members": {"ast_nodes": [nid], "files": src.get("files", []), "classes": src.get("classes", []), "functions": src.get("functions", [])},
            "interfaces": {"inputs": [], "outputs": []},
            "kind_specific": {},
            "position": {"x": 0, "y": 0},
            "stats": {"degree": 0},
            "provenance": {"from_ast": True},
            "completeness": {"coverage_pct": 0, "stub": False},
        }
        ensure_placeholders(node)
        viz_nodes[nid] = node

    # Copy contains edges
    viz_edges = []
    for e in ast_edges:
        if (e.get("type") or "").lower() == "contains":
            frm = e.get("from_node") or e.get("from")
            to = e.get("to_node") or e.get("to")
            viz_edges.append({
                "id": f"{frm}->{to}",
                "from": frm,
                "to": to,
                "type": "contains",
                "weight": 1,
                "examples": [],
                "label_visibility": "highlight_only",
                "evidence": [],
                "rollup_from_ast": [],
                "provenance": {"from_ast": True},
            })

    # Build depends_on rollups from calls between different SYSTEM parents
    weights = defaultdict(int)
    for e in ast_edges:
        if (e.get("type") or "").lower() == "calls":
            a = e.get("from_node") or e.get("from")
            b = e.get("to_node") or e.get("to")
            sys_a = find_ancestor_level(a, "SYSTEM", nodes_by_id, parent_of)
            sys_b = find_ancestor_level(b, "SYSTEM", nodes_by_id, parent_of)
            if sys_a and sys_b and sys_a != sys_b:
                weights[(sys_a, sys_b)] += 1

    # Prune to TOP_N per source
    per_src = defaultdict(list)
    for (sa, sb), w in weights.items():
        per_src[sa].append((sb, w))
    for sa, lst in per_src.items():
        lst.sort(key=lambda x: (-x[1], x[0]))
        for sb, w in lst[:TOP_N_DEPENDS]:
            if w < MIN_WEIGHT:
                continue
            viz_edges.append({
                "id": f"{sa}->{sb}#dep",
                "from": sa,
                "to": sb,
                "type": "depends_on",
                "weight": int(w),
                "examples": [],
                "label_visibility": "highlight_only",
                "evidence": [],
                "rollup_from_ast": ["calls_rollup"],
                "provenance": {"from_ast": True},
            })

    # External stubs based on implementation hints
    # Map impl nodes to their system parent
    impl_parent = {iid: find_ancestor_level(iid, "SYSTEM", nodes_by_id, parent_of) for iid in impl_ids}
    for iid, sp in impl_parent.items():
        nm = (nodes_by_id.get(iid, {}).get("name", iid)).lower()
        files = nodes_by_id.get(iid, {}).get("files", [])
        if sp:
            if "externalapi" in nm or any("external_api" in f or "integrations/external_api" in f for f in files):
                add_external_stub(viz_nodes, viz_edges, sp, "external_api_provider", "External API", "External_API")
            if "llm" in nm or any("llm_service" in f for f in files):
                add_external_stub(viz_nodes, viz_edges, sp, "external_llm_service", "LLM Service", "LLM_Service")
            if "auth" in nm or any("auth_provider" in f for f in files):
                # Prefer link from API system if present
                api_sys = next((sid for sid in system_ids if "api" in (nodes_by_id.get(sid, {}).get("name"," ").lower())), sp)
                add_external_stub(viz_nodes, viz_edges, api_sys, "external_auth_provider", "Auth Provider", "Auth_Provider")

    # Optional Actor(User) stub if any API present
    api_sys = next((sid for sid in system_ids if "api" in (nodes_by_id.get(sid, {}).get("name"," ").lower())), None)
    if api_sys:
        add_external_stub(viz_nodes, viz_edges, api_sys, "actor_user", "User", "Actor")

    # Compute degree for nodes
    for e in viz_edges:
        frm, to = e["from"], e["to"]
        if frm in viz_nodes:
            viz_nodes[frm]["stats"]["degree"] += 1
        if to in viz_nodes:
            viz_nodes[to]["stats"]["degree"] += 1

    # Layout: fixed y rows and degree-centered x ordering
    bx = {}
    b_order = sorted(business_ids)
    for i, bid in enumerate(b_order):
        x = 200 + i * 350
        y = LEVEL_ROWS["BUSINESS"][0 if i % 2 == 0 else 1]
        viz_nodes[bid]["position"] = {"x": x, "y": y}
        bx[bid] = x

    sys_groups = defaultdict(list)
    for sid in system_ids:
        bp = parent_of.get(sid)
        sys_groups[bp].append(sid)
    sx = {}
    for bp, group in sys_groups.items():
        ordered = degree_center_order(group, viz_edges)
        center = bx.get(bp, 200)
        for j, sid in enumerate(ordered):
            offset = (j - (len(ordered) - 1) / 2.0) * 180
            y = LEVEL_ROWS["SYSTEM"][0 if j % 2 == 0 else 1]
            viz_nodes[sid]["position"] = {"x": center + offset, "y": y}
            sx[sid] = center + offset

    impl_groups = defaultdict(list)
    for iid in impl_ids:
        sp = find_ancestor_level(iid, "SYSTEM", nodes_by_id, parent_of)
        impl_groups[sp].append(iid)
    for sp, group in impl_groups.items():
        cx = sx.get(sp, 200)
        ordered = degree_center_order(group, viz_edges)
        for k, iid in enumerate(ordered):
            offset = (k - (len(ordered) - 1) / 2.0) * 140
            y = LEVEL_ROWS["IMPLEMENTATION"][0 if k % 2 == 0 else 1]
            viz_nodes[iid]["position"] = {"x": cx + offset, "y": y}

    viz = {
        "metadata": {
            "source_ast_graph_version": "1.x",
            "generated_at": datetime.utcnow().isoformat(),
            "codebase_path": ast_graph.get("metadata", {}).get("graph_metadata", {}).get("codebase_path", ""),
            "rules_version": "v1",
            "layout": {
                "y_layers": Y_LAYERS,
                "levels": {"BUSINESS": LEVEL_ROWS["BUSINESS"], "SYSTEM": LEVEL_ROWS["SYSTEM"], "IMPLEMENTATION": LEVEL_ROWS["IMPLEMENTATION"]},
                "ordering": "degree_center",
                "deterministic": True,
            },
            "counters": {
                "business_nodes": len(business_ids),
                "system_nodes": len(system_ids),
                "implementation_nodes": len(impl_ids),
                "edges": len(viz_edges),
                "coverage_pct": 0,
            },
        },
        "nodes": list(viz_nodes.values()),
        "edges": viz_edges,
        "legend": {
            "node_kinds": list(CANON_KINDS),
            "edge_types": ["contains","depends_on","calls"],
            "style": {
                "nodes": {
                    "BUSINESS": {"fill": "#E8EEF7", "border": "#2B3A55"},
                    "SYSTEM": {"fill": "#F6E9EA", "border": "#5A2E35"},
                    "IMPLEMENTATION": {"fill": "#EEF3EE", "border": "#2E4B2F"},
                },
                "edges": {
                    "contains": {"color": "#2E7D32", "style": "solid", "opacity_default": 0.2},
                    "depends_on": {"color": "#1565C0", "style": "dashed", "opacity_default": 0.2},
                    "calls": {"color": "#EF6C00", "style": "dotted", "opacity_default": 0.2},
                },
                "label_policy": "hidden_by_default_show_on_highlight",
            },
        },
    }
    return viz


def main():
    ast_path = load_latest_ast()
    with ast_path.open("r", encoding="utf-8") as f:
        ast_graph = json.load(f)
    viz = build_viz(ast_graph)
    out_dir = Path("graph/viz")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = ast_path.stem.replace("autograph_graph_", "viz_draft_")
    out_path = out_dir / f"{stem}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(viz, f, indent=2)
    print(str(out_path))


if __name__ == "__main__":
    main()