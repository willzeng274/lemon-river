"""
Processes voice transcriptions through LLM.
"""

import logging
from multiprocessing import Queue
from queue import Empty
from collections import deque
from dotenv import load_dotenv

from llm import OllamaClient, OllamaModelConfig
from command_handler import CommandExecutor

load_dotenv()

ACTIVATION_PHRASE = "lemon river"
DEACTIVATION_PHRASE = "lemon sneeze"
SAVE_PHRASE = "lemon save"


class VoiceProcessor:
    """
    Processes voice transcriptions through LLM.
    """

    def __init__(self, max_tokens: int = 100, window_queue: Queue = None):
        self.context_window = deque(maxlen=max_tokens)
        self.session_active = False
        self.llm_client = OllamaClient(OllamaModelConfig())
        self.command_executor = CommandExecutor(window_queue) if window_queue else None

    def clear_context(self):
        """Clear the context window"""
        self.context_window.clear()

    def add_to_context(self, text: str):
        """Add new text to context window, splitting by words as rough token approximation"""
        words = text.split()
        self.context_window.extend(words)

    def get_context(self) -> str:
        """Get the current context window as a single string"""
        return " ".join(list(self.context_window))

    def process_command(self, text: str):
        """Process potential command text"""
        if self.command_executor:
            self.command_executor.process_voice_input(text)


def process_transcriptions(queue: Queue, window_queue: Queue, logger: logging.Logger):
    """
    Processes transcriptions from the queue and sends them to LLM.
    """
    logger.info("Starting LLM processor")
    processor = VoiceProcessor(window_queue=window_queue)
    
    timeout = 5.0

    while True:
        try:
            text = queue.get(timeout=timeout)
            logger.info("Processing transcription: %s", text)

            if ACTIVATION_PHRASE in text.lower():
                processor.session_active = True
                logger.info("Session activated: Sending show window command")
                window_queue.put({"type": "session_start"})
                processor.clear_context()
                continue
            elif DEACTIVATION_PHRASE in text.lower():
                processor.session_active = False
                processor.clear_context()
                logger.info("Session deactivated: Sending hide window command")
                window_queue.put({"type": "session_end"})
                continue
            elif SAVE_PHRASE in text.lower():
                processor.session_active = False
                processor.clear_context()
                logger.info("Session deactivated: Sending save command")
                window_queue.put({"type": "save"})
                continue

            if processor.session_active:
                processor.add_to_context(text)
                processor.process_command(text)
                processor.clear_context()
            else:
                logger.info(f"Waiting for activation phrase '{ACTIVATION_PHRASE}'")

        except Empty:
            continue
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error(f"Error processing transcription: {str(e)}", exc_info=True)


if __name__ == "__main__":
    from logging import getLogger

    logger_ = getLogger(__name__)
    process_transcriptions(Queue(), Queue(), logger_)
