# Software Requirements Specification (SRS)
## AutoGraph – Agent-Aware Hierarchical Codebase Graph Generator (HLD + LLD)

### Project Purpose
Create a tool that automatically analyzes any given codebase and generates a dual-layer, navigable representation of its architecture — a high-level design (HLD) and low-level design (LLD) graph — where each component is treated as an entity with linked metadata. **AutoGraph is specifically designed for enterprise teams using AI agents, providing agent-aware architectural visualization and explainability for compliance and debugging.**

**Ultimate Vision**: This will become an HLD-LLD creation engine that can be paired with agents like Cursor to provide engineers with a visual way to view HLD graphs on their phones, zoom into LLD parts, and click on LLD components to navigate to exact code locations. This will be invaluable for PM-Engineering discussions and code navigation.

**Current Scope**: Web-based interactive codebase analysis with real-time graph visualization, multi-format export capabilities, and agent-aware audit mode for enterprise compliance.

---

## 🧩 Functional Requirements

### 1. Input Processing
- **Primary**: Local codebase path or GitHub URL
- **Web Interface**: File upload with drag-and-drop support
- **Optional**: Configuration parameters (exclude test files, specific file types, etc.)
- **Validation**: Must verify codebase exists and is accessible

### 2. Output Generation
- **Primary**: Programmatic JSON graph representing HLD + LLD entities and relationships
- **Web Display**: Interactive graph visualization in browser
- **Multi-Format Export**: JSON, YAML, CSV, DOT, HTML, and Mermaid formats
- **Storage**: Separate `/graph/` directory, never overwrite original codebase

### 3. Core Features

#### 3.1 Codebase Ingestion
- Traverse file system, identify relevant source files
- Categorize into: frontend/backend/modules/test/config/etc.
- Generate file inventory with metadata (size, type, last modified)
- Support for ZIP file uploads and extraction

#### 3.2 Structure Extraction
- Parse files for classes, functions, imports, and relationships
- Generate symbol maps and dependency chains
- Extract function signatures, class hierarchies, import statements
- Handle multiple programming languages (Python, JavaScript, Go, etc.)

#### 3.3 Semantic Labeling (LLM-Powered)
- Identify purpose and responsibility of each file/module using LLM
- Classify as HLD (e.g., service layer, API, database client) or LLD (e.g., handler functions, utility classes, components)
- Extract business logic context and module relationships
- Intelligent caching to reduce API costs and improve performance

#### 3.4 Hierarchical Graph Construction
**HLD Nodes**: Modules, APIs, Database Clients, Service Layers
**LLD Nodes**: Components, Functions, Classes, Utilities
**Edge Types**: 
- Dependency (uses)
- Containment (has child)
- Communication (calls, imports)
- Data flow (passes data to)

#### 3.5 Web Interface
- **Real-time Analysis**: Live progress tracking and status updates
- **Interactive Visualization**: HLD/LLD graph display with node spacing
- **File Upload**: Drag-and-drop interface for codebase uploads
- **Analysis Logs**: Real-time display of processing steps
- **Export Management**: Easy access to all exported formats
- **Audit Mode Toggle**: Switch between standard and agent-aware views

#### 3.6 Graph Export
Each node includes:
- Unique ID, Name, Type, Level (HLD/LLD)
- File paths, Line numbers
- Children/Parents relationships
- Metadata (complexity, dependencies, purpose)

#### 3.7 Agent Detection & Audit Mode
- **Agent Usage Detection**: Identify AI agent invocation patterns (OpenAI, LangChain, Anthropic, etc.)
- **Agent Context Analysis**: Extract business purpose and risk level of agent-touched components
- **Audit Mode Visualization**: Filter and highlight agent-touched components in graph view
- **Compliance Export**: Generate audit reports for enterprise compliance (SOC2, HIPAA, etc.)
- **Risk Assessment**: Categorize agent components by business risk level (high/medium/low)
- **Business Context Extraction**: Use LLM to explain business impact of agent decisions

---

## 🎯 Success Metrics & Quality Criteria

### Coverage Metrics
- **File Coverage**: ≥95% of source files successfully parsed
- **Function Coverage**: ≥90% of functions/classes identified
- **Relationship Coverage**: ≥85% of import/dependency relationships captured

