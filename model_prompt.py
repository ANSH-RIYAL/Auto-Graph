import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


TEMPLATE_JSON = {
    "metadata": {
        "source_ast_graph_version": "1.x",
        "generated_at": "",
        "codebase_path": "",
        "rules_version": "v1",
        "layout": {
            "y_layers": [150, 230, 310, 390, 470, 550],
            "levels": {"BUSINESS": [150, 230], "SYSTEM": [310, 390], "IMPLEMENTATION": [470, 550]},
            "ordering": "degree_center",
            "deterministic": True,
        },
        "counters": {
            "business_nodes": 0,
            "system_nodes": 0,
            "implementation_nodes": 0,
            "edges": 0,
            "coverage_pct": 0,
        },
    },
    "nodes": [],
    "edges": [],
    "legend": {
        "node_kinds": [
            "Domain",
            "Actor",
            "Service",
            "Module",
            "Database",
            "Message_Bus",
            "Queue",
            "Cache",
            "Storage",
            "Search",
            "Scheduler",
            "External_API",
            "LLM_Service",
            "Auth_Provider",
            "File",
            "Class",
            "Function_Group",
        ],
        "edge_types": ["contains", "depends_on", "calls"],
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


SYSTEM_PROMPT = (
    "You transform an AST graph into a standardized visualization-graph. "
    "Do not invent edges. Group and name modules deterministically. "
    "Strictly output JSON matching the provided schema, and compute positions using the fixed six y-layers."
)


def load_ast_graph(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_prompt(schema: dict, ast_graph: dict) -> str:
    return (
        "Schema (must match exactly):\n" + json.dumps(schema, ensure_ascii=False) +
        "\n\nAST graph:\n" + json.dumps(ast_graph, ensure_ascii=False)
    )


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
    # Locate the last AST export if present; else read path from argv
    default_ast = Path("graph").glob("**/autograph_graph_*.json")
    ast_path = None
    try:
        ast_path = max(default_ast, key=lambda p: p.stat().st_mtime)
    except ValueError:
        raise SystemExit("No AST graph found under ./graph. Provide one first.")

    ast_graph = load_ast_graph(ast_path)
    prompt = build_prompt(TEMPLATE_JSON, ast_graph)
    viz = call_openai(prompt)

    out_dir = Path("graph") / "viz"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (ast_path.stem.replace("autograph_graph_", "viz_graph_") + ".json")
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(viz, f, indent=2)
    print(str(out_file))


if __name__ == "__main__":
    main()

