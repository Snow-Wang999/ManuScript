# -*- coding: utf-8 -*-
"""
ManuScript v0.1 Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """Configuration class"""

    # RAGFlow API
    RAGFLOW_API_BASE: str = os.getenv("RAGFLOW_API_BASE", "http://localhost:9380")
    RAGFLOW_API_KEY: str = os.getenv("RAGFLOW_API_KEY", "")

    # LLM API (Priority: Qwen > DeepSeek > OpenRouter > OpenAI)
    OPENAI_API_KEY: str = (
        os.getenv("QWEN_API_KEY") or
        os.getenv("DEEPSEEK_API_KEY") or
        os.getenv("OPENROUTER_API_KEY") or
        os.getenv("OPENAI_API_KEY", "")
    )
    OPENAI_API_BASE: str = (
        os.getenv("QWEN_API_BASE") or
        os.getenv("DEEPSEEK_API_BASE") or
        os.getenv("OPENROUTER_API_BASE") or
        os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    OPENAI_MODEL: str = (
        os.getenv("QWEN_MODEL") or
        os.getenv("DEEPSEEK_MODEL") or
        os.getenv("OPENROUTER_MODEL") or
        os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    )

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls, require_ragflow: bool = False) -> list[str]:
        """Validate required config, return list of missing items"""
        missing = []
        if require_ragflow and not cls.RAGFLOW_API_KEY:
            missing.append("RAGFLOW_API_KEY")
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        return missing


# Global config instance
config = Config()
