# RUNBOOKS

## Cost Ceiling Hit
- Detect: API returns 429 or budget exceeded.
- Action: Switch to AST-only mode; return partial results with `stage: "fallback_ast"`.
- Log: Reason, request params (no secrets), budget snapshot.
- User Message: "Service busy; partial analysis shown. Try export or retry later."

## API Failure (5xx/Timeout)
- Retries: Exponential backoff (e.g., 3 attempts: 0.5s, 2s, 5s).
- Circuit Breaker: If 3 consecutive failures, open for 2 minutes and serve cache/AST-only.
- Status: Set `status: in_progress` with `stage: "retry"` then `"fallback_ast"` if breaker opens.

## Cache Policy
- Cache Key: model_name + normalized prompt + content hash.
- TTL: 24h default. Invalidate on codebase change or version bump.
- Serving: Prefer cached response when available and within TTL.

## Minimal Debug Ritual (5–10 min)
1) Upload a known sample from `examples/sample_codebases/`.
2) Watch `/status` for stage transitions: `upload → parse → analyze → graph → export`.
3) If stalls > 15s, check logs; fallback to AST-only if LLM unreachable.
4) Export and compare counts to `examples/sample_graphs/` (±5%).
5) Record any deviation in Decision Log if it implies a rule change.

## Clustering/Leveling Fallbacks
- If import/call graph tools are unavailable, derive a simple import graph from our AST and cluster using NetworkX greedy modularity.
- If clustering fails or yields trivial output, create one `SYSTEM` node per top-level directory and assign `IMPLEMENTATION` children accordingly.
- Always produce a valid Business level by aggregating related System nodes (directory or name-based heuristics). Label can be generic but must be present.

## UI Safety Toggles
- Default view shows only `contains` edges; `depends_on` and `calls` are opt-in checkboxes.
- Level slider defaults to `SYSTEM` (2). Users can switch to `BUSINESS` or `IMPLEMENTATION` without re-analysis.

