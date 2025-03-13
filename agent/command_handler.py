"""
Handles voice commands for job application management
"""

from typing import Optional, Tuple, Dict, Any
from enum import Enum
import logging
import json

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
            system_prompt="""<BEGIN SYSTEM PROMPT>
You are a voice command processor for a job application tracking system.
Your task is to identify explicit commands and determine if they are complete. You also must provide a reason for your decision.

When calling tools, ALWAYS use the EXACT parameter names:
- "command_type": Must be one of these exact values: ADD_URL, ADD_TITLE, ADD_COMPANY, ADD_LOCATION, ADD_DURATION, ADD_DESCRIPTION, ADD_QUESTION, ADD_ANSWER, ADD_NOTE, ADD_CHECK_URL, ADD_LINK, ADD_NOTES, ADD_ROLE, ADD_NODES, ADD_JOB_TITLE, UNKNOWN
- "reasoning": A brief explanation for your decision

STRICT RULES FOR USING TOOLS:
1. ONLY call process_command when the user explicitly mentions "add", "paste", or "update" followed by a specific, complete type (like "title", "url", "company")
2. Convert any "update" or "store" commands to their "ADD_" equivalents (e.g., "update title" should use command_type "ADD_TITLE")
3. ALWAYS call wait_for_completion (NOT process_command) when:
   - The user ONLY said "add" without specifying what to add
   - The user said something like "I need to add" without specifying what
   - The user said "add the" without completing the command
   - The command is unclear or ambiguous
   - The user expressed uncertainty about the command (e.g., "add title but I'm not sure")
   - The user said "add link wait" or similar with "wait" indicating uncertainty
4. DO NOT call ANY tool if the user is just making a statement or asking a question 
   - For example: "this job has good benefits" or "I like this company" should NOT trigger ANY tool calls
   - DO NOT respond with ANY tool call for casual conversation

EXAMPLES OF WHEN TO USE WAIT_FOR_COMPLETION:
- "add"
- "I need to add"
- "add the"
- "add title but I'm not sure"
- "add link wait"

EXAMPLES OF STATEMENTS THAT SHOULD NOT TRIGGER ANY TOOL CALLS:
- "this job has good benefits"
- "I like this company"

WHEN DETERMINING COMMAND TYPE:
- For "add title", use ADD_TITLE
- For "add link" or "add url", use ADD_URL (or ADD_LINK)
- For "add company", use ADD_COMPANY
- For "add location", use ADD_LOCATION
- For "add duration", use ADD_DURATION
- For "add description", use ADD_DESCRIPTION
- For "add question", use ADD_QUESTION
- For "add answer", use ADD_ANSWER
- For "add note" or "add notes", use ADD_NOTE (or ADD_NOTES)
- For unclear commands, use UNKNOWN

Remember, the clipboard will contain the relevant content - there are no parameters to provide in the command.
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

                # Extract arguments - could be a string or dict
                args = tool_call["function"]["arguments"]
                if not isinstance(args, dict):
                    try:
                        args = json.loads(args)
                    except (json.JSONDecodeError, TypeError):
                        logger.error("Error parsing tool arguments: Invalid arguments format")
                        return CommandType.UNKNOWN, False
                
                logger.debug("Parsed arguments: %s", args)
                
                # Extract command_type from different possible locations
                cmd_type_str = None
                if "command_type" in args:
                    cmd_type_str = args["command_type"]
                elif "parameters" in args and "command_type" in args["parameters"]:
                    cmd_type_str = args["parameters"]["command_type"]
                
                if not cmd_type_str:
                    logger.error("Missing command_type in arguments")
                    return CommandType.UNKNOWN, False

                try:
                    # Convert string format if needed (like UPDATE_ to ADD_)
                    if cmd_type_str.startswith("UPDATE_"):
                        cmd_type_str = cmd_type_str.replace("UPDATE_", "ADD_")
                    
                    cmd_type = CommandType[cmd_type_str]
                    is_complete = tool_call["function"]["name"] == "process_command"
                    logger.info(
                        "Determined command: type=%s, complete=%s",
                        cmd_type,
                        is_complete,
                    )
                    return cmd_type, is_complete
                except (KeyError, ValueError) as e:
                    logger.error("Error parsing command type: %s", e)
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
