"""
Ollama wrapper for the LLM model.
"""

import logging
import os
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
from ollama import chat, embeddings
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

    temperature: float = Config.llm_temperature()
    max_tokens: int = Config.llm_max_tokens()
    top_p: float = Config.llm_top_p()
    top_k: int = Config.llm_top_k()
    system_prompt: str = "You are a helpful assistant."

    context_window: Optional[List[Dict[str, str]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for ollama API"""
        return {
            "temperature": self.temperature,
            "num_predict": self.max_tokens,
            "top_p": self.top_p,
            "top_k": self.top_k
        }


class OllamaClient:
    """
    Generates text using the Ollama API.
    """

    def __init__(self, config: OllamaModelConfig):
        self.config = config
        setup_process_logging()
        self.logger = logging.getLogger(__name__)
        self._messages = [{"role": "system", "content": config.system_prompt}]

        self.context_cache = {}
        if config.context_window is not None:
            self._messages.extend(config.context_window)

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
                options=self.config.to_dict()
            )
            self._messages.append(response["message"])

            if len(self._messages) > 10:
                # system prompt is [0], get 9 most recent messages + system prompt
                self._messages = [self._messages[0]] + self._messages[-9:]
                
            return response
        except Exception as e:
            self.logger.error("Error generating text: %s", str(e), exc_info=True)
            raise
    
    # useless for now
    def get_embedding(self, text: str) -> List[float]:
        """Get embeddings for text using Ollama"""
        try:
            response = embeddings(model=self.config.model, prompt=text)
            return response.get('embedding', [])
        except Exception as e:
            self.logger.error(f"Error getting embeddings: {str(e)}")
            return []


if __name__ == "__main__":
    client = OllamaClient(OllamaModelConfig())
    response = client.complete("What is love? Baby don't hurt me.")
    print(response["message"]["content"])
