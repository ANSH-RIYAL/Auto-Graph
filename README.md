# AutoGraph – LLM-powered Hierarchical Codebase Graph Generator

## Overview
AutoGraph is a tool that automatically analyzes any given codebase and generates a dual-layer, navigable representation of its architecture — a high-level design (HLD) and low-level design (LLD) graph — where each component is treated as an entity with linked metadata.

## Project Status
Currently in **Phase 1: Foundation** - Basic file parser and symbol extraction

## Features
- **Static Codebase Analysis**: AST-based parsing for Python codebases
- **Hierarchical Graph Generation**: HLD (modules, APIs, services) and LLD (components, functions, classes) representation
- **Rich Metadata**: Each node includes purpose, complexity, dependencies, and relationships
- **JSON Export**: Structured, queryable graph data for programmatic access

## Installation
```bash
# Clone the repository
git clone <repository-url>
cd autograph

# Install dependencies
pip install -r requirements.txt
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
- **Phase 2**: Analysis Engine - LLM integration and classification
- **Phase 3**: Graph Builder - Hierarchical graph construction
- **Phase 4**: Testing & Refinement - Performance optimization

## Contributing
Please read the `Software_Requirements.md` for detailed development guidelines and safety practices. 