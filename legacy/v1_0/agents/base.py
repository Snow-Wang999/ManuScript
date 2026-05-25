"""
ManuScript v1.0 Agent 基类

所有 Agent 继承此基类
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from logger import get_logger


class AgentInput(BaseModel):
    """Agent 输入基类"""
    pass


class AgentOutput(BaseModel):
    """Agent 输出基类"""
    success: bool = True
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Agent 基类

    所有 Agent 必须实现:
    - name: Agent 名称
    - run(): 执行逻辑
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 名称"""
        pass

    @abstractmethod
    async def run(self, input_data: AgentInput) -> AgentOutput:
        """
        执行 Agent 逻辑

        Args:
            input_data: 输入数据

        Returns:
            输出数据
        """
        pass

    def log_start(self, input_data: Any) -> None:
        """记录开始日志"""
        self.logger.info(f"[{self.name}] 开始执行")

    def log_end(self, output_data: Any) -> None:
        """记录结束日志"""
        self.logger.info(f"[{self.name}] 执行完成")

    def log_error(self, error: Exception) -> None:
        """记录错误日志"""
        self.logger.error(f"[{self.name}] 执行失败: {error}")
