"""
ManuScript Langfuse 集成

提供统一的追踪和评测记录功能，支持所有版本的评测
"""
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator
from functools import wraps

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class LangfuseConfig:
    """Langfuse 配置"""
    public_key: str
    secret_key: str
    host: str = "https://cloud.langfuse.com"
    enabled: bool = True


def get_langfuse_config() -> LangfuseConfig:
    """从环境变量获取 Langfuse 配置"""
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # 如果没有配置 key，则禁用
    enabled = bool(public_key and secret_key)

    return LangfuseConfig(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
        enabled=enabled
    )


class LangfuseTracer:
    """
    Langfuse 追踪器

    封装 Langfuse 的 trace 和 span 功能，支持：
    - 追踪各版本的生成过程
    - 记录评测分数
    - 在 Dashboard 上可视化对比
    """

    def __init__(self, config: LangfuseConfig | None = None):
        self.config = config or get_langfuse_config()
        self._client = None
        self._current_trace = None

    @property
    def client(self):
        """延迟初始化 Langfuse 客户端"""
        if self._client is None and self.config.enabled:
            try:
                from langfuse import Langfuse
                self._client = Langfuse(
                    public_key=self.config.public_key,
                    secret_key=self.config.secret_key,
                    host=self.config.host
                )
            except ImportError:
                print("警告: langfuse 未安装，请运行 pip install langfuse")
                self.config.enabled = False
            except Exception as e:
                print(f"警告: Langfuse 初始化失败: {e}")
                self.config.enabled = False
        return self._client

    def is_enabled(self) -> bool:
        """检查 Langfuse 是否可用"""
        return self.config.enabled and self.client is not None

    @contextmanager
    def trace(
        self,
        name: str,
        version: str,
        test_case_id: str,
        metadata: dict | None = None
    ) -> Generator[Any, None, None]:
        """
        创建一个追踪上下文

        Args:
            name: 追踪名称（如 "write_section"）
            version: 版本号（如 "v0_1", "v2_0"）
            test_case_id: 测试用例 ID
            metadata: 额外元数据

        Yields:
            trace 对象（如果 Langfuse 不可用则为 None）

        Usage:
            with tracer.trace("write_section", "v0_1", "tc_001") as trace:
                # 执行生成逻辑
                result = await generate(...)
                # 记录结果
                if trace:
                    trace.update(output=result)
        """
        if not self.is_enabled():
            yield None
            return

        trace = self.client.trace(
            name=name,
            metadata={
                "version": version,
                "test_case_id": test_case_id,
                **(metadata or {})
            },
            tags=[version, test_case_id]
        )
        self._current_trace = trace

        try:
            yield trace
        finally:
            self._current_trace = None
            # 确保数据发送
            self.client.flush()

    @contextmanager
    def span(
        self,
        name: str,
        trace: Any = None,
        input_data: Any = None,
        metadata: dict | None = None
    ) -> Generator[Any, None, None]:
        """
        在 trace 中创建一个 span（子步骤）

        Args:
            name: span 名称（如 "rag_retrieval", "llm_generation"）
            trace: 父 trace 对象
            input_data: 输入数据
            metadata: 额外元数据

        Yields:
            span 对象
        """
        trace = trace or self._current_trace
        if trace is None:
            yield None
            return

        span = trace.span(
            name=name,
            input=input_data,
            metadata=metadata
        )

        try:
            yield span
        finally:
            pass

    def score(
        self,
        trace: Any,
        name: str,
        value: float,
        comment: str | None = None
    ) -> None:
        """
        为 trace 添加评分

        Args:
            trace: trace 对象
            name: 评分名称（如 "citation_accuracy", "faithfulness"）
            value: 评分值 (0-1)
            comment: 评分说明
        """
        if trace is None:
            return

        trace.score(
            name=name,
            value=value,
            comment=comment
        )

    def log_generation(
        self,
        trace: Any,
        name: str,
        model: str,
        prompt: str,
        completion: str,
        usage: dict | None = None
    ) -> None:
        """
        记录一次 LLM 生成

        Args:
            trace: trace 对象
            name: 生成名称
            model: 模型名称
            prompt: 输入 prompt
            completion: 生成结果
            usage: token 使用情况
        """
        if trace is None:
            return

        trace.generation(
            name=name,
            model=model,
            input=prompt,
            output=completion,
            usage=usage
        )

    def flush(self) -> None:
        """确保所有数据都已发送"""
        if self.client:
            self.client.flush()


# 全局单例
_tracer: LangfuseTracer | None = None


def get_tracer() -> LangfuseTracer:
    """获取全局 Langfuse 追踪器"""
    global _tracer
    if _tracer is None:
        _tracer = LangfuseTracer()
    return _tracer


def observe(name: str | None = None):
    """
    装饰器：自动追踪函数调用

    Usage:
        @observe("retrieve_chunks")
        async def retrieve(query: str) -> list[dict]:
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            func_name = name or func.__name__

            with tracer.span(func_name, input_data={"args": str(args), "kwargs": str(kwargs)}) as span:
                result = await func(*args, **kwargs)
                if span:
                    span.end(output=str(result)[:1000])  # 截断避免过长
                return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            func_name = name or func.__name__

            with tracer.span(func_name, input_data={"args": str(args), "kwargs": str(kwargs)}) as span:
                result = func(*args, **kwargs)
                if span:
                    span.end(output=str(result)[:1000])
                return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


if __name__ == "__main__":
    # 测试 Langfuse 连接
    tracer = get_tracer()

    if tracer.is_enabled():
        print("Langfuse 已连接")
        with tracer.trace("test_trace", "test", "test_001") as trace:
            print(f"创建了 trace: {trace}")
            tracer.score(trace, "test_score", 0.95, "测试评分")
        print("测试完成")
    else:
        print("Langfuse 未配置或不可用")
        print("请在 .env 中配置 LANGFUSE_PUBLIC_KEY 和 LANGFUSE_SECRET_KEY")
