# LLM Integration for AutoGraph

## Overview
AutoGraph now includes LLM (Large Language Model) integration for enhanced semantic analysis of code components. This feature provides intelligent, context-aware analysis of code files to determine their purpose, complexity, and relationships.

## Features

### ✅ **What's Implemented**
- **OpenAI Integration**: Uses GPT-4o-mini for semantic analysis
- **Intelligent Caching**: Caches LLM responses to avoid repeated API calls
- **Fallback Analysis**: Graceful degradation when LLM is unavailable
- **Robust Error Handling**: Continues analysis even if some files fail
- **Configuration Management**: Environment-based configuration

### 🎯 **Analysis Capabilities**
The LLM analyzes each code file to determine:
- **Purpose**: What the component does in the system
- **Level**: HLD (High-Level Design) or LLD (Low-Level Design)
- **Component Type**: Module, API, Service, Function, Class, etc.
- **Complexity**: Low, Medium, or High
- **Relationships**: Key dependencies and interactions
- **Confidence**: Analysis confidence score (0.0-1.0)

## Setup

### 1. Environment Configuration
Create a `.env` file in the project root:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# LLM Analysis Configuration
LLM_ENABLED=true
LLM_CACHE_ENABLED=true
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.1
```

### 2. Install Dependencies
```bash
pip install openai python-dotenv
```

## Usage

### Basic Usage
The LLM integration is automatically used when analyzing codebases:

```bash
python3 -m src.main --codebase /path/to/your/codebase --verbose
```

### Configuration Options
- `LLM_ENABLED`: Enable/disable LLM analysis (default: true)
- `LLM_CACHE_ENABLED`: Enable response caching (default: true)
- `LLM_MAX_TOKENS`: Maximum tokens for LLM responses (default: 2000)
- `LLM_TEMPERATURE`: Response creativity (default: 0.1 for consistent results)

## How It Works

### 1. **File Analysis Pipeline**
```
Code File → AST Parsing → Symbol Extraction → LLM Analysis → Graph Node
```

### 2. **LLM Prompt Structure**
The system sends structured prompts to the LLM:
- File path and name
- Functions, classes, and imports
- File content preview (first 500 characters)
- System prompt for architectural analysis

### 3. **Response Processing**
- JSON response parsing with fallback text parsing
- Result validation and normalization
- Integration with existing graph structure

### 4. **Caching Strategy**
- Cache key based on file content hash and symbols
- Stored in `cache/llm/` directory
- Automatic cache invalidation on file changes

## Example Output

### LLM Analysis Result
```json
{
  "purpose": "Service for performing mathematical calculations and operations.",
  "level": "LLD",
  "component_type": "Service",
  "complexity": "medium",
  "relationships": [
    "math (standard library)",
    "typing (for type hints)",
    "utils.exceptions.CalculationError (custom exception)"
  ],
  "confidence": 0.9,
  "analysis_method": "llm"
}
```

### Enhanced Graph Statistics
```
Semantic analysis: {
  'total_files_analyzed': 13,
  'cached_results': 13,
  'analysis_method': 'llm',
  'llm_integration_ready': True,
  'llm_analyses': 13,
  'fallback_analyses': 0
}
```

## Fallback Behavior

When LLM is unavailable (no API key, network issues, etc.), the system:
1. Logs a warning message
2. Uses rule-based analysis as fallback
3. Continues processing all files
4. Reports fallback usage in statistics

## Performance Considerations

- **Caching**: Significantly reduces API calls for repeated analysis
- **Content Preview**: Limits file content to 500 characters to manage token usage
- **Batch Processing**: Processes files sequentially to avoid rate limits
- **Error Isolation**: Individual file failures don't stop the entire analysis

## Troubleshooting

### Common Issues

1. **"LLM client not initialized"**
   - Check your `.env` file exists and has valid API key
   - Verify `LLM_ENABLED=true`

2. **"Failed to parse LLM response"**
   - Usually indicates malformed JSON from LLM
   - System automatically falls back to text parsing

3. **"Analysis failed"**
   - Check network connectivity
   - Verify OpenAI API key is valid
   - Check API rate limits

### Debug Mode
Enable verbose logging to see detailed LLM interaction:
```bash
python3 -m src.main --codebase /path/to/codebase --verbose
```

## Future Enhancements

- **Multi-LLM Support**: Add support for Claude, Gemini, etc.
- **Advanced Caching**: Implement cache expiration and cleanup
- **Batch Analysis**: Process multiple files in single LLM call
- **Custom Prompts**: Allow user-defined analysis prompts
- **Language-Specific Analysis**: Tailored prompts for different programming languages 