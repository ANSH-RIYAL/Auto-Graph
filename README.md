# AutoGraph – LLM-powered Hierarchical Codebase Graph Generator

## Overview
AutoGraph is a tool that automatically analyzes any given codebase and generates a dual-layer, navigable representation of its architecture — a high-level design (HLD) and low-level design (LLD) graph — where each component is treated as an entity with linked metadata.

## Project Status
Currently in **Phase 2: Analysis Engine** - LLM integration and semantic analysis ✅

## Features
- **Static Codebase Analysis**: AST-based parsing for Python codebases
- **LLM-Powered Semantic Analysis**: Intelligent analysis using OpenAI GPT-4o-mini
- **Hierarchical Graph Generation**: HLD (modules, APIs, services) and LLD (components, functions, classes) representation
- **Rich Metadata**: Each node includes purpose, complexity, dependencies, and relationships
- **Multi-Format Export**: JSON, YAML, CSV, DOT, HTML, and Mermaid formats
- **Intelligent Caching**: Optimized performance with LLM response caching
- **Robust Fallback**: Graceful degradation when LLM is unavailable

## Installation
```bash
# Clone the repository
git clone <repository-url>
cd autograph

# Install dependencies
pip install -r requirements.txt

# Set up environment (optional)
cp env_template.txt .env
# Edit .env with your OpenAI API key
```

## Usage
```bash
# Analyze a codebase
python -m src.main --codebase /path/to/your/codebase

# Output will be saved to /graph/ directory
```

## Project Structure
```
autograph/
├── src/                    # Source code
│   ├── parser/            # AST parsing and symbol extraction
│   ├── analyzer/          # Codebase analysis and traversal
│   ├── models/            # Data models and schemas
│   └── utils/             # Utilities and helpers
├── tests/                 # Test suite
├── graph/                 # Output directory for generated graphs
├── logs/                  # Application logs
├── cache/                 # LLM response caching
└── examples/              # Sample codebases for testing
```

## Development Phases
- **Phase 1**: Foundation - Basic parsing and symbol extraction ✅
- **Phase 2**: Analysis Engine - LLM integration and semantic analysis ✅
- **Phase 3**: Graph Builder - Hierarchical graph construction ✅
- **Phase 4**: API Layer - REST/GraphQL interface for graph querying
- **Phase 5**: Testing & Refinement - Performance optimization

## Contributing
Please read the `Software_Requirements.md` for detailed development guidelines and safety practices. 