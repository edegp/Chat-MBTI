# LangGraph Architecture Redesign

## Current Problems

1. **Dependency Inversion Violation**: Usecase layer directly imports from driver layer
2. **Mixed Responsibilities**: Graph.py contains AI orchestration, data access, and business logic
3. **No Abstraction**: LangGraph specifics are tightly coupled to business logic
4. **Testing Difficulty**: Hard to mock AI components and test business logic separately

## Proposed Architecture

### Layer Responsibilities

```
Controller (API endpoints)
    ↓
Usecase (Business Logic)
    ↓
Gateway (Port adapters - abstractions)
    ↓
Driver (External dependencies - LLM, DB, etc.)
```

### 1. Port Interfaces (New Layer)

Create abstract interfaces that define contracts:

```python
# src/port/llm_port.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMPort(ABC):
    @abstractmethod
    def generate_question(self, chat_history: str, context: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def generate_options(self, messages: str, existing_options: List[str]) -> str:
        pass

# src/port/workflow_port.py
class WorkflowPort(ABC):
    @abstractmethod
    def execute_conversation_flow(self, user_input: str, session_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_conversation_state(self, session_id: str) -> Dict[str, Any]:
        pass

# src/port/repository_port.py
class QuestionRepositoryPort(ABC):
    @abstractmethod
    def save_question(self, question_data: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def get_question_by_session(self, session_id: str, order: int) -> Dict[str, Any]:
        pass
```

### 2. Gateway Layer (Adapters)

Implement the ports using drivers:

```python
# src/gateway/llm_gateway.py
from ..port.llm_port import LLMPort
from ..driver.model import llm
from ..usecase.prompt import mbti_question_prompt, gen_user_message_prompt

class LLMGateway(LLMPort):
    def __init__(self):
        self.llm = llm

    def generate_question(self, chat_history: str, context: Dict[str, Any]) -> str:
        response = self.llm.invoke(mbti_question_prompt.format(chat_history=chat_history))
        return response.content

    def generate_options(self, messages: str, existing_options: List[str]) -> str:
        options = _combine_options_list(existing_options)
        prompt = gen_user_message_prompt.format(messages=messages, options=options)
        response = self.llm.invoke(prompt)
        return response.content.strip()

# src/gateway/workflow_gateway.py
from ..port.workflow_port import WorkflowPort
from ..driver.langgraph_driver import LangGraphDriver

class WorkflowGateway(WorkflowPort):
    def __init__(self, langgraph_driver: 'LangGraphDriver'):
        self.driver = langgraph_driver

    def execute_conversation_flow(self, user_input: str, session_id: str) -> Dict[str, Any]:
        return self.driver.run_workflow(user_input, session_id)

    def get_conversation_state(self, session_id: str) -> Dict[str, Any]:
        return self.driver.get_state(session_id)
```

### 3. Driver Layer (LangGraph Specific)

Isolate LangGraph complexity:

```python
# src/driver/langgraph_driver.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from .db import create_checkpointer
from ..usecase.type import ChatState

class LangGraphDriver:
    def __init__(self, llm_gateway, repository_gateway):
        self.llm_gateway = llm_gateway
        self.repository_gateway = repository_gateway
        self.graph_builder = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create LangGraph StateGraph with nodes and edges"""
        sg = StateGraph(ChatState)

        # Register nodes
        sg.add_node("generate_question", self._generate_question_node)
        sg.add_node("generate_options", self._generate_options_node)

        # Define edges
        sg.add_edge(START, "generate_question")
        sg.add_edge("generate_question", "generate_options")
        sg.add_edge("generate_options", END)

        return sg

    def _generate_question_node(self, state: ChatState) -> ChatState:
        """LangGraph node for question generation"""
        chat_history = self._organize_chat_history(state["messages"])

        # Use gateway (abstraction) instead of direct driver access
        question = self.llm_gateway.generate_question(chat_history, {
            "personality_element_id": state["personality_element_id"],
            "next_display_order": state["next_display_order"]
        })

        # Save to repository through gateway
        qid = self.repository_gateway.save_question({
            "session_id": state["session_id"],
            "question": question,
            "display_order": state["next_display_order"]
        })

        # Return updated state
        return {
            "messages": [AIMessageWithID(content=question)],
            "pending_question": question,
            "session_id": state["session_id"],
            "next_display_order": state["next_display_order"] + 1
        }

    def run_workflow(self, user_messages: List[Message], session_id: str) -> Dict[str, Any]:
        """Execute the LangGraph workflow"""
        checkpointer = create_checkpointer()
        config = {"configurable": {"thread_id": session_id}}

        graph_with_memory = self.graph_builder.compile(checkpointer=checkpointer)

        state = {
            "session_id": session_id,
            "messages": user_messages,
            "next_display_order": 0
        }

        result = graph_with_memory.invoke(state, config=config)
        return result
```

