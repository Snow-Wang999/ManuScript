# ManuScript v3.0 开发计划

> **文档版本**: 1.2
> **创建日期**: 2026-02-05
> **最后更新**: 2026-02-06
> **依据文档**: 09-14_ManuScript_v3.0_*.md

---

## 目录

1. [开发策略](#1-开发策略)
2. [任务分解](#2-任务分解)
3. [依赖关系图](#3-依赖关系图)
4. [开发里程碑](#4-开发里程碑)
5. [风险评估](#5-风险评估)

---

## 1. 开发策略

### 1.1 总体策略

| 策略 | 说明 |
|------|------|
| **自底向上** | 先实现数据层，再向上实现工具层、Agent 层、API 层 |
| **单个 Agent 单独测试** | 每个 Agent 开发完成后单独测试，再进行编排 |
| **先脚本后 UI** | 核心逻辑先在脚本中验证，UI 最后添加 |
| **版本独立开发** | v3_0 目录独立开发，不依赖之前版本 |

### 1.2 开发顺序

```
┌─────────────────────────────────────────────────────────────────┐
│                      开发顺序（5个阶段）                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: 基础设施 ─────────────────────────────────► 3-4天      │
│  • 项目结构搭建                                                   │
│  • 数据模型定义（models/）                                         │
│  • 配置和日志 + **GPU检测脚本**                                   │
│  • ID 生成器、文件工具等 utils                                    │
│                                                                 │
│  Phase 2: 数据层 ─────────────────────────────────► 5-6天        │
│  • PaperRepository（论文存储）                                    │
│  • IndexRepository（索引存储）                                    │
│  • FTSRepository（FTS5 全文索引）                                 │
│  • VectorRepository（ChromaDB 向量）                              │
│  • SessionRepository（会话存储）                                  │
│  • ProjectStateRepository（项目状态）                             │
│  • **EmbeddingService（本地+API）** - 提前到Phase 2               │
│                                                                 │
│  Phase 3: 工具层 ─────────────────────────────────► 6-7天        │
│  • FulltextSearchTool（ripgrep + FTS5）                           │
│  • VectorSearchTool + ResultRanker（RRF融合）                     │
│  • HybridSearchTool（混合检索整合）                               │
│  • NoteManager（笔记管理）                                        │
│  • MarkerParser（学术PDF解析）                                    │
│  • PyMuPDFParser（Fallback解析器）                                │
│  • ParagraphIndexer（段落索引）                                   │
│  • PaperParser（解析整合 + 异步向量化触发）                        │
│  • Summarizer（摘要生成）                                         │
│  • **Exporter 移到 Phase 5（P1功能）**                            │
│                                                                 │
│  Phase 4: Agent 层 ──────────────────────────────► 3-4天          │
│  • ConversationManager（对话管理）                                │
│  • MemoryManager（记忆管理）                                      │
│  • MainAgent（主 Agent）                                          │
│  • IntentRouter（意图路由）                                       │
│                                                                 │
│  Phase 5: API & UI 层 ────────────────────────────► 4-5天         │
│  • FastAPI 应用和路由                                             │
│  • Gradio UI 组件                                                │
│  • WebSocket 支持                                                │
│  • **Exporter（P1功能）**                                        │
│  • 集成测试                                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

总计: 21-27 天（约 4-5 周，增加混合检索和向量相关任务）

关键调整：
• EmbeddingService 从 Phase 3 移到 Phase 2（VectorRepository 依赖）
• Day 7 检索任务拆分到 Day 7-9（避免单日过重）
• Exporter 从 Phase 3 移到 Phase 5（非关键路径）
• Day 1 新增 GPU 检测脚本
```

### 1.3 技术选型确认

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **语言** | Python | 3.10+ | 主开发语言 |
| **Web 框架** | FastAPI | 0.100+ | 异步 API |
| **UI 框架** | Gradio | 4.x | MVP 快速开发 |
| **数据校验** | Pydantic | 2.x | 类型安全 |
| **PDF 解析** | Marker | 最新 | 学术PDF主解析器 |
| | PyMuPDF | 最新 | Fallback解析器 |
| | pylatexenc | 最新 | LaTeX解析（P1） |
| **全文检索** | ripgrep | 最新 | 精确关键词匹配 |
| | SQLite FTS5 | 3.x | 全文倒排索引 |
| **向量检索** | ChromaDB | 0.4+ | 向量相似度检索 |
| **Embedding** | BGE-M3 | 最新 | 本地模式（多语言） |
| | OpenAI API | - | API模式（可选） |
| **LLM** | OpenAI API | gpt-4o-mini | 文本生成 |
| **存储** | JSON/Markdown | - | 本地文件 |

---

## 2. 任务分解

### 2.1 Phase 1: 基础设施（3-4天）

| ID | 任务 | 交付物 | 估算 | 依赖 |
|----|------|--------|------|------|
| **P1-1** | 项目结构搭建 | v3_0/ 目录及所有子目录 | 0.5天 | - |
| **P1-2** | 数据模型定义 | models/*.py | 1天 | P1-1 |
| **P1-3** | 配置系统 | config.py, settings.yaml, embedding_config.json | 0.5天 | P1-1 |
| **P1-4** | 日志系统 | logger.py | 0.5天 | P1-1 |
| **P1-5** | 工具函数 | utils/*.py | 1天 | P1-1 |

#### P1-1: 项目结构搭建
```
v3_0/
├── main.py
├── config.py
├── logger.py
├── models/
├── schemas/
├── router/
├── agent/
├── tools/
├── repositories/
├── api/
├── ui/
├── services/
├── utils/
├── config/
├── tests/
└── (仓库根目录) data/   # 由 DATA_DIR 配置指定
```

#### P1-2: 数据模型定义
- [ ] `models/paper.py` - PaperMetadata, ParseStatus, **EmbeddingStatus**
- [ ] `models/paragraph.py` - Paragraph, ParagraphType
- [ ] `models/note.py` - Note, NoteCreate
- [ ] `models/session.py` - Session, AgentState
- [ ] `models/message.py` - Message, MessageRole
- [ ] `models/search.py` - SearchQuery, SearchResult（**混合检索评分**）
- [ ] `models/embedding.py` - **EmbeddingConfig, EmbeddingMode（新增）**
- [ ] `models/memory.py` - MemoryType, MemoryItem
- [ ] `models/error.py` - ErrorCode, ErrorResponse（**新增向量错误码**）

#### P1-5: 工具函数
- [ ] `utils/file_utils.py` - 文件操作
- [ ] `utils/hash_utils.py` - 哈希计算（SHA256）
- [ ] `utils/id_generator.py` - 各类 ID 生成
- [ ] `utils/datetime_utils.py` - 时间处理
- [ ] `utils/ripgrep_wrapper.py` - ripgrep 命令行封装
- [ ] `utils/file_lock.py` - **文件锁（并发安全，P0优先级）**
- [ ] `utils/hardware_detector.py` - **GPU检测脚本（新增）**

#### P1-5a: GPU检测脚本（新增）
```python
# utils/hardware_detector.py
class HardwareDetector:
    """硬件检测"""

    @staticmethod
    def detect_gpu() -> dict:
        """检测 GPU 可用性"""
        # 1. 检测 CUDA 可用性
        # 2. 检测显存大小
        # 3. 返回检测结果
        return {
            "cuda_available": bool,
            "gpu_name": str | None,
            "gpu_memory_gb": float | None,
            "recommended_mode": "local" | "api"
        }

    @staticmethod
    def write_to_config(result: dict):
        """写入配置文件"""
        # 更新 embedding_config.json 的 mode
```

---

### 2.2 Phase 2: 数据层（5-6天）

| ID | 任务 | 交付物 | 估算 | 依赖 |
|----|------|--------|------|------|
| **P2-1** | 接口定义 | repositories/interface.py | 0.5天 | P1-2 |
| **P2-2** | 工厂模式 | repositories/factory.py | 0.5天 | P2-1 |
| **P2-3** | FileLock工具 | utils/file_lock.py | 0.5天 | P1-5 |
| **P2-4** | PaperRepository | repositories/paper_repository.py | 1.5天 | P2-2, P2-3 |
| **P2-5** | IndexRepository | repositories/index_repository.py | 1天 | P2-2, P1-5 |
| **P2-6** | **FTSRepository** | **repositories/fts_repository.py** | **1天** | **P2-2** |
| **P2-7** | **VectorRepository** | **repositories/vector_repository.py** | **1天** | **P2-2** |
| **P2-8** | SessionRepository | repositories/session_repository.py | 0.5天 | P2-2, P1-5 |
| **P2-9** | ProjectStateRepository | repositories/project_state_repository.py | 0.5天 | P2-2 |
| **P2-10** | SummaryRepository | repositories/summary_repository.py | 0.5天 | P2-2 |
| **P2-11** | **EmbeddingService（本地）** | **tools/embedding/local_embedding.py** | **1天** | **P1-2, P1-5a** |
| **P2-12** | **EmbeddingService（API）** | **tools/embedding/api_embedding.py** | **0.5天** | **P1-2, P2-11** |
| **P2-13** | **EmbeddingFactory** | **tools/embedding/embedding_factory.py** | **0.5天** | **P2-11, P2-12** |

#### P2-4: PaperRepository 实现要点
```python
class PaperRepository(IPaperRepository):
    async def save_metadata(self, paper: PaperMetadata) -> bool
    async def get_metadata(self, paper_id: str) -> Optional[PaperMetadata]
    async def list_all(self) -> List[PaperMetadata]
    async def delete(self, paper_id: str) -> bool
    async def update_metadata(self, paper_id: str, updates: dict) -> bool
    async def update_embedding_status(self, paper_id: str, status: EmbeddingStatus) -> bool
    async def get_content_path(self, paper_id: str) -> Optional[str]
    async def get_notes_path(self, paper_id: str) -> Optional[str]
    async def get_index_path(self, paper_id: str) -> Optional[str]
```

#### P2-5: IndexRepository 实现要点
- 读取 `index.json` 获取段落索引
- 根据 `offset/length` 从 `content.md` 提取段落
- 计算文件哈希确保索引一致性
- 支持索引重建

#### P2-6: FTSRepository 实现要点（新增）
```python
class FTSRepository(IFTSRepository):
    """SQLite FTS5 全文索引"""
    async def initialize(self) -> None
    async def add_document(self, paper_id: str, paragraphs: List[Paragraph]) -> None
    async def search(self, query: str, top_k: int) -> List[SearchResult]
    async def delete_document(self, paper_id: str) -> None
```

#### P2-7: VectorRepository 实现要点（新增）
```python
class VectorRepository(IVectorRepository):
    """ChromaDB 向量索引"""
    async def initialize(self) -> None
    async def add_documents(self, paper_id: str, embeddings: List[float], paragraphs: List[str]) -> None
    async def search(self, query_embedding: List[float], top_k: int) -> List[SearchResult]
    async def delete_document(self, paper_id: str) -> None
```

#### P2-11/12/13: EmbeddingService 实现要点（调整到 Phase 2）
```python
class IEmbeddingService(ABC):
    async def encode(self, texts: List[str]) -> List[List[float]]
    def get_dimension(self) -> int
    def get_mode(self) -> str  # "local" | "api"

class LocalEmbeddingService(IEmbeddingService):
    """本地 BGE-M3 模型"""
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "auto")

class APIEmbeddingService(IEmbeddingService):
    """OpenAI API 模式"""
    def __init__(self, api_key: str, model: str = "text-embedding-3-small")

class EmbeddingFactory:
    """根据配置自动选择模式（优先使用检测结果）"""
    @staticmethod
    def create(config: EmbeddingConfig, hardware_info: dict) -> IEmbeddingService
```

---

### 2.3 Phase 3: 工具层（6-7天）

| ID | 任务 | 交付物 | 估算 | 依赖 |
|----|------|--------|------|------|
| **P3-1** | 接口定义 | tools/interface.py | 0.5天 | P1-2 |
| **P3-2** | 工具工厂 | tools/factory.py | 0.5天 | P3-1 |
| **P3-3** | RipgrepWrapper | utils/ripgrep_wrapper.py | 0.5天 | P1-5 |
| **P3-4** | FulltextSearchTool | tools/search/fulltext_search.py（ripgrep + FTS5） | 1天 | P3-2, P3-3, P2-6 |
| **P3-5** | VectorSearchTool + RRF | tools/search/vector_search.py, result_ranker.py | 1天 | P3-2, P2-7, P2-13 |
| **P3-6** | HybridSearchTool | tools/search/hybrid_search.py（RRF融合） | 1天 | P3-4, P3-5 |
| **P3-7** | NoteManager | tools/note/note_manager.py | 1天 | P3-2, P2-4 |
| **P3-8** | MarkerParser | tools/parse/marker_parser.py | 1天 | P3-2, P1-5 |
| **P3-9** | PyMuPDFParser | tools/parse/pymupdf_parser.py（Fallback） | 0.5天 | P3-2, P1-5 |
| **P3-10** | ParagraphIndexer | tools/parse/paragraph_indexer.py | 1天 | P3-2, P1-5 |
| **P3-11** | PaperParser（整合） | tools/parse/paper_parser.py（**含异步向量化触发**） | 0.5天 | P3-8, P3-9, P3-10, P2 |
| **P3-12** | Summarizer | tools/summary/summarizer.py | 1天 | P3-2, P2-10 |
| ~~**P3-17**~~ | ~~Exporter~~ | **移到 Phase 5（P1功能）** | ~~0.5天~~ | ~~P3-2, P2~~ |

#### P3-4/5/6: 混合检索实现要点（调整后）
```python
class FulltextSearchTool(IFulltextSearchTool):
    """ripgrep + FTS5 关键词检索"""
    async def search(self, query: str, top_k: int) -> List[SearchResult]

class VectorSearchTool(IVectorSearchTool):
    """ChromaDB 向量检索"""
    async def search(self, query: str, top_k: int) -> List[SearchResult]

class ResultRanker:
    """RRF 融合排序器"""
    async def rrf_fusion(
        keyword_results: List[SearchResult],
        vector_results: List[SearchResult],
        k: int = 60
    ) -> List[SearchResult]

class HybridSearchTool(ISearchTool):
    """RRF 融合混合检索"""
    async def search(self, query: SearchQuery, mode: str = "hybrid") -> SearchResponse
    # mode: "keyword" | "vector" | "hybrid"
```

#### P3-8/9/11: PaperParser 实现要点（使用 Marker）
- Marker 解析学术 PDF（表格/公式/多栏）
- PyMuPDF Fallback（扫描件/损坏 PDF）
- 识别章节结构（Abstract, Introduction, ...）
- 生成段落 ID（基于内容哈希，重解析稳定）
- 写入 `content.md`
- 构建索引写入 `index.json`
- 创建空的 `notes.md`
- 保存 `metadata.json`（含 `embedding_status`）
- **异步向量化段落**（后台任务）：
  ```python
  async def parse_and_index(self, pdf_path: str, paper_id: str) -> Paper:
      # 1. Marker 解析
      result = await self._marker_parser.parse(pdf_path)
      # 2. 生成段落索引
      paragraphs = self._indexer.index(result.content)
      # 3. 更新 embedding_status = "processing"
      await self._paper_repo.update_embedding_status(paper_id, EmbeddingStatus.PROCESSING)
      # 4. 异步向量化（不阻塞）
      asyncio.create_task(self._embed_paragraphs(paper_id, paragraphs))
      return paper

  async def _embed_paragraphs(self, paper_id: str, paragraphs: list[str]):
      """异步向量化段落"""
      try:
          embeddings = await self._embedding_service.encode(paragraphs)
          await self._vector_repo.add(paper_id, embeddings, paragraphs)
          # 更新状态
          await self._paper_repo.update_embedding_status(
              paper_id, EmbeddingStatus.SUCCESS,
              embedding_model=self._embedding_service.get_mode()
          )
      except Exception as e:
          await self._paper_repo.update_embedding_status(paper_id, EmbeddingStatus.FAILED)
          logger.error(f"Embedding failed for {paper_id}: {e}")
  ```

---

### 2.4 Phase 4: Agent 层（3-4天）

| ID | 任务 | 交付物 | 估算 | 依赖 |
|----|------|--------|------|------|
| **P4-1** | 接口定义 | agent/interface.py | 0.5天 | P1-2 |
| **P4-2** | ConversationManager | agent/conversation_manager.py | 1天 | P4-1, P2-8 |
| **P4-3** | MemoryManager | agent/memory_manager.py | 1天 | P4-1, P2 |
| **P4-4** | IntentDetector | router/intent_detector.py | 0.5天 | P4-1 |
| **P4-5** | IntentRouter | router/intent_router.py | 0.5天 | P4-4, P3 |
| **P4-6** | RouteConfig | router/route_config.py | 0.5天 | P4-5 |
| **P4-7** | MainAgent | agent/main_agent.py | 1天 | P4-2, P4-3, P4-6, P3 |

#### P4-5: IntentRouter 实现要点
```python
class IntentRouter:
    # 意图类型
    # - CHAT: 闲聊/对话
    # - SEARCH: 全文检索
    # - NOTE_SEARCH: 笔记检索
    # - NOTE_ADD: 添加笔记
    # - NOTE_EDIT: 编辑笔记
    # - SUMMARIZE: 生成摘要
    # - PARSE: 论文解析
    # - TRACE: 溯源查看
    # - EXPORT: 导出
```

#### P4-7: MainAgent 实现要点
- 管理会话状态（AgentState）
- 协调工具调用
- 管理长期记忆
- 判断是否需要摘要

---

### 2.5 Phase 5: API & UI 层（4-5天）

| ID | 任务 | 交付物 | 估算 | 依赖 |
|----|------|--------|------|------|
| **P5-1** | FastAPI 应用 | api/app.py | 0.5天 | P1-1 |
| **P5-2** | 中间件 | api/middleware.py | 0.5天 | P5-1 |
| **P5-3** | 依赖注入 | api/dependencies.py | 0.5天 | P5-1, P2, P3, P4 |
| **P5-4** | 论文路由 | api/routes/papers.py | 0.5天 | P5-3, P3-11 |
| **P5-5** | 检索路由 | api/routes/search.py（**支持search_mode**） | 0.5天 | P5-3, P3-6 |
| **P5-6** | 笔记路由 | api/routes/notes.py | 0.5天 | P5-3, P3-7 |
| **P5-7** | 会话路由 | api/routes/sessions.py | 0.5天 | P5-3, P4 |
| **P5-8** | 摘要路由 | api/routes/summaries.py | 0.5天 | P5-3, P2-10 |
| **P5-9** | **Embedding配置路由** | **api/routes/embedding.py** | **0.5天** | **P5-3, P2-13** |
| **P5-10** | WebSocket | api/routes/websocket.py | 0.5天 | P5-3 |
| **P5-11** | Gradio 布局 | ui/app.py | 1天 | P5-1 |
| **P5-12** | UI 组件 | ui/components/*.py | 1天 | P5-11 |
| **P5-13** | **Exporter（P1功能）** | **tools/export/exporter.py + api/routes/export.py** | **0.5天** | **P5-3** |
| **P5-14** | 集成测试 | tests/integration/*.py | 1天 | 全部 |

#### P5-10: Gradio 布局要点
```
┌─────────────┬──────────────────────────────────────┐
│ 会话列表     │ 主对话区域                             │
│ (左侧)      │                                       │
│             │                                       │
│ [+ 新建]    │ [输入框]                              │
└─────────────┴──────────────────────────────────────┘
│ 状态栏：已导入 23 篇论文 | Token: 12,345               │
└──────────────────────────────────────────────────────┘
```

---

### 2.6 测试计划

| 类型 | 覆盖范围 | 估算 |
|------|----------|------|
| **单元测试** | 每个 Repository 和 Tool | 分散在各阶段 |
| **集成测试** | 端到端流程 | P5-14 |
| **手动测试** | 真实论文场景 | P5 后 |
| **Schema 校验测试** | `content_hash`、索引字段完整性、段落 ID 稳定性 | Phase 2-3 |
| **并发测试** | 多会话同时修改、文件锁冲突 | Phase 2-3 |
| **向量检索测试** | Embedding 双模式切换、RRF 融合效果 | Phase 3 |

---

## 3. 依赖关系图

### 3.1 模块依赖图

```
┌─────────────────────────────────────────────────────────────────┐
│                          Phase 5: API & UI                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ FastAPI App  │  │ Gradio UI    │  │ WebSocket    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Phase 4: Agent                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ MainAgent    │◄─┤ IntentRouter │  │ Conversation │          │
│  │              │  │              │  │ Manager      │          │
│  └──────┬───────┘  └──────────────┘  └──────┬───────┘          │
│         │                                       │                 │
│         └───────────┬───────────────────────────┘                 │
│                     ▼                                             │
│              ┌──────────────┐                                     │
│              │MemoryManager │                                     │
│              └──────────────┘                                     │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Phase 3: Tools                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Hybrid  │ │ Embedding │ │  Parser  │ │ Summary  │           │
│  │  Search  │ │  Service  │ │ (Marker) │ │          │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │            │            │            │                   │
│   ┌───┴────┐  ┌───┴────┐  ┌───┴────┐  ┌───┴────┐              │
│   │ripgrep│  │BGE-M3  │  │Marker  │  │  Note  │              │
│   │ FTS5  │  │OpenAI  │  │PyMuPDF │  │Manager │              │
│   └───────┘  └────────┘  └────────┘  └────────┘              │
└───────┼────────────┼────────────┼────────────┼───────────────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Phase 2: Data                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │   Paper  │ │    FTS   │ │  Vector  │ │ Session  │           │
│  │    Repo  │ │   Repo   │ │   Repo   │ │   Repo   │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
└───────┼────────────┼────────────┼────────────┼───────────────────┘
        │            │            │            │
        └────────────┴────────────┴────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Phase 1: Infra                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Models  │ │   Utils  │ │  Config  │ │  Logger  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 任务依赖关系

```
P1-1 (项目结构)
 ├── P1-2 (数据模型)
 ├── P1-3 (配置 + embedding_config.json)
 ├── P1-4 (日志)
 └── P1-5 (工具函数 + GPU检测)
      ├── P2-* (数据层)
      │    ├── P2-6 (FTSRepository)
      │    ├── P2-7 (VectorRepository)
      │    ├── P2-11~13 (EmbeddingService) ← 调整到Phase 2
      │    ├── P3-* (工具层)
      │    │    ├── P3-4~6 (混合检索：Fulltext + Vector + Hybrid)
      │    │    ├── P3-8~11 (解析器 + 向量化触发)
      │    │    ├── P4-* (Agent 层)
      │    │    │    └── P5-* (API/UI 层)
      │    │    └── P5-* (部分)
      │    └── P4-* (部分)
      └── P3-* (部分)
```

---

## 4. 开发里程碑

### 4.1 Milestone 1: 基础设施完成（Day 4）

**验收标准**：
- [ ] 项目目录结构完整
- [ ] 所有数据模型定义完成，通过 Pydantic 校验
- [ ] 配置系统可以加载 settings.yaml
- [ ] 日志可以正常输出到文件和控制台
- [ ] ID 生成器可以生成各种类型的 ID
- [ ] ripgrep 可以通过 wrapper 正常调用

### 4.2 Milestone 2: 数据持久化可用（Day 9）

**验收标准**：
- [ ] 可以导入论文，生成 metadata.json（含 `embedding_status`）
- [ ] 可以解析论文，生成 content.md 和 index.json
- [ ] **FTS5 索引可以正常创建和查询**
- [ ] **ChromaDB 向量索引可以正常创建和查询**
- [ ] **EmbeddingService 可用（本地/API 双模式）**
- [ ] **GPU检测结果已写入配置**
- [ ] 可以列出所有论文
- [ ] 可以获取论文详情
- [ ] 可以创建会话，添加消息
- [ ] 项目状态可以正常读写
- [ ] **文件锁机制正常工作**（并发修改不会数据丢失）
- [ ] **段落 ID 基于内容哈希生成**（重解析后 ID 稳定）

### 4.3 Milestone 3: 核心功能可用（Day 16）

**验收标准**：
- [ ] **混合检索可以搜索论文内容**（ripgrep + FTS5 + 向量）
- [ ] **RRF 融合排序正常工作**
- [ ] **Embedding 本地/API 双模式可切换**
- [ ] 检索结果可以追溯到原文段落
- [ ] 可以添加、编辑、删除笔记
- [ ] 笔记可以被搜索
- [ ] **Marker 可以解析学术 PDF**
- [ ] **PyMuPDF Fallback 正常工作**
- [ ] 可以生成会话摘要
- [ ] 意图路由可以正确识别用户意图
- [ ] 摘要 `key_findings[*].source_paragraphs` 非空，且每个 ID 可 trace 到原文
- [ ] **重解析论文后，用户笔记关联仍然有效**（段落 ID 稳定性验证）
- [ ] **两个会话同时修改同一论文笔记时，不会发生数据丢失**

### 4.4 Milestone 4: MVP 完成（Day 21）

**验收标准**：
- [ ] FastAPI 服务可以正常启动
- [ ] 所有 REST API 可以正常调用
- [ ] `GET /api/v1/summaries` 可返回摘要列表
- [ ] `POST /api/v1/search` 支持 `search_mode` 参数
- [ ] **`GET /api/v1/embedding/config` 可获取/设置 Embedding 模式**
- [ ] Gradio UI 可以正常显示
- [ ] 可以通过 UI 完成核心流程：
  - [ ] 上传论文
  - [ ] 检索内容（关键词/向量/混合）
  - [ ] 查看原文
  - [ ] 添加笔记
  - [ ] 多会话切换
  - [ ] **切换 Embedding 模式**
- [ ] WebSocket 可以实时推送消息
- [ ] `trace` 接口可根据 `paper_id + paragraph_id` 稳定返回原段落

### 4.5 Milestone 5: 测试与优化（Day 25）

**验收标准**：
- [ ] 单元测试覆盖率 > 70%
- [ ] 集成测试通过
- [ ] 用 3 篇真实论文测试，功能正常
- [ ] 性能指标达标（检索 < 2s，溯源 < 0.5s）
- [ ] 文档完整

---

## 5. 风险评估

### 5.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| PDF 解析效果差 | 高 | 中 | Marker + PyMuPDF 双重兜底，保留纯文本 |
| ripgrep 不可用 | 高 | 低 | 检测 ripgrep 是否安装，提供安装指引，备用 Python grep |
| **GPU 不可用导致向量检索慢** | **中** | **中** | **支持 API 模式（OpenAI Embedding）** |
| **BGE-M3 模型加载失败** | **中** | **低** | **自动切换到 API 模式** |
| LLM API 限流 | 中 | 中 | 实现 Token 计数和警告，支持本地模型 |
| **RRF 融合效果不佳** | **中** | **低** | **支持单独模式切换（keyword/vector）** |
| ChromaDB 兼容性问题 | 中 | 低 | 使用持久化目录，版本锁定 |
| 中文搜索效果差 | 中 | 低 | FTS5 + 向量检索双保险 |

### 5.2 进度风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 估算偏乐观 | 高 | 中 | 预留 20% 缓冲时间 |
| 某个模块卡住 | 中 | 低 | 可以跳过，用 Mock 替代 |
| 需求变更 | 中 | 低 | 保持架构灵活，接口稳定 |

### 5.3 质量风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 索引不一致 | 高 | 中 | 增加 hash 校验，提供重建功能 |
| 溯源定位错误 | 高 | 低 | 严格测试索引生成逻辑 |
| 会话状态丢失 | 中 | 低 | 定期持久化，实现快照 |
| **向量索引损坏** | **中** | **低** | **ChromaDB 持久化，提供重建功能** |
| **Embedding 状态不一致** | **中** | **低** | **异步任务重试机制，状态字段跟踪** |

---

## 6. 每周计划

### Week 1: Day 1-5

| Day | 主要任务 | 交付物 |
|-----|----------|--------|
| Day 1 | P1-1 ~ P1-3 | 项目结构、配置、日志、**embedding_config.json**、**GPU检测脚本** |
| Day 2 | P1-4 ~ P1-5, P2-1 | 工具函数、数据层接口（**含向量相关接口**） |
| Day 3 | P2-2 ~ P2-4 | Repository 工厂、PaperRepository、**FileLock** |
| Day 4 | P2-5 ~ P2-7 | IndexRepository、**FTSRepository、VectorRepository** |
| Day 5 | P2-8 ~ P2-13 | SessionRepository、SummaryRepository、ProjectState、**EmbeddingService（本地+API+工厂）** |

### Week 2: Day 6-12

| Day | 主要任务 | 交付物 |
|-----|----------|--------|
| Day 6 | P3-1 ~ P3-3 | 工具层接口、RipgrepWrapper |
| Day 7 | P3-4 | **FulltextSearchTool（ripgrep + FTS5）** |
| Day 8 | P3-5 | **VectorSearchTool + ResultRanker（RRF）** |
| Day 9 | P3-6 + 测试 | **HybridSearchTool + 混合检索集成测试** |
| Day 10 | P3-7 | NoteManager |
| Day 11 | P3-8 ~ P3-9 | **MarkerParser + PyMuPDFParser** |
| Day 12 | P3-10 ~ P3-11 | ParagraphIndexer、PaperParser 整合（**含向量化触发**） |

### Week 3: Day 13-19

| Day | 主要任务 | 交付物 |
|-----|----------|--------|
| Day 13 | P3-12, P4-1 | Summarizer、Agent 接口 |
| Day 14 | P4-2 ~ P4-4 | ConversationManager、MemoryManager、IntentDetector |
| Day 15 | P4-5 ~ P4-7 | IntentRouter、RouteConfig、MainAgent |
| Day 16 | P5-1 ~ P5-3 | FastAPI 应用、中间件、依赖注入 |
| Day 17 | P5-4 ~ P5-6 | 论文路由、**检索路由（支持search_mode）**、笔记路由 |
| Day 18 | P5-7 ~ P5-9 | 会话路由、摘要路由、**Embedding配置路由** |
| Day 19 | P5-10 ~ P5-11 | WebSocket、Gradio 应用框架、UI 组件 |

### Week 4: Day 20-25

| Day | 主要任务 | 交付物 |
|-----|----------|--------|
| Day 20 | P5-12 ~ P5-13 | UI 组件、**Exporter（P1功能）** |
| Day 21 | 测试 | 混合检索测试（3种模式） |
| Day 22 | 测试 | 真实论文场景测试、**Embedding模式切换测试** |
| Day 23 | 优化 | 性能优化（**向量检索缓存**） |
| Day 24 | 文档 | 用户文档、API 文档、部署文档、**硬件要求说明** |
| Day 25 | 验收 | 最终验收 |

---

## 附录 A：检查清单

### 启动前检查

- [ ] Python 3.10+ 已安装
- [ ] ripgrep 已安装（`rg --version`）
- [ ] OpenAI API Key 已配置
- [ ] 虚拟环境已创建
- [ ] 依赖包已安装
  - [ ] FastAPI, Gradio, Pydantic
  - [ ] **Marker**
  - [ ] **PyMuPDF**
  - [ ] **ChromaDB**
  - [ ] **sentence-transformers（本地Embedding可选）**
- [ ] **GPU 检测脚本可正常运行**（检测 CUDA/显存）

### 每个 Phase 完成检查

- [ ] 代码符合 PEP 8 规范
- [ ] 类型注解完整
- [ ] Docstring 完整
- [ ] 单元测试通过
- [ ] 日志输出正常

### 发布前检查

- [ ] 所有 P0 任务完成
- [ ] 集成测试通过
- [ ] 真实论文测试通过
- [ ] **混合检索测试通过（3种模式）**
- [ ] **Embedding 双模式切换测试通过**
- [ ] 性能指标达标
  - [ ] 关键词检索 < 2s
  - [ ] **向量检索 < 3s**
  - [ ] **混合检索 < 4s**
  - [ ] 溯源 < 0.5s
- [ ] 文档完整

---

*文档版本: 1.3 | 最后更新: 2026-02-06*

---

## 附录 B：修改记录

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 1.2 | 2026-02-06 | 增加混合检索、向量化相关任务 |
| **1.3** | **2026-02-06** | **调整任务优先级和依赖关系：<br>• EmbeddingService 从 Phase 3 移到 Phase 2<br>• Day 7 检索任务拆分到 Day 7-9<br>• Day 1 新增 GPU 检测脚本<br>• Exporter 从 Phase 3 移到 Phase 5（P1）<br>• P3-11 补充异步向量化触发逻辑** |
