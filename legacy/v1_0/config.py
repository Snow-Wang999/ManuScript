"""
ManuScript v1.0 配置管理
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

    # LLM API - 优先使用 Qwen，备用 DeepSeek / OpenRouter
    # Qwen (主要)
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    QWEN_API_BASE: str = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "qwen-plus")

    # DeepSeek (备用)
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # OpenRouter (备用)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_BASE: str = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    # 统一 LLM 接口 - 自动选择可用的 API
    @classmethod
    def get_llm_config(cls) -> dict:
        """获取可用的 LLM 配置"""
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

    # 兼容旧代码的属性
    @property
    def OPENAI_API_KEY(self) -> str:
        return self.get_llm_config()["api_key"]

    @property
    def OPENAI_API_BASE(self) -> str:
        return self.get_llm_config()["api_base"]

    @property
    def OPENAI_MODEL(self) -> str:
        return self.get_llm_config()["model"]

    # v1.0 特有配置
    MAX_QUERIES_PER_SECTION: int = int(os.getenv("MAX_QUERIES_PER_SECTION", "5"))
    TOP_K_CHUNKS: int = int(os.getenv("TOP_K_CHUNKS", "10"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "2"))
    VERIFIER_ENABLED: bool = os.getenv("VERIFIER_ENABLED", "true").lower() == "true"

    # 日志
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> list:
        """验证必需的配置项"""
        missing = []
        llm_config = cls.get_llm_config()
        if not llm_config["api_key"]:
            missing.append("LLM_API_KEY (QWEN/DEEPSEEK/OPENROUTER)")
        return missing


config = Config()
