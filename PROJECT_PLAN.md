# AutoGraph Project Plan (BSI Migration and Beyond)

This plan guides the evolution from the current codebase to a unified Business/System/Implementation (BSI) model, followed by quality and capability upgrades.

## Principles
- Single canonical JSON graph with levels: BUSINESS (1), SYSTEM (2), IMPLEMENTATION (3)
- Edge types limited to: contains, depends_on, calls
- JSON export only (others optional later)
- Backward compatibility: map legacy HLD→BUSINESS, LLD→IMPLEMENTATION when loading
- Keep changes incremental and reversible

## Phase 1 — BSI Schema + UI Alignment (Current Phase)
- Replace HLD/LLD with BUSINESS/SYSTEM/IMPLEMENTATION in `src/models/schemas.py`
  - Add `technical_depth` (1/2/3) and BSI counts in statistics
- Update analyzer and enhanced graph builder to output BUSINESS/IMPLEMENTATION
  - Maintain containment edges
  - Set metadata.technical_depth defaults (BUSINESS=1 for business nodes; SYSTEM used for mid-level metadata until clustering added)
- Web UI
  - Use `technical_depth` and BSI levels everywhere
  - Simplify exports to JSON only (no alternate formats in this phase)
  - Support folder uploads via `webkitdirectory` and multiple files FormData
  - Node-centric highlighting: clicking a node makes its incident edges opaque; others remain translucent
  - Edge labels hidden by default; shown only when highlighted (via node click or edge select)
  - Edge-type filters (contains/depends_on/calls) with colors: green/blue(dashed)/orange(dotted)
- Docs
  - Knowledge docs updated with canonical graph templates and deterministic intermediary outputs
  - README updated to reflect BSI and JSON-only

Exit Criteria
- App runs and renders graphs using BSI terms only
- Exported JSON matches canonical structure in REALITY_TESTS
- API checks pass:
  - `ys` for nodes are exactly `[150,330,510]`
  - Toggling edge-type filters changes edge counts without any node position changes
  - Clicking a node highlights only its incident edges (labels appear only on highlighted edges)

## Phase 2 — System Clustering (Static-Analysis First)
- Build import graph from existing AST parse (no external tools yet)
- Cluster files into SYSTEM nodes using NetworkX greedy modularity (deterministic: sorted inputs, stable seeds)
- Construct contains edges: IMPLEMENTATION → SYSTEM, SYSTEM → BUSINESS
- Collapse import/call edges to SYSTEM-level `depends_on` (aggregate weights)
- Update stats to include system_nodes count and edge rollups
 - Populate `edge.metadata.examples` when recognizable (HTTP routes, DB ops)

Layout Refinement (within fixed anchors)
- Within each y-layer, position higher-degree nodes closer to column center; low-degree nodes toward sides. Degree = in+out incident edges after filtering by depth.
- Keep absolute anchors for BUSINESS/SYSTEM/IMPLEMENTATION y positions; only x is adjusted deterministically by degree ordering.

Coverage/Completeness
- Add a simple "coverage" counter: percent of implementation files assigned to some SYSTEM cluster and having at least one outward edge.
- Track "unknown" external references (imports to stdlib/third-party not in repo) and emit external stub nodes (see Entity Taxonomy) with `level: SYSTEM` or `BUSINESS` as appropriate.

Deterministic Layout & Zoning (part 1)
- Compute stable positions server-side and ship with graph (no layout jitter in UI):
- Use 6 y-layers for clarity:
  - BUSINESS rows: 150, 230
  - SYSTEM rows: 310, 390
  - IMPLEMENTATION rows: 470, 550
- Place nodes under parents; alternate between the two rows per level to reduce clutter.
- Persist positions in each node as `position: {x, y}` (absolute canvas coords)
- UI uses preset layout; slider only hides/shows nodes by `technical_depth` and never recomputes positions

