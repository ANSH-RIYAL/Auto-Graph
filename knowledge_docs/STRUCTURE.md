# STRUCTURE

## Directory Layout (Immutable Skeleton)
```
Auto-Graph/
├── src/
│   ├── parser/
│   ├── analyzer/
│   ├── llm_integration/
│   ├── graph_builder/
│   ├── export/
│   ├── visualization/
│   ├── agent_detection/
│   ├── models/
│   ├── utils/
│   └── web/
├── examples/
├── graph/
├── cache/
└── logs/
```

## Layer Responsibilities
- **/parser**: AST/symbol parsing.
- **/analyzer**: Pipeline coordination and unified graph assembly.
- **/llm_integration**: Single LLM client, prompts, retries, caching.
- **/graph_builder**: Business/System/Implementation construction and metadata aggregation; merges import/call graphs.
- **/export**: Multi-format export.
- **/visualization**: Graph visualizer helpers.
- **/agent_detection**: Pattern-based detection; no ML.
- **/web**: Flask app, endpoints, static/templates.
- **/models**: Pydantic/dataclasses for requests/responses/graph.
- **/utils**: File IO, logging.

## Immutable Interface Contracts
- **JSON shape**: `{ success, data, error }`.
- **Endpoints**:
  - POST `/api/analysis/upload` (multipart)
  - GET  `/api/analysis/<id>/status`
  - GET  `/api/analysis/<id>/result`
  - GET  `/api/analysis/<id>/export?format=...`
- **Status fields**: `analysis_id, status, progress, stage, estimated_completion`.
- **Export formats**: `json,yaml,csv,dot,html,mermaid`.

## Unified Graph Schema (BSI)
- Node: `id, name, type, level ∈ {BUSINESS,SYSTEM,IMPLEMENTATION}, technical_depth ∈ {1,2,3}, files[], functions[], classes[], imports[], metadata, pm_metadata, enhanced_metadata`.
- Edge: `from, to, type ∈ {contains, depends_on, calls}, metadata`.
- Backward compatibility: when loading legacy graphs, map `HLD→BUSINESS`, `LLD→IMPLEMENTATION`, and infer `technical_depth`.

## Dependencies (Minimal Set)
- `networkx` for clustering/graph ops (required).
- `radon` for basic complexity metrics (optional but recommended).
- `pyan` for static call graph (optional; DOT import path).
- `snakefood` or built-in AST import graph (optional; we can start with built-in).

## Golden Artifacts
- Location: `examples/sample_graphs/`.
- Purpose: Manual debug baseline; compare node/edge counts and metadata keys.
- Tolerance: counts within ±5% unless otherwise specified.