### Accuracy Metrics
- **Classification Accuracy**: ≥80% of HLD/LLD classifications match human expert assessment
- **Relationship Accuracy**: ≥85% of identified relationships are correct
- **Metadata Completeness**: ≥90% of nodes have complete metadata
- **Agent Detection Accuracy**: ≥90% of agent invocation points identified correctly
- **Risk Assessment Accuracy**: ≥80% of risk levels match manual review

### Performance Metrics
- **Processing Speed**: ≤30 seconds for 100 files
- **Memory Usage**: ≤500MB for typical codebase (1000 files)
- **Output Size**: Graph JSON ≤10MB for typical codebase
- **Web Response Time**: ≤2 seconds for graph display

### Validation Criteria
- **Consistency**: No orphaned nodes (all nodes must have at least one relationship)
- **Completeness**: All identified functions/classes must have corresponding LLD nodes
- **Hierarchy**: All LLD nodes must have parent HLD nodes

---

## 🛠 Implementation Guidelines for Cursor AI

### ✅ CRITICAL: Project Preservation Rules
**NEVER DELETE OR MODIFY THESE FILES:**
- `Software_Requirements.md` (this document)
- `README.md` (project overview)
- `project_structure.txt` (file organization)
- `Project goals.txt` (original vision)
- Any existing working modules

**ALWAYS:**
- Create new files in appropriate directories
- Use version suffixes for experimental files (e.g., `parser_v2.py`)
- Keep original files as backup (e.g., `parser_backup.py`)
- Document all changes in `CHANGELOG.md`

### ✅ Development Safety Practices
1. **State Management**: Use explicit, typed schemas for all data structures
2. **Error Handling**: Skip unparseable files with warnings, never crash
3. **Output Isolation**: All outputs go to `/graph/` directory
4. **Logging**: Maintain detailed logs in `/logs/` directory
5. **Testing**: Create test cases for each module before integration
6. **Web Safety**: Validate all file uploads and prevent path traversal attacks

### ✅ Current Project Structure
```
vc-one/
├── Software_Requirements.md (THIS FILE - NEVER DELETE)
├── README.md
├── CHANGELOG.md
├── project_structure.txt
├── Project goals.txt
├── run_web.py (MAIN ENTRY POINT)
├── src/
│   ├── parser/
│   ├── analyzer/
│   ├── llm_integration/
│   ├── graph_builder/
│   ├── export/
│   ├── visualization/
│   ├── config/
│   ├── web/ (FLASK APPLICATION)
│   └── utils/
├── tests/
├── graph/ (output directory)
├── logs/
└── examples/
```

### ✅ Agent-Aware Feature Implementation
**NEW MODULES TO ADD:**
```
src/
├── agent_detection/           # NEW: Agent detection and analysis
│   ├── __init__.py
│   ├── agent_detector.py      # Detect AI agent usage patterns
│   ├── risk_assessor.py       # Assess business risk of agent components
│   └── context_extractor.py   # Extract business context of agent usage
├── observability/             # NEW: Audit and compliance features
│   ├── __init__.py
│   ├── audit_mode.py          # Audit mode functionality
│   ├── compliance_reporter.py # Generate compliance reports
│   └── business_context.py    # Business context analysis
```

**EXISTING MODULES TO ENHANCE:**
- `src/llm_integration/semantic_analyzer.py`: Add agent detection to existing analysis
- `src/graph_builder/enhanced_graph_builder.py`: Add agent metadata to graph nodes
- `src/export/enhanced_exporter.py`: Add audit report export functionality
- `src/web/flask_app.py`: Add audit mode toggle and agent visualization
- `src/web/static/js/app.js`: Add audit mode UI controls

### ⚠️ Common Agent Mistakes to Avoid
1. **File Deletion**: Never delete existing working code when debugging
2. **Scope Creep**: Stick to current phase, don't jump to advanced features yet
3. **Silent Failures**: Always log errors and provide meaningful error messages
4. **Hardcoded Paths**: Use relative paths and configuration files
5. **Memory Issues**: Process files sequentially, avoid loading entire codebase into memory
6. **LLM Overuse**: Cache LLM responses, don't re-analyze unchanged files
7. **Web Security**: Always validate file uploads and prevent XSS attacks
8. **Agent Detection Overreach**: Focus on clear agent patterns, avoid false positives

---

## 🔄 Development Phases

