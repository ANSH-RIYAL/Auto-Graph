# Calculator Web App

A simple Flask-based calculator web application with multiple components for testing AutoGraph's HLD/LLD capabilities.

## Features

- Basic mathematical operations (add, subtract, multiply, divide)
- Advanced operations (power, sqrt, log, sin, cos, tan)
- Calculation history management
- RESTful API endpoints
- Input validation
- Error handling

## Project Structure

```
calculator_app/
├── app.py                 # Main Flask application
├── calculator/            # Calculator package
│   ├── __init__.py
│   ├── services/          # Business logic services
│   │   ├── __init__.py
│   │   ├── calculator_service.py
│   │   └── history_service.py
│   ├── models/            # Data models
│   │   ├── __init__.py
│   │   └── calculation.py
│   └── utils/             # Utility functions
│       ├── __init__.py
│       ├── exceptions.py
│       ├── validators.py
│       └── formatters.py
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

The application will start on `http://localhost:5000`

## API Endpoints

- `GET /` - Main page
- `POST /api/calculate` - Perform calculation
- `GET /api/history` - Get calculation history
- `GET /api/history/<id>` - Get specific calculation
- `DELETE /api/clear-history` - Clear history
- `GET /health` - Health check

## Example Usage

```bash
# Add two numbers
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"operation": "add", "operands": [5, 3]}'

# Get history
curl http://localhost:5000/api/history
```

## Testing AutoGraph

This application is designed to test AutoGraph's ability to:

1. **Parse Python files** - Multiple Python modules with different purposes
2. **Extract symbols** - Functions, classes, imports, and variables
3. **Categorize components** - Services, models, utilities, API endpoints
4. **Build HLD/LLD graph** - Hierarchical relationship between components
5. **Identify relationships** - Dependencies between modules and functions

The app includes:
- **HLD components**: API layer, service layer, data models
- **LLD components**: Individual functions, classes, utility methods
- **Multiple file types**: Python files with different purposes
- **Complex relationships**: Imports, dependencies, service interactions 