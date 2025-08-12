# FOUNDATION

## Build Philosophy
- **Simplicity First**: Minimal stack (Flask + HTML/CSS/JS). Prefer straightforward, human-readable code.
- **Stable Evolution**: Add capability without breaking existing flows. Backward-compatible graph schema changes only.
- **Single Canonical Graph**: One JSON graph that supports multiple views via filters; no duplicated "modes".
- **Performance Conscious**: Basic caching, graceful degradation to AST-only if LLM/tools unavailable.
- **File Preservation**: Never mutate analyzed repos; write outputs to dedicated directories.
- **Human-Legible Outputs**: Structures designed for skimmability and business consumption.
- **Debug-First**: Logs and golden samples precede heavy test harnessing during iteration.

## Roles & Division of Labor
- **Cursor**: Backend logic, parsers, clustering, graph construction, API.
- **Replit**: Frontend (HTML/CSS/JS), forms, graph visualization, UX.
- **ChatGPT**: Project scoping, prompt refinement, doc grooming.

## Invariants (Do Not Change)
- **Response schema**: `{ success, data, error }` for all JSON endpoints.
- **Endpoints**: `/api/analysis/upload`, `/api/analysis/<id>/status`, `/api/analysis/<id>/graph`, `/api/analysis/<id>/logs`, `/api/download/<format>`.
- **Progress**: Polling-based status updates (no WebSockets).
- **LLM Access**: Single client with retries, backoff, caching, and fallback.
- **Directory Names**: Keep established module folders and file names stable.
- **Non-Goals**: No auth/DB/WebSockets/queues/custom ML in core variant.
- **View Contract**: UI renders a single preset-layout graph with filters. HLD/LLD is a peer view consumed via exports (not a separate in-app mode).

## Decision Log (Terse)
Use `YYYY-MM | Decision | Why | Status(Immutable/Tentative)`
- `2024-01 | Flask + HTML/CSS/JS stack | simplest viable | Immutable`
- `2024-01 | Polling for progress | simpler than WS | Immutable`
- `2024-01 | Single LLM client + cache | cost/latency control | Immutable`
- `2025-08 | Replace HLD/LLD with Business/System/Implementation (BSI) | clearer abstraction, fewer modes | Immutable`
- `2025-08 | One canonical graph + filters | reduce complexity, improve reliability | Immutable`
- `2025-08 | Cluster system level via import/call graphs | practical, static-analysis-first | Tentative`
- `2025-08 | Enrich with Radon metrics | lightweight utility | Tentative`

## Data Handling Policy
- **Allowed to LLM**: Non-sensitive code/text needed for analysis; redact secrets/API keys.
- **Redaction**: Mask `.env`, credentials, tokens, private keys, and obvious secrets before sending.
- **Retention**: Cache TTL default 24h; cache is file-based and purgeable.
- **Local-Only Mode**: If LLM disabled, run AST-only and annotate `stage: "fallback_ast"`.
- **Access Keys**: Scope keys to analysis-only usage; never persist keys in logs/exports.

## Output Goals
- **AST graph** and **VIZ graph** as export-grade JSONs.
- **Layout**: 12 anchors, bands 1/3/8, positions embedded.
- **Edge Types**: `contains`, `depends_on`, `calls`.
- **Metadata**: node module facts; edge intents with examples.
- **UX**: Upload → progress → results → export (preset layout).

## Canonical Graph Principles
- Each node has `level ∈ {BUSINESS, SYSTEM, IMPLEMENTATION}` and `technical_depth ∈ {1,2,3}`.
- Aggregation only upward (Implementation → System → Business) via `contains` edges.
- Dependency and call edges may exist at any level; UI can show/hide them by type.
- Backward compatibility: legacy `HLD/LLD` values map to `BUSINESS/IMPLEMENTATION` at load time.



IMPORTANT POINTS CONSIDER ONE BY ONE


I like it but I need you to increase the spacing between the Business and system level nodes

also we need to work on the connections now
I don't like how all business modules only have 'contains' type edges and all implementation modules only have 'calls' 
I mean if that is the only valid kind then why give it as an option to select why not just use them as their defaults and then people can just adjust the slider between business sytem and implementation to adjust the level of depth they want to see

one way to cut down connections is to remove the ones between a business level module and the implementation level ones if they are connected through a system level one in the middle

I also need you to increase the number of colors included in our pallete so that we have different colors

feel free to use this conversation I had with chatgpt earlier -

* Nodes at different levels have distinct, visually separable palettes.
* Nodes within the same level have color variations without becoming chaotic.
* Edge colors change based on **connection type** ("call", "contains", "depends on") while remaining legible in dense graphs.
* This works for potentially *thousands* of connections without eye strain.

---

## **Node Color Scheme**

### Principles

* **High level modules**: Saturated but not neon; fewer modules so stronger distinction is fine.
* **Mid level modules**: Muted variants of the high-level hues, still distinguishable.
* **Low level modules**: Light/desaturated variants to reduce visual overload.
* Within a level: use hue shifts of \~30° in color wheel to separate but keep within a family.

---

### **Nodes (by level)**

