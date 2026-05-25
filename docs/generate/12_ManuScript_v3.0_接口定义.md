# ManuScript v3.0 接口定义

> **文档版本**: 1.1
> **创建日期**: 2026-02-04
> **最后更新**: 2026-02-05
> **依据文档**: 11_ManuScript_v3.0_数据结构设计.md
> **架构层级**: 5层架构（UI → 路由 → 主 Agent → 工具 → 数据）

---

## 目录

1. [接口设计原则](#1-接口设计原则)
2. [路由层接口](#2-路由层接口)
3. [主 Agent 接口](#3-主-agent-接口)
4. [工具层接口](#4-工具层接口)
5. [数据层接口](#5-数据层接口)
6. [前后端通信协议](#6-前后端通信协议)
7. [错误码定义](#7-错误码定义)

---

## 1. 接口设计原则

### 1.1 设计规范

| 原则 | 说明 | 示例 |
|------|------|------|
| **RESTful 风格** | HTTP 方法语义化 | GET=查询，POST=创建，PUT=更新，DELETE=删除 |
| **统一响应格式** | 所有接口返回相同结构 | `{"code": 0, "data": {...}, "message": "ok"}` |
| **版本化** | URL 包含版本号 | `/api/v1/papers` |
| **幂等性** | PUT/DELETE 操作幂等 | 重复调用结果相同 |
| **异步优先** | 长时间操作异步处理（解析/导出） | 返回 task_id，轮询状态 |

### 1.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| API 路径 | kebab-case | `/api/v1/full-text-search` |
| 函数名 | snake_case | `search_papers()` |
| 类名 | PascalCase | `SearchService` |
| 常量 | UPPER_SNAKE_CASE | `MAX_SESSIONS` |

### 1.3 通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "request_id": "req_20240204_143000",
  "timestamp": "2024-02-04T14:30:00Z"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 0=成功，非0=错误码 |
| message | string | 描述信息 |
| data | object/array | 业务数据 |
| request_id | string | 请求追踪 ID |
| timestamp | string | 响应时间 |

---

## 2. 路由层接口

路由层负责意图识别与请求分发，是系统的入口。

### 2.1 意图识别接口

```python
# router/intent_router.py

from enum import Enum
from pydantic import BaseModel, Field
from enum import Enum
from typing import Literal, Optional
from datetime import datetime


class IntentType(str, Enum):
    """意图类型"""
    CHAT = "chat"                    # 闲聊
    SEARCH = "search"                # 全文检索
    NOTE_SEARCH = "note_search"      # 笔记检索
    NOTE_ADD = "note_add"            # 添加笔记
    NOTE_EDIT = "note_edit"          # 编辑笔记
    SUMMARIZE = "summarize"          # 会话摘要
    EXPORT = "export"                # 导出
    PARSE = "parse"                  # 论文解析
    TRACE = "trace"                  # 溯源查看


class IntentRequest(BaseModel):
    """意图识别请求"""
    query: str                       # 用户输入
    session_id: Optional[str] = None # 会话 ID（可选）
    context: Optional[dict] = None   # 上下文信息


class IntentResult(BaseModel):
    """意图识别结果"""
    intent: IntentType               # 识别的意图
    confidence: float                # 置信度 (0-1)
    parameters: dict                 # 提取的参数
    should_route_to_llm: bool        # 是否需要 LLM 处理


class IIntentRouter:
    """意图识别路由器接口"""

    async def detect_intent(self, request: IntentRequest) -> IntentResult:
        """
        识别用户意图

        Args:
            request: 意图识别请求

        Returns:
            IntentResult: 识别结果
        """
        raise NotImplementedError

    async def route_request(self, request: IntentRequest, intent: IntentResult):
        """
        根据意图路由请求到相应处理器

        Args:
            request: 原始请求
            intent: 意图识别结果

        Returns:
            处理器返回的结果
        """
        raise NotImplementedError
```

### 2.2 路由配置

```python
# router/route_config.py

from dataclasses import dataclass
from typing import Callable, Awaitable


@dataclass
class RouteConfig:
    """路由配置"""
    intent: IntentType
    handler: Callable[[IntentRequest, IntentResult], Awaitable[dict]]
    require_llm: bool = False
    timeout_seconds: int = 30


# 路由表
ROUTE_TABLE: dict[IntentType, RouteConfig] = {
    IntentType.CHAT: RouteConfig(
        intent=IntentType.CHAT,
        handler=lambda req, intent: chat_handler.handle(req, intent),
        require_llm=True,
        timeout_seconds=10
    ),
    IntentType.SEARCH: RouteConfig(
        intent=IntentType.SEARCH,
        handler=lambda req, intent: search_handler.handle(req, intent),
        require_llm=False,
        timeout_seconds=5
    ),
    IntentType.NOTE_SEARCH: RouteConfig(
        intent=IntentType.NOTE_SEARCH,
        handler=lambda req, intent: note_handler.search(req, intent),
        require_llm=False,
        timeout_seconds=5
    ),
    IntentType.NOTE_ADD: RouteConfig(
        intent=IntentType.NOTE_ADD,
        handler=lambda req, intent: note_handler.add(req, intent),
        require_llm=False,
        timeout_seconds=3
    ),
    IntentType.SUMMARIZE: RouteConfig(
        intent=IntentType.SUMMARIZE,
        handler=lambda req, intent: summary_handler.generate(req, intent),
        require_llm=True,
        timeout_seconds=30
    ),
    IntentType.TRACE: RouteConfig(
        intent=IntentType.TRACE,
        handler=lambda req, intent: trace_handler.show(req, intent),
        require_llm=False,
        timeout_seconds=2
    ),
}
```

---

## 3. 主 Agent 接口

主 Agent 是有状态的协调者，管理对话状态和长期记忆。

### 3.1 Agent 状态管理

```python
# agent/main_agent.py

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class AgentState(BaseModel):
    """Agent 状态"""
    session_id: str
    current_intent: Optional[IntentType] = None
    user_journey_state: Optional[Literal["exploring", "structuring", "writing", "polishing"]] = None
    pending_tasks: list[str] = Field(default_factory=list)
    last_action: Optional[str] = None
    last_action_timestamp: Optional[datetime] = None
    context: dict = Field(default_factory=dict)


class IMainAgent:
    """主 Agent 接口"""

    async def initialize(self, session_id: str) -> AgentState:
        """
        初始化 Agent 状态

        Args:
            session_id: 会话 ID

        Returns:
            AgentState: 初始状态
        """
        raise NotImplementedError

    async def process_message(self, message: str, session_id: str) -> str:
        """
        处理用户消息

        Args:
            message: 用户消息
            session_id: 会话 ID

        Returns:
            str: Agent 响应
        """
        raise NotImplementedError

    async def get_state(self, session_id: str) -> AgentState:
        """
        获取当前 Agent 状态

        Args:
            session_id: 会话 ID

        Returns:
            AgentState: 当前状态
        """
        raise NotImplementedError

    async def update_state(self, session_id: str, updates: dict) -> AgentState:
        """
        更新 Agent 状态

        Args:
            session_id: 会话 ID
            updates: 更新字段

        Returns:
            AgentState: 更新后的状态
        """
        raise NotImplementedError

    async def should_summarize(self, session_id: str) -> bool:
        """
        判断是否需要触发会话摘要

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否需要摘要
        """
        raise NotImplementedError

    async def access_memory(self, memory_type: str, query: str) -> list:
        """
        访问长期记忆

        Args:
            memory_type: 记忆类型 (global/session/summary)
            query: 查询条件

        Returns:
            list: 检索结果
        """
        raise NotImplementedError
```

### 3.2 对话管理接口

```python
# agent/conversation_manager.py

from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime


class Message(BaseModel):
    """对话消息"""
    message_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    token_count: int = 0
    metadata: dict = Field(default_factory=dict)


class ConversationContext(BaseModel):
    """对话上下文"""
    session_id: str
    messages: List[Message]
    total_tokens: int
    current_state: str
    last_paper_id: Optional[str] = None
    last_paragraph_id: Optional[str] = None


class IConversationManager:
    """对话管理器接口"""

    async def add_message(self, session_id: str, message: Message) -> Message:
        """添加消息到会话"""
        raise NotImplementedError

    async def get_history(self, session_id: str, limit: int = 100) -> List[Message]:
        """获取对话历史"""
        raise NotImplementedError

    async def get_context(self, session_id: str) -> ConversationContext:
        """获取对话上下文"""
        raise NotImplementedError

    async def estimate_tokens(self, messages: List[Message]) -> int:
        """估算 Token 数量"""
        raise NotImplementedError

    async def trim_history(self, session_id: str, max_tokens: int) -> List[Message]:
        """裁剪历史（保留最近的消息）"""
        raise NotImplementedError
```

### 3.3 记忆管理接口

```python
# agent/memory_manager.py

from pydantic import BaseModel
from typing import Literal, Optional


class MemoryType(str, Enum):
    """记忆类型"""
    GLOBAL_SHARED = "global_shared"      # 全局共享（论文库元数据、用户笔记、项目状态、用户偏好）
    SESSION_INDEPENDENT = "session"      # 会话独立（对话历史、临时搜索结果）
    REFERENCABLE = "summary"             # 可引用（会话摘要、关键事实）


class MemoryQuery(BaseModel):
    """记忆查询"""
    memory_type: MemoryType
    query: str
    session_id: Optional[str] = None
    limit: int = 10


class MemoryItem(BaseModel):
    """记忆项"""
    item_id: str
    type: str
    content: str
    source_session_id: Optional[str] = None
    created_at: datetime
    metadata: dict = Field(default_factory=dict)


class IMemoryManager:
    """记忆管理器接口"""

    async def store(self, item: MemoryItem, memory_type: MemoryType) -> str:
        """
        存储记忆项

        Args:
            item: 记忆项
            memory_type: 记忆类型

        Returns:
            str: 存储 ID
        """
        raise NotImplementedError

    async def retrieve(self, query: MemoryQuery) -> list[MemoryItem]:
        """
        检索记忆项

        Args:
            query: 查询条件

        Returns:
            list[MemoryItem]: 匹配的记忆项
        """
        raise NotImplementedError

    async def get_global_context(self) -> dict:
        """
        获取全局上下文（论文库元数据、项目状态等）

        Returns:
            dict: 全局上下文
        """
        raise NotImplementedError

    async def get_session_memory(self, session_id: str) -> dict:
        """
        获取会话独立记忆

        Args:
            session_id: 会话 ID

        Returns:
            dict: 会话记忆
        """
        raise NotImplementedError

    async def get_summaries(self, session_id: Optional[str] = None) -> list[dict]:
        """
        获取会话摘要

        Args:
            session_id: 指定会话 ID，None 表示全部

        Returns:
            list[dict]: 摘要列表
        """
        raise NotImplementedError

    async def create_summary(self, session_id: str, summary_type: Literal["auto", "user_requested", "session_end"]) -> dict:
        """
        创建会话摘要

        Args:
            session_id: 会话 ID
            summary_type: 摘要类型

        Returns:
            dict: 生成的摘要
        """
        raise NotImplementedError
```

---

## 4. 工具层接口

工具层是逻辑无状态的工具集合，不持久化会话状态（实例可由容器复用）。

### 4.1 全文检索工具

```python
# tools/fulltext_search.py

from pydantic import BaseModel
from typing import Literal, Optional


class SearchQuery(BaseModel):
    """检索查询"""
    query: str                           # 搜索词
    query_type: Literal["keyword", "natural_language", "auto"] = "auto"
    top_k: int = 10
    source_filter: Literal["all", "content_only", "note_only"] = "all"
    paper_ids: Optional[list[str]] = None
    case_sensitive: bool = False
    include_context: bool = True


class SearchResult(BaseModel):
    """检索结果"""
    paragraph_id: str
    paper_id: str
    type: Literal["content", "note"]
    text: str
    highlighted_text: Optional[str] = None
    score: float
    section: Optional[str] = None
    paper_title: str
    paper_authors: list[str]
    paper_year: Optional[int] = None
    offset: Optional[int] = None
    line_number: Optional[int] = None


class SearchResponse(BaseModel):
    """检索响应"""
    results: list[SearchResult]
    total: int
    returned: int
    query: str
    rewritten_query: Optional[str] = None
    search_duration_ms: int
    papers_searched: int


class IFulltextSearchTool:
    """全文检索工具接口"""

    async def search(self, query: SearchQuery) -> SearchResponse:
        """
        执行全文检索

        Args:
            query: 检索查询

        Returns:
            SearchResponse: 检索结果
        """
        raise NotImplementedError

    async def rewrite_query(self, query: str, intent: str) -> str:
        """
        改写查询（可选）

        Args:
            query: 原始查询
            intent: 用户意图

        Returns:
            str: 改写后的查询
        """
        raise NotImplementedError

    async def get_paragraph_by_id(self, paragraph_id: str, paper_id: str) -> Optional[dict]:
        """
        根据段落 ID 获取段落内容（溯源）

        Args:
            paragraph_id: 段落 ID
            paper_id: 论文 ID

        Returns:
            Optional[dict]: 段落内容，不存在返回 None
        """
        raise NotImplementedError


class ISearchTool:
    """混合检索工具接口"""

    async def search(
        self,
        query: SearchQuery,
        mode: Literal["keyword", "vector", "hybrid"] = "hybrid"
    ) -> SearchResponse:
        """
        混合检索

        Args:
            query: 检索查询
            mode: 检索模式
                - keyword: 仅关键词（ripgrep + FTS5）
                - vector: 仅向量（ChromaDB）
                - hybrid: 混合（默认，RRF融合）

        Returns:
            SearchResponse: 检索结果
        """
        raise NotImplementedError

    async def keyword_search(self, query: str, top_k: int = 20) -> list[SearchResult]:
        """关键词检索（ripgrep + FTS5）"""
        raise NotImplementedError

    async def vector_search(self, query: str, top_k: int = 20) -> list[SearchResult]:
        """向量检索（ChromaDB）"""
        raise NotImplementedError

    async def fuse_results(
        self,
        keyword_results: list[SearchResult],
        vector_results: list[SearchResult],
        method: Literal["rrf", "weighted"] = "rrf"
    ) -> list[SearchResult]:
        """RRF融合排序"""
        raise NotImplementedError


class IVectorSearchTool:
    """向量检索工具接口"""

    async def embed_document(self, paper_id: str, paragraphs: list[str]) -> bool:
        """
        向量化文档段落

        Args:
            paper_id: 论文ID
            paragraphs: 段落文本列表

        Returns:
            bool: 是否成功
        """
        raise NotImplementedError

    async def search_similar(
        self,
        query: str,
        top_k: int = 10,
        paper_ids: Optional[list[str]] = None
    ) -> list[dict]:
        """
        语义相似度检索

        Args:
            query: 查询文本
            top_k: 返回数量
            paper_ids: 限定论文范围

        Returns:
            list[dict]: 检索结果，包含 paragraph_id, score
        """
        raise NotImplementedError

    async def delete_embeddings(self, paper_id: str) -> bool:
        """删除论文的向量索引"""
        raise NotImplementedError


class IEmbeddingService:
    """Embedding服务接口（支持本地/API切换）"""

    async def encode(self, texts: list[str]) -> list[list[float]]:
        """
        文本向量化

        Args:
            texts: 文本列表

        Returns:
            list[list[float]]: 向量列表
        """
        raise NotImplementedError

    def get_dimension(self) -> int:
        """获取向量维度"""
        raise NotImplementedError

    def get_mode(self) -> str:
        """获取当前模式（local/api）"""
        raise NotImplementedError
```

### 4.2 笔记管理工具

```python
# tools/note_manager.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Note(BaseModel):
    """笔记"""
    note_id: str
    paper_id: str
    linked_paragraphs: list[str] = Field(default_factory=list)
    content: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None


class NoteCreate(BaseModel):
    """创建笔记请求"""
    paper_id: str
    linked_paragraphs: list[str] = Field(default_factory=list)
    content: str
    tags: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    """更新笔记请求"""
    note_id: str
    content: Optional[str] = None
    linked_paragraphs: Optional[list[str]] = None
    tags: Optional[list[str]] = None


class INoteManager:
    """笔记管理工具接口"""

    async def create(self, request: NoteCreate) -> Note:
        """创建笔记"""
        raise NotImplementedError

    async def get(self, note_id: str) -> Optional[Note]:
        """获取笔记"""
        raise NotImplementedError

    async def update(self, request: NoteUpdate) -> Note:
        """更新笔记"""
        raise NotImplementedError

    async def delete(self, note_id: str) -> bool:
        """删除笔记"""
        raise NotImplementedError

    async def list_by_paper(self, paper_id: str) -> list[Note]:
        """获取论文的所有笔记"""
        raise NotImplementedError

    async def search(self, query: str, paper_id: Optional[str] = None) -> list[Note]:
        """搜索笔记"""
        raise NotImplementedError
```

### 4.3 摘要生成工具

```python
# tools/summarizer.py

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class SummaryRequest(BaseModel):
    """摘要生成请求"""
    session_id: str
    summary_type: Literal["auto", "user_requested", "session_end"]
    detail_level: Literal["brief", "medium", "detailed"] = "medium"
    include_key_findings: bool = True
    include_referenced_papers: bool = True


class KeyFinding(BaseModel):
    """关键发现"""
    topic: str
    finding: str
    source_paragraphs: list[str]


class Summary(BaseModel):
    """会话摘要"""
    summary_id: str
    session_id: str
    summary_type: Literal["auto", "user_requested", "session_end"]
    created_at: datetime
    original_message_count: int
    original_token_count: int
    summary: str
    key_findings: list[KeyFinding] = Field(default_factory=list)
    referenced_papers: list[str] = Field(default_factory=list)
    referenced_notes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ISummarizer:
    """摘要生成工具接口"""

    async def generate(self, request: SummaryRequest) -> Summary:
        """
        生成会话摘要

        Args:
            request: 摘要请求

        Returns:
            Summary: 生成的摘要
        """
        raise NotImplementedError

    async def get(self, summary_id: str) -> Optional[Summary]:
        """获取摘要"""
        raise NotImplementedError

    async def list_by_session(self, session_id: str) -> list[Summary]:
        """获取会话的所有摘要"""
        raise NotImplementedError
```

### 4.4 论文解析工具

```python
# tools/parser.py

from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime


class ParseRequest(BaseModel):
    """解析请求"""
    file_path: str
    source: Literal["arxiv", "local_upload", "pubmed"]
    paper_id: Optional[str] = None


class ParseProgress(BaseModel):
    """解析进度"""
    paper_id: str
    status: Literal["pending", "parsing", "success", "partial_failure", "failed"]
    progress: float  # 0-1
    current_step: str
    error: Optional[str] = None


class ParseResult(BaseModel):
    """解析结果"""
    paper_id: str
    status: Literal["success", "partial_failure", "failed"]
    metadata: dict
    total_paragraphs: int
    warnings: list[str] = []


class IPaperParser:
    """论文解析工具接口"""

    async def parse(self, request: ParseRequest) -> ParseResult:
        """
        解析论文

        Args:
            request: 解析请求

        Returns:
            ParseResult: 解析结果
        """
        raise NotImplementedError

    async def get_progress(self, paper_id: str) -> ParseProgress:
        """获取解析进度"""
        raise NotImplementedError

    async def cancel(self, paper_id: str) -> bool:
        """取消解析"""
        raise NotImplementedError
```

### 4.5 导出工具

```python
# tools/exporter.py

from pydantic import BaseModel
from typing import Literal, Optional


class ExportRequest(BaseModel):
    """导出请求"""
    export_type: Literal["papers", "session", "notes", "all"]
    session_id: Optional[str] = None
    paper_ids: Optional[list[str]] = None
    format: Literal["zip", "markdown", "json"] = "zip"


class ExportResult(BaseModel):
    """导出结果"""
    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error: Optional[str] = None


class IExporter:
    """导出工具接口"""

    async def export(self, request: ExportRequest) -> ExportResult:
        """
        导出数据

        Args:
            request: 导出请求

        Returns:
            ExportResult: 导出结果
        """
        raise NotImplementedError

    async def get_export_status(self, task_id: str) -> ExportResult:
        """获取导出状态"""
        raise NotImplementedError

    async def download(self, task_id: str) -> bytes:
        """下载导出文件"""
        raise NotImplementedError
```

---

## 5. 数据层接口

数据层负责所有持久化操作。

### 5.1 论文存储接口

```python
# repositories/paper_repository.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PaperMetadata(BaseModel):
    """论文元数据"""
    paper_id: str
    title: str
    authors: List[str]
    year: Optional[int]
    source: str
    arxiv_id: Optional[str]
    doi: Optional[str]
    abstract: Optional[str]
    created_at: datetime
    parsed_at: Optional[datetime]
    file_path: Optional[str]
    total_paragraphs: int
    total_notes: int
    parse_status: str


class IPaperRepository:
    """论文存储接口"""

    async def save_metadata(self, paper: PaperMetadata) -> bool:
        """保存论文元数据"""
        raise NotImplementedError

    async def get_metadata(self, paper_id: str) -> Optional[PaperMetadata]:
        """获取论文元数据"""
        raise NotImplementedError

    async def list_all(self) -> List[PaperMetadata]:
        """列出所有论文"""
        raise NotImplementedError

    async def delete(self, paper_id: str) -> bool:
        """删除论文"""
        raise NotImplementedError

    async def update_metadata(self, paper_id: str, updates: dict) -> bool:
        """更新元数据"""
        raise NotImplementedError

    async def get_content_path(self, paper_id: str) -> Optional[str]:
        """获取正文文件路径"""
        raise NotImplementedError

    async def get_notes_path(self, paper_id: str) -> Optional[str]:
        """获取笔记文件路径"""
        raise NotImplementedError

    async def get_index_path(self, paper_id: str) -> Optional[str]:
        """获取索引文件路径"""
        raise NotImplementedError
```

### 5.2 段落索引接口

```python
# repositories/index_repository.py

from pydantic import BaseModel
from typing import Optional, Literal


class ParagraphIndexEntry(BaseModel):
    """段落索引条目"""
    type: Literal["content", "note"]
    offset: int
    length: int
    line_number: Optional[int] = None
    section: Optional[str] = None
    file: Literal["content.md", "notes.md"]


class IIndexRepository:
    """段落索引接口"""

    async def save_index(self, paper_id: str, index: dict[str, ParagraphIndexEntry]) -> bool:
        """保存段落索引"""
        raise NotImplementedError

    async def get_index(self, paper_id: str) -> Optional[dict[str, ParagraphIndexEntry]]:
        """获取段落索引"""
        raise NotImplementedError

    async def get_paragraph(self, paper_id: str, paragraph_id: str) -> Optional[dict]:
        """获取段落内容"""
        raise NotImplementedError

    async def update_entry(self, paper_id: str, paragraph_id: str, entry: ParagraphIndexEntry) -> bool:
        """更新单个索引条目"""
        raise NotImplementedError

    async def delete_entry(self, paper_id: str, paragraph_id: str) -> bool:
        """删除索引条目"""
        raise NotImplementedError

    async def rebuild_index(self, paper_id: str) -> bool:
        """重建索引"""
        raise NotImplementedError
```

### 5.3 会话存储接口

```python
# repositories/session_repository.py

from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime


class Session(BaseModel):
    """会话"""
    session_id: str
    title: str
    status: Literal["active", "paused", "archived", "deleted"]
    state: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    total_messages: int = 0
    total_tokens: int = 0


class Message(BaseModel):
    """消息"""
    message_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    token_count: int = 0


class ISessionRepository:
    """会话存储接口"""

    async def create_session(self, session_id: str, title: str) -> Session:
        """创建会话"""
        raise NotImplementedError

    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        raise NotImplementedError

    async def list_sessions(self, status: Optional[str] = None) -> List[Session]:
        """列出会话"""
        raise NotImplementedError

    async def update_session(self, session_id: str, updates: dict) -> bool:
        """更新会话"""
        raise NotImplementedError

    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        raise NotImplementedError

    async def add_message(self, session_id: str, message: Message) -> bool:
        """添加消息"""
        raise NotImplementedError

    async def get_messages(self, session_id: str, limit: int = 100) -> List[Message]:
        """获取消息列表"""
        raise NotImplementedError

    async def get_active_session_id(self) -> Optional[str]:
        """获取当前活跃会话 ID"""
        raise NotImplementedError

    async def set_active_session(self, session_id: str) -> bool:
        """设置活跃会话"""
        raise NotImplementedError
```

### 5.4 项目状态接口

```python
# repositories/project_state_repository.py

from pydantic import BaseModel, Field
from typing import Optional, List


class ProjectState(BaseModel):
    """项目状态"""
    version: int
    created_at: str
    updated_at: str
    research_topic: Optional[str] = None
    research_stage: Optional[str] = None
    total_papers: int = 0
    total_sessions: int = 0
    total_notes: int = 0
    active_session_id: Optional[str] = None
    recent_papers: List[str] = Field(default_factory=list)


class IProjectStateRepository:
    """项目状态接口"""

    async def get_state(self) -> ProjectState:
        """获取项目状态"""
        raise NotImplementedError

    async def update_state(self, updates: dict) -> ProjectState:
        """更新项目状态"""
        raise NotImplementedError

    async def increment_papers(self) -> int:
        """增加论文计数"""
        raise NotImplementedError

    async def increment_sessions(self) -> int:
        """增加会话计数"""
        raise NotImplementedError

    async def increment_notes(self) -> int:
        """增加笔记计数"""
        raise NotImplementedError

    async def add_recent_paper(self, paper_id: str) -> bool:
        """添加最近论文"""
        raise NotImplementedError
```

---

## 6. 前后端通信协议

### 6.1 HTTP REST API

#### 6.1.1 论文管理

```yaml
# 论文管理 API

# 上传论文
POST /api/v1/papers/upload
Content-Type: multipart/form-data
Request:
  file: <binary>
  source: "local_upload" | "arxiv"
  arxiv_id?: string
Response:
  200: { code: 0, data: { paper_id: string, status: "parsing" } }

# 获取论文列表
GET /api/v1/papers
Response:
  200: {
    code: 0,
    data: {
      papers: [
        {
          paper_id: string
          title: string
          authors: string[]
          year: number
          source: string
          total_paragraphs: number
          total_notes: number
          parse_status: string
        }
      ],
      total: number
    }
  }

# 获取论文详情
GET /api/v1/papers/{paper_id}
Response:
  200: { code: 0, data: PaperMetadata }

# 删除论文
DELETE /api/v1/papers/{paper_id}
Response:
  200: { code: 0, message: "deleted" }

# 获取论文正文
GET /api/v1/papers/{paper_id}/content
Response:
  200: { code: 0, data: { content: string, paragraphs: ParagraphIndex[] } }

# 获取论文笔记
GET /api/v1/papers/{paper_id}/notes
Response:
  200: { code: 0, data: { notes: Note[] } }
```

#### 6.1.2 检索与溯源

```yaml
# 检索 API

# 混合检索（支持关键词/向量/混合模式）
POST /api/v1/search
Request:
  {
    query: string,
    top_k?: number (default: 10),
    source_filter?: "all" | "content_only" | "note_only",
    paper_ids?: string[],
    search_mode?: "keyword" | "vector" | "hybrid",  # 新增，默认hybrid
    include_scores?: boolean   # 新增，是否返回详细得分
  }
Response:
  200: {
    code: 0,
    data: {
      results: SearchResult[],
      total: number,
      search_mode: string,     # 实际使用的模式
      search_duration_ms: number
    }
  }

# 溯源查看
GET /api/v1/trace/{paper_id}/{paragraph_id}
Response:
  200: {
    code: 0,
    data: {
      paragraph: Paragraph,
      context: {
        before: string
        after: string
        section: string
      },
      paper: PaperMetadata
    }
  }
```

#### 6.1.3 笔记管理

```yaml
# 笔记 API

# 创建笔记
POST /api/v1/notes
Request:
  {
    paper_id: string
    linked_paragraphs?: string[]
    content: string
    tags?: string[]
  }
Response:
  201: { code: 0, data: Note }

# 更新笔记
PUT /api/v1/notes/{note_id}
Request:
  {
    content?: string
    linked_paragraphs?: string[]
    tags?: string[]
  }
Response:
  200: { code: 0, data: Note }

# 删除笔记
DELETE /api/v1/notes/{note_id}
Response:
  200: { code: 0, message: "deleted" }

# 搜索笔记
GET /api/v1/notes/search?q={query}
Response:
  200: { code: 0, data: { results: Note[] } }
```

#### 6.1.4 会话管理

```yaml
# 会话 API

# 创建会话
POST /api/v1/sessions
Request:
  {
    title?: string
  }
Response:
  201: { code: 0, data: { session_id: string, title: string } }

# 获取会话列表
GET /api/v1/sessions
Response:
  200: {
    code: 0,
    data: {
      sessions: Session[],
      active_session_id: string
    }
  }

# 获取会话详情
GET /api/v1/sessions/{session_id}
Response:
  200: { code: 0, data: { session: Session, messages: Message[] } }

# 切换活跃会话
PUT /api/v1/sessions/{session_id}/activate
Response:
  200: { code: 0, message: "activated" }

# 关闭会话
PUT /api/v1/sessions/{session_id}/close
Response:
  200: { code: 0, message: "closed" }

# 删除会话
DELETE /api/v1/sessions/{session_id}
Response:
  200: { code: 0, message: "deleted" }
```

#### 6.1.5 对话与摘要

```yaml
# 对话 API

# 发送消息
POST /api/v1/sessions/{session_id}/messages
Request:
  {
    content: string
  }
Response:
  200: {
    code: 0,
    data: {
      message_id: string
      response: string
      metadata: {
        search_results?: SearchResult[]
        tool_calls?: object[]
      }
    }
  }

# 获取消息历史
GET /api/v1/sessions/{session_id}/messages?limit=100
Response:
  200: { code: 0, data: { messages: Message[] } }

# 生成摘要
POST /api/v1/sessions/{session_id}/summary
Request:
  {
    summary_type?: "auto" | "user_requested" | "session_end"
    detail_level?: "brief" | "medium" | "detailed"
  }
Response:
  200: { code: 0, data: Summary }

# 获取摘要列表
GET /api/v1/summaries
Response:
  200: { code: 0, data: { summaries: Summary[] } }
```

#### 6.1.6 导出

```yaml
# 导出 API

# 创建导出任务
POST /api/v1/export
Request:
  {
    export_type: "papers" | "session" | "notes" | "all"
    session_id?: string
    paper_ids?: string[]
    format: "zip" | "markdown" | "json"
  }
Response:
  202: { code: 0, data: { task_id: string, status: "processing" } }

# 获取导出状态
GET /api/v1/export/status/{task_id}
Response:
  200: {
    code: 0,
    data: {
      task_id: string
      status: "pending" | "processing" | "completed" | "failed"
      file_path?: string
      file_size?: number
    }
  }

# 下载导出文件
GET /api/v1/export/download/{task_id}
Response:
  200: <file binary>
```

### 6.2 WebSocket API

```python
# WebSocket 协议定义

from typing import Literal


class WSMessage(BaseModel):
    """WebSocket 消息基类"""
    type: str
    data: dict
    timestamp: str


# 客户端 → 服务器消息类型
class ClientMessageType(str, Enum):
    """客户端消息类型"""
    SEND_MESSAGE = "send_message"           # 发送对话消息
    TYPING_START = "typing_start"           # 开始输入
    TYPING_STOP = "typing_stop"             # 停止输入
    SUBSCRIBE_SESSION = "subscribe"         # 订阅会话更新
    UNSUBSCRIBE_SESSION = "unsubscribe"     # 取消订阅


# 服务器 → 客户端消息类型
class ServerMessageType(str, Enum):
    """服务器消息类型"""
    MESSAGE_RESPONSE = "message_response"   # 消息响应
    STREAM_CHUNK = "stream_chunk"           # 流式响应片段
    SEARCH_PROGRESS = "search_progress"     # 检索进度
    PARSE_PROGRESS = "parse_progress"       # 解析进度
    SESSION_UPDATED = "session_updated"     # 会话更新
    ERROR = "error"                         # 错误


# WebSocket 连接
WS_URL = "ws://localhost:8000/ws"

# 订阅会话
{
  "type": "subscribe",
  "data": {
    "session_id": "session_20240204_143000"
  }
}

# 发送消息
{
  "type": "send_message",
  "data": {
    "session_id": "session_20240204_143000",
    "content": "CNN 在医学影像中的应用有哪些？"
  }
}

# 流式响应
{
  "type": "stream_chunk",
  "data": {
    "chunk": "找到 3 篇相关论文：",
    "is_final": false
  }
}
```

---

## 7. 错误码定义

### 7.1 错误码规范

```python
# models/error_codes.py

from enum import IntEnum


class ErrorCode(IntEnum):
    """错误码定义

    错误码格式：{HTTP状态码}{模块序号}{具体错误}
    - 0: 成功
    - 4xxxx: 客户端错误
    - 5xxxx: 服务端错误
    """

    # ========== 成功 ==========
    SUCCESS = 0

    # ========== 通用错误 (40001-40999) ==========
    UNKNOWN_ERROR = 40000
    INVALID_REQUEST = 40001
    INVALID_PARAMETER = 40002
    MISSING_PARAMETER = 40003
    UNAUTHORIZED = 40004
    FORBIDDEN = 40005
    RATE_LIMIT_EXCEEDED = 40006

    # ========== 论文相关 (40101-40199) ==========
    PAPER_NOT_FOUND = 40101
    PAPER_ALREADY_EXISTS = 40102
    PARSE_FAILED = 40103
    INDEX_CORRUPTED = 40104
    INVALID_FILE_FORMAT = 40105
    FILE_TOO_LARGE = 40106
    FILE_NOT_FOUND = 40107
    PARSE_INCOMPLETE = 40108        # 解析不完整（部分失败）
    INDEX_MISMATCH = 40109         # 索引与内容不匹配

    # ========== 段落相关 (40201-40299) ==========
    PARAGRAPH_NOT_FOUND = 40201
    PARAGRAPH_ID_INVALID = 40202
    PARAGRAPH_CONTENT_MISMATCH = 40203  # 内容哈希不匹配

    # ========== 检索相关 (40301-40399) ==========
    SEARCH_FAILED = 40301
    SEARCH_TIMEOUT = 40302
    NO_RESULTS_FOUND = 40303
    INVALID_SEARCH_QUERY = 40304
    SEARCH_ENGINE_UNAVAILABLE = 40305  # ripgrep 不可用

    # ========== 向量检索相关 (40351-40399) ==========
    VECTOR_INDEX_NOT_FOUND = 40351       # 向量索引不存在
    VECTOR_INDEX_CORRUPTED = 40352       # 向量索引损坏
    EMBEDDING_FAILED = 40353             # 向量化失败
    EMBEDDING_MODEL_NOT_AVAILABLE = 40354  # Embedding模型不可用
    EMBEDDING_DIMENSION_MISMATCH = 40355   # 向量维度不匹配
    GPU_NOT_AVAILABLE = 40356            # GPU不可用（本地模式）

    # ========== 笔记相关 (40401-40499) ==========
    NOTE_NOT_FOUND = 40401
    NOTE_CREATE_FAILED = 40402
    NOTE_UPDATE_FAILED = 40403
    NOTE_DELETE_FAILED = 40404
    NOTE_ID_INVALID = 40405

    # ========== 会话相关 (40501-40599) ==========
    SESSION_NOT_FOUND = 40501
    SESSION_LIMIT_EXCEEDED = 40502
    SESSION_CREATE_FAILED = 40503
    MESSAGE_SEND_FAILED = 40504
    SESSION_ALREADY_EXISTS = 40505

    # ========== 摘要相关 (40601-40699) ==========
    SUMMARY_GENERATE_FAILED = 40601
    SUMMARY_NOT_FOUND = 40602
    TOKEN_LIMIT_EXCEEDED = 40603
    SUMMARY_INCOMPLETE = 40604      # 摘要缺少必要字段

    # ========== 导出相关 (40701-40799) ==========
    EXPORT_FAILED = 40701
    EXPORT_NOT_FOUND = 40702
    EXPORT_IN_PROGRESS = 40703
    EXPORT_TASK_EXPIRED = 40704

    # ========== LLM 相关 (40801-40899) ==========
    LLM_API_ERROR = 40801
    LLM_TIMEOUT = 40802
    LLM_QUOTA_EXCEEDED = 40803
    LLM_INVALID_RESPONSE = 40804
    LLM_RATE_LIMIT = 40805
    LLM_CONTENT_FILTERED = 40806   # 内容被过滤

    # ========== 并发相关 (40901-40999) ==========
    CONCURRENT_MODIFICATION = 40901  # 并发修改冲突
    FILE_LOCK_TIMEOUT = 40902        # 文件锁超时
    FILE_LOCK_ACQUISITION_FAILED = 40903  # 获取文件锁失败

    # ========== 导出相关 (40701-40799) ==========
    EXPORT_FAILED = 7001
    EXPORT_NOT_FOUND = 7002
    EXPORT_IN_PROGRESS = 7003

    # ========== LLM 相关 (40801-40899) ==========
    LLM_API_ERROR = 8001
    LLM_TIMEOUT = 8002
    LLM_QUOTA_EXCEEDED = 8003
    LLM_INVALID_RESPONSE = 8004


class ErrorResponse(BaseModel):
    """错误响应"""
    code: ErrorCode
    message: str
    details: Optional[dict] = None
    request_id: str
    timestamp: str
```

### 7.2 错误响应示例

```json
{
  "code": 2001,
  "message": "Paper not found",
  "details": {
    "paper_id": "arxiv_2401.12345",
    "suggestion": "Check if the paper ID is correct or import the paper first"
  },
  "request_id": "req_20240204_143000",
  "timestamp": "2024-02-04T14:30:00Z"
}
```

---

## 附录 A：接口依赖关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                         UI Layer (Gradio)                       │
└─────────────────────────────────────┬───────────────────────────┘
                                      │ HTTP/WebSocket
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                  API + Router Layer (Intent Routing)            │
│  ┌────────────┬────────────┬────────────┬────────────┬────────┐ │
│  │ Chat Route │ Search Rt  │ Note Route │ Summary Rt │ Export │ │
│  └────────────┴────────────┴────────────┴────────────┴────────┘ │
└─────────────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Main Agent (State + Memory)                   │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │ Conversation Mgr │◄────────────►│   Memory Manager │        │
│  └──────────────────┘              └──────────────────┘        │
└─────────────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Tool Layer (Logic Stateless)                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │ Fulltext     │ Note         │ Summarizer   │ Parser       │ │
│  │ Search       │ Manager      │              │              │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
└─────────────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer (Repositories)                    │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │ Paper        │ Index        │ Session      │ Project      │ │
│  │ Repository   │ Repository   │ Repository   │ State Repo   │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 附录 B：接口调用时序图

### 场景：用户进行全文检索

```
User          UI           Router          Agent          SearchTool       DataRepo
 │             │              │               │                │               │
 │─"CNN医学影像"→│              │               │                │               │
 │             │─POST /search─→│               │                │               │
 │             │              │─detect_intent→│                │               │
 │             │              │←Intent:SEARCH─│                │               │
 │             │              │─route(Search) │                │               │
 │             │              │               │─search(query)──→│               │
 │             │              │               │                │─ripgrep──────→│
 │             │              │               │                │←results───────│
 │             │              │               │←SearchResponse─│               │
 │             │←─200 Results─│               │                │               │
 │←─显示结果───│              │               │                │               │
```

---

*文档版本: 1.1 | 最后更新: 2026-02-05*
