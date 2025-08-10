# PROMPTS

## Canonical System Prompts

### Cursor (Backend)
- **Goal**: Implement or edit code in `src/` to satisfy endpoint and pipeline requirements.
- **Respect**: Invariants in `FOUNDATION.md` and contracts in `STRUCTURE.md`.
- **Do Not**: Rename endpoints/dirs, introduce DB/auth/WebSockets/queues, change JSON schema.
- **Outputs**: Edits only; keep code readable; include imports; preserve existing style.
- **Fallback**: If LLM unavailable, ensure AST-only path works and set `stage` accordingly.
- **Leveling Rule**: Levels are Business/System/Implementation. Do not re-introduce HLD/LLD.

### Replit (Frontend)
- **Goal**: Single-page upload → progress → results → export UI.
- **Respect**: Endpoint paths and JSON schema.
- **Do Not**: Add frameworks or auth; keep plain HTML/CSS/JS.
- **Outputs**: Accessible UI; graceful errors; no renames of IDs/paths.

### ChatGPT (Docs/Prompts)
- **Goal**: Keep docs skimmable; update Decision Log when choices change.
- **Respect**: Invariants; avoid proposing out-of-scope tech.
- **Outputs**: Minimal edits with clear bullets; no large rewrites.
- **Terminology**: Use Business/System/Implementation; avoid HLD/LLD.

## Prompt Variables
- `codebase_path`, `analysis_id`, `model_name`, `budget_tokens`, `cache_key`, `failure_policy`.
- `leveling_strategy` (fixed to BSI but allows heuristic tuning)
- `clustering_method` (e.g., greedy_modularity, louvain)

## Anti-Patterns (Avoid)
- Renaming endpoints or directories.
- Adding authentication/databases/WebSockets/queues.
- Changing `{ success, data, error }` response shape.
- Long-running chains that ignore cost ceilings.
- Re-introducing HLD/LLD nomenclature or adding multiple redundant view modes.

## Analysis Prompts

### Business Label Summarization (optional LLM assist)
"Given the following cluster summary (files, primary imports, centrality), provide a concise business-facing label and one-sentence purpose. Avoid implementation jargon."

Inputs: `files[]`, `top_imports[]`, `neighbors[]`, `sample_symbols[]`.

### Risk/Agent Detection Prompt
"Scan this file for AI agent usage (OpenAI/LangChain/Anthropic/etc.). If found, summarize purpose and business impact in one sentence; assign risk: high/medium/low."

