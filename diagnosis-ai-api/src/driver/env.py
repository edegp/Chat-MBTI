import yaml
import numpy as np

import logging

logger = logging.getLogger(__name__)


def load_env(file_path: str) -> dict:
    """Load environment variables from a YAML file."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            env_vars = yaml.safe_load(file)
        return env_vars
    except FileNotFoundError:
        raise FileNotFoundError(f"Environment file '{file_path}' not found.")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")


def get_elements() -> dict:
    """Get specific elements from the environment variables."""
    return load_env("config/element.yaml")


class ElementsDriver:
    """Driver to access elements from the environment variables."""

    def __init__(self):
        elements = get_elements()
        self.elements = [elements[k] for k in elements.keys()]

    def get_element(self, element_id: int) -> dict:
        """Get element by ID."""
        if 1 <= element_id <= len(self.elements):
            return self.elements[element_id - 1]
        else:
            raise KeyError(f"Element with ID {element_id} not found.")

    def get_initial_question(self, id: int = 1) -> str:
        """Get the initial question from the elements."""
        logger.info(f"Fetching element info for ID: {id}")
        # Ensure element_id is within valid range (1-4)
        element_index = max(0, min(id - 1, len(self.elements) - 1))
        if id < 1 or id > len(self.elements):
            logger.warning(
                f"Element ID {id} out of range, using element {element_index + 1}"
            )
        return np.random.choice(self.elements[element_index]["initial_questions"])

    def get_element_info(self, id: int) -> dict:
        """Get element information by ID."""
        logger.info(f"Fetching element info for ID: {id}")
        # Ensure element_id is within valid range (1-4)
        element_index = max(0, min(id - 1, len(self.elements) - 1))
        if id < 1 or id > len(self.elements):
            logger.warning(
                f"Element ID {id} out of range, using element {element_index + 1}"
            )
        return self.elements[element_index]["element"], self.elements[element_index][
            "element_description"
        ]