| Level      | Base Hues (Hex)                                                                              | Example Shades (variation across modules)                   |
| ---------- | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| High-Level | `#1F77B4` (blue), `#FF7F0E` (orange), `#2CA02C` (green), `#D62728` (red), `#9467BD` (purple) | Darker/lighter tints per module: `#145A86`, `#418FBE`, etc. |
| Mid-Level  | Derived from high-level, \~20% desaturation, +10 lightness                                   | e.g., from blue: `#4A90C2`, `#5FA1CC`                       |
| Low-Level  | Pastel/desaturated variants (\~40% desaturation, +25 lightness)                              | e.g., from blue: `#A6C8E8`, `#BBD7F0`                       |

---

**Example Node Palette**

```js
{
  high:  ["#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD"],
  mid:   ["#4A90C2", "#FFAA52", "#5FAF5F", "#E45555", "#A07BC0"],
  low:   ["#A6C8E8", "#FFD6A3", "#B6E2B6", "#F5B6B6", "#D4B8E6"]
}
```

Each hue gets 3 levels: **high** → **mid** → **low**.

---

## **Edge Color Scheme**

### Connection Types

* **Call** → functional / active link → strong blue
* **Contains** → structural / hierarchical → green
* **Depends On** → dependency / prerequisite → orange

Within each type:

* **High-Level edges**: fully saturated color
* **Mid-Level edges**: slightly muted
* **Low-Level edges**: lightest

---

**Example Edge Palette**

```js
{
  call: {
    high: "#007AFF", // vivid blue
    mid:  "#4DA3FF", // lighter blue
    low:  "#A3D0FF"  // pastel blue
  },
  contains: {
    high: "#28A745", // vivid green
    mid:  "#5BC66B",
    low:  "#A8E0B2"
  },
  depends_on: {
    high: "#FF9500", // vivid orange
    mid:  "#FFB84D",
    low:  "#FFD9A3"
  }
}
```

---

## **Usage in Large Graphs**

* **Level perception** comes from **lightness/saturation differences**, not just hue.
* **Connection perception** comes from **hue category** (blue/green/orange).
* You avoid random chaos but still have per-module variation via tint shifts.






don't forget the next steps you yourself told me

also instead of statically fixing the position of the business and system level modules I would rather us fix the total x range of positions of the implementation modules and then adjust the business and system level ones to remain spread out

also for the implementation level, are you sure there are supposed to be that many modules? if you are then don't change anything about it except maybe ensuring that the positions are decided in a way that no 2 modules can overlap with each other

I also discussed this for a revamping of the structure we are using or the terms we are using and trying to compare against in the BSI view


what is the term that consultants like Korn Ferry and McKinsey and Accenture etc. use which is similar to HLD/LLD in Engineering?
like a graph which they use to explain the product structure when selling a product or something to a new client etc.


I am making a codebase visualization tool and I want to use the same language and format and structures that they use


ChatGPT said:
What you’re describing — the consulting-world equivalent of HLD (High-Level Design) and LLD (Low-Level Design) — isn’t usually called that in their world.
Firms like McKinsey, Accenture, Korn Ferry tend to use business-friendly or strategy-friendly language, even when they’re describing technical architectures.

The closest equivalents you’ll see are terms like:

1. Operating Model Diagram
Purpose: Shows how the business functions at a macro level — capabilities, processes, org units, and sometimes tech systems.

Analogy to HLD: Similar to a high-level system architecture, but framed around business capabilities instead of modules/classes.

Format: Usually boxes for capabilities, swimlanes for processes, and arrows for flows.

Example: “Digital Banking Operating Model” diagram showing channels, core systems, and customer touchpoints.

2. Solution Architecture / Conceptual Architecture
Purpose: Shows the conceptual technology stack and major integration points, without going into code-level detail.

Analogy: This is their “HLD” in tech-heavy engagements.

Format: Layers (e.g., Presentation Layer → Integration Layer → Data Layer) with labeled components and arrows.

Example: “Omnichannel Retail Solution Architecture” showing POS, CRM, Data Warehouse, APIs.

3. Capability Map / Capability Model
Purpose: Business-first view of what the organization can do, often mapped to the systems or products that enable each capability.

Analogy: Think of it like a module dependency diagram, but for business capabilities.

Format: Nested boxes grouped by domains (e.g., “Customer Management” → “Loyalty Program” → “Rewards Redemption Engine”).

Example: A retail capability map with technology enablers tagged to each capability.

4. Value Chain / Value Stream Map
Purpose: Shows the flow of value from input to customer delivery, often overlaying where different systems/products fit in.

Analogy: Similar to a system sequence diagram in engineering.

Format: Horizontal chain from left to right; sometimes with swimlanes for people/process/tech.

5. Process Flow (BPMN, Swimlanes)
Purpose: Describes how something happens step-by-step, and where systems interact.

Analogy: More like LLD sequence diagrams.

Example: Onboarding workflow with API calls shown between internal CRM and external KYC provider.

💡 Why this matters for your tool
If you want your codebase visualization to “speak” to consulting clients, you’d probably get the most buy-in if you:

Present two layers:

Capability / Operating Model view (business language, grouping code modules into “capabilities” or “functions”)

Solution Architecture view (tech stack components + integrations, mapped from your analysis)

Avoid engineering acronyms (HLD/LLD) in the client-facing view — use Conceptual Architecture or Solution Blueprint instead.

If you want, I can give you a hybrid diagram structure that maps directly from a codebase to the kind of Operating Model → Solution Architecture diagram McKinsey or Accenture would present. That would let you use their language and format but keep the underlying tech fidelity.









