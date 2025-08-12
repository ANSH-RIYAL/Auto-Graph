# Decision Map — Auto-Graph (BSI-first, HLD parity via exports)

This decision map tracks the why/what/how across the pipeline, aligned with the BSI model and current project plan.

Status legend: Implemented | In-Progress | Planned | Deferred

## Invariants (do not change)
- Response shape: `{ success, data, error }` (Implemented)
- Endpoints: `/api/analysis/upload`, `/api/analysis/<id>/status`, `/api/analysis/<id>/graph`, `/api/analysis/<id>/logs` (Implemented)
- Leveling terms: Business/System/Implementation only (Implemented)

## Schema and Core Graph
- Canonical artifacts: `ast_graph.json`, `viz_graph.json` (Implemented/Expanding)
- Edge types: `contains`, `depends_on`, `calls` (Implemented; stronger rollups Planned)
- Entity taxonomy: External_API, LLM_Service, Auth_Provider, User, Managed_DB (Planned → Implement)

## Backend Pipeline
- AST parse (Implemented)
- Deterministic positions: 12 rows, bands 1/3/8; persisted in export (In-Progress)
- Module facts + edge intents (Planned → Implement)
- System rollups with weights (Planned)
- Externals detection (Planned)
- Optional: metrics/callgraph later (Deferred)

## Web UI/Interaction
- Preset layout only; filters do not move nodes (Implemented)
- Edge-type filters and node-centric highlighting (Implemented)
- Folder uploads (Implemented)
- Extras deferred (Deferred)

## Documentation
- Condensed `README.md`, `PROJECT_PLAN.md`, `ENTITY_TAXONOMY.md`, `PROMPTS.md`, `REALITY_CHECKS.md` (In-Progress)

## Current Cross-Reference
- Want: Stable VIZ export with positions, module facts, edge intents, externals (Planned/Implementing)
- Can now: AST-only + server positions + filters (Implemented)
- Next: rollups, enrichment, validation checks (Planned)

## Open Items & Decisions
- Reintroduce alternate exports (YAML/CSV/DOT/HTML/Mermaid) only if trivial wrappers around canonical JSON. (Planned)
- System clustering determinism: input ordering + fixed seeds; fallback to directory-based grouping if clustering is trivial. (Planned)
- Keep unit tests minimal during rapid iteration; prioritize debug-first docs and golden samples. (Deferred)

## Traceability (recent notable changes)
- Server enforces vertical zoning and widened horizontal spacing to reduce collisions. (Implemented)
- UI switched to node-centric highlighting; edge labels shown only when highlighted. (Implemented)
- Edge details panel supports `edge.metadata.examples`. (Implemented)
- Removed legacy “All Connections/Hierarchy” toggle; one deterministic view. (Implemented)

