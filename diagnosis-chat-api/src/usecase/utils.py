# Helper functions from your notebook
def _combine_options_list(options_list: list[str]) -> str:
    """Combines generated answer options into a string"""
    if len(options_list) == 0:
        options_str = "まだ候補がありません"
    else:
        options_str = "\n".join(options_list)
    return options_str


def _organize_chat_history(raw_messages):
    """Formats chat history into a string"""
    messages = "\n".join(
        f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
        for msg in raw_messages
        if msg.get("role") and msg.get("content")
    )
    return messages
