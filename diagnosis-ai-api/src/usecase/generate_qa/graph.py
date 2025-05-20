from langgraph.graph import StateGraph
from langgraph.graph import START, END

from .type import State
from .model import llm
from .utils import (
    _organaize_chat_history,
    _combine_options_list,
)
from .prompt import (
    mbti_question_prompt,
    gen_user_message_prompt,
)
from src.driver.checkpointer_factory import create_checkpointer
# Initialize Gemini model (similar to your notebook)


# Define the graph builder
graph_builder = StateGraph(State)


# Define node functions
def generate_question(state: State) -> State:
    """Generate MBTI question based on conversation history"""
    chat_history = _organaize_chat_history(
        [{"role": msg["role"], "content": msg["content"]} for msg in state["messages"]]
    )

    # Generate question
    response = llm.invoke(mbti_question_prompt.format(chat_history=chat_history))
    question = response.content

    # Add the generated question to messages
    new_message = {"role": "assistant", "content": question}
    return {"messages": [new_message]}


def generate_options(state: State) -> State:
    """Generate answer options for the current question"""
    messages = _organaize_chat_history(
        [{"role": msg["role"], "content": msg["content"]} for msg in state["messages"]]
    )

    num_options = 3
    options_list = []

    # Generate options
    for i in range(num_options):
        options = _combine_options_list(options_list)
        prompt = gen_user_message_prompt.format(messages=messages, options=options)

        # Get a new option
        response = llm.invoke(prompt)
        new_option = response.content.strip()

        # Clean up the option
        if new_option.startswith("user: "):
            new_option = new_option[6:]
        elif new_option.startswith("human: "):
            new_option = new_option[7:]

        options_list.append(new_option)

    return {"options": [options_list]}


# Define the graph
graph_builder.add_node("generate_question", generate_question)
graph_builder.add_node("generate_options", generate_options)

# Add edges
graph_builder.add_edge(START, "generate_question")
graph_builder.add_edge("generate_question", "generate_options")
graph_builder.add_edge("generate_options", END)