### Phase 1: Foundation ✅ COMPLETED
- [x] Project structure setup
- [x] Basic file parser (AST-based)
- [x] Symbol extraction (functions, classes, imports)
- [x] Simple JSON output structure

### Phase 2: Analysis Engine ✅ COMPLETED
- [x] LLM integration for semantic analysis
- [x] HLD/LLD classification logic
- [x] Relationship mapping
- [x] Graph node/edge construction

### Phase 3: Graph Builder ✅ COMPLETED
- [x] Hierarchical graph construction
- [x] Metadata enrichment
- [x] Graph validation and consistency checks
- [x] Export functionality

### Phase 4: Web Integration ✅ COMPLETED
- [x] Flask-based web application
- [x] File upload and analysis interface
- [x] Real-time progress tracking
- [x] Interactive HLD/LLD graph visualization
- [x] Frontend-backend synchronization
- [x] Node spacing and layout improvements

### Phase 5: Agent-Aware Analysis 🔄 CURRENT PHASE
- [ ] **Agent Detection Module**: Detect AI agent usage patterns in code
- [ ] **Risk Assessment**: Categorize agent components by business risk level
- [ ] **Business Context Extraction**: Extract business purpose of agent components
- [ ] **Enhanced Metadata**: Add agent context to existing graph nodes
- [ ] **Audit Mode Toggle**: Add UI control for agent-aware view
- [ ] **Agent Visualization**: Highlight agent-touched components in graph

### Phase 6: Audit Mode & Compliance ✅ NEXT PHASE
- [ ] **Audit Mode Interface**: Filter view to show only agent-touched components
- [ ] **Compliance Reporting**: Generate audit reports for enterprise compliance
- [ ] **Risk Assessment Export**: Export risk analysis for stakeholders
- [ ] **Business Context Reports**: Generate business impact documentation
- [ ] **Executive Summary**: Create high-level audit summaries for PMs/CTOs

### Phase 7: Advanced Graph Integration (Future)
- [ ] **HLD-LLD Connection Visualization**: Implement the core vision of connected hierarchical graphs
- [ ] **Interactive Navigation**: Click HLD nodes to reveal connected LLD components
- [ ] **Metadata-Driven Relationships**: Use existing metadata to create meaningful connections
- [ ] **Graph Layout Engine**: Proper positioning and edge rendering
- [ ] **Zoom and Navigation**: Functional zoom in/out and graph exploration
- [ ] **Edge Visualization**: Display relationship lines between connected nodes

### Phase 8: Enhanced Visualization (Future)
- [ ] Professional graph rendering (D3.js or Cytoscape.js)
- [ ] Advanced interactions (drag, drop, expand, collapse nodes)
- [ ] Search and filter functionality
- [ ] Export to visual formats (PNG, SVG, PDF)

### Phase 9: Mobile and Accessibility (Future)
- [ ] Mobile-friendly interface
- [ ] Touch interactions (swipe, pinch-to-zoom, tap navigation)
- [ ] Accessibility features (screen reader support, keyboard navigation)

---

## 📊 Example Output Schema

```json
{
  "metadata": {
    "codebase_path": "/path/to/codebase",
    "analysis_timestamp": "2024-01-15T10:30:00Z",
    "file_count": 150,
    "coverage_percentage": 96.5,
    "agent_components": 12,
    "high_risk_components": 3
  },
  "nodes": [
    {
      "id": "module_api",
      "name": "API Layer",
      "type": "Module",
      "level": "HLD",
      "files": ["api/routes/user.js", "api/routes/auth.js"],
      "children": ["component_userController", "component_authController"],
      "metadata": {
        "purpose": "Handles HTTP requests and routing",
        "complexity": "medium",
        "dependencies": ["express", "middleware"],
        "agent_touched": false,
        "risk_level": "low"
      }
    },
    {
      "id": "component_ai_classifier",
      "name": "AI Customer Classifier",
      "type": "Component",
      "level": "LLD",
      "files": ["services/ai_classifier.py"],
      "functions": ["classify_customer", "process_risk"],
      "parent": "module_ai_services",
      "metadata": {
        "purpose": "AI-powered customer risk classification",
        "complexity": "high",
        "line_count": 120,
        "agent_touched": true,
        "agent_types": ["openai", "langchain"],
        "risk_level": "high",
        "business_impact": "Customer credit decisions",
        "agent_context": "Uses GPT-4 to classify customer risk based on transaction history"
      }
    }
  ],
  "edges": [
    {
      "from": "module_api",
      "to": "component_userController",
      "type": "contains",
      "metadata": {
        "relationship_type": "hierarchy"
      }
    }
  ]
}
```

