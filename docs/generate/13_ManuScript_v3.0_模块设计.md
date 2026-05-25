# ManuScript v3.0 模块设计

> **文档版本**: 1.2
> **创建日期**: 2026-02-04
> **最后更新**: 2026-02-06
> **依据文档**: 11_ManuScript_v3.0_数据结构设计.md, 12_ManuScript_v3.0_接口定义.md

---

## 目录

1. [设计原则](#1-设计原则)
2. [目录结构](#2-目录结构)
3. [路由层模块](#3-路由层模块)
4. [主 Agent 模块](#4-主-agent-模块)
5. [工具层模块](#5-工具层模块)
6. [数据层模块](#6-数据层模块)
7. [API 层模块](#7-api-层模块)
8. [UI 层模块](#8-ui-层模块)
9. [模块依赖关系](#9-模块依赖关系)

---

## 1. 设计原则

### 1.1 架构原则

| 原则 | 说明 | 应用 |
|------|------|------|
| **分层隔离** | 各层只依赖下层，不跨层调用 | UI → Router → Agent → Tool → Data |
| **接口优先** | 先定义接口，再实现类 | 所有模块都有对应的 Interface 抽象类 |
| **依赖注入** | 通过构造函数注入依赖 | 便于测试和替换实现 |
| **单一职责** | 每个类只负责一个功能 | SearchTool 只负责检索，不负责存储 |
| **工具逻辑无状态** | 工具不持久化会话状态，可由容器单例管理实例 | 实例可复用，状态在 Agent/Repository |

### 1.2 命名规范

| 类型 | 命名规范 | 示例 |
|------|----------|------|
| 接口类 | `I{Name}` | `ISearchTool`, `IPaperRepository` |
| 实现类 | `{Name}Impl` 或直接 `{Name}` | `SearchTool`, `PaperRepository` |
| 工厂类 | `{Name}Factory` | `ToolFactory`, `RepositoryFactory` |
| 配置类 | `{Name}Config` | `SearchConfig`, `RouterConfig` |
| 异常类 | `{Name}Error` | `SearchError`, `PaperNotFoundError` |

### 1.3 依赖注入模式

```python
# 使用依赖注入的示例
class MainAgent:
    def __init__(
        self,
        search_tool: ISearchTool,
        note_tool: INoteTool,
        memory_manager: IMemoryManager,
        conversation_manager: IConversationManager,
    ):
        self._search_tool = search_tool
        self._note_tool = note_tool
        self._memory_manager = memory_manager
        self._conversation_manager = conversation_manager
```

---

## 2. 目录结构

### 2.1 完整目录树

```
v3_0/
├── main.py                          # 应用入口
├── config.py                        # 全局配置
├── logger.py                        # 日志配置
│
├── models/                          # 数据模型
│   ├── __init__.py
│   ├── paper.py                     # Paper 相关模型
│   ├── paragraph.py                 # Paragraph 相关模型
│   ├── note.py                      # Note 相关模型
│   ├── session.py                   # Session 相关模型
│   ├── message.py                   # Message 相关模型
│   ├── search.py                    # Search 相关模型
│   ├── memory.py                    # Memory 相关模型
│   └── error.py                     # 错误模型
│
├── schemas/                         # JSON Schema 定义
│   ├── __init__.py
│   └── schemas.py                   # 所有 JSON Schema
│
├── router/                          # 路由层
│   ├── __init__.py
│   ├── interface.py                 # 意图路由接口
│   ├── intent_router.py             # 意图路由实现
│   ├── route_config.py              # 路由配置
│   └── intent_detector.py           # 意图识别器
│
├── agent/                           # 主 Agent 层
│   ├── __init__.py
│   ├── interface.py                 # Agent 接口定义
│   ├── main_agent.py                # 主 Agent 实现
│   ├── conversation_manager.py      # 对话管理
│   ├── memory_manager.py            # 记忆管理
│   └── state.py                     # Agent 状态
│
├── tools/                           # 工具层
│   ├── __init__.py
│   ├── interface.py                 # 工具接口定义
│   ├── factory.py                   # 工具工厂
│   ├── search/
│   │   ├── __init__.py
│   │   ├── fulltext_search.py       # 全文检索（ripgrep + FTS5）
│   │   ├── vector_search.py         # 向量检索（ChromaDB）- 新增
│   │   ├── hybrid_search.py         # 混合检索（RRF融合）- 新增
│   │   ├── query_rewriter.py        # 查询改写器
│   │   └── result_ranker.py         # RRF融合排序器
│   ├── embedding/                   # 新增目录
│   │   ├── __init__.py
│   │   ├── interface.py             # Embedding接口
│   │   ├── local_embedding.py       # 本地BGE-M3
│   │   ├── api_embedding.py         # OpenAI API
│   │   └── embedding_factory.py     # 工厂类
│   ├── note/
│   │   ├── __init__.py
│   │   ├── note_manager.py          # 笔记管理工具
│   │   └── note_parser.py           # 笔记解析器
│   ├── summary/
│   │   ├── __init__.py
│   │   ├── summarizer.py            # 摘要生成工具
│   │   └── summary_prompt.py        # 摘要提示词模板
│   ├── parse/
│   │   ├── __init__.py
│   │   ├── paper_parser.py          # 论文解析工具
│   │   ├── marker_parser.py         # Marker解析器（学术PDF）- 新增
│   │   ├── pdf_parser.py            # PyMuPDF解析器（fallback）
│   │   ├── latex_parser.py          # LaTeX解析器 (P1)
│   │   └── paragraph_indexer.py     # 段落索引器
│   └── export/
│       ├── __init__.py
│       └── exporter.py              # 导出工具
│
├── repositories/                    # 数据层
│   ├── __init__.py
│   ├── interface.py                 # Repository 接口
│   ├── factory.py                   # Repository 工厂
│   ├── paper_repository.py          # 论文存储
│   ├── index_repository.py          # 索引存储
│   ├── vector_repository.py         # 向量索引存储（ChromaDB）- 新增
│   ├── fts_repository.py            # FTS5索引存储（SQLite）- 新增
│   ├── session_repository.py        # 会话存储
│   ├── summary_repository.py        # 摘要存储
│   ├── project_state_repository.py  # 项目状态
│   └── user_preferences_repository.py # 用户偏好
│
├── api/                             # API 层
│   ├── __init__.py
│   ├── app.py                       # FastAPI 应用
│   ├── middleware.py                # 中间件
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── papers.py                # 论文相关路由
│   │   ├── search.py                # 检索相关路由
│   │   ├── notes.py                 # 笔记相关路由
│   │   ├── sessions.py              # 会话相关路由
│   │   ├── export.py                # 导出相关路由
│   │   └── websocket.py             # WebSocket 路由
│   └── dependencies.py              # 依赖注入
│
├── ui/                              # UI 层 (Gradio)
│   ├── __init__.py
│   ├── app.py                       # Gradio 应用
│   ├── components/
│   │   ├── __init__.py
│   │   ├── session_list.py          # 会话列表组件
│   │   ├── chat_area.py             # 对话区域组件
│   │   ├── trace_sidebar.py         # 溯源侧边栏组件
│   │   └── status_bar.py            # 状态栏组件
│   └── callbacks.py                 # 回调函数
│
├── services/                        # 业务服务
│   ├── __init__.py
│   ├── search_service.py            # 检索服务
│   ├── parse_service.py             # 解析服务
│   ├── export_service.py            # 导出服务
│   └── llm_service.py               # LLM 服务
│
├── utils/                           # 工具函数
│   ├── __init__.py
│   ├── file_utils.py                # 文件操作
│   ├── hash_utils.py                # 哈希计算
│   ├── id_generator.py              # ID 生成器
│   ├── datetime_utils.py            # 时间处理
│   └── ripgrep_wrapper.py           # ripgrep 封装
│
├── config/                          # 配置文件目录
│   ├── settings.yaml                # 系统设置
│   └── prompts.yaml                 # LLM 提示词
│
├── tests/                           # 测试
│   ├── __init__.py
│   ├── unit/                        # 单元测试
│   ├── integration/                 # 集成测试
│   └── fixtures/                    # 测试数据
│
└── ../data/                         # 仓库级运行时数据目录（gitignore）
    ├── papers/                      # 论文存储
    │   ├── {paper_id}/
    │   │   ├── metadata.json
    │   │   ├── content.md
    │   │   ├── notes.md
    │   │   └── index.json
    │   └── _papers_index.json
    ├── memory/                      # 记忆存储
    │   ├── sessions/
    │   ├── summaries/
    │   ├── project_state.json
    │   └── user_preferences.json
    ├── cache/                       # 缓存
    ├── exports/                     # 导出文件
    └── logs/                        # 日志
```

### 2.2 模块分层图

```
┌─────────────────────────────────────────────────────────────┐
│                        UI Layer (Gradio)                     │
│                     ui/app.py, components/                   │
└────────────────────────────────────┬────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────┐
│                      API Layer (FastAPI)                     │
│                   api/app.py, api/routes/                    │
└────────────────────────────────────┬────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────┐
│                    Router Layer (路由层)                     │
│              router/intent_router.py, route_config.py        │
└────────────────────────────────────┬────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────┐
│                   Main Agent Layer (主 Agent)                │
│    agent/main_agent.py, conversation_manager.py, memory/     │
└────────────────────────────────────┬────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────┐
│                    Tool Layer (工具层)                       │
│        tools/search/, tools/note/, tools/summary/, ...       │
└────────────────────────────────────┬────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────┐
│                   Data Layer (数据层)                        │
│                repositories/, models/                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 路由层模块

### 3.1 模块结构

```
router/
├── interface.py          # 接口定义
├── intent_router.py      # 意图路由实现
├── route_config.py       # 路由配置
└── intent_detector.py    # 意图识别器
```

### 3.2 接口定义

```python
# router/interface.py

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Optional
from pydantic import BaseModel
from models.message import Message


class IntentType(str, Enum):
    """意图类型枚举"""
    CHAT = "chat"
    SEARCH = "search"
    NOTE_SEARCH = "note_search"
    NOTE_ADD = "note_add"
    NOTE_EDIT = "note_edit"
    SUMMARIZE = "summarize"
    EXPORT = "export"
    PARSE = "parse"
    TRACE = "trace"


class IntentResult(BaseModel):
    """意图识别结果"""
    intent: IntentType
    confidence: float
    parameters: dict
    should_route_to_llm: bool


class IIntentDetector(ABC):
    """意图识别器接口"""

    @abstractmethod
    async def detect(self, query: str, context: Optional[dict] = None) -> IntentResult:
        """识别用户意图"""
        pass


class IIntentRouter(ABC):
    """意图路由器接口"""

    @abstractmethod
    async def route(self, message: Message, context: Optional[dict] = None) -> dict:
        """根据意图路由请求"""
        pass

    @abstractmethod
    def register_handler(self, intent: IntentType, handler: Callable):
        """注册意图处理器"""
        pass
```

### 3.3 意图识别器

```python
# router/intent_detector.py

from typing import Optional
import re
from router.interface import IIntentDetector, IntentResult, IntentType


class IntentDetector(IIntentDetector):
    """基于规则的意图识别器（MVP）"""

    # 意图关键词映射
    INTENT_PATTERNS = {
        IntentType.SEARCH: [
            r"搜索", r"查找", r"找", r"search", r"find",
            r"有哪些", r"关于", r"怎么样"
        ],
        IntentType.NOTE_SEARCH: [
            r"我的笔记", r"笔记里", r"note"
        ],
        IntentType.NOTE_ADD: [
            r"添加笔记", r"新建笔记", r"记一下", r"add note"
        ],
        IntentType.NOTE_EDIT: [
            r"编辑笔记", r"修改笔记", r"edit note"
        ],
        IntentType.SUMMARIZE: [
            r"总结", r"摘要", r"summarize", r"生成摘要"
        ],
        IntentType.EXPORT: [
            r"导出", r"export", r"下载"
        ],
        IntentType.TRACE: [
            r"查看原文", r"溯源", r"trace", r"定位"
        ],
    }

    # 笔记添加的特殊标记
    NOTE_ADD_PREFIX = "//note"

    async def detect(self, query: str, context: Optional[dict] = None) -> IntentResult:
        """
        识别用户意图

        Args:
            query: 用户输入
            context: 上下文信息

        Returns:
            IntentResult: 识别结果
        """
        query_lower = query.lower().strip()

        # 检查特殊前缀
        if query_lower.startswith(self.NOTE_ADD_PREFIX):
            return IntentResult(
                intent=IntentType.NOTE_ADD,
                confidence=1.0,
                parameters={"content": query[len(self.NOTE_ADD_PREFIX):].strip()},
                should_route_to_llm=False
            )

        # 匹配关键词模式
        best_intent = IntentType.CHAT  # 默认为闲聊
        best_score = 0

        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in query_lower:
                    score = len(pattern) / len(query_lower)
                    if score > best_score:
                        best_score = score
                        best_intent = intent

        # 判断是否需要 LLM 处理
        should_route_to_llm = best_intent == IntentType.CHAT

        return IntentResult(
            intent=best_intent,
            confidence=min(best_score + 0.5, 1.0),
            parameters={"query": query},
            should_route_to_llm=should_route_to_llm
        )


class LLMIntentDetector(IIntentDetector):
    """基于 LLM 的意图识别器（P1）"""

    def __init__(self, llm_service: 'ILLMService'):
        self._llm = llm_service

    async def detect(self, query: str, context: Optional[dict] = None) -> IntentResult:
        """使用 LLM 识别意图"""
        # P1 实现
        pass
```

### 3.4 意图路由器

```python
# router/intent_router.py

from typing import Callable, Dict, Optional
import asyncio
import logging
from pydantic import BaseModel
from router.interface import IIntentRouter, IntentResult, IntentType
from models.message import Message

logger = logging.getLogger(__name__)


class RouteHandler(BaseModel):
    """路由处理器"""
    handler: Callable
    require_llm: bool = False
    timeout: int = 30


class IntentRouter(IIntentRouter):
    """意图路由器"""

    def __init__(self, detector: 'IIntentDetector'):
        self._detector = detector
        self._handlers: Dict[IntentType, RouteHandler] = {}
        self._default_handler: Optional[RouteHandler] = None

    def register_handler(
        self,
        intent: IntentType,
        handler: Callable,
        require_llm: bool = False,
        timeout: int = 30
    ):
        """注册意图处理器"""
        self._handlers[intent] = RouteHandler(
            handler=handler,
            require_llm=require_llm,
            timeout=timeout
        )

    def set_default_handler(
        self,
        handler: Callable,
        require_llm: bool = False,
        timeout: int = 30
    ):
        """设置默认处理器"""
        self._default_handler = RouteHandler(
            handler=handler,
            require_llm=require_llm,
            timeout=timeout
        )

    async def route(self, message: Message, context: Optional[dict] = None) -> dict:
        """
        根据意图路由请求

        Args:
            message: 用户消息
            context: 上下文

        Returns:
            dict: 处理结果
        """
        # 识别意图
        intent_result = await self._detector.detect(
            message.content,
            context
        )

        logger.info(f"Intent detected: {intent_result.intent} (confidence: {intent_result.confidence})")

        # 获取处理器
        handler_info = self._handlers.get(intent_result.intent)
        if not handler_info:
            handler_info = self._default_handler

        if not handler_info:
            raise ValueError(f"No handler registered for intent: {intent_result.intent}")

        # 调用处理器
        try:
            result = await asyncio.wait_for(
                handler_info.handler(message, intent_result.parameters),
                timeout=handler_info.timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"Handler timeout for intent: {intent_result.intent}")
            raise
```

### 3.5 路由配置

```python
# router/route_config.py

from router.intent_router import IntentRouter, RouteHandler
from router.intent_detector import IntentDetector
from tools.search.fulltext_search import FulltextSearchTool
from tools.note.note_manager import NoteManager
from tools.summary.summarizer import Summarizer
from agent.main_agent import MainAgent


def create_router(
    search_tool: 'ISearchTool',
    note_tool: 'INoteTool',
    summary_tool: 'ISummarizer',
    main_agent: 'IMainAgent',
) -> IntentRouter:
    """创建配置好的路由器"""

    detector = IntentDetector()
    router = IntentRouter(detector)

    # 注册处理器
    router.register_handler(
        IntentType.SEARCH,
        handler=lambda msg, params: search_tool.search(
            SearchQuery(query=params["query"])
        ),
        require_llm=False,
        timeout=5
    )

    router.register_handler(
        IntentType.NOTE_SEARCH,
        handler=lambda msg, params: note_tool.search(params["query"]),
        require_llm=False,
        timeout=3
    )

    router.register_handler(
        IntentType.NOTE_ADD,
        handler=lambda msg, params: note_tool.create(
            NoteCreate(**params)
        ),
        require_llm=False,
        timeout=3
    )

    router.register_handler(
        IntentType.SUMMARIZE,
        handler=lambda msg, params: summary_tool.generate(
            SummaryRequest(**params)
        ),
        require_llm=True,
        timeout=30
    )

    router.register_handler(
        IntentType.CHAT,
        handler=lambda msg, params: main_agent.process_message(
            msg.content,
            params.get("session_id")
        ),
        require_llm=True,
        timeout=30
    )

    return router
```

---

## 4. 主 Agent 模块

### 4.1 模块结构

```
agent/
├── interface.py              # 接口定义
├── main_agent.py             # 主 Agent 实现
├── conversation_manager.py   # 对话管理
├── memory_manager.py         # 记忆管理
└── state.py                  # Agent 状态
```

### 4.2 接口定义

```python
# agent/interface.py

from abc import ABC, abstractmethod
from typing import Optional, List
from models.message import Message
from models.session import Session, AgentState


class IMainAgent(ABC):
    """主 Agent 接口"""

    @abstractmethod
    async def initialize(self, session_id: str) -> AgentState:
        """初始化 Agent 状态"""
        pass

    @abstractmethod
    async def process_message(self, message: str, session_id: str) -> str:
        """处理用户消息"""
        pass

    @abstractmethod
    async def get_state(self, session_id: str) -> AgentState:
        """获取当前状态"""
        pass

    @abstractmethod
    async def should_summarize(self, session_id: str) -> bool:
        """判断是否需要摘要"""
        pass


class IConversationManager(ABC):
    """对话管理器接口"""

    @abstractmethod
    async def add_message(self, session_id: str, message: Message) -> Message:
        """添加消息"""
        pass

    @abstractmethod
    async def get_history(self, session_id: str, limit: int = 100) -> List[Message]:
        """获取历史"""
        pass

    @abstractmethod
    async def get_context(self, session_id: str) -> dict:
        """获取上下文"""
        pass

    @abstractmethod
    async def estimate_tokens(self, messages: List[Message]) -> int:
        """估算 Token"""
        pass


class IMemoryManager(ABC):
    """记忆管理器接口"""

    @abstractmethod
    async def store(self, item: dict, memory_type: str) -> str:
        """存储记忆"""
        pass

    @abstractmethod
    async def retrieve(self, query: dict) -> List[dict]:
        """检索记忆"""
        pass

    @abstractmethod
    async def get_global_context(self) -> dict:
        """获取全局上下文"""
        pass

    @abstractmethod
    async def create_summary(self, session_id: str, summary_type: str) -> dict:
        """创建摘要"""
        pass
```

### 4.3 主 Agent 实现

```python
# agent/main_agent.py

from typing import Optional
from agent.interface import IMainAgent, IConversationManager, IMemoryManager
from agent.state import AgentState
from models.message import Message
from tools.interface import ISearchTool, INoteTool


class MainAgent(IMainAgent):
    """
    主 Agent - 有状态的协调者

    职责：
    1. 管理对话状态
    2. 理解用户意图
    3. 协调工具调用
    4. 管理长期记忆
    """

    def __init__(
        self,
        conversation_manager: IConversationManager,
        memory_manager: IMemoryManager,
        search_tool: ISearchTool,
        note_tool: INoteTool,
        llm_service: 'ILLMService',
    ):
        self._conversation = conversation_manager
        self._memory = memory_manager
        self._search = search_tool
        self._note = note_tool
        self._llm = llm_service

        # 状态缓存（可选，用于性能优化）
        self._state_cache: dict[str, AgentState] = {}

    async def initialize(self, session_id: str) -> AgentState:
        """初始化 Agent 状态"""
        state = AgentState(
            session_id=session_id,
            current_intent=None,
            user_journey_state="exploring",
            pending_tasks=[],
            context=await self._memory.get_global_context()
        )
        self._state_cache[session_id] = state
        return state

    async def process_message(self, message: str, session_id: str) -> str:
        """
        处理用户消息

        流程：
        1. 添加用户消息到历史
        2. 获取对话上下文
        3. 调用 LLM 生成响应
        4. 添加助手消息到历史
        5. 检查是否需要摘要
        """
        # 1. 添加用户消息
        user_msg = Message(
            message_id=generate_message_id(),
            role="user",
            content=message,
            timestamp=datetime.utcnow()
        )
        await self._conversation.add_message(session_id, user_msg)

        # 2. 获取上下文
        context = await self._build_context(session_id)

        # 3. 调用 LLM
        response = await self._llm.chat(
            messages=context["messages"],
            tools=[self._search, self._note],
            context=context
        )

        # 4. 添加助手消息
        assistant_msg = Message(
            message_id=generate_message_id(),
            role="assistant",
            content=response["content"],
            timestamp=datetime.utcnow(),
            metadata=response.get("metadata", {})
        )
        await self._conversation.add_message(session_id, assistant_msg)

        # 5. 检查是否需要摘要
        if await self.should_summarize(session_id):
            await self._memory.create_summary(session_id, "auto")

        return response["content"]

    async def get_state(self, session_id: str) -> AgentState:
        """获取当前状态"""
        if session_id in self._state_cache:
            return self._state_cache[session_id]

        # 从存储加载
        state = await self._load_state(session_id)
        self._state_cache[session_id] = state
        return state

    async def should_summarize(self, session_id: str) -> bool:
        """判断是否需要摘要"""
        messages = await self._conversation.get_history(session_id)
        token_count = await self._conversation.estimate_tokens(messages)

        # 获取配置
        from config import settings
        threshold = settings.TOKEN_WARNING_THRESHOLD

        return token_count >= threshold

    async def _build_context(self, session_id: str) -> dict:
        """构建对话上下文"""
        messages = await self._conversation.get_history(session_id)
        global_context = await self._memory.get_global_context()

        return {
            "messages": messages,
            "global_context": global_context,
            "session_id": session_id
        }
```

### 4.4 对话管理器

```python
# agent/conversation_manager.py

from typing import List, Optional
from agent.interface import IConversationManager
from models.message import Message
from repositories.session_repository import ISessionRepository


class ConversationManager(IConversationManager):
    """对话管理器"""

    def __init__(
        self,
        session_repo: ISessionRepository,
        max_history: int = 1000
    ):
        self._session_repo = session_repo
        self._max_history = max_history
        self._message_cache: dict[str, List[Message]] = {}

    async def add_message(self, session_id: str, message: Message) -> Message:
        """添加消息到会话"""
        # 存储消息
        await self._session_repo.add_message(session_id, message)

        # 更新缓存
        if session_id not in self._message_cache:
            self._message_cache[session_id] = []
        self._message_cache[session_id].append(message)

        # 限制缓存大小
        if len(self._message_cache[session_id]) > self._max_history:
            self._message_cache[session_id] = self._message_cache[session_id][-self._max_history:]

        return message

    async def get_history(self, session_id: str, limit: int = 100) -> List[Message]:
        """获取对话历史"""
        # 优先从缓存获取
        if session_id in self._message_cache:
            cached = self._message_cache[session_id]
            return cached[-limit:] if len(cached) > limit else cached

        # 从存储加载
        messages = await self._session_repo.get_messages(session_id, limit)
        self._message_cache[session_id] = messages
        return messages

    async def get_context(self, session_id: str) -> dict:
        """获取对话上下文"""
        messages = await self.get_history(session_id)
        session = await self._session_repo.get_session(session_id)

        return {
            "session_id": session_id,
            "messages": messages,
            "total_tokens": await self.estimate_tokens(messages),
            "current_state": session.state if session else None,
            "last_paper_id": session.context.get("last_paper_id") if session else None
        }

    async def estimate_tokens(self, messages: List[Message]) -> int:
        """估算 Token 数量"""
        # 简单估算：英文约 4 字符/token，中文约 2 字符/token
        total_chars = sum(len(m.content) for m in messages)

        # 检测中英文比例
        chinese_chars = sum(sum(1 for c in m.content if '\u4e00' <= c <= '\u9fff') for m in messages)
        english_chars = total_chars - chinese_chars

        return int(chinese_chars / 2 + english_chars / 4)

    async def trim_history(self, session_id: str, max_tokens: int) -> List[Message]:
        """裁剪历史（保留最近的消息）"""
        messages = await self.get_history(session_id)
        result = []
        total_tokens = 0

        for msg in reversed(messages):
            msg_tokens = len(msg.content) // 3  # 粗略估算
            if total_tokens + msg_tokens > max_tokens:
                break
            result.insert(0, msg)
            total_tokens += msg_tokens

        return result
```

### 4.5 记忆管理器

```python
# agent/memory_manager.py

from typing import List, Optional
from agent.interface import IMemoryManager
from repositories.summary_repository import ISummaryRepository
from repositories.project_state_repository import IProjectStateRepository
from tools.summary.summarizer import ISummarizer


class MemoryManager(IMemoryManager):
    """
    记忆管理器 - 三层记忆策略

    1. 全局共享：论文库元数据、用户笔记、项目状态、用户偏好
    2. 会话独立：对话历史、临时搜索结果
    3. 可引用：会话摘要、关键事实
    """

    def __init__(
        self,
        summary_repo: ISummaryRepository,
        project_state_repo: IProjectStateRepository,
        summarizer: ISummarizer,
    ):
        self._summary_repo = summary_repo
        self._project_state_repo = project_state_repo
        self._summarizer = summarizer

    async def store(self, item: dict, memory_type: str) -> str:
        """存储记忆项"""
        if memory_type == "global":
            # 存储到项目状态
            await self._project_state_repo.update_state(item)
        elif memory_type == "summary":
            # 存储摘要
            summary = await self._summary_repo.create(item)
            return summary.summary_id

        return item.get("id", "")

    async def retrieve(self, query: dict) -> List[dict]:
        """检索记忆"""
        memory_type = query.get("memory_type", "all")

        if memory_type in ["global", "all"]:
            state = await self._project_state_repo.get_state()
            return [state.model_dump()]

        if memory_type in ["summary", "all"]:
            session_id = query.get("session_id")
            summaries = await self._summary_repo.list_by_session(session_id)
            return [s.model_dump() for s in summaries]

        return []

    async def get_global_context(self) -> dict:
        """获取全局上下文"""
        state = await self._project_state_repo.get_state()
        return {
            "research_topic": state.research_topic,
            "research_stage": state.research_stage,
            "total_papers": state.total_papers,
            "total_notes": state.total_notes,
            "recent_papers": state.recent_papers
        }

    async def get_session_memory(self, session_id: str) -> dict:
        """获取会话独立记忆"""
        # 会话独立记忆存储在 session repository 中
        pass

    async def get_summaries(self, session_id: Optional[str] = None) -> List[dict]:
        """获取会话摘要"""
        if session_id:
            summaries = await self._summary_repo.list_by_session(session_id)
        else:
            summaries = await self._summary_repo.list_all()
        return [s.model_dump() for s in summaries]

    async def create_summary(self, session_id: str, summary_type: str) -> dict:
        """创建会话摘要"""
        from tools.summary import SummaryRequest

        request = SummaryRequest(
            session_id=session_id,
            summary_type=summary_type
        )
        summary = await self._summarizer.generate(request)
        return summary.model_dump()
```

---

## 5. 工具层模块

### 5.1 模块结构

```
tools/
├── interface.py              # 工具接口定义
├── factory.py                # 工具工厂
├── search/
│   ├── fulltext_search.py    # 全文检索工具
│   ├── query_rewriter.py     # 查询改写器
│   └── result_ranker.py      # 结果排序器
├── note/
│   ├── note_manager.py       # 笔记管理工具
│   └── note_parser.py        # 笔记解析器
├── summary/
│   ├── summarizer.py         # 摘要生成工具
│   └── summary_prompt.py     # 摘要提示词模板
├── parse/
│   ├── paper_parser.py       # 论文解析工具
│   ├── pdf_parser.py         # PDF 解析器
│   ├── latex_parser.py       # LaTeX 解析器
│   └── paragraph_indexer.py  # 段落索引器
└── export/
    └── exporter.py           # 导出工具
```

### 5.2 混合检索工具（重构）

```python
# tools/search/fulltext_search.py
# 关键词检索（ripgrep + FTS5）

import asyncio
from typing import Optional
from tools.interface import IFulltextSearchTool
from models.search import SearchQuery, SearchResponse, SearchResult
from repositories.index_repository import IIndexRepository
from repositories.paper_repository import IPaperRepository
from repositories.fts_repository import IFTSRepository  # 新增
from utils.ripgrep_wrapper import RipgrepWrapper


class FulltextSearchTool(IFulltextSearchTool):
    """
    关键词检索工具 - ripgrep + FTS5

    检索策略：
    1. ripgrep 精确匹配
    2. FTS5 模糊匹配
    3. 合并去重
    """

    def __init__(
        self,
        paper_repo: IPaperRepository,
        index_repo: IIndexRepository,
        fts_repo: IFTSRepository,      # 新增
        ripgrep: RipgrepWrapper
    ):
        self._paper_repo = paper_repo
        self._index_repo = index_repo
        self._fts_repo = fts_repo
        self._ripgrep = ripgrep

    async def search(self, query: str, top_k: int = 20) -> list[SearchResult]:
        """
        执行关键词检索

        Returns:
            list[SearchResult]: 检索结果
        """
        # 1. ripgrep 精确匹配
        ripgrep_results = await self._ripgrep_search(query, top_k)

        # 2. FTS5 模糊匹配
        fts_results = await self._fts_repo.search(query, top_k)

        # 3. 合并去重
        return self._merge_results(ripgrep_results, fts_results, top_k)

    async def _ripgrep_search(self, query: str, top_k: int) -> list[SearchResult]:
        """ripgrep 精确匹配"""
        # ... ripgrep 搜索逻辑

    async def _merge_results(
        self,
        ripgrep_results: list[SearchResult],
        fts_results: list[SearchResult],
        top_k: int
    ) -> list[SearchResult]:
        """合并去重，优先保留 ripgrep 结果"""
        # ... 合并逻辑


# tools/search/vector_search.py（新增）
# 向量检索（ChromaDB）

class VectorSearchTool(IVectorSearchTool):
    """
    向量检索工具 - ChromaDB

    检索策略：
    1. 查询向量化
    2. ChromaDB 向量相似度搜索
    3. 返回排序结果
    """

    def __init__(
        self,
        vector_repo: IVectorRepository,
        embedding_service: IEmbeddingService
    ):
        self._vector_repo = vector_repo
        self._embedding_service = embedding_service

    async def search(self, query: str, top_k: int = 20) -> list[SearchResult]:
        """向量检索"""
        # 1. 查询向量化
        query_vector = await self._embedding_service.encode([query])

        # 2. 向量相似度搜索
        results = await self._vector_repo.search(
            query_embedding=query_vector[0],
            top_k=top_k
        )

        # 3. 转换为 SearchResult
        return [self._to_search_result(r) for r in results]


# tools/search/hybrid_search.py（新增）
# 混合检索（RRF融合）

class HybridSearchTool(ISearchTool):
    """
    混合检索工具 - RRF融合排序

    检索策略：
    1. 并行执行关键词和向量检索
    2. RRF (Reciprocal Rank Fusion) 融合
    3. 返回 Top-K 结果
    """

    def __init__(
        self,
        fulltext_tool: IFulltextSearchTool,
        vector_tool: IVectorSearchTool,
        ranker: IResultRanker
    ):
        self._fulltext_tool = fulltext_tool
        self._vector_tool = vector_tool
        self._ranker = ranker

    async def search(
        self,
        query: SearchQuery,
        mode: str = "hybrid"
    ) -> SearchResponse:
        """
        混合检索

        Args:
            query: 检索查询
            mode: 检索模式
                - keyword: 仅关键词（ripgrep + FTS5）
                - vector: 仅向量（ChromaDB）
                - hybrid: 混合（默认，RRF融合）
        """
        if mode == "keyword":
            keyword_results = await self._fulltext_tool.search(query.query, query.top_k)
            return SearchResponse(
                results=keyword_results,
                total=len(keyword_results),
                returned=len(keyword_results),
                query=query.query,
                search_mode="keyword",
                search_duration_ms=0
            )
        elif mode == "vector":
            vector_results = await self._vector_tool.search(query.query, query.top_k)
            return SearchResponse(
                results=vector_results,
                total=len(vector_results),
                returned=len(vector_results),
                query=query.query,
                search_mode="vector",
                search_duration_ms=0
            )
        else:
            # 混合模式
            # 1. 并行检索
            keyword_results, vector_results = await asyncio.gather(
                self._fulltext_tool.search(query.query, query.top_k * 2),
                self._vector_tool.search(query.query, query.top_k * 2)
            )

            # 2. RRF 融合
            fused = await self._ranker.rrf_fusion(
                keyword_results,
                vector_results
            )

            return SearchResponse(
                results=fused[:query.top_k],
                total=len(fused),
                returned=query.top_k,
                query=query.query,
                search_mode="hybrid",
                search_duration_ms=0
            )


# tools/search/result_ranker.py（修改）
# RRF 融合排序器

class ResultRanker(IResultRanker):
    """结果排序器 - RRF 融合"""

    async def rrf_fusion(
        self,
        keyword_results: list[SearchResult],
        vector_results: list[SearchResult],
        k: int = 60
    ) -> list[SearchResult]:
        """
        Reciprocal Rank Fusion 融合排序

        公式：score = 1/(k + rank)
        """
        # 计算每个结果的 RRF 得分
        scores = {}

        for rank, result in enumerate(keyword_results):
            paragraph_id = result.paragraph_id
            scores[paragraph_id] = scores.get(paragraph_id, 0) + 1/(k + rank + 1)
            result.keyword_score = 1 - rank/len(keyword_results)  # 归一化

        for rank, result in enumerate(vector_results):
            paragraph_id = result.paragraph_id
            scores[paragraph_id] = scores.get(paragraph_id, 0) + 1/(k + rank + 1)
            result.vector_score = 1 - rank/len(vector_results)  # 归一化

        # 合并结果并设置最终得分
        merged = {r.paragraph_id: r for r in keyword_results + vector_results}
        for paragraph_id, result in merged.items():
            result.final_score = min(scores.get(paragraph_id, 0), 1.0)
            result.match_source = "hybrid"

        # 按 RRF 得分排序
        return sorted(merged.values(), key=lambda r: r.final_score, reverse=True)
```

### 5.3 笔记管理工具

```python
# tools/note/note_manager.py

from typing import Optional
from tools.interface import INoteTool
from models.note import Note, NoteCreate, NoteUpdate
from repositories.paper_repository import IPaperRepository
from utils.id_generator import generate_note_id


class NoteManager(INoteTool):
    """笔记管理工具"""

    def __init__(self, paper_repo: IPaperRepository):
        self._paper_repo = paper_repo

    async def create(self, request: NoteCreate) -> Note:
        """创建笔记"""
        # 生成笔记 ID
        note_id = generate_note_id()

        # 构建笔记内容（Markdown 格式）
        content = self._format_note_content(request)

        # 追加到 notes.md
        notes_path = await self._paper_repo.get_notes_path(request.paper_id)
        with open(notes_path, 'a', encoding='utf-8') as f:
            f.write(content)

        # 更新元数据
        await self._paper_repo.increment_notes(request.paper_id)

        return Note(
            note_id=note_id,
            paper_id=request.paper_id,
            linked_paragraphs=request.linked_paragraphs,
            content=request.content,
            tags=request.tags,
            created_at=datetime.utcnow()
        )

    async def get(self, note_id: str) -> Optional[Note]:
        """获取笔记"""
        # 从 notes.md 解析
        pass

    async def update(self, request: NoteUpdate) -> Note:
        """更新笔记"""
        # 需要重写整个 notes.md
        pass

    async def delete(self, note_id: str) -> bool:
        """删除笔记"""
        pass

    async def list_by_paper(self, paper_id: str) -> list[Note]:
        """获取论文的所有笔记"""
        notes_path = await self._paper_repo.get_notes_path(paper_id)
        return await self._parse_notes_file(notes_path)

    async def search(self, query: str, paper_id: Optional[str] = None) -> list[Note]:
        """搜索笔记"""
        # 使用 ripgrep 搜索 notes.md 文件
        pass

    def _format_note_content(self, request: NoteCreate) -> str:
        """格式化笔记内容为 Markdown"""
        note_id = generate_note_id()
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

        linked = ", ".join(request.linked_paragraphs) if request.linked_paragraphs else "无"

        return f"""

## Notes [@note:note_{timestamp}]

**创建时间**: {datetime.utcnow().isoformat()}
**关联段落**: {linked}

{request.content}

"""
```

### 5.4 摘要生成工具

```python
# tools/summary/summarizer.py

from typing import Optional
from tools.interface import ISummarizer
from models.summary import Summary, SummaryRequest
from repositories.session_repository import ISessionRepository
from services.llm_service import ILLMService


class Summarizer(ISummarizer):
    """摘要生成工具"""

    def __init__(
        self,
        session_repo: ISessionRepository,
        llm_service: ILLMService,
    ):
        self._session_repo = session_repo
        self._llm = llm_service

    async def generate(self, request: SummaryRequest) -> Summary:
        """生成会话摘要"""
        # 1. 获取会话历史
        messages = await self._session_repo.get_messages(request.session_id)

        if not messages:
            raise ValueError("No messages to summarize")

        # 2. 构建摘要提示词
        prompt = self._build_summary_prompt(messages, request.detail_level)

        # 3. 调用 LLM
        response = await self._llm.complete(prompt)

        # 4. 解析响应
        summary = self._parse_summary_response(response, request.session_id, request.summary_type)

        # 5. 存储摘要
        await self._save_summary(summary)

        return summary

    def _build_summary_prompt(self, messages: list, detail_level: str) -> str:
        """构建摘要提示词"""
        # 将对话历史转换为文本
        conversation = "\n".join([
            f"{m.role}: {m.content}" for m in messages
        ])

        detail_instructions = {
            "brief": "用2-3句话概括主要讨论内容。",
            "medium": "详细总结讨论内容，列出3-5个关键发现。",
            "detailed": "全面总结对话，包括所有重要观点、引用的论文和结论。"
        }

        return f"""请总结以下对话：

{detail_instructions.get(detail_level, detail_instructions["medium"])}

对话内容：
{conversation}

请以以下格式回复：
## 摘要
[总结内容]

## 关键发现
1. [发现1]
2. [发现2]

## 引用的论文
- [论文1]
- [论文2]
"""

    def _parse_summary_response(self, response: str, session_id: str, summary_type: str) -> Summary:
        """解析 LLM 响应"""
        # 解析 Markdown 格式的响应
        # ...

    async def _save_summary(self, summary: Summary):
        """存储摘要"""
        pass
```

### 5.5 论文解析工具（使用 Marker）

```python
# tools/parse/marker_parser.py（新增）
# Marker PDF 解析器（学术PDF专用）

from typing import Optional
from tools.interface import IPDFParser
from models.paper import ParseResult


class MarkerParser(IPDFParser):
    """
    Marker PDF 解析器

    特点：
    - 处理学术PDF（表格/公式/多栏）
    - 保留文档结构
    - Fallback 到 PyMuPDF
    """

    def __init__(self, use_gpu: bool = True):
        from marker.converters.pdf import PdfConverter
        self._converter = PdfConverter()
        self._use_gpu = use_gpu
        self._fallback_parser = None  # PyMuPDF fallback

    def set_fallback(self, parser: 'PyMuPDFParser'):
        """设置 fallback 解析器"""
        self._fallback_parser = parser

    async def parse(self, pdf_path: str) -> ParseResult:
        """
        使用 Marker 解析 PDF

        Returns:
            ParseResult: 包含 Markdown 内容和元数据
        """
        try:
            result = self._converter(pdf_path)
            return ParseResult(
                content=result.markdown,
                metadata=result.metadata,
                status="success"
            )
        except Exception as e:
            # Fallback 到 PyMuPDF
            if self._fallback_parser:
                return await self._fallback_parser.parse(pdf_path)
            raise


# tools/parse/pdf_parser.py（修改）
# PyMuPDF 解析器（Fallback）

class PyMuPDFParser(IPDFParser):
    """
    PyMuPDF 解析器

    作为 Marker 的 fallback：
    - 处理扫描版 PDF
    - 处理损坏的 PDF
    - 基础文本提取
    """

    async def parse(self, pdf_path: str) -> ParseResult:
        """使用 PyMuPDF 解析 PDF"""
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        content_parts = []

        for page in doc:
            text = page.get_text()
            content_parts.append(text)

        content = "\n\n".join(content_parts)
        doc.close()

        return ParseResult(
            content=content,
            metadata={"pages": len(doc)},
            status="success"
        )


# tools/parse/paper_parser.py（修改）
# 论文解析工具（整合）

class PaperParser(IPaperParser):
    """
    论文解析工具（整合版）

    流程：
    1. Marker 解析（主）
    2. PyMuPDF Fallback
    3. 生成段落索引
    4. 向量化（异步）
    """

    def __init__(
        self,
        marker_parser: MarkerParser,      # 主解析器
        pymupdf_parser: PyMuPDFParser,    # Fallback
        indexer: ParagraphIndexer,
        embedding_service: IEmbeddingService  # 新增：解析后自动向量化
    ):
        self._marker_parser = marker_parser
        self._pymupdf_parser = pymupdf_parser
        self._indexer = indexer
        self._embedding_service = embedding_service

        # 设置 fallback
        self._marker_parser.set_fallback(self._pymupdf_parser)

    async def parse_and_index(self, pdf_path: str, paper_id: str) -> Paper:
        """
        解析并索引论文

        流程：
        1. Marker 解析
        2. 生成段落索引
        3. 向量化（异步）
        """
        # 1. Marker 解析
        result = await self._marker_parser.parse(pdf_path)

        # 2. 生成段落索引
        paragraphs = self._indexer.index(result.content)

        # 3. 向量化（异步，不阻塞）
        asyncio.create_task(self._embed_paragraphs(paper_id, paragraphs))

        return paper

    async def _embed_paragraphs(self, paper_id: str, paragraphs: list[str]):
        """异步向量化段落"""
        try:
            embeddings = await self._embedding_service.encode(paragraphs)
            # 存储到向量数据库
            await self._vector_repo.add(paper_id, embeddings, paragraphs)
        except Exception as e:
            logger.error(f"Embedding failed for {paper_id}: {e}")
```

### 5.6 工具工厂

```python
# tools/factory.py

from typing import Optional
from tools.search.fulltext_search import FulltextSearchTool
from tools.note.note_manager import NoteManager
from tools.summary.summarizer import Summarizer
from tools.parse.paper_parser import PaperParser
from tools.export.exporter import Exporter


class ToolFactory:
    """工具工厂 - 负责创建和管理工具实例"""

    def __init__(self, container: 'DIContainer'):
        self._container = container

    def create_search_tool(self) -> ISearchTool:
        """创建检索工具"""
        return FulltextSearchTool(
            index_repo=self._container.index_repository,
            paper_repo=self._container.paper_repository,
            ripgrep=self._container.ripgrep_wrapper
        )

    def create_note_tool(self) -> INoteTool:
        """创建笔记工具"""
        return NoteManager(
            paper_repo=self._container.paper_repository
        )

    def create_summary_tool(self) -> ISummarizer:
        """创建摘要工具"""
        return Summarizer(
            session_repo=self._container.session_repository,
            llm_service=self._container.llm_service
        )

    def create_parser_tool(self) -> IPaperParser:
        """创建解析工具"""
        return PaperParser(
            paper_repo=self._container.paper_repository,
            pdf_parser=self._container.pdf_parser,
            indexer=self._container.paragraph_indexer
        )

    def create_exporter_tool(self) -> IExporter:
        """创建导出工具"""
        return Exporter(
            paper_repo=self._container.paper_repository,
            session_repo=self._container.session_repository
        )
```

---

## 6. 数据层模块

### 6.1 模块结构

```
repositories/
├── interface.py                 # Repository 接口定义
├── factory.py                   # Repository 工厂
├── paper_repository.py          # 论文存储
├── index_repository.py          # 索引存储
├── session_repository.py        # 会话存储
├── summary_repository.py        # 摘要存储
├── project_state_repository.py  # 项目状态
└── user_preferences_repository.py # 用户偏好
```

### 6.2 并发控制工具（新增）

```python
# utils/file_lock.py

import asyncio
import fcntl
import aiofiles
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)


class FileLockTimeoutError(Exception):
    """文件锁超时异常"""
    pass


class FileLock:
    """文件锁 - 用于防止并发写入冲突

    使用 fcntl 实现跨进程文件锁（Linux/Mac）
    Windows 下使用 msvcrt.locking
    """

    def __init__(self, timeout: float = 5.0):
        """
        Args:
            timeout: 获取锁的超时时间（秒）
        """
        self._timeout = timeout

    @asynccontextmanager
    async def lock(self, path: str) -> AsyncGenerator:
        """
        获取文件锁（异步上下文管理器）

        Args:
            path: 文件路径

        Yields:
            文件对象

        Raises:
            FileLockTimeoutError: 获取锁超时
        """
        async with aiofiles.open(path, 'r+') as f:
            try:
                # 尝试获取锁（非阻塞）
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                yield f

            except BlockingIOError:
                # 锁被占用，等待超时
                try:
                    await asyncio.wait_for(
                        self._acquire_lock_async(f.fileno()),
                        timeout=self._timeout
                    )
                    yield f
                except asyncio.TimeoutError:
                    raise FileLockTimeoutError(
                        f"无法在 {self._timeout}s 内获取文件锁: {path}"
                    )
            finally:
                # 释放锁
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    async def _acquire_lock_async(self, fileno: int) -> bool:
        """异步等待获取锁"""
        while True:
            try:
                fcntl.flock(fileno, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except BlockingIOError:
                await asyncio.sleep(0.1)


class ConcurrentModificationError(Exception):
    """并发修改冲突异常"""
    pass
```

### 6.3 论文存储实现

```python
# repositories/paper_repository.py

import json
from pathlib import Path
from typing import Optional, List
from repositories.interface import IPaperRepository
from models.paper import PaperMetadata
from utils.file_lock import FileLock, ConcurrentModificationError


class PaperRepository(IPaperRepository):
    """论文存储实现 - 基于本地文件系统（支持并发安全）"""

    def __init__(self, data_dir: Path):
        self._papers_dir = data_dir / "papers"
        self._papers_dir.mkdir(parents=True, exist_ok=True)

        # 全局索引文件
        self._index_file = self._papers_dir / "_papers_index.json"

        # 文件锁
        self._file_lock = FileLock(timeout=5.0)

    async def save_metadata(self, paper: PaperMetadata) -> bool:
        """保存论文元数据（并发安全）"""
        paper_dir = self._papers_dir / paper.paper_id
        paper_dir.mkdir(exist_ok=True)

        meta_file = paper_dir / "metadata.json"

        # 使用文件锁确保并发安全
        async with self._file_lock.lock(str(meta_file)):
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(paper.model_dump(mode='json'), f, indent=2, ensure_ascii=False)

        # 更新全局索引
        await self._update_global_index(paper)
        return True

    async def get_metadata(self, paper_id: str) -> Optional[PaperMetadata]:
        """获取论文元数据"""
        meta_file = self._papers_dir / paper_id / "metadata.json"
        if not meta_file.exists():
            return None

        with open(meta_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return PaperMetadata(**data)

    async def list_all(self) -> List[PaperMetadata]:
        """列出所有论文"""
        # 从全局索引读取（更快）
        if self._index_file.exists():
            with open(self._index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [PaperMetadata(**p) for p in data.get("papers", [])]

        # 扫描目录
        papers = []
        for paper_dir in self._papers_dir.iterdir():
            if paper_dir.is_dir() and not paper_dir.name.startswith('_'):
                paper = await self.get_metadata(paper_dir.name)
                if paper:
                    papers.append(paper)
        return papers

    async def delete(self, paper_id: str) -> bool:
        """删除论文"""
        paper_dir = self._papers_dir / paper_id
        if not paper_dir.exists():
            return False

        # 删除目录
        import shutil
        shutil.rmtree(paper_dir)

        # 更新全局索引
        await self._update_global_index()
        return True

    async def update_metadata(self, paper_id: str, updates: dict) -> bool:
        """更新元数据"""
        paper = await self.get_metadata(paper_id)
        if not paper:
            return False

        for key, value in updates.items():
            setattr(paper, key, value)

        return await self.save_metadata(paper)

    def get_content_path(self, paper_id: str) -> Optional[str]:
        """获取正文文件路径"""
        path = self._papers_dir / paper_id / "content.md"
        return str(path) if path.exists() else None

    def get_notes_path(self, paper_id: str) -> Optional[str]:
        """获取笔记文件路径"""
        path = self._papers_dir / paper_id / "notes.md"
        return str(path) if path.exists() else None

    def get_index_path(self, paper_id: str) -> Optional[str]:
        """获取索引文件路径"""
        path = self._papers_dir / paper_id / "index.json"
        return str(path) if path.exists() else None

    async def _update_global_index(self, paper: Optional[PaperMetadata] = None):
        """更新全局论文索引"""
        papers = await self.list_all()

        index_data = {
            "version": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "total_papers": len(papers),
            "papers": [
                {
                    "paper_id": p.paper_id,
                    "title": p.title,
                    "authors": p.authors,
                    "year": p.year,
                    "source": p.source,
                    "created_at": p.created_at,
                    "total_paragraphs": p.total_paragraphs,
                    "total_notes": p.total_notes,
                    "tags": p.tags
                }
                for p in papers
            ]
        }

        with open(self._index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
```

### 6.3 索引存储实现

```python
# repositories/index_repository.py

import json
from pathlib import Path
from typing import Optional
from repositories.interface import IIndexRepository
from models.index import ParagraphIndex, ParagraphIndexEntry


class IndexRepository(IIndexRepository):
    """段落索引存储实现"""

    def __init__(self, data_dir: Path):
        self._papers_dir = data_dir / "papers"

    async def save_index(self, paper_id: str, index: dict[str, ParagraphIndexEntry]) -> bool:
        """保存段落索引"""
        index_file = self._papers_dir / paper_id / "index.json"

        # 计算哈希
        content_hash = await self._compute_hash(self._papers_dir / paper_id / "content.md")
        notes_hash = await self._compute_hash(self._papers_dir / paper_id / "notes.md")

        index_data = {
            "paper_id": paper_id,
            "version": 1,
            "created_at": datetime.utcnow().isoformat(),
            "content_hash": content_hash,
            "notes_hash": notes_hash,
            "encoding": "utf-8",
            "line_ending": "LF",
            "total_paragraphs": sum(1 for e in index.values() if e.type == "content"),
            "total_notes": sum(1 for e in index.values() if e.type == "note"),
            "paragraphs": {
                pid: entry.model_dump() for pid, entry in index.items()
            }
        }

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

        return True

    async def get_index(self, paper_id: str) -> Optional[dict]:
        """获取段落索引"""
        index_file = self._papers_dir / paper_id / "index.json"
        if not index_file.exists():
            return None

        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def get_paragraph(self, paper_id: str, paragraph_id: str) -> Optional[dict]:
        """获取段落内容"""
        index = await self.get_index(paper_id)
        if not index or paragraph_id not in index["paragraphs"]:
            return None

        entry = index["paragraphs"][paragraph_id]
        file_path = self._papers_dir / paper_id / entry["file"]

        with open(file_path, 'r', encoding='utf-8') as f:
            f.seek(entry["offset"])
            content = f.read(entry["length"])

        return {
            "paragraph_id": paragraph_id,
            "text": content,
            "section": entry.get("section"),
            "line_number": entry.get("line_number")
        }

    async def rebuild_index(self, paper_id: str) -> bool:
        """重建索引"""
        # 重新解析 content.md 和 notes.md
        pass
```

### 6.4 会话存储实现

```python
# repositories/session_repository.py

import json
from pathlib import Path
from typing import Optional, List
from repositories.interface import ISessionRepository
from models.session import Session, Message


class SessionRepository(ISessionRepository):
    """会话存储实现"""

    def __init__(self, data_dir: Path):
        self._sessions_dir = data_dir / "memory" / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        self._active_file = data_dir / "memory" / "active_session.txt"

    async def create_session(self, session_id: str, title: str) -> Session:
        """创建会话"""
        session = Session(
            session_id=session_id,
            title=title,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await self._save_session(session)
        await self.set_active_session(session_id)
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        session_file = self._sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return None

        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return Session(**data)

    async def list_sessions(self, status: Optional[str] = None) -> List[Session]:
        """列出会话"""
        sessions = []
        for session_file in self._sessions_dir.glob("*.json"):
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                session = Session(**data)
                if status is None or session.status == status:
                    sessions.append(session)
        return sorted(sessions, key=lambda s: s.updated_at, reverse=True)

    async def update_session(self, session_id: str, updates: dict) -> bool:
        """更新会话"""
        session = await self.get_session(session_id)
        if not session:
            return False

        for key, value in updates.items():
            setattr(session, key, value)
        session.updated_at = datetime.utcnow()

        await self._save_session(session)
        return True

    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        session_file = self._sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return False

        session_file.unlink()
        return True

    async def add_message(self, session_id: str, message: Message) -> bool:
        """添加消息"""
        session = await self.get_session(session_id)
        if not session:
            return False

        if not session.messages:
            session.messages = []
        session.messages.append(message)
        session.total_messages += 1
        session.total_tokens += message.token_count
        session.updated_at = datetime.utcnow()

        await self._save_session(session)
        return True

    async def get_messages(self, session_id: str, limit: int = 100) -> List[Message]:
        """获取消息列表"""
        session = await self.get_session(session_id)
        if not session or not session.messages:
            return []

        messages = session.messages[-limit:] if limit else session.messages
        return [Message(**m.model_dump()) if not isinstance(m, Message) else m for m in messages]

    async def get_active_session_id(self) -> Optional[str]:
        """获取活跃会话 ID"""
        if self._active_file.exists():
            with open(self._active_file, 'r') as f:
                return f.read().strip()
        return None

    async def set_active_session(self, session_id: str) -> bool:
        """设置活跃会话"""
        with open(self._active_file, 'w') as f:
            f.write(session_id)
        return True

    async def _save_session(self, session: Session):
        """保存会话到文件"""
        session_file = self._sessions_dir / f"{session.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.model_dump(mode='json'), f, indent=2, ensure_ascii=False)
```

---

## 7. API 层模块

### 7.1 模块结构

```
api/
├── app.py                       # FastAPI 应用
├── middleware.py                # 中间件
├── dependencies.py              # 依赖注入
└── routes/
    ├── papers.py                # 论文路由
    ├── search.py                # 检索路由
    ├── notes.py                 # 笔记路由
    ├── sessions.py              # 会话路由
    ├── export.py                # 导出路由
    └── websocket.py             # WebSocket 路由
```

### 7.2 FastAPI 应用

```python
# api/app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.middleware import ErrorHandler, RequestLogger
from config import settings


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""

    app = FastAPI(
        title="ManuScript API",
        description="对话式文献研究助手 API",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 自定义中间件
    app.add_middleware(ErrorHandler)
    app.add_middleware(RequestLogger)

    # 注册路由
    from api.routes import papers, search, notes, sessions, export, websocket

    app.include_router(papers.router, prefix="/api/v1/papers", tags=["papers"])
    app.include_router(search.router, prefix="/api/v1", tags=["search"])
    app.include_router(notes.router, prefix="/api/v1/notes", tags=["notes"])
    app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
    app.include_router(export.router, prefix="/api/v1/export", tags=["export"])
    app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": "3.0.0"}

    return app


# 应用入口
app = create_app()
```

### 7.3 论文路由

```python
# api/routes/papers.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from pathlib import Path
from uuid import uuid4
import re
from models.paper import PaperMetadata, ParseResult
from api.dependencies import get_paper_parser, get_paper_repo


router = APIRouter()


@router.post("/upload", response_model=dict)
async def upload_paper(
    file: UploadFile = File(...),
    source: str = "local_upload",
    parser=Depends(get_paper_parser),
    repo=Depends(get_paper_repo)
):
    """上传论文"""
    # 保存文件（文件名清洗 + 随机前缀，避免路径穿越和重名）
    temp_dir = Path("data/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", file.filename or "upload.pdf")
    file_path = temp_dir / f"{uuid4().hex}_{safe_name}"
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    # 解析
    result = await parser.parse(ParseRequest(
        file_path=str(file_path),
        source=source
    ))

    return {
        "code": 0,
        "data": {
            "paper_id": result.paper_id,
            "status": result.status
        }
    }


@router.get("", response_model=dict)
async def list_papers(repo=Depends(get_paper_repo)):
    """获取论文列表"""
    papers = await repo.list_all()
    return {
        "code": 0,
        "data": {
            "papers": [p.model_dump() for p in papers],
            "total": len(papers)
        }
    }


@router.get("/{paper_id}", response_model=dict)
async def get_paper(paper_id: str, repo=Depends(get_paper_repo)):
    """获取论文详情"""
    paper = await repo.get_metadata(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {
        "code": 0,
        "data": paper.model_dump()
    }


@router.delete("/{paper_id}", response_model=dict)
async def delete_paper(paper_id: str, repo=Depends(get_paper_repo)):
    """删除论文"""
    success = await repo.delete(paper_id)
    if not success:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {
        "code": 0,
        "message": "deleted"
    }


@router.get("/{paper_id}/content", response_model=dict)
async def get_paper_content(paper_id: str, repo=Depends(get_paper_repo)):
    """获取论文正文"""
    content_path = await repo.get_content_path(paper_id)
    if not content_path:
        raise HTTPException(status_code=404, detail="Content not found")

    with open(content_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return {
        "code": 0,
        "data": {
            "content": content,
            "paper_id": paper_id
        }
    }
```

### 7.4 检索路由

```python
# api/routes/search.py

from fastapi import APIRouter, Query
from models.search import SearchQuery, SearchResponse
from api.dependencies import get_search_tool


router = APIRouter()


@router.post("/search", response_model=dict)
async def search(
    query: SearchQuery,
    search_tool=Depends(get_search_tool)
):
    """全文检索"""
    result = await search_tool.search(query)
    return {
        "code": 0,
        "data": result.model_dump()
    }


@router.get("/trace/{paper_id}/{paragraph_id}", response_model=dict)
async def trace_paragraph(
    paper_id: str,
    paragraph_id: str,
    search_tool=Depends(get_search_tool)
):
    """溯源查看段落"""
    paragraph = await search_tool.get_paragraph_by_id(paragraph_id, paper_id)
    if not paragraph:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Paragraph not found")

    return {
        "code": 0,
        "data": paragraph
    }
```

### 7.5 依赖注入

```python
# api/dependencies.py

from fastapi import Depends
from typing import AsyncGenerator
from tools.factory import ToolFactory
from repositories.factory import RepositoryFactory
from services.llm_service import LLMService


# 单例容器
class DIContainer:
    """依赖注入容器"""

    def __init__(self):
        from config import settings
        from pathlib import Path

        data_dir = Path(settings.DATA_DIR)

        # Repositories
        self.repo_factory = RepositoryFactory(data_dir)
        self.paper_repository = self.repo_factory.create_paper_repository()
        self.index_repository = self.repo_factory.create_index_repository()
        self.session_repository = self.repo_factory.create_session_repository()

        # Services
        self.llm_service = LLMService(settings.OPENAI_API_KEY)

        # Tools
        self.tool_factory = ToolFactory(self)
        self.search_tool = self.tool_factory.create_search_tool()
        self.note_tool = self.tool_factory.create_note_tool()
        self.summary_tool = self.tool_factory.create_summary_tool()
        self.paper_parser = self.tool_factory.create_parser_tool()


# 全局容器
container = DIContainer()


# 依赖函数
async def get_search_tool() -> AsyncGenerator:
    yield container.search_tool


async def get_note_tool() -> AsyncGenerator:
    yield container.note_tool


async def get_paper_parser() -> AsyncGenerator:
    yield container.paper_parser


async def get_paper_repo() -> AsyncGenerator:
    yield container.paper_repository
```

---

## 8. UI 层模块

### 8.1 模块结构

```
ui/
├── app.py                       # Gradio 应用入口
├── components/                 # UI 组件
│   ├── __init__.py
│   ├── paper_browser.py        # 论文浏览器（左侧栏）
│   ├── chat_area.py            # 对话区域（中间栏）
│   ├── status_panel.py         # 状态面板（右侧栏）
│   ├── source_viewer.py        # 溯源查看器
│   └── note_editor.py          # 笔记编辑器
└── layouts/
    ├── __init__.py
    └── main_layout.py          # 主布局（三栏）
```

### 8.2 三栏布局设计（借鉴知识管理系统）

```
┌─────────────┬──────────────────────────────────────┬─────────────┐
│   论文导航   │            主交互区域                 │   状态/笔记  │
│  (可折叠)    │         (对话/检索)                  │   (可折叠)   │
│             │                                      │             │
│ 📁 按分类    │ ┌────────────────────────────────┐  │ 📊 索引状态  │
│ 📌 按标签    │ │    AI 对话区                   │  │             │
│ 📅 按时间    │ │    ...                         │  │ FTS5: ✅    │
│             │ └────────────────────────────────┘  │ Vector: ✅   │
│ [+ 新建分类] │                                      │ GPU: 4GB     │
│             │ [输入框]                              │             │
│             │                                      │ 📝 阅读笔记  │
│             │                                      │ - paper_1... │
└─────────────┴──────────────────────────────────────┴─────────────┘
```

### 8.3 左侧栏：论文导航（PaperBrowser）

```python
# ui/components/paper_browser.py

import gradio as gr
from typing import List, Callable
from models.paper import PaperMetadata


class PaperBrowser:
    """论文浏览器组件"""

    def __init__(self):
        self.categories = ["全部", "attention", "transformer", "bert", "gpt", "multimodal"]
        self.current_category = "全部"
        self.current_sort = "created_at"  # created_at | title | year

    def build(self) -> gr.Column:
        """构建论文浏览界面"""

        with gr.Column(visible=True) as self.container:
            # 标题和折叠按钮
            with gr.Row():
                gr.Markdown("### 📚 论文库")
                self.collapse_btn = gr.Button("◀", size="sm", scale=0)

            # 搜索框
            self.search_box = gr.Textbox(
                placeholder="搜索论文标题、作者...",
                show_label=False,
                scale=4
            )

            # 视图切换
            with gr.Row():
                self.view_mode = gr.Radio(
                    choices=["分类", "标签", "时间"],
                    value="分类",
                    scale=3,
                    show_label=False
                )
                self.sort_btn = gr.Button("排序▼", scale=1, size="sm")

            # 论文列表
            self.paper_list = self._build_paper_list()

            # 上传按钮
            self.upload_btn = gr.UploadButton(
                "📤 上传论文",
                file_types=[".pdf"],
                size="sm"
            )

            # 统计信息
            self.stats = gr.Markdown("**127** 篇论文 | **120** 篇已索引")

        return self.container

    def _build_paper_list(self) -> gr.List:
        """构建论文列表"""
        # 使用可折叠的分组
        papers_by_category = {
            "attention": ["Attention Is All You Need", "Self-Attention with Relative Position..."],
            "transformer": ["Transformer-XL", "Linformer", "Reformer"],
            # ...
        }

        items = []
        for category, papers in papers_by_category.items():
            with gr.Accordion(category, open=False):
                for paper in papers:
                    btn = gr.Button(paper, size="sm", variant="secondary")
                    items.append(btn)

        return gr.Column(*items)

    def update_paper_list(self, category: str, sort_by: str) -> List[PaperMetadata]:
        """更新论文列表"""
        # 调用 API 获取论文列表
        pass

    def on_paper_select(self, paper_id: str) -> None:
        """论文选择事件"""
        # 更新中间和右侧栏
        pass
```

### 8.4 中间栏：主交互区域（ChatArea）

```python
# ui/components/chat_area.py

import gradio as gr
from typing import List, Optional


class ChatArea:
    """主对话区域组件"""

    def __init__(self):
        self.messages = []
        self.current_search_mode = "hybrid"  # keyword | vector | hybrid

    def build(self) -> gr.Column:
        """构建对话界面"""

        with gr.Column(scale=2) as self.container:
            # 搜索模式选择
            with gr.Row():
                self.search_mode = gr.Radio(
                    choices=[
                        ("混合检索", "hybrid"),
                        ("关键词", "keyword"),
                        ("语义检索", "vector")
                    ],
                    value="hybrid",
                    show_label=False,
                    scale=2
                )
                self.settings_btn = gr.Button("⚙️", scale=0, size="sm")

            # 对话历史
            self.chatbot = gr.Chatbot(
                label="",
                height=500,
                show_copy_button=True,
                avatar_images=("👤", "🤖")
            )

            # 输入区域
            with gr.Row():
                self.input_box = gr.Textbox(
                    placeholder="输入问题或搜索关键词...",
                    show_label=False,
                    scale=4,
                    lines=2
                )
                self.send_btn = gr.Button("发送", scale=1, variant="primary")

            # 检索结果展示（可展开）
            with gr.Accordion("检索结果", open=False):
                self.search_results = self._build_search_results()

            # 快捷操作
            with gr.Row():
                self.summary_btn = gr.Button("📝 生成摘要", size="sm")
                self.export_btn = gr.Button("📤 导出对话", size="sm")
                self.clear_btn = gr.Button("🗑️ 清空对话", size="sm")

        return self.container

    def _build_search_results(self) -> gr.Column:
        """构建检索结果展示"""
        with gr.Column():
            self.result_count = gr.Markdown("**找到 5 个相关段落**")

            # 结果列表（每个结果包含：高亮文本、来源、跳转按钮）
            with gr.Column():
                for i in range(5):  # 默认显示前5个
                    with gr.Group():
                        result_text = gr.Markdown(
                            f"**结果 {i+1}**\n\n> 相关段落内容高亮显示..."
                        )
                        with gr.Row():
                            source_badge = gr.Markdown("**arxiv_1706.03762**")
                            jump_btn = gr.Button("查看原文", size="sm")

        return gr.Column()

    def on_message_send(self, message: str, search_mode: str) -> None:
        """发送消息事件"""
        # 调用 API
        # 更新 chatbot
        # 更新 search_results
        pass
```

### 8.5 右侧栏：状态与笔记（StatusPanel）

```python
# ui/components/status_panel.py

import gradio as gr


class StatusPanel:
    """状态面板组件"""

    def __init__(self):
        self.current_paper_id = None

    def build(self) -> gr.Column:
        """构建状态面板"""

        with gr.Column(visible=True) as self.container:
            # 标题和折叠按钮
            with gr.Row():
                gr.Markdown("### 状态 & 笔记")
                self.collapse_btn = gr.Button("▶", size="sm", scale=0)

            # 索引状态卡片
            with gr.Group():
                gr.Markdown("#### 📊 索引状态")
                self.fts_status = gr.Markdown("FTS5: ✅ 正常")
                self.vector_status = gr.Markdown("Vector: ✅ 正常")
                self.gpu_status = gr.Markdown("GPU: 4GB (CUDA可用)")
                self.embedding_mode = gr.Markdown("Embedding: 本地 (BGE-M3)")

            # 当前论文信息
            with gr.Group():
                gr.Markdown("#### 📄 当前论文")
                self.paper_title = gr.Markdown("*未选择论文*")
                self.paper_stats = gr.Markdown("")

            # 笔记编辑区
            with gr.Group():
                gr.Markdown("#### 📝 我的笔记")
                self.note_list = self._build_note_list()

                self.new_note = gr.Textbox(
                    placeholder="添加新笔记...",
                    lines=3,
                    show_label=False
                )
                self.add_note_btn = gr.Button("添加笔记", size="sm")

            # 任务清单（来自 tasks/）
            with gr.Accordion("📋 研究任务", open=False):
                self.task_list = self._build_task_list()

        return self.container

    def _build_note_list(self) -> gr.Column:
        """构建笔记列表"""
        # 从当前论文的 notes.md 读取
        with gr.Column():
            note1 = gr.Markdown("- [x] 关键点1: 自注意力机制")
            note2 = gr.Markdown("- [ ] 待验证: 复杂度分析")
            note3 = gr.Markdown("- [ ] 相关论文: Linformer, Reformer")
        return gr.Column(note1, note2, note3)

    def _build_task_list(self) -> gr.Column:
        """构建任务列表（从 data/tasks/ 读取）"""
        # 读取 tasks/ 目录下的 .md 文件
        with gr.Column():
            task1 = gr.Markdown("[ ] 完成Transformer综述")
            task2 = gr.Markdown("[x] 阅读Attention论文")
            task3 = gr.Markdown("[ ] 整理架构演进时间线")
        return gr.Column(task1, task2, task3)

    def update_status(self, paper_id: str) -> None:
        """更新状态（论文切换时）"""
        # 调用 API 获取论文信息
        # 更新显示
        pass
```

### 8.6 溯源查看器（SourceViewer）

```python
# ui/components/source_viewer.py

import gradio as gr


class SourceViewer:
    """溯源查看器 - 弹窗显示原文"""

    def __init__(self):
        self.current_paragraph = None

    def build(self) -> gr.Box:
        """构建溯源查看器（模态框）"""

        with gr.Box(visible=False) as self.modal:
            gr.Markdown("### 📖 原文溯源")

            # 来源信息
            with gr.Row():
                self.paper_link = gr.Markdown("**Attention Is All You Need**")
                self.section_tag = gr.Markdown("`Section 3.2`")

            # 段落内容（高亮显示）
            self.paragraph_content = gr.Markdown(
                "> The transformer allows... **highlighted text** ..."
            )

            # 上下文导航
            with gr.Row():
                self.prev_btn = gr.Button("↑ 上一段")
                self.next_btn = gr.Button("↓ 下一段")
                self.close_btn = gr.Button("关闭")

            # 操作
            with gr.Row():
                self.copy_btn = gr.Button("📋 复制")
                self.add_note_btn = gr.Button("📝 添加笔记")
                self.link_btn = gr.Button("🔗 复制链接")

        return self.modal

    def show_paragraph(self, paper_id: str, paragraph_id: str) -> None:
        """显示指定段落"""
        # 调用 API 获取段落内容
        # 高亮显示
        # 显示模态框
        pass
```

### 8.7 主布局（MainLayout）

```python
# ui/layouts/main_layout.py

import gradio as gr
from ui.components.paper_browser import PaperBrowser
from ui.components.chat_area import ChatArea
from ui.components.status_panel import StatusPanel
from ui.components.source_viewer import SourceViewer


class MainLayout:
    """主布局 - 三栏设计"""

    def __init__(self):
        self.paper_browser = PaperBrowser()
        self.chat_area = ChatArea()
        self.status_panel = StatusPanel()
        self.source_viewer = SourceViewer()

        # 状态
        self.left_collapsed = False
        self.right_collapsed = False

    def build(self) -> gr.Blocks:
        """构建完整布局"""

        with gr.Blocks(title="ManuScript v3.0", theme=gr.themes.Soft()) as app:
            # 顶部标题栏
            gr.Markdown("# 📚 ManuScript v3.0 - 对话式文献研究助手")

            # 主布局
            with gr.Row():
                # 左侧栏 - 论文导航
                with gr.Column(scale=1, min_width=250) as self.left_col:
                    self.paper_browser.build()

                # 中间栏 - 主交互区域
                with gr.Column(scale=3, min_width=500):
                    self.chat_area.build()

                # 右侧栏 - 状态与笔记
                with gr.Column(scale=1, min_width=250) as self.right_col:
                    self.status_panel.build()

            # 溯源查看器（隐藏）
            self.source_viewer.build()

            # 绑定事件
            self._bind_events()

        return app

    def _bind_events(self) -> None:
        """绑定事件处理"""

        # 左侧折叠
        self.paper_browser.collapse_btn.click(
            fn=self._toggle_left,
            inputs=[],
            outputs=[self.left_col, self.paper_browser.collapse_btn]
        )

        # 右侧折叠
        self.status_panel.collapse_btn.click(
            fn=self._toggle_right,
            inputs=[],
            outputs=[self.right_col, self.status_panel.collapse_btn]
        )

        # 论文选择
        # self.paper_browser.paper_list.select(...)
        #   → 更新中间和右侧栏

        # 消息发送
        self.chat_area.send_btn.click(
            fn=self._on_send,
            inputs=[self.chat_area.input_box, self.chat_area.search_mode],
            outputs=[self.chat_area.chatbot, self.chat_area.search_results]
        )

        # 添加笔记
        self.status_panel.add_note_btn.click(
            fn=self._add_note,
            inputs=[self.status_panel.new_note],
            outputs=[self.status_panel.note_list]
        )

    def _toggle_left(self):
        """切换左侧栏"""
        self.left_collapsed = not self.left_collapsed
        visible = not self.left_collapsed
        icon = "▶" if self.left_collapsed else "◀"
        return gr.Column(visible=visible), gr.Button(value=icon)

    def _toggle_right(self):
        """切换右侧栏"""
        self.right_collapsed = not self.right_collapsed
        visible = not self.right_collapsed
        icon = "◀" if self.right_collapsed else "▶"
        return gr.Column(visible=visible), gr.Button(value=icon)

    def _on_send(self, message: str, search_mode: str):
        """发送消息"""
        # 调用 API
        # 返回更新后的对话和检索结果
        return [], {}  # 占位

    def _add_note(self, note_content: str):
        """添加笔记"""
        # 调用 API
        # 返回更新后的笔记列表
        return gr.Column()  # 占位
```

### 8.8 应用入口

```python
# ui/app.py

import gradio as gr
from ui.layouts.main_layout import MainLayout
from api.app import app as api_app


def create_ui() -> gr.Blocks:
    """创建 Gradio UI"""

    layout = MainLayout()
    return layout.build()


# Gradio 独立运行
def run_gradio(host: str = "127.0.0.1", port: int = 7860):
    """运行 Gradio 服务器"""
    ui = create_ui()
    ui.launch(
        server_name=host,
        server_port=port,
        share=False,
        show_error=True
    )


# FastAPI 集成模式（推荐）
def mount_to_fastapi(app):
    """将 Gradio UI 挂载到 FastAPI"""
    from gradio.routes import mount_gradio_app
    ui = create_ui()
    mount_gradio_app(app, ui, path="/")
```

### 8.9 响应式设计

| 屏幕宽度 | 布局调整 |
|----------|----------|
| > 1400px | 三栏完整显示 |
| 1000-1400px | 左右栏可折叠 |
| < 1000px | 单栏模式，Tab切换 |
| < 600px | 移动端优化布局 |

---

## 9. 模块依赖关系

### 8.1 依赖图

```
┌──────────────────────────────────────────────────────────────────────┐
│                               UI Layer                                │
│                           ui/app.py                                  │
└──────────────────────────────────────┬───────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────┐
│                              API Layer                                │
│                    api/app.py, api/routes/                            │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    Dependencies                                  │   │
│  │  • IIntentRouter → IntentRouter                                 │   │
│  │  • IMainAgent → MainAgent                                       │   │
│  └────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────┬───────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────┐
│                           Router Layer                                │
│              router/intent_router.py, route_config.py                 │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │              IIntentRouter → IntentRouter                       │   │
│  │              IIntentDetector → IntentDetector                   │   │
│  └────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────┬───────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────┐
│                           Agent Layer                                 │
│    agent/main_agent.py, conversation_manager.py, memory_manager.py   │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │              IMainAgent → MainAgent                             │   │
│  │              IConversationManager → ConversationManager        │   │
│  │              IMemoryManager → MemoryManager                     │   │
│  │                                                               │   │
│  │  依赖:                                                         │   │
│  │  • ISearchTool                                                │   │
│  │  • INoteTool                                                  │   │
│  │  • ISummarizer                                                │   │
│  │  • ILLMService                                                │   │
│  └────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────┬───────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────┐
│                            Tool Layer                                 │
│  tools/search/, tools/note/, tools/summary/, tools/parse/            │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │              ISearchTool → FulltextSearchTool                    │   │
│  │              INoteTool → NoteManager                             │   │
│  │              ISummarizer → Summarizer                            │   │
│  │              IPaperParser → PaperParser                          │   │
│  │              IExporter → Exporter                                │   │
│  │                                                               │   │
│  │  依赖:                                                         │   │
│  │  • IPaperRepository                                            │   │
│  │  • IIndexRepository                                            │   │
│  │  • ISessionRepository                                          │   │
│  │  • ILLMService                                                 │   │
│  │  • RipgrepWrapper                                              │   │
│  └────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────┬───────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────┐
│                            Data Layer                                 │
│  repositories/paper_repository.py, index_repository.py, ...          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │              IPaperRepository → PaperRepository                 │   │
│  │              IIndexRepository → IndexRepository                 │   │
│  │              ISessionRepository → SessionRepository             │   │
│  │              ISummaryRepository → SummaryRepository             │   │
│  │              IProjectStateRepository → ProjectStateRepository   │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  依赖:                                                                │
│  • 文件系统 (Path, json)                                             │
│  • models/ (数据模型)                                                │
└───────────────────────────────────────────────────────────────────────┘
```

### 8.2 模块职责矩阵

| 模块 | 职责 | 依赖 | 被依赖 |
|------|------|------|--------|
| **UI Layer** | 用户界面展示和交互 | API Layer | - |
| **API Layer** | HTTP 请求处理、路由分发 | Router, Agent | UI Layer |
| **Router Layer** | 意图识别、请求路由 | IIntentDetector, Agent | API Layer |
| **Agent Layer** | 对话状态管理、工具协调 | IConversationManager, IMemoryManager, Tools | Router |
| **ConversationManager** | 对话历史管理 | ISessionRepository | Agent |
| **MemoryManager** | 长期记忆管理 | ISummaryRepository, IProjectStateRepository | Agent |
| **Tool Layer** | 具体功能实现 | Repositories, Services, Utils | Agent |
| **FulltextSearchTool** | 全文检索 | IIndexRepository, IPaperRepository, RipgrepWrapper | - |
| **NoteManager** | 笔记管理 | IPaperRepository | - |
| **Summarizer** | 摘要生成 | ISessionRepository, ILLMService | - |
| **PaperParser** | 论文解析 | IPaperRepository, PDFParser, ParagraphIndexer | - |
| **Data Layer** | 数据持久化 | 文件系统, models | Tools, Agent |
| **Repositories** | CRUD 操作 | 文件系统 | Tools, Agent |
| **Services** | 外部服务调用 | OpenAI API | Tools, Agent |

---

*文档版本: 1.1 | 最后更新: 2026-02-05*
