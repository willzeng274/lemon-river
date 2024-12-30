"""
Ollama wrapper for the LLM model.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from ollama import chat

load_dotenv()

@dataclass
class OllamaModelConfig:
    """
    Config for all Ollama models
    """

    model: str = "llama3.2"
    temperature: float = 0.9
    max_tokens: Optional[int] = 4096
    top_p: float = 0.9
    system_prompt: str = "You are a helpful assistant."

class OllamaClient:
    """
    Generates text using the Ollama API.
    """

    def __init__(self, config: OllamaModelConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._messages = [{"role": "system", "content": config.system_prompt}]
 
    # This is actually not used in the codebase
    # keeping it here for testing purposes
    def complete(self, text: str) -> Dict[str, Any]:
        """
        Generate a completion for the given text.
        """
        self.logger.info("Generating completion for text: %s", text)
        try:
            self._messages.append({"role": "user", "content": text})
            response = chat(
                model=self.config.model,
                messages=self.messages,
                options={
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "top_p": self.config.top_p,
                }
            )
            self._messages.append(response["message"])
            # return raw so I can do more processing
            return response
        except Exception as e:
            self.logger.exception("Error generating completion: %s", e)
            # raise is probably better than just eating it
            # because template responses are not very helpful
            raise

if __name__ == "__main__":
    client = OllamaClient(OllamaModelConfig())
    response = client.complete("Hello, how are you?")
    print(response["message"]["content"])