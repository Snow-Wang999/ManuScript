"""
ManuScript v0.2 配置管理
"""
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """配置类"""

    # RAGFlow API
    RAGFLOW_API_BASE: str = os.getenv("RAGFLOW_API_BASE", "http://localhost:9380")
    RAGFLOW_API_KEY: str = os.getenv("RAGFLOW_API_KEY", "")

    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # v0.2 特有配置
    MAX_QUERIES_PER_SECTION: int = int(os.getenv("MAX_QUERIES_PER_SECTION", "3"))
    TOP_K_CHUNKS: int = int(os.getenv("TOP_K_CHUNKS", "5"))

    # 日志
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> list[str]:
        """验证必需的配置项"""
        missing = []
        if not cls.RAGFLOW_API_KEY:
            missing.append("RAGFLOW_API_KEY")
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        return missing


config = Config()