### 4. Usecase Layer (Pure Business Logic)

Clean business logic without external dependencies:

```python
# src/usecase/mbti_conversation_service.py
from ..port.workflow_port import WorkflowPort
from ..port.repository_port import QuestionRepositoryPort

class MBTIConversationService:
    def __init__(self,
                 workflow_port: WorkflowPort,
                 question_repository: QuestionRepositoryPort):
        self.workflow = workflow_port
        self.question_repository = question_repository

    def start_conversation(self, user_id: str) -> str:
        """Start a new MBTI conversation"""
        # Pure business logic - no external dependencies
        session_id = self._create_new_session(user_id)
        initial_message = "Let's start your MBTI assessment!"

        result = self.workflow.execute_conversation_flow(initial_message, session_id)
        return result["messages"][-1]["content"]

    def process_user_response(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Process user response and generate next question"""
        session_id = self._get_session_for_user(user_id)

        # Business rule: Check if we have enough questions
        question_count = self._get_question_count(session_id)
        if question_count >= 20:
            return {"phase": "diagnosis", "message": "Ready for diagnosis!"}

        # Execute workflow through port
        result = self.workflow.execute_conversation_flow(user_input, session_id)

        return {
            "phase": "question",
            "question": result["messages"][-1]["content"],
            "options": result.get("options", [])
        }
```

### 5. Controller Layer (Clean API)

```python
# src/controller/mbti_controller.py
from ..usecase.mbti_conversation_service import MBTIConversationService

class MBTIController:
    def __init__(self, mbti_service: MBTIConversationService):
        self.mbti_service = mbti_service

    async def start_conversation(self, user_id: str):
        """Start MBTI conversation endpoint"""
        try:
            question = self.mbti_service.start_conversation(user_id)
            return {"status": "success", "question": question}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def submit_answer(self, user_id: str, answer: str):
        """Submit user answer endpoint"""
        try:
            result = self.mbti_service.process_user_response(answer, user_id)
            return {"status": "success", **result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
```

## Benefits of This Architecture

1. **Testability**: Easy to mock ports for unit testing
2. **Flexibility**: Can swap LangGraph for other orchestration tools
3. **Clean Separation**: Each layer has single responsibility
4. **Dependency Inversion**: Usecase depends on abstractions, not concretions
5. **Maintainability**: LangGraph complexity isolated in driver layer

## Implementation Steps

1. Create port interfaces
2. Implement gateway adapters
3. Refactor current Graph class into LangGraphDriver
4. Create clean usecase services
5. Update controllers to use new services
6. Add comprehensive tests

## Testing Strategy

```python
# tests/usecase/test_mbti_service.py
def test_conversation_flow():
    # Mock the ports
    mock_workflow = Mock(spec=WorkflowPort)
    mock_repository = Mock(spec=QuestionRepositoryPort)

    # Test pure business logic
    service = MBTIConversationService(mock_workflow, mock_repository)
    result = service.process_user_response("Yes", "user123")

    # Assert business rules
    assert result["phase"] == "question"
    mock_workflow.execute_conversation_flow.assert_called_once()
```

This architecture properly separates LangGraph orchestration concerns from business logic while maintaining clean dependency relationships.
