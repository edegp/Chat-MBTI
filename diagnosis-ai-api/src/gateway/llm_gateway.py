"""
Gateway implementations for LLM operations.
This layer adapts the driver layer to the port interfaces.
"""

from typing import Dict, Any, List
from ..port.ports import LLMPort
from ..driver.model import llm
from ..usecase.prompt import mbti_question_prompt, gen_user_message_prompt
from ..usecase.utils import _combine_options_list


class LLMGateway(LLMPort):
    """Gateway implementation for LLM operations using Google Gemini"""

    def __init__(self):
        self.llm = llm

    def generate_question(self, chat_history: str, context: Dict[str, Any]) -> str:
        """Generate MBTI question based on conversation history"""
        try:
            response = self.llm.invoke(
                mbti_question_prompt.format(chat_history=chat_history)
            )
            return response.content
        except Exception as e:
            raise RuntimeError(f"Failed to generate question: {str(e)}")

    def generate_options(self, messages: str, existing_options: List[str]) -> str:
        """Generate answer options for current question"""
        try:
            options = _combine_options_list(existing_options)
            prompt = gen_user_message_prompt.format(messages=messages, options=options)

            response = self.llm.invoke(prompt)
            new_option = response.content.strip()

            # Clean up the option
            if ":" in new_option:
                new_option = new_option.split(":")[-1].strip()

            return new_option
        except Exception as e:
            raise RuntimeError(f"Failed to generate options: {str(e)}")
