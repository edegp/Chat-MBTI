"""
Gateway implementations for LLM operations.
This layer adapts the driver layer to the port interfaces.
"""

from typing import Dict, Any, List
from ..port.ports import LLMPort
from ..driver.model import llm
from ..usecase.prompt import mbti_question_prompt, gen_user_message_prompt
from ..usecase.utils import _combine_options_list
from ..driver.env import ElementsDriver

import logging

logger = logging.getLogger(__name__)


class LLMGateway(LLMPort):
    """Gateway implementation for LLM operations using Google Gemini"""

    def __init__(self):
        self.llm = llm
        self.elements_driver = ElementsDriver()

    def generate_question(self, chat_history: str, context: Dict[str, Any]) -> str:
        """Generate MBTI question based on conversation history"""

        element, description = self.elements_driver.get_element_info(
            context["personality_element_id"]
        )
        try:
            logger.info(
                "Generating MBTI question prompt: %s",
                mbti_question_prompt.format(
                    element=element,
                    description=description,
                    chat_history=chat_history,
                ),
            )
            response = self.llm.invoke(
                mbti_question_prompt.format(
                    element=element,
                    description=description,
                    chat_history=chat_history,
                )
            )
            return response.content
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            raise RuntimeError(f"Failed to generate question: {str(e)}")

    def generate_options(self, messages: str, existing_options: List[str]) -> str:
        """Generate answer options for current question"""
        try:
            options = _combine_options_list(existing_options)
            logger.info(
                "Generating options prompt: %s",
                gen_user_message_prompt.format(messages=messages, options=options),
            )

            response = self.llm.invoke(
                gen_user_message_prompt.format(messages=messages, options=options)
            )
            new_option = response.content.strip()
            logger.debug(f"Generated option: {new_option}")
            # Clean up the option
            if ":" in new_option:
                new_option = new_option.split(":")[-1].strip()

            return new_option
        except Exception as e:
            raise RuntimeError(f"Failed to generate options: {str(e)}")
