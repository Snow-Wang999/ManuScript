# -*- coding: utf-8 -*-
"""
ManuScript v2.0 Configuration Management

Orchestrator-Worker dynamic dispatch version
"""
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """Configuration class for v2.0"""

    # RAGFlow API
    RAGFLOW_API_BASE: str = os.getenv("RAGFLOW_API_BASE", "http://localhost:9380")
    RAGFLOW_API_KEY: str = os.getenv("RAGFLOW_API_KEY", "")

    # LLM API - Priority: Qwen > DeepSeek > OpenRouter
    # Qwen (Primary)
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    QWEN_API_BASE: str = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "qwen-plus")

    # DeepSeek (Backup)
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # OpenRouter (Fallback)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_BASE: str = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    @classmethod
    def get_llm_config(cls) -> dict:
        """Get available LLM configuration with fallback"""
        if cls.QWEN_API_KEY:
            return {
                "api_key": cls.QWEN_API_KEY,
                "api_base": cls.QWEN_API_BASE,
                "model": cls.QWEN_MODEL,
                "provider": "qwen"
            }
        elif cls.DEEPSEEK_API_KEY:
            return {
                "api_key": cls.DEEPSEEK_API_KEY,
                "api_base": cls.DEEPSEEK_API_BASE,
                "model": cls.DEEPSEEK_MODEL,
                "provider": "deepseek"
            }
        elif cls.OPENROUTER_API_KEY:
            return {
                "api_key": cls.OPENROUTER_API_KEY,
                "api_base": cls.OPENROUTER_API_BASE,
                "model": cls.OPENROUTER_MODEL,
                "provider": "openrouter"
            }
        else:
            return {
                "api_key": "",
                "api_base": "",
                "model": "",
                "provider": "none"
            }

    # Compatibility properties for existing code
    @classmethod
    def get_api_key(cls) -> str:
        return cls.get_llm_config()["api_key"]

    @classmethod
    def get_api_base(cls) -> str:
        return cls.get_llm_config()["api_base"]

    @classmethod
    def get_model(cls) -> str:
        return cls.get_llm_config()["model"]

    # v2.0 Specific Configuration - Orchestrator-Worker
    MAX_PARALLEL_WORKERS: int = int(os.getenv("MAX_PARALLEL_WORKERS", "3"))

    # Section type classification
    SIMPLE_SECTION_TYPES: list[str] = [
        "background", "conclusion", "abstract", "introduction",
        "acknowledgement", "appendix"
    ]
    COMPLEX_SECTION_TYPES: list[str] = [
        "method", "methodology", "experiment", "results",
        "discussion", "analysis", "evaluation", "implementation"
    ]

    # Chinese section type mapping
    SECTION_TYPE_CN_MAP: dict[str, str] = {
        "background": "background",
        "conclusion": "conclusion",
        "abstract": "abstract",
        "introduction": "introduction",
        "method": "method",
        "methodology": "method",
        "experiment": "experiment",
        "results": "results",
        "discussion": "discussion",
        "analysis": "analysis"
    }

    # Retrieval settings
    TOP_K_CHUNKS: int = int(os.getenv("TOP_K_CHUNKS", "10"))
    MAX_QUERIES_PER_SECTION: int = int(os.getenv("MAX_QUERIES_PER_SECTION", "5"))

    # RAGFlow retrieval optimization (based on RAGFlow source analysis)
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))  # Filter low relevance (default 0.2)
    VECTOR_SIMILARITY_WEIGHT: float = float(os.getenv("VECTOR_SIMILARITY_WEIGHT", "0.5"))  # Balance semantic vs keyword (default 0.3)
    RERANK_MODEL_ID: str = os.getenv("RERANK_MODEL_ID", "gte-rerank")  # gte-rerank, bge-reranker-v2-m3

    # Worker settings
    SIMPLE_WORKER_QUERIES: int = 2
    COMPLEX_WORKER_QUERIES: int = 5
    REVIEW_MAX_ITERATIONS: int = 2

    # Log settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration"""
        missing = []
        if not cls.RAGFLOW_API_KEY:
            missing.append("RAGFLOW_API_KEY")
        llm_config = cls.get_llm_config()
        if not llm_config["api_key"]:
            missing.append("LLM_API_KEY (QWEN/DEEPSEEK/OPENROUTER)")
        return missing

    @classmethod
    def get_section_complexity(cls, section_type: str) -> str:
        """
        Determine section complexity based on type

        Returns: "simple", "complex", or "unknown"
        """
        section_type_lower = section_type.lower()
        if section_type_lower in cls.SIMPLE_SECTION_TYPES:
            return "simple"
        elif section_type_lower in cls.COMPLEX_SECTION_TYPES:
            return "complex"
        else:
            return "unknown"


config = Config()
