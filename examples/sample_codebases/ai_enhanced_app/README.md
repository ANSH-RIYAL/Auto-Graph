# AI-Enhanced Application Example

This is a sample application demonstrating AI agent usage for testing AutoGraph's agent detection capabilities.

## Overview

This example application showcases:
- **OpenAI Integration**: Customer risk classification using GPT-4
- **LangChain Integration**: Sentiment analysis using LangChain
- **Business Logic**: Processing AI results and making business decisions
- **Real-world Patterns**: Common AI agent usage patterns found in enterprise applications

## Structure

```
ai_enhanced_app/
├── app.py                    # Main application with AI integration
├── ai_services/             # AI agent implementations
│   ├── classifier.py        # OpenAI-based risk classifier
│   └── analyzer.py          # LangChain-based sentiment analyzer
├── services/                # Business logic services
│   └── business_logic.py    # Business decision processing
└── README.md               # This file
```

## Features

### Customer Risk Classification
- Uses OpenAI GPT-4 to analyze customer transaction data
- Provides risk scores between 0 and 1
- Includes risk explanation capabilities

### Sentiment Analysis
- Uses LangChain with OpenAI for sentiment analysis
- Analyzes customer feedback and reviews
- Provides sentiment scores between -1 and 1
- Supports batch processing

### Business Logic Processing
- Combines AI analysis results
- Makes business decisions based on risk and sentiment
- Generates action plans and escalation paths
- Calculates business impact and recommended budgets

## Usage

```python
from app import AIEnhancedApp

# Initialize the application
app = AIEnhancedApp()

# Generate a customer report
report = app.generate_customer_report("CUST123")

# Process results
print(f"Risk Score: {report['analysis']['risk_score']}")
print(f"Sentiment: {report['analysis']['sentiment']}")
print(f"Business Decision: {report['analysis']['business_decision']}")
```

## AI Agent Detection

This application is designed to test AutoGraph's agent detection capabilities:

### OpenAI Patterns
- `openai.ChatCompletion.create()`
- `openai.api_key`
- `gpt-4` model references

### LangChain Patterns
- `langchain.LLMChain`
- `langchain.PromptTemplate`
- `langchain.llms.OpenAI`

### Business Context
- Customer data processing
- Financial risk assessment
- Sentiment analysis
- Business decision making

## Testing AutoGraph

To test AutoGraph's agent detection with this example:

1. **Upload the entire `ai_enhanced_app/` directory** to AutoGraph
2. **Enable audit mode** to see agent-touched components
3. **Review the analysis** to verify:
   - OpenAI usage is detected in `classifier.py`
   - LangChain usage is detected in `analyzer.py`
   - Risk levels are properly assessed
   - Business context is extracted

## Expected Results

When analyzed by AutoGraph, this application should show:

- **Agent Components**: 3 (app.py, classifier.py, analyzer.py)
- **Agent Types**: OpenAI, LangChain
- **Risk Levels**: High (due to customer data and financial logic)
- **Business Domains**: Finance, Customer Service
- **Compliance Implications**: GDPR, SOC2, PCI (due to customer data)

## Dependencies

This example requires:
- `openai` library
- `langchain` library
- Python 3.7+

Note: This is a demonstration application and does not include actual API keys or production-ready error handling. 