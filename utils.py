"""
Shared utilities for lemon river
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Configuration manager that reads from environment variables.
    """
    
    @staticmethod
    def get_str(key: str, default: Optional[str] = None) -> str:
        """Get string value from environment variable."""
        return os.getenv(key, default or "")
    
    @staticmethod
    def get_int(key: str, default: Optional[int] = None) -> int:
        """Get integer value from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default or 0
        try:
            return int(value)
        except ValueError:
            return default or 0
    
    @staticmethod
    def get_float(key: str, default: Optional[float] = None) -> float:
        """Get float value from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default or 0.0
        try:
            return float(value)
        except ValueError:
            return default or 0.0
    
    @staticmethod
    def get_bool(key: str, default: Optional[bool] = None) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default or False
        return value.lower() in ("true", "1", "t", "yes", "y")
    
    @staticmethod
    def microphone_index() -> Optional[int]:
        """Get microphone index. None means use system default."""
        value = os.getenv("MICROPHONE_INDEX")
        if value is None or value.lower() == "default" or value.lower() == "none":
            return None
        try:
            return int(value)
        except ValueError:
            return None
    
    @staticmethod
    def max_queue_size() -> int:
        """Get maximum queue size."""
        return Config.get_int("MAX_QUEUE_SIZE", 0)
    
    @staticmethod
    def process_timeout() -> int:
        """Get process timeout in seconds."""
        return Config.get_int("PROCESS_TIMEOUT", 5)
    
    @staticmethod
    def debug_mode() -> bool:
        """Check if debug mode is enabled."""
        return Config.get_bool("DEBUG_MODE", False)
    
    @staticmethod
    def activation_phrase() -> str:
        """Get voice activation phrase."""
        return Config.get_str("ACTIVATION_PHRASE", "lemon river").lower()
    
    @staticmethod
    def deactivation_phrase() -> str:
        """Get voice deactivation phrase."""
        return Config.get_str("DEACTIVATION_PHRASE", "lemon sneeze").lower()
    
    @staticmethod
    def save_phrase() -> str:
        """Get voice save phrase."""
        return Config.get_str("SAVE_PHRASE", "lemon save").lower()
    
    @staticmethod
    def llm_model() -> str:
        """Get LLM model name."""
        return Config.get_str("LLM_MODEL", "llama3.2")
    
    @staticmethod
    def audio_recording_sample_rate() -> int:
        """Get audio recording sample rate."""
        return Config.get_int("AUDIO_RECORDING_SAMPLE_RATE", 44100)
    
    @staticmethod
    def audio_chunk_duration() -> float:
        """Get audio chunk duration in seconds."""
        return Config.get_float("AUDIO_CHUNK_DURATION", 0.5)
    
    @staticmethod
    def audio_silence_threshold() -> float:
        """Get silence threshold for audio detection."""
        return Config.get_float("AUDIO_SILENCE_THRESHOLD", 0.01)
    
    @staticmethod
    def audio_silence_duration() -> float:
        """Get duration of silence that ends recording (in seconds)."""
        return Config.get_float("AUDIO_SILENCE_DURATION", 1.5)
    
    @staticmethod
    def recordings_dir() -> str:
        """Get the directory path for audio recordings."""
        return Config.get_str("RECORDINGS_DIR", "./recordings")


def setup_process_logging(
    level: str = os.getenv("LOG_LEVEL", "DEBUG"),
    log_dir: str = os.getenv("LOG_DIR", "logs")
):
    """
    Setup logging for a new process.
    """
    root_logger = logging.getLogger()

    log_level = getattr(logging, level.upper(), logging.DEBUG)
    root_logger.setLevel(log_level)

    root_logger.handlers = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(log_format)
    
    root_logger.addHandler(console_handler)
    
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        log_filename = f"application_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(
            Path(log_dir) / log_filename
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)
    
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
    
    if os.getenv("DEBUG_MODE", "False").lower() == "true":
        logging.getLogger("urllib3").setLevel(logging.DEBUG)
        logging.getLogger("requests").setLevel(logging.DEBUG)
    else:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
