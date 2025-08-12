# AutoGraph — Canonical Graphs for Real Codebases

## Overview
AutoGraph analyzes a repository and emits two artifacts:
- AST graph: exhaustive, low-level implementation structure
- Visualization graph (BSI): Business/System/Implementation view with deterministic positions and structured metadata for PM/consultant readability

## Project Status
Focusing on core extraction and representation using `vizro-core` as the target. UI is minimal; no extra exports/tests until the graph JSONs are stable.

## What the VIZ graph guarantees
- Levels: BUSINESS (1 band), SYSTEM (3 bands), IMPLEMENTATION (8 bands)
- Edge types: `contains`, `depends_on`, `calls`
- Positions: absolute preset layout; 12 y-anchors embedded in `metadata.layout`
- Metadata: structured module facts for nodes; edge `intent` with examples
- Externals: explicit nodes (User, External_API, LLM_Service, Auth_Provider, etc.)

## Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Optional: set OPENAI_API_KEY for enrichment
```

## Usage
### Web Application
```bash
# Start the web application
python run_web.py

# Open http://localhost:5000 and upload a codebase (try vizro-core)
```

### Outputs
- `graph/<project>/exports/ast_graph.json`
- `graph/<project>/exports/viz_graph.json`

## Project Structure
```
Auto-Graph/
├── run_web.py                   # Main web application entry point
├── src/                         # Source code
│   ├── parser/                  # AST parsing and symbol extraction
│   ├── analyzer/                # Codebase analysis and traversal
│   ├── llm_integration/         # LLM-powered semantic analysis
│   ├── graph_builder/           # Graph construction and management
│   ├── export/                  # JSON export (others deferred)
│   ├── visualization/           # Graph visualization helpers
│   ├── config/                  # Configuration management
│   ├── web/                     # Flask web application
│   └── utils/                   # Utilities and helpers
├── tests/                       # Test suite
├── graph/                       # Output directory for generated graphs
├── logs/                        # Application logs
├── cache/                       # LLM response caching
└── examples/                    # Sample codebases for testing
```

## Roadmap (condensed)
- Phase A: Stable positions embedded in VIZ export
- Phase B: Module facts + externals + edge intents populated
- Phase C: System-level depends_on rollups; raw calls only at implementation
- Phase D: Schema-locked LLM summaries for Business/System nodes

## Notes
- HLD/LLD is a peer view produced by HLDBuilder from our AST/VIZ exports. It is not the old legacy mode.

## Upcoming Features (Phase 5)

### Enhanced Business Intelligence
- **Executive Dashboard**: High-level business metrics and KPI tracking
- **Stakeholder Reports**: Customized reports for different business roles
- **Risk Trend Analysis**: Historical risk assessment and trend identification
- **Compliance Monitoring**: Real-time compliance status tracking
- **Business Impact Mapping**: Visual representation of component business value

### Advanced Analytics
- **Predictive Risk Modeling**: AI-powered risk prediction for new components
- **Cost-Benefit Analysis**: Business impact assessment for architectural decisions
- **Team Performance Metrics**: Development team efficiency and productivity tracking
- **Strategic Planning Tools**: Long-term architecture planning and roadmapping

## Configuration
- `OPENAI_API_KEY`: optional; enables schema-locked enrichment for Business/System node summaries.

## Use Cases
- PM/Consultant overview (VIZ graph)
- Engineer drill-down (AST graph + Implementation layer)

## Contributing
Please read the `Software_Requirements.md` for detailed development guidelines and safety practices.

### Key Development Principles
- **Business Value First**: Focus on features that provide clear business impact
- **User Experience**: Design for non-technical stakeholders while maintaining technical depth
- **Compliance Ready**: Ensure all features support enterprise compliance requirements
- **Performance**: Optimize for large enterprise codebases and real-time analysis

## Quick test
Upload `vizro-core` and verify the export files under `graph/vizro-core/exports/`.

## Export
- JSON only (canonical)

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: AutoGraph bridges the gap between technical implementation and business strategy. It transforms complex codebases into actionable business intelligence, making technical complexity accessible to business stakeholders while providing the depth engineers need for effective decision-making. 