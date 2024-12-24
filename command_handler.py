"""
Handles voice commands for job application management
"""

from typing import Optional, Tuple, Dict, Any
from enum import Enum
import logging

# pylint: disable=import-error
import pyperclip
import ollama
from llm import OllamaModelConfig

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Types of commands that can be processed"""

    ADD_URL = "ADD_URL"
    ADD_TITLE = "ADD_TITLE" 
    ADD_COMPANY = "ADD_COMPANY"
    ADD_LOCATION = "ADD_LOCATION"
    ADD_DURATION = "ADD_DURATION"
    ADD_DESCRIPTION = "ADD_DESCRIPTION"
    ADD_QUESTION = "ADD_QUESTION"
    ADD_ANSWER = "ADD_ANSWER"
    ADD_NOTE = "ADD_NOTE"
    ADD_CHECK_URL = "ADD_CHECK_URL"
    # Aliases
    ADD_LINK = "ADD_LINK"
    ADD_NOTES = "ADD_NOTES"
    ADD_ROLE = "ADD_ROLE"
    ADD_JOB_TITLE = "ADD_JOB_TITLE"
    ADD_NODES = "ADD_NODES"
    UNKNOWN = "UNKNOWN"


def process_command(command_type: CommandType, reasoning: str) -> Dict[str, Any]:
    """"""
    pass


# pylint: disable=too-many-lines
class CommandDeterminer:
    """
    Determines if a voice command is complete using LLM
    """

    def __init__(self):
        logger.info("Initializing CommandDeterminer")


class CommandExecutor:
    """
    Executes commands on the job application window
    """

    def __init__(self, window_queue):
        logger.info("Initializing CommandExecutor")
        self.window_queue = window_queue
        self.determiner = CommandDeterminer()
        self.current_application = None