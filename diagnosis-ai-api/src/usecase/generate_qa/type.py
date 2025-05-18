from typing_extensions import TypedDict, Annotated


# Define state management (from your notebook)
def add_messages(messages, new_messages):
    return messages + new_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]
    options: list[list[str]]
