# AutoGraph – LLM-powered Hierarchical Codebase Graph Generator

## Overview
AutoGraph is a tool that automatically analyzes any given codebase and generates a dual-layer, navigable representation of its architecture — a high-level design (HLD) and low-level design (LLD) graph — where each component is treated as an entity with linked metadata.

## Project Status
Currently in **Phase 5: Advanced Graph Integration** - HLD-LLD connection visualization and interactive navigation 🔄

## Features
- **Static Codebase Analysis**: AST-based parsing for Python codebases
- **LLM-Powered Semantic Analysis**: Intelligent analysis using OpenAI GPT-4o-mini
- **Hierarchical Graph Generation**: HLD (modules, APIs, services) and LLD (components, functions, classes) representation
- **Rich Metadata**: Each node includes purpose, complexity, dependencies, and relationships
- **Multi-Format Export**: JSON, YAML, CSV, DOT, HTML, and Mermaid formats
- **Intelligent Caching**: Optimized performance with LLM response caching
- **Robust Fallback**: Graceful degradation when LLM is unavailable
- **Web Interface**: Interactive Flask-based web application
- **Real-time Analysis**: Live progress tracking and status updates
- **File Upload**: Drag-and-drop interface for codebase uploads
- **Export Management**: Easy access to all exported formats

## Installation
```bash
# Clone the repository
git clone <repository-url>
cd vc-one

# Install dependencies
pip install -r requirements.txt

# Set up environment (optional)
cp .env.example .env
# Edit .env with your OpenAI API key
```

## Usage

### Web Application (Recommended)
```bash
# Start the web application
python run_web.py

# Open your browser to: http://localhost:5000
# Upload a codebase and view the interactive graph
```

### Command Line (Legacy)
```bash
# Analyze a codebase
python -m src.main --codebase /path/to/your/codebase

# Output will be saved to /graph/ directory
```

## Project Structure
```
vc-one/
├── run_web.py                   # Main web application entry point
├── src/                         # Source code
│   ├── parser/                  # AST parsing and symbol extraction
│   ├── analyzer/                # Codebase analysis and traversal
│   ├── llm_integration/         # LLM-powered semantic analysis
│   ├── graph_builder/           # Graph construction and management
│   ├── export/                  # Multi-format export functionality
│   ├── visualization/           # Graph visualization components
│   ├── config/                  # Configuration management
│   ├── web/                     # Flask web application
│   └── utils/                   # Utilities and helpers
├── tests/                       # Test suite
├── graph/                       # Output directory for generated graphs
├── logs/                        # Application logs
├── cache/                       # LLM response caching
└── examples/                    # Sample codebases for testing
```

## Development Phases
- **Phase 1**: Foundation - Basic parsing and symbol extraction ✅
- **Phase 2**: Analysis Engine - LLM integration and semantic analysis ✅
- **Phase 3**: Graph Builder - Hierarchical graph construction ✅
- **Phase 4**: Web Integration - Flask web application ✅
- **Phase 5**: Advanced Graph Integration - HLD-LLD connection visualization 🔄
- **Phase 6**: Enhanced Visualization - Professional graph rendering
- **Phase 7**: Mobile and Accessibility - Mobile-friendly interface

## Current Achievements

### Performance Metrics
- **59 nodes, 1288 edges** generated from sample calculator app
- **15 files analyzed** with 57.7% coverage (normal for small codebase)
- **100% LLM cache hit rate** for repeated analyses
- **<30 seconds** processing time for typical codebases
- **<500MB** memory usage for standard analysis

### Technical Features
- ✅ **End-to-End Pipeline**: Complete analysis from upload to visualization
- ✅ **LLM Integration**: Semantic analysis with intelligent caching
- ✅ **Multi-Format Export**: 6 different output formats
- ✅ **Web Interface**: Functional and responsive Flask application
- ✅ **Real-time Analysis**: Live progress tracking
- ✅ **File Upload**: Working drag-and-drop interface
- ✅ **Graph Visualization**: Basic HLD/LLD node display with improved spacing

## Upcoming Features (Phase 5)

### HLD-LLD Connection Visualization
- **Interactive Navigation**: Click HLD nodes to reveal connected LLD components
- **Metadata-Driven Relationships**: Enhanced edge visualization using existing metadata
- **Graph Layout Engine**: Professional positioning and edge rendering algorithms
- **Zoom and Navigation**: Functional zoom in/out and graph exploration
- **Edge Visualization**: Display relationship lines between connected nodes

### Enhanced User Experience
- **Connected Graph Display**: Visual representation of HLD-LLD relationships
- **Interactive Node Exploration**: Click-to-expand functionality for hierarchical navigation
- **Professional Layout**: D3.js or similar library integration for proper graph positioning
- **Smooth Interactions**: Responsive design and fluid animations

## Configuration

### Environment Variables
Create a `.env` file with the following variables:
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# LLM Analysis Configuration
LLM_ENABLED=true
LLM_CACHE_ENABLED=true
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.1
LLM_DISABLE_FOR_TESTING=false
```

## Contributing
Please read the `Software_Requirements.md` for detailed development guidelines and safety practices.

### Key Development Principles
- **File Preservation**: Never delete working files, use version suffixes for experiments
- **Safety First**: Always validate inputs and handle errors gracefully
- **Performance**: Cache LLM responses and optimize for large codebases
- **User Experience**: Focus on intuitive interfaces and clear feedback

## Testing
```bash
# Run all tests
python -m pytest tests/

# Run integration tests
python test_integration.py

# Test web application
python run_web.py
# Then upload a sample codebase in the browser
```

## Export Formats
AutoGraph supports multiple export formats:
- **JSON**: Structured data for programmatic access
- **YAML**: Human-readable configuration format
- **CSV**: Tabular data for analysis tools
- **DOT**: Graphviz-compatible format
- **HTML**: Web-based interactive viewer
- **Mermaid**: Markdown-compatible diagrams

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: AutoGraph is designed to help engineers understand codebases better through visual navigation and hierarchical analysis. The tool focuses on accuracy and usefulness over fancy features, providing practical value for development teams. 