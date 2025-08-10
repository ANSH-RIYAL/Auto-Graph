# Decision Map — Auto-Graph (BSI Migration → UI/Backend)

This decision map tracks the why/what/how across the pipeline, aligned with the BSI model and current project plan.

Status legend: Implemented | In-Progress | Planned | Deferred

## Invariants (do not change)
- Response shape: `{ success, data, error }` (Implemented)
- Endpoints: `/api/analysis/upload`, `/api/analysis/<id>/status`, `/api/analysis/<id>/result`, `/api/analysis/<id>/export` (Implemented)
- Leveling terms: Business/System/Implementation only; map legacy HLD→BUSINESS, LLD→IMPLEMENTATION (Implemented)

## Schema and Core Graph
- Single canonical JSON graph with BSI levels and `technical_depth ∈ {1,2,3}` (Implemented)
- Edge types limited to `contains`, `depends_on`, `calls` (Implemented; UI filters wired, back-end rollups for depends_on slated)
- Backward compatibility mapping from legacy graphs at load time (Implemented)
- JSON export only in current phase; alternate exports are optional later (Implemented → Planned for reintroduction)

## Backend Pipeline
- AST parsing to extract files/functions/classes/imports (Implemented)
- Deterministic positions emitted server-side: BUSINESS y=150, SYSTEM y=330, IMPLEMENTATION y=510; positions persisted in node `position` (Implemented)
- Depends-on rollups from imports at SYSTEM level (Planned)
- System clustering via static import graph and NetworkX greedy modularity (Planned)
- Business aggregation over System clusters with optional LLM label (Planned)
- Radon complexity metrics enrichment (Deferred/Optional)
- Optional call graph ingestion (pyan) with DOT import path (Deferred/Optional)

## Web UI/Interaction
- Single-page flow: upload → progress → results → export (Implemented)
- Level slider filters by `technical_depth`; layout never recomputes on filter (Implemented)
- Edge-type filters: contains=green, depends_on=blue (dashed), calls=orange (dotted) (Implemented)
- Default edges translucent; highlighted edges opaque with labels (Implemented)
- Node-centric highlighting: clicking a node highlights incident edges; clicking edge opens detail panel (Implemented)
- Clear selection on background click (Implemented)
- Tiny legend for edge colors/types (Planned)
- Folder uploads via `webkitdirectory` + multi-file FormData (Planned)

## Documentation
- `PROJECT_PLAN.md` drives phases; BSI terms used consistently (Implemented)
- `knowledge_docs_templates_2/*` aligned to BSI; Decision Log in `FOUNDATION.md` retained (Implemented)
- Decision Map (this file) added to document development/feature choices and status across pipeline (Implemented)

## Current Cross-Reference (What/Can/Plan)
- What we want: Single canonical BSI graph, deterministic layout, JSON-first export, clear UI filters. (Can: Implemented)
- What we can do now: AST-only pipeline with server-side positions, node-centric highlighting, edge filters/coloring. (Implemented)
- What we plan next: System clustering, depends_on rollups, small UI legend, optional metrics/call graph later. (Planned)

## Open Items & Decisions
- Reintroduce alternate exports (YAML/CSV/DOT/HTML/Mermaid) only if trivial wrappers around canonical JSON. (Planned)
- System clustering determinism: input ordering + fixed seeds; fallback to directory-based grouping if clustering is trivial. (Planned)
- Keep unit tests minimal during rapid iteration; prioritize debug-first docs and golden samples. (Deferred)

## Traceability (recent notable changes)
- Server enforces vertical zoning and widened horizontal spacing to reduce collisions. (Implemented)
- UI switched to node-centric highlighting; edge labels shown only when highlighted. (Implemented)
- Edge details panel supports `edge.metadata.examples`. (Implemented)
- Removed legacy “All Connections/Hierarchy” toggle; one deterministic view. (Implemented)