---

## 🧠 LLM Integration Guidelines

### Prompt Templates
Use structured prompts like:
```
"Given this file and its function list, analyze its role in the system:
1. What is the primary purpose of this file?
2. Is this a high-level module (HLD) or low-level component (LLD)?
3. What other modules/components does it interact with?
4. What is its complexity level (low/medium/high)?
5. Does this file use AI agents (OpenAI, LangChain, Anthropic, etc.)?
6. If yes, what business decisions does the AI make?
7. What is the business impact if this AI component fails?

File: {file_path}
Functions: {function_list}
Imports: {import_list}"
```

### Agent Detection Prompts
```
"Analyze this code for AI agent usage:
1. Identify any AI agent libraries or APIs used (OpenAI, LangChain, Anthropic, etc.)
2. What business logic does the AI control?
3. What data does the AI process?
4. What is the risk level if this AI fails (high/medium/low)?
5. How would you explain this to a compliance officer?

Code: {file_content}"
```

### Caching Strategy
- Cache LLM responses by file hash
- Re-analyze only when files change
- Store responses in `/cache/` directory
- Implement cache invalidation for updated files

---

## 🌐 Web Interface Requirements

### User Experience
- **Intuitive Upload**: Drag-and-drop file upload with progress indication
- **Real-time Feedback**: Live analysis progress and status updates
- **Interactive Graphs**: Clickable nodes with detailed information
- **Export Options**: Easy access to all export formats
- **Responsive Design**: Works on desktop and tablet devices
- **Audit Mode Toggle**: Easy switch between standard and agent-aware views
- **Agent Highlighting**: Clear visual distinction of agent-touched components

### Technical Requirements
- **Flask Backend**: Python web framework for API and file serving
- **Static Assets**: CSS and JavaScript served directly from Flask
- **File Upload**: Secure file handling with validation
- **Session Management**: Track analysis sessions and results
- **Error Handling**: Graceful error display and recovery
- **Audit Mode API**: Backend support for agent-aware filtering and export

---

## 🎯 Success Validation

### Test Codebases
1. **Simple API**: 5-10 files, basic CRUD operations
2. **Medium App**: 50-100 files, multiple modules
3. **Complex System**: 200+ files, microservices architecture
4. **AI-Enhanced System**: Codebase with OpenAI/LangChain integration

### Validation Checklist
- [x] All files processed without errors
- [x] Graph structure is consistent and complete
- [x] HLD/LLD classifications make sense
- [x] Relationships accurately reflect code structure
- [x] Performance meets specified metrics
- [x] Output is human-readable and well-structured
- [x] Web interface is functional and responsive
- [x] File upload and analysis work end-to-end
- [ ] Agent detection accurately identifies AI components
- [ ] Risk assessment matches manual review
- [ ] Audit mode provides clear agent-focused view
- [ ] Compliance reports meet enterprise requirements

---

## 📝 Notes for Cursor AI Development

**Remember**: This is a tool for engineers and PMs to understand codebases better, especially those using AI agents. Focus on accuracy and usefulness over fancy features. The goal is to create something that actually helps teams navigate and understand their AI-enhanced code, not just look impressive.

**Key Principle**: If you're unsure about a design decision, prioritize safety and robustness over cleverness. It's better to have a working, simple solution than a complex, broken one.

**Debugging Strategy**: When things go wrong, check the logs first, then the graph output, then the individual parser results. Don't delete files - create new versions and compare.

**Web Development**: The Flask application should be simple and functional. Focus on making the graph visualization work properly before adding advanced features.

**Agent Detection**: Focus on clear, reliable agent detection patterns. Avoid false positives that could confuse users.

**Audit Mode Priority**: The audit mode should provide clear business value - helping PMs understand AI risk exposure and compliance requirements.

**Success Definition**: The tool successfully generates a meaningful, accurate graph representation of a codebase that a PM can use to understand AI architecture, assess risks, and generate compliance documentation through an intuitive web interface. 