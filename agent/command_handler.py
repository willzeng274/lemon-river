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
    """
    Process a complete voice command.

    Args:
        command_type: The type of command to execute (ADD_URL, ADD_TITLE, ADD_COMPANY, ADD_LOCATION, ADD_DURATION, ADD_DESCRIPTION, ADD_QUESTION, ADD_ANSWER, ADD_NOTE, ADD_CHECK_URL, ADD_LINK, ADD_NOTES, ADD_ROLE, ADD_NODES, ADD_JOB_TITLE, UNKNOWN)
        reasoning: The reason why what the user said was a command

    Returns:
        Dict[str, Any]: Dictionary containing command type, and completion status
    """
    logger.info(
        "Tool called: process_command with type=%s, reasoning=%s",
        command_type,
        reasoning,
    )
    result = {"command_type": command_type, "complete": True}
    logger.debug("process_command returning: %s", result)
    return result


def wait_for_completion(command_type: CommandType, reasoning: str) -> Dict[str, Any]:
    """
    Indicate a command needs more information.

    Args:
        command_type: The type of command detected
        reasoning: The reason why what the user said was not a command

    Returns:
        Dict[str, Any]: Dictionary containing command type, and incomplete status
    """
    logger.info(
        "Tool called: wait_for_completion with type=%s, reasoning=%s",
        command_type,
        reasoning,
    )
    result = {"command_type": command_type, "complete": False}
    logger.debug("wait_for_completion returning: %s", result)
    return result


# pylint: disable=too-many-lines
class CommandDeterminer:
    """
    Determines if a voice command is complete using LLM
    """

    def __init__(self):
        logger.info("Initializing CommandDeterminer")
        self.config = OllamaModelConfig(
            # model is set in the main app
            temperature=0.1,
            max_tokens=512,
            system_prompt="""<BEGIN SYSTEM PROMPT>
You are a voice command processor for a job application tracking system.
Your task is to identify explicit commands and determine if they are complete. You also must provide a reason for your decision.

ONLY call process_command when ALL these conditions are met:
1. The user explicitly mentions "add", "paste", or "update" followed by the type

Call wait_for_completion when:
1. The user only said "add", "store", or "update" without specifying a command. However, keep in mind that there should be no parameters to add/update/store. It will be from the clipboard.
2. The command is unclear

IMPORTANT:
- If the user says "add", "store", or "update", lean towards processing the command that the user is most likely to be adding.
- "store" and "update" are synonymous with "add" for commands.
- There is no need to ask the user to provide more information, there are no parameters to add/update/store. It will be from the clipboard.

MOST IMPORTANT:
- If the user is only talking about the description, note, question, answer, company, location, etc, DO NOT process the command unless "add", "store", or "update" is explicitly mentioned.
- ONLY call process_command if the user clearly states "add", "store", or "update".
- Use the "UNKNOWN" command if the user is not talking about a specific command.
- You do not have to call any tools if the user is not talking about a specific command.

Available commands:
ADD_URL, ADD_TITLE, ADD_COMPANY, ADD_LOCATION, ADD_DURATION,
ADD_DESCRIPTION, ADD_QUESTION, ADD_ANSWER, ADD_NOTE, ADD_CHECK_URL,
ADD_LINK, ADD_NOTES, ADD_ROLE, ADD_NODES, ADD_JOB_TITLE, UNKNOWN

<END SYSTEM PROMPT>
""",
            # Examples were detrimental to the model's performance for some reason
            # Examples:
            # "add url from clipboard please" -> process_command(ADD_URL)
            # "add the" -> wait_for_completion(UNKNOWN)
            # "add the link wait" -> wait_for_completion(ADD_URL)
            # "I think I have to do something" -> no tools
            # "I need to add a job" -> no tools
            # "add title from clipboard thanks" -> process_command(ADD_TITLE)
        )

    def determine_command(self, text: str) -> Tuple[Optional[CommandType], bool]:
        """Determine the command from the user's input"""
        try:
            logger.debug("Sending prompt to Ollama: %s", text)

            system_prompt = self.config.system_prompt

            response = ollama.chat(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"""
                     <BEGIN USER PROMPT>
                     {text}
                     <END USER PROMPT>
                     """,
                    },
                ],
                tools=[process_command, wait_for_completion],
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                },
            )
            logger.debug("Received response from Ollama: %s", response)

            if response["message"].get("tool_calls"):
                tool_call = response["message"]["tool_calls"][0]
                logger.info("Tool call received: %s", tool_call["function"]["name"])

                args = tool_call["function"]["arguments"]
                logger.debug("Tool call arguments: %s", args)

                try:
                    raw_cmd_type = args["command_type"]
                    if raw_cmd_type.startswith("UPDATE_"):
                        raw_cmd_type = raw_cmd_type.replace("UPDATE_", "ADD_")
                    cmd_type = CommandType[raw_cmd_type]
                    is_complete = tool_call["function"]["name"] == "process_command"
                    logger.info(
                        "Determined command: type=%s, complete=%s",
                        cmd_type,
                        is_complete,
                    )
                    return cmd_type, is_complete
                except (KeyError, ValueError) as e:
                    logger.error("Error parsing tool arguments: %s", e)
                    return CommandType.UNKNOWN, False
            else:
                logger.warning("No tool calls in response")
                return CommandType.UNKNOWN, False

        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Error in determine_command: %s", str(e), exc_info=True)
            return CommandType.UNKNOWN, False


class CommandExecutor:
    """
    Executes commands on the job application window
    """

    def __init__(self, window_queue):
        logger.info("Initializing CommandExecutor")
        self.window_queue = window_queue
        self.determiner = CommandDeterminer()
        self.current_application = None

    def show_window(self, command):
        """Send window command through queue"""
        try:
            self.window_queue.put(command)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Error sending window command: %s", e)

    def process_voice_input(self, text: str):
        """
        Processes voice input and executes commands if complete
        """
        logger.info("Processing voice input: %s", text)
        command_type, is_complete = self.determiner.determine_command(text)
        logger.info(
            "Command determination result: type=%s, complete=%s",
            command_type,
            is_complete,
        )

        if not is_complete:
            return

        if command_type == CommandType.UNKNOWN:
            logger.warning("Unknown command type, ignoring")
            return

        clipboard_content = "" if not pyperclip.paste() else pyperclip.paste().strip()
        logger.debug("Clipboard content: %s", clipboard_content)

        if (
            command_type == CommandType.ADD_URL or command_type == CommandType.ADD_LINK
        ) and clipboard_content:
            logger.info("Processing ADD_URL command")
            self.show_window({"type": "update_url", "url": clipboard_content})

        elif (
            command_type == CommandType.ADD_TITLE
            or command_type == CommandType.ADD_ROLE
            or command_type == CommandType.ADD_JOB_TITLE
        ) and clipboard_content:
            logger.info("Processing ADD_TITLE command")
            self.show_window({"type": "update_title", "title": clipboard_content})

        elif command_type == CommandType.ADD_COMPANY and clipboard_content:
            logger.info("Processing ADD_COMPANY command")
            self.show_window({"type": "update_company", "company": clipboard_content})

        elif command_type == CommandType.ADD_LOCATION and clipboard_content:
            logger.info("Processing ADD_LOCATION command")
            self.show_window({"type": "update_location", "location": clipboard_content})

        elif command_type == CommandType.ADD_DURATION and clipboard_content:
            logger.info("Processing ADD_DURATION command")
            self.show_window({"type": "update_duration", "duration": clipboard_content})

        elif command_type == CommandType.ADD_DESCRIPTION and clipboard_content:
            logger.info("Processing ADD_DESCRIPTION command")
            self.show_window(
                {"type": "update_description", "description": clipboard_content}
            )

        elif command_type == CommandType.ADD_QUESTION and clipboard_content:
            logger.info("Processing ADD_QUESTION command")
            self.show_window({"type": "update_question", "question": clipboard_content})

        elif command_type == CommandType.ADD_ANSWER and clipboard_content:
            logger.info("Processing ADD_ANSWER command")
            self.show_window({"type": "update_answer", "answer": clipboard_content})

        elif (
            command_type == CommandType.ADD_NOTE
            or command_type == CommandType.ADD_NOTES
            or command_type == CommandType.ADD_NODES
        ) and clipboard_content:
            logger.info("Processing ADD_NOTE command")
            self.show_window({"type": "update_note", "note": clipboard_content})
