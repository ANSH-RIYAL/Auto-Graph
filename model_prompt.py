import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


ENRICHMENT_SCHEMA = {
    "schema_version": "viz-enrich-1",
    "nodes": [
        {
            "id": "string",
            "name": "string?",
            "summary": "string?",
            "responsibilities": ["string"],
            "interfaces": ["string"],
            "top_dependencies": ["string"]
        }
    ]
}


SYSTEM_PROMPT = (
    "You enrich Business/System nodes with human-friendly names and concise summaries. "
    "Do NOT invent nodes or relationships. Do NOT change ids. "
    "Output JSON matching the schema exactly; strings must be short and business-facing."
)


def load_ast_graph(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_prompt(schema: dict, viz_core: dict) -> str:
    # Build compact enrichment input from viz_core
    nodes = []
    # Precompute light neighbor map (top weights if present)
    neighbors = {}
    for e in viz_core.get("edges", []):
        if e.get("type") != "depends_on":
            continue
        src = e.get("from_node"); dst = e.get("to_node")
        neighbors.setdefault(src, []).append({"id": dst, "weight": (e.get("metadata") or {}).get("weight", 1)})
    name_lookup = { n.get("id"): n.get("name") for n in viz_core.get("nodes", []) }
    for n in viz_core.get("nodes", []):
        lvl = n.get("level");
        if lvl not in ("BUSINESS","SYSTEM"):
            continue
        node = {
            "id": n.get("id"),
            "level": lvl,
            "component_kind": n.get("type"),
            "current_name": n.get("name"),
            "member_samples": (n.get("files") or [])[:5],
            "neighbor_systems": [
                {"id": m.get("id"), "name": name_lookup.get(m.get("id")), "weight": m.get("weight")}
                for m in sorted(neighbors.get(n.get("id"), []), key=lambda x: -x.get("weight",1))[:3]
            ]
        }
        nodes.append(node)
    payload = {
        "schema": schema,
        "immutable": ["id","level"],
        "nodes_for_enrichment": nodes
    }
    return json.dumps(payload, ensure_ascii=False)


def call_openai(prompt: str) -> dict:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment or .env")
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    return json.loads(content)


def main():
    # Load latest viz_core.json under exports
    candidates = sorted(Path("graph").glob("**/exports/viz_core.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise SystemExit("No viz_core.json found. Run analysis first.")
    viz_core = json.loads(candidates[0].read_text(encoding='utf-8'))
    prompt = build_prompt(ENRICHMENT_SCHEMA, viz_core)
    enriched = call_openai(prompt)
    out_file = candidates[0].with_name('viz_meta.json')
    out_file.write_text(json.dumps(enriched, indent=2), encoding='utf-8')
    print(str(out_file))


if __name__ == "__main__":
    main()

