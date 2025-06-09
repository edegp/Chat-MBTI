# New MBTI Architecture Implementation

## Overview

This document describes the new Port & Adapter architecture implementation for the MBTI conversation API. The architecture provides clean separation of concerns and follows dependency inversion principles.

## Architecture Layers

### 1. Port Layer (`src/port/`)

- **Purpose**: Abstract interfaces defining contracts between layers
- **Files**: `ports.py`
- **Key Interfaces**:
  - `LLMPort`: Abstract interface for AI model operations
  - `WorkflowPort`: Abstract interface for conversation orchestration
  - `QuestionRepositoryPort`: Abstract interface for question data operations
  - `SessionRepositoryPort`: Abstract interface for session management

### 2. Gateway Layer (`src/gateway/`)

- **Purpose**: Adapter implementations that convert between external systems and internal interfaces
- **Files**:
  - `llm_gateway.py`: Adapts Google Gemini LLM to LLMPort interface
  - `repository_gateway.py`: Adapts database drivers to repository ports
  - `workflow_gateway.py`: Adapts LangGraph driver to WorkflowPort interface

### 3. Driver Layer (`src/driver/`)

- **Purpose**: External system integrations (databases, APIs, frameworks)
- **Files**:
  - `langgraph_driver.py`: LangGraph-specific workflow orchestration
  - `model.py`: Google Gemini API client
  - `db.py`: Database connection and operations

### 4. Usecase Layer (`src/usecase/`)

- **Purpose**: Pure business logic without external dependencies
- **Files**:
  - `mbti_conversation_service.py`: Core MBTI conversation business logic

### 5. Controller Layer (`src/controller/`)

- **Purpose**: API endpoints and HTTP request handling
- **Files**:
  - `mbti_controller.py`: Clean controller with minimal logic
  - `mbti_routes.py`: FastAPI route definitions

## Key Benefits

1. **Testability**: Easy to mock ports for unit testing
2. **Flexibility**: Can swap LangGraph for other orchestration tools
3. **Clean Separation**: Each layer has single responsibility
4. **Dependency Inversion**: Usecase depends on abstractions, not concretions
5. **Maintainability**: LangGraph complexity isolated in driver layer

## API Endpoints

### Start Conversation

```http
POST /api/v1/conversation/start
Content-Type: application/json

{
  "user_id": "user123"
}
```

### Submit Answer

```http
POST /api/v1/conversation/answer
Content-Type: application/json

{
  "user_id": "user123",
  "answer": "I prefer outdoor activities"
}
```

### Get Options

```http
GET /api/v1/conversation/options/user123
```

### Get Progress

```http
GET /api/v1/conversation/progress/user123
```

### Complete Assessment

```http
POST /api/v1/conversation/complete
Content-Type: application/json

{
  "user_id": "user123"
}
```

## Usage Example

```python
from src.di_container import container

# Get the configured controller
controller = container.get_mbti_controller()

# Start a conversation
result = await controller.start_conversation("user123")
print(result["question"])

# Submit an answer
result = await controller.submit_answer("user123", "I love hiking")
print(result["question"])
```

## Testing

Run the unit tests:

```bash
python -m pytest tests/test_mbti_service.py -v
```

## Dependency Injection

The `DIContainer` class manages all dependencies:

```python
from src.di_container import container

# All dependencies are automatically wired
mbti_service = container.get_mbti_service()
```

## Migration from Old Architecture

1. **Old Route**: `/generate_qa` → **New Route**: `/api/v1/conversation/start`
2. **Old Service**: Direct LangGraph usage → **New Service**: Clean business logic
3. **Old Testing**: Hard to mock → **New Testing**: Easy to mock ports

## Future Enhancements

1. **Add Different LLM Providers**: Implement new LLMPort adapters
2. **Add Caching**: Implement caching at the gateway layer
3. **Add Monitoring**: Add metrics and logging at appropriate layers
4. **Add Validation**: Add input validation at the controller layer

## Error Handling

All layers implement proper error handling:

- **Controller**: HTTP error responses
- **Service**: Business logic errors
- **Gateway**: External system errors
- **Driver**: Low-level system errors

## Configuration

The system uses environment variables for configuration:

- `GEMINI_API_KEY`: Google Gemini API key
- Database connection settings in `src/driver/db.py`
