# REALITY_TESTS

## Sample Data Payloads

### Request Example
```json
{
  "input_data": "example input",
  "context": {},
  "options": {}
}
```

### Response Example
```json
{
  "success": true,
  "data": {
    "result": "example output",
    "metadata": {}
  },
  "error": null
}
```

### Frontend Inputs
- Define the HTML form fields and their purposes
- Specify input validation requirements
- Define user interaction patterns

## Critical User Flows
- **Primary Flow:** Define the main user journey from start to finish
- **Error Flow:** Define how the system handles errors and failures
- **Recovery Flow:** Define how the system recovers from failures
- **Alternative Flows:** Define any secondary user journeys

## Edge Cases
- **Input Validation:** What happens with invalid or malformed inputs
- **Service Failures:** What happens when external services fail
- **Performance Limits:** What happens under high load or resource constraints
- **Data Corruption:** What happens when data is corrupted or incomplete
- **Network Issues:** What happens during network interruptions

## Performance Test Scenarios
- **Concurrent Users:** How many simultaneous users can be handled
- **Large Data Sets:** How the system handles large amounts of data
- **Complex Operations:** How the system handles resource-intensive operations
- **Memory Usage:** How the system manages memory under load
- **Response Times:** Expected latency for different operations

## Expected Behavior on Failure
- **Backend:**
  - HTTP status codes to return
  - Error message format and content
  - Logging and monitoring requirements
- **Frontend:**
  - How errors are displayed to users
  - Retry mechanisms and user guidance
  - Graceful degradation strategies

## Quality Assurance Requirements
- **Testing Strategy:** How to test the system functionality
- **Error Handling:** What error scenarios must be handled
- **Performance Monitoring:** How to track system performance
- **User Experience:** How to ensure good user experience during failures
- **Security:** How to protect against common security issues 

---

## Canonical API Contracts (must remain stable)
- Upload: POST `/api/analysis/upload` (multipart file)
  - Response: `{ "success": true, "analysisId": "<uuid>", "status": "processing" }`
- Status: GET `/api/analysis/<analysis_id>/status`
  - Response: `{ "status": "processing|completed|error", "progress": <int>, "message": "..." }`
- Graph: GET `/api/analysis/<analysis_id>/graph`
  - Response: the canonical graph object defined below
- Logs: GET `/api/analysis/<analysis_id>/logs`
  - Response: `{ "logs": ["..."] }`

## Canonical Graph Templates (BSI)
- Node (common fields):
```json
{
  "id": "system_user_service",
  "name": "User Service",
  "type": "Service|Module|Component|Function_Group|Class",
  "level": "BUSINESS|SYSTEM|IMPLEMENTATION",
  "technical_depth": 2,
  "files": ["src/services/user_service.py"],
  "functions": ["create_user"],
  "classes": ["UserService"],
  "imports": ["utils.db"],
  "metadata": {"purpose": "...", "complexity": "low|medium|high", "dependencies": ["..."], "line_count": 123}
}
```
- Edge:
```json
{ "from": "system_user_service", "to": "implementation_todo_create", "type": "contains", "metadata": {"relationship_type": "hierarchy"} }
```

### Final Graph Object Shape
```json
{ "metadata": {"codebase_path": "...", "analysis_timestamp": "..."}, "nodes": [], "edges": [] }
```

## Grounding Example: todo_flask_app (real-world small app)
Location: `examples/real_world/todo_flask_app/`

### Expected Intermediary Outputs (deterministic examples for the agent)
1) Implementation symbols (AST-only):
```json
{
  "files": [
    {"path": "app.py", "functions": ["health", "list_todos", "create_todo", "complete_todo"], "classes": []},
    {"path": "services/todo_service.py", "functions": ["list_todos", "create_todo", "complete_todo"], "classes": ["TodoService"]},
    {"path": "models/todo.py", "functions": ["to_dict"], "classes": ["Todo"]},
    {"path": "utils/db.py", "functions": ["add", "list", "get", "update"], "classes": ["InMemoryDB"]}
  ],
  "imports": {
    "app.py": ["services.todo_service.TodoService"],
    "services/todo_service.py": ["utils.db.InMemoryDB", "models.todo.Todo"],
    "utils/db.py": ["models.todo.Todo"]
  }
}
```

2) System clusters (import/call based; clustered):
```json
{
  "system_nodes": [
    {"id": "system_api", "name": "API", "members": ["app.py"], "technical_depth": 2},
    {"id": "system_core", "name": "Core Services", "members": ["services/todo_service.py", "utils/db.py", "models/todo.py"], "technical_depth": 2}
  ],
  "system_edges": [
    {"from": "system_api", "to": "system_core", "type": "depends_on", "weight": 2}
  ]
}
```

3) Business domains (directory/name aggregation with optional LLM label):
```json
{
  "business_nodes": [
    {"id": "business_todo", "name": "Todo Management", "members": ["system_api", "system_core"], "technical_depth": 1}
  ]
}
```

4) Canonical Final Graph (BSI):
```json
{
  "metadata": {"codebase_path": "examples/real_world/todo_flask_app", "analysis_timestamp": "2025-08-10T00:00:00Z"},
  "nodes": [
    {"id": "business_todo", "name": "Todo Management", "type": "Domain", "level": "BUSINESS", "technical_depth": 1, "files": [], "functions": [], "classes": [], "imports": [], "metadata": {"purpose": "End-user task tracking"}},
    {"id": "system_api", "name": "API", "type": "Service", "level": "SYSTEM", "technical_depth": 2, "files": ["app.py"], "functions": ["list_todos", "create_todo", "complete_todo"], "classes": [], "imports": ["services.todo_service.TodoService"], "metadata": {"purpose": "HTTP routing and handlers"}},
    {"id": "system_core", "name": "Core Services", "type": "Service", "level": "SYSTEM", "technical_depth": 2, "files": ["services/todo_service.py", "utils/db.py", "models/todo.py"], "functions": [], "classes": ["TodoService", "Todo", "InMemoryDB"], "imports": ["utils.db", "models.todo"], "metadata": {"purpose": "Business logic and storage"}},
    {"id": "implementation_api_create", "name": "create_todo", "type": "Function_Group", "level": "IMPLEMENTATION", "technical_depth": 3, "files": ["app.py"], "functions": ["create_todo"], "classes": [], "imports": ["services.todo_service.TodoService"], "metadata": {"purpose": "Create todo via POST"}}
  ],
  "edges": [
    {"from": "business_todo", "to": "system_api", "type": "contains", "metadata": {"relationship_type": "hierarchy"}},
    {"from": "business_todo", "to": "system_core", "type": "contains", "metadata": {"relationship_type": "hierarchy"}},
    {"from": "system_api", "to": "system_core", "type": "depends_on"},
    {"from": "system_api", "to": "implementation_api_create", "type": "contains"}
  ]
}
```