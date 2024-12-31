"""
Ollama wrapper for the LLM model.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from ollama import chat
from utils import setup_process_logging, Config

load_dotenv()


@dataclass
class OllamaModelConfig:
    """
    Config for the Ollama Model.
    """

    model: str = Config.llm_model()
    # model: str = "qwen2.5:3b"
    # model: str = "llama3-groq-tool-use"

    # these will be overridden by the command handler
    # this is only here to show an example
    temperature: float = 0.6
    max_tokens: Optional[int] = 4096
    top_p: float = 0.95
    system_prompt: str = "You are a helpful assistant."


class OllamaClient:
    """
    Generates text using the Ollama API.
    """

    def __init__(self, config: OllamaModelConfig):
        self.config = config
        setup_process_logging()
        self.logger = logging.getLogger(__name__)
        self._messages = [{"role": "system", "content": config.system_prompt}]

    def complete(self, text: str) -> Dict[str, Any]:
        """
        Completes text using the LLM.
        """
        self.logger.info("Generating text for input: %s", text)
        try:
            self._messages.append({"role": "user", "content": text})
            response = chat(
                model=self.config.model,
                messages=self._messages,
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                    "top_p": self.config.top_p,
                },
            )
            self._messages.append(response["message"])
            return response
        except Exception as e:
            self.logger.error("Error generating text: %s", str(e), exc_info=True)
            raise


if __name__ == "__main__":
    client = OllamaClient(OllamaModelConfig())
    response = client.complete("What is love? Baby don't hurt me.")
    print(response["message"]["content"])
