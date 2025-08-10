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
  - Simplify exports to JSON only
  - Support folder uploads via `webkitdirectory` and multiple files FormData
- Docs
  - Knowledge docs updated with canonical graph templates and deterministic intermediary outputs
  - README updated to reflect BSI and JSON-only

Exit Criteria
- App runs and renders graphs using BSI terms only
- Exported JSON matches canonical structure in REALITY_TESTS

## Phase 2 — System Clustering (Static-Analysis First)
- Build import graph from existing AST parse (no external tools yet)
- Cluster files into SYSTEM nodes using NetworkX greedy modularity (deterministic: sorted inputs, stable seeds)
- Construct contains edges: IMPLEMENTATION → SYSTEM, SYSTEM → BUSINESS
- Collapse import/call edges to SYSTEM-level `depends_on` (aggregate weights)
- Update stats to include system_nodes count and edge rollups

Deterministic Layout & Zoning (part 1)
- Compute stable positions server-side and ship with graph (no layout jitter in UI):
  - Place BUSINESS nodes in fixed columns (left→right by name), y-level = 1
  - Place SYSTEM clusters directly under their BUSINESS parent within that column, y-level = 2
  - Place IMPLEMENTATION nodes under their SYSTEM parent (fan-out grid), y-level = 3
- Persist positions in each node as `position: {x, y}` (absolute canvas coords)
- UI uses preset layout; slider only hides/shows nodes by `technical_depth` and never recomputes positions

Exit Criteria
- For `todo_flask_app`, BUSINESS nodes remain in the same x-columns when toggling depth; SYSTEM/IMPLEMENTATION stay clustered beneath their parents
- Switching depth does not move any node; only visibility changes

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

Exit Criteria
- Usability improvements without changing the canonical JSON

Risks & Mitigations
- Ambiguity in clustering → provide deterministic fallback (directory-based grouping)
- Performance on large repos → cap nodes at implementation view; show summaries at higher levels
- Drift in agentic steps → guarded by REALITY_TESTS templates and canonical schema