Exit Criteria
- For `todo_flask_app`, BUSINESS nodes remain in the same x-columns when toggling depth; SYSTEM/IMPLEMENTATION stay clustered beneath their parents
- Switching depth does not move any node; only visibility changes
- jq check for y-layers returns `[150,330,510]` and is stable across depth toggles
- In-layer x-ordering reflects degree: top-3 highest-degree nodes sit nearest the column center
- Coverage metric ≥ 95% of implementation files assigned; unknown externals are represented as stubs

Exit Criteria
- For `examples/real_world/todo_flask_app`, SYSTEM nodes match REALITY_TESTS examples
- UI filters show meaningful structure at depth 2

## Phase 3 — Optional Enhancers (Lightweight)
- Add Radon metrics to enrich node complexity (no blocking if unavailable)
- Optional call graph ingestion (pyan) if present; otherwise skip
- Basic circular dependency detection at SYSTEM level

Deterministic Layout & Zoning (part 2)
- Add bounding boxes per BUSINESS and SYSTEM cluster to keep the visual zoning clear
- Add minimal overlap-avoidance (simple grid snap) while preserving fixed anchors
 - Add tiny legend for edge colors/types

Exit Criteria
- Complexity fields populated when Radon is available; pipeline remains stable without it
- Visual clusters clearly bounded; anchors unchanged across depth changes

## Phase 4 — UX and Export Polish
- Improve layout presets for BSI levels (business row, system clusters, implementation fan-out)
- Add minimal search/filter in UI (by name/type)
- Reintroduce optional alternate exports only if trivial (e.g., YAML wrapper around JSON)

Grounded Examples & Debug-first Checks
- REALITY_TESTS includes exact canonical JSON fragments for:
  - Implementation symbols (AST)
  - System clusters (ids, member files)
  - Business domains (members)
  - Final graph with node positions for `todo_flask_app`
- Acceptance: positions for `business_todo`, `system_api`, `system_core` are unchanged when toggling depth
- Entity taxonomy examples: external API, LLM, user input, auth provider stubs included with example edges

Exit Criteria
- Usability improvements without changing the canonical JSON

Risks & Mitigations
- Ambiguity in clustering → provide deterministic fallback (directory-based grouping)
- Performance on large repos → cap nodes at implementation view; show summaries at higher levels
- Drift in agentic steps → guarded by REALITY_TESTS templates and canonical schema

## Entity Taxonomy (Core, Phase 2 scope)
- Implementation entities: File, Class, Function_Group
- System entities: API, Web_App, Mobile_App, Service, Module, Database, Cache, Message_Bus, Queue/Task_Runner, Stream_Processor, Scheduler, Storage, Search, Auth_Provider, Secrets_Config, Observability, External_API, LLM_Service
- Business entities: Domain
- External stubs (no code in repo):
  - `External_API` (HTTP/REST/GraphQL)
  - `LLM_Service` (OpenAI/Gemini/etc.)
  - `Auth_Provider` (OIDC/SAML/Custom)
  - `User` (End-User input/source)
  - `Third_Party_DB` or `Managed_DB`
- Edge types: `contains`, `depends_on`, `calls` (all others deferred)
## LLM Procedure (Core)
- Inputs: canonical AST graph + initial viz graph draft (project-agnostic rollups, positions, externals)
- Constraints: JSON schema enforced; temperature 0–0.2; response_format=json; topology and positions immutable
- Allowed to edit: names, summaries, responsibilities, interfaces, domain_tags, kind_specific fields, trivial merge/split flags (no edge changes)
- Validation: Pydantic schema; counters must match; re-prompt on violation
- Output: finalized visualization-graph (`/api/analysis/<id>/viz`)

## Deferred Backlog (do not implement until core complete)
- Alternate exports beyond JSON
- Executive dashboards/PM metrics beyond counts
- Compliance/regulatory reports
- Fancy animations/layouts beyond grid-snap and bounding boxes
- Search bar, fuzzy filters, tag faceting

