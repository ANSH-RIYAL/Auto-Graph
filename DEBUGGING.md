# Debugging Guide for AutoGraph

## Overview
AutoGraph has been configured to run silently by default to reduce console clutter. This guide explains how to enable logging and debugging when needed.

## Silent Mode (Default)
By default, AutoGraph runs with all logging disabled to keep the console clean and focused on actual errors.

## Enabling Debug Logging

### Method 1: Enable Logging in Code
To enable logging for debugging, add this line at the top of any file where you want to debug:

```python
from src.utils.logger import enable_logging_for_debug
enable_logging_for_debug()
```

### Method 2: Enable Logging for Specific Module
To enable logging for a specific module:

```python
from src.utils.logger import get_logger
logger = get_logger("module_name", enable_logging=True)
```

### Method 3: Enable Logging for Web Application
To enable logging for the Flask web application, modify `src/web/flask_app.py`:

```python
from src.utils.logger import enable_logging_for_debug
enable_logging_for_debug()
```

## Debugging Specific Issues

### 1. File Parsing Issues
If you're having trouble with file parsing, enable logging in `src/parser/`:

```python
# In src/parser/file_parser.py or src/parser/ast_parser.py
from src.utils.logger import get_logger
logger = get_logger("parser", enable_logging=True)
```

### 2. LLM Integration Issues
For LLM-related problems, enable logging in `src/llm_integration/`:

```python
# In src/llm_integration/llm_client.py or src/llm_integration/semantic_analyzer.py
from src.utils.logger import get_logger
logger = get_logger("llm", enable_logging=True)
```

### 3. Web Application Issues
For Flask app problems, enable logging in `src/web/flask_app.py`:

```python
# At the top of src/web/flask_app.py
from src.utils.logger import enable_logging_for_debug
enable_logging_for_debug()
```

### 4. Graph Building Issues
For graph construction problems, enable logging in `src/graph_builder/`:

```python
# In src/graph_builder/enhanced_graph_builder.py
from src.utils.logger import get_logger
logger = get_logger("graph_builder", enable_logging=True)
```

## Log Files
When logging is enabled, log files are created in the `logs/` directory:
- `autograph.log` - General application logs
- `autograph_errors.log` - Error-specific logs
- Module-specific logs (e.g., `src.parser.file_parser.log`)

## Console Output
When logging is enabled, you'll see:
- File processing progress
- LLM API calls and responses
- Graph construction details
- Error messages and stack traces

## Disabling Logging
To disable logging again, simply remove the `enable_logging_for_debug()` call or set `enable_logging=False` in `get_logger()`.

## Common Debugging Scenarios

### Issue: File Not Being Parsed
1. Enable logging in `src/parser/file_parser.py`
2. Check the logs for parsing errors
3. Verify file path and permissions

### Issue: LLM Analysis Failing
1. Enable logging in `src/llm_integration/llm_client.py`
2. Check API key configuration
3. Look for network or rate limiting errors

### Issue: Graph Not Displaying
1. Enable logging in `src/web/flask_app.py`
2. Check browser console for JavaScript errors
3. Verify data format conversion

### Issue: Export Failing
1. Enable logging in `src/export/enhanced_exporter.py`
2. Check file permissions in output directory
3. Verify export format configuration

## Performance Debugging
To debug performance issues:
1. Enable logging in the specific module
2. Look for slow operations in the logs
3. Check for repeated LLM calls (caching issues)
4. Monitor memory usage during large codebase analysis

## Remember
- Logging is disabled by default to keep the console clean
- Only enable logging when you need to debug a specific issue
- Disable logging after debugging to maintain clean output
- Log files are automatically rotated to prevent disk space issues 