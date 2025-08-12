# AutoGraph Project Plan (Condensed, BSI-first)

We are cleaning up to focus on core extraction and representation using `vizro-core` as the target codebase.

## Invariants
- Canonical artifacts: `ast_graph.json` and `viz_graph.json` under `graph/<project>/exports/`
- Levels: BUSINESS/System/Implementation only
- Edges: `contains`, `depends_on`, `calls`
- Layout: 12 rows total with bands 1/3/8; positions embedded in export
- UI: preset layout only; filters toggle visibility, never positions

## Phase A — Stable VIZ Export (positions + schema)
- Embed `metadata.layout = { rows:12, bands:{ business:[1], system:[2,3,4], implementation:[5..12] }, anchors_px:[y1..y12] }`
- Ensure every node has absolute `{x,y}`; y maps to anchors; x grouped by parent and ordered by degree
- Save both AST and VIZ exports per project; add `export_report.md` with counts

Exit
- `jq` checks for 12 anchors; all nodes positioned and within bands
- Edge types ⊆ {contains, depends_on, calls}

## Phase B — Module Facts and Edge Intents
- Auto-extract for each system node: files_count, classes_count, public_functions, routes, db_ops, cache_ops, external_calls, msg_bus/queue ops, entrypoints, top_dependencies
- For each edge: populate `metadata.intent` (HTTP verbs, DB ops, publish/consume, enqueue/dequeue, external API/LLM calls) with counts and 1–2 examples
- Detect externals/actors and emit explicit nodes

Exit
- Non-empty structured metadata on Business/System nodes; intents present where detectable

## Phase C — System Rollups
- Aggregate calls/imports into weighted system-level `depends_on` edges; keep raw calls at implementation
- Expose top-N functions per pair in `edge.metadata.top_calls`

Exit
- Depends_on edges present with weights; raw calls pruned from higher levels

## Phase D — LLM Enrichment (Schema-Locked)
- Business/System nodes only: concise `name`, `purpose`, `responsibilities`, `interfaces`, `top_dependencies`
- temperature ≤ 0.1; topology/positions immutable; Pydantic validation + 1 retry

Exit
- PM-readable summaries without topology drift

## Out of Scope (until D complete)
- Tests, dashboards, non-JSON exports, heavy visual polish

## Acceptance (vizro-core)
- Exports generated; anchors length 12; externals included when detected
- System-level rollups visible; node popovers show auto facts and examples

