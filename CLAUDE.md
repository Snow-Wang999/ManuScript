# ManuScript 开发规则

> 此文件用于告诉 AI 项目的技术规范和开发规则

---

## 项目概述

ManuScript 是一个 AI 辅助的学术论文写作工具，帮助用户基于本地文献库生成带引用的论文段落。

**v3.0 定位**: 对话式文献研究助手（硕士研究生版）

**核心价值主张**: "让每一句话都能追溯到原文段落"

---

## 技术栈

| 组件 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| **语言** | Python | 3.10+ | 主开发语言 |
| **前端** | Gradio | 4.x | MVP 快速原型 |
| **后端** | FastAPI | 0.100+ | 异步 REST API |
| **数据模型** | Pydantic | 2.x | 类型安全 |
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

## 代码风格

```python
# 命名规范
class SectionPlanner:     # 类名: PascalCase
def generate_query():     # 函数名: snake_case
section_title: str        # 变量名: snake_case
MAX_RETRIES = 3           # 常量: UPPER_SNAKE_CASE

# 异步编程
async def fetch_documents():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

# 类型注解
def process_chunks(chunks: list[dict]) -> str:
    pass

# 日志使用
from logger import get_logger
logger = get_logger(__name__)
logger.info("Processing section", extra={"section": title})
```

---

## 开发规范

### 版本独立原则
- 每个版本（v0_1, v0_2, v1_0, v2_0, v3_0）是独立目录
- 版本间代码不共享，允许适度重复
- 每次只开发一个版本

### 开发顺序（v3.0）
1. **Phase 1: 基础设施** - 项目结构、数据模型、配置、日志
2. **Phase 2: 数据层** - Repository、EmbeddingService（提前到此阶段）
3. **Phase 3: 工具层** - 检索、解析、笔记管理
4. **Phase 4: Agent 层** - 对话管理、记忆管理、意图路由
5. **Phase 5: API & UI 层** - FastAPI、Gradio、集成测试

### v3.0 核心架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户交互层                                │
│                     Gradio UI / FastAPI                         │
└─────────────────────────────────────┬───────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                         Agent 层                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ IntentRouter │→ │ MainAgent    │→ │ Conversation │          │
│  │              │  │              │  │ Manager      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────┬───────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                        工具层（Tools）                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ HybridSearch │  │ PaperParser  │  │ NoteManager  │          │
│  │ (混合检索)    │  │ (Marker)     │  │              │          │
│  └──────┬───────┘  └──────────────┘  └──────────────┘          │
│         │                                                             │
│    ┌────┴────┬─────────┬──────────┐                                  │
│    ↓         ↓         ↓          ↓                                  │
│  ripgrep   FTS5    ChromaDB   Embedding                            │
└─────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                        数据层（Repositories）                      │
│  PaperRepo │ IndexRepo │ VectorRepo │ SessionRepo │ SummaryRepo  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 目录结构（v3.0）

```
v3_0/
├── main.py                        # 应用入口
├── config.py                      # 配置加载
├── models/                        # Pydantic 数据模型
│   ├── paper.py                   # PaperMetadata, ParseStatus, EmbeddingStatus
│   ├── paragraph.py               # Paragraph, ParagraphType
│   ├── note.py                    # Note, NoteCreate
│   ├── session.py                 # Session, AgentState
│   ├── message.py                 # Message, MessageRole
│   ├── search.py                  # SearchQuery, SearchResult（混合检索评分）
│   ├── embedding.py               # EmbeddingConfig, EmbeddingMode
│   ├── memory.py                  # MemoryType, MemoryItem
│   └── error.py                   # ErrorCode, ErrorResponse
├── repositories/                  # 数据访问层
│   ├── interface.py               # 接口定义
│   ├── factory.py                 # 工厂模式
│   ├── paper_repository.py
│   ├── index_repository.py
│   ├── fts_repository.py          # SQLite FTS5
│   ├── vector_repository.py       # ChromaDB
│   ├── session_repository.py
│   ├── project_state_repository.py
│   └── summary_repository.py
├── tools/                         # 工具层
│   ├── interface.py               # 工具接口
│   ├── factory.py                 # 工具工厂
│   ├── search/                    # 检索工具
│   │   ├── fulltext_search.py     # ripgrep + FTS5
│   │   ├── vector_search.py       # ChromaDB
│   │   ├── hybrid_search.py       # RRF融合
│   │   ├── query_rewriter.py
│   │   └── result_ranker.py       # RRF融合排序
│   ├── parse/                     # 解析工具
│   │   ├── marker_parser.py       # Marker解析器
│   │   ├── pymupdf_parser.py      # Fallback解析器
│   │   ├── paragraph_indexer.py
│   │   └── paper_parser.py        # 整合解析器
│   ├── note/                      # 笔记管理
│   │   └── note_manager.py
│   ├── summary/                   # 摘要生成
│   │   └── summarizer.py
│   └── embedding/                 # Embedding服务
│       ├── interface.py
│       ├── local_embedding.py     # BGE-M3
│       ├── api_embedding.py       # OpenAI API
│       └── embedding_factory.py
├── agent/                         # Agent层
│   ├── interface.py
│   ├── conversation_manager.py
│   ├── memory_manager.py
│   └── main_agent.py
├── router/                        # 路由层
│   ├── intent_detector.py
│   ├── intent_router.py
│   └── route_config.py
├── api/                           # FastAPI
│   ├── app.py
│   ├── middleware.py
│   ├── dependencies.py
│   └── routes/
│       ├── papers.py
│       ├── search.py
│       ├── notes.py
│       ├── sessions.py
│       ├── summaries.py
│       ├── embedding.py
│       └── websocket.py
├── ui/                            # Gradio
│   ├── app.py
│   └── components/
├── utils/                         # 工具函数
│   ├── file_utils.py
│   ├── hash_utils.py
│   ├── id_generator.py
│   ├── datetime_utils.py
│   ├── ripgrep_wrapper.py
│   ├── file_lock.py               # 并发安全
│   └── hardware_detector.py       # GPU检测
├── config/
│   ├── settings.yaml
│   └── embedding_config.json
├── logger.py
└── tests/
```

---

## 数据存储结构

```
data/
├── papers/                          # 论文存储
│   └── {paper_id}/
│       ├── metadata.json            # 元数据（含embedding_status）
│       ├── content.md               # 正文（带段落ID）
│       ├── notes.md                 # 用户笔记
│       └── index.json               # 段落位置索引
│
├── indexes/                         # 全局索引层
│   ├── fts.db                      # SQLite FTS5 全文索引
│   └── vectors/                    # 向量索引
│       └── chroma/                 # ChromaDB 持久化
│           ├── chroma.sqlite3
│           └── embeddings/
│
└── config/
    └── embedding_config.json       # Embedding配置（local/api/auto）
```

---

## 混合检索架构

v3.0 采用混合检索策略：

```
用户查询
    ↓
Query Processor（意图识别 → 查询重写）
    ↓
┌───────────┬────────────┬─────────────┐
│  ripgrep  │   FTS5     │  向量检索   │
│  精确匹配 │  倒排索引  │  语义相似   │
└─────┬─────┴──────┬─────┴──────┬──────┘
      └────────────┼────────────┘
                   ↓
         RRF 融合排序（Reciprocal Rank Fusion）
                   ↓
              Top-K 结果
```

### 检索模式

| 模式 | 触发条件 | 说明 |
|------|----------|------|
| `keyword` | 引号包裹、特定术语 | ripgrep + FTS5 |
| `vector` | 自然语言问句 | ChromaDB |
| `hybrid` | 默认 | RRF融合三者结果 |

---

## Embedding 配置

### 模式选择

| 模式 | 模型 | 要求 | 适用场景 |
|------|------|------|----------|
| `local` | BGE-M3 | 4GB显存 | 隐私敏感 |
| `api` | OpenAI text-embedding-3-small | API Key | 无显卡用户 |
| `auto` | 自动检测GPU | - | 默认模式 |

### 配置文件

```json
{
  "mode": "auto",
  "auto_detect_gpu": true,
  "local": {
    "model_name": "BAAI/bge-m3",
    "device": "auto",
    "batch_size": 32
  },
  "api": {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "api_key_env": "OPENAI_API_KEY"
  }
}
```

---

## 硬件要求

| 配置 | 要求 | 体验说明 |
|------|------|----------|
| **最低** | 8GB内存，无显卡 | 解析较慢，Embedding建议用API |
| **推荐** | 16GB内存，4GB显卡 | 全功能本地运行 |

### 首次导入性能预估（200篇论文）

| 环节 | 有GPU | 无GPU（CPU） | 无GPU（API） |
|------|-------|--------------|--------------|
| PDF解析 | ~15分钟 | ~100分钟 | ~100分钟 |
| Embedding | ~3分钟 | ~60分钟 | ~7分钟（$0.1） |
| 索引构建 | <1分钟 | <1分钟 | <1分钟 |

---

## 注意事项

1. **引用准确性是最高优先级** - 每句话都能追溯到原文段落
2. **段落ID基于内容哈希** - 重解析后ID保持稳定，用户笔记关联不丢失
3. **并发安全** - 使用文件锁避免多会话同时修改导致数据丢失
4. **降级策略** - GPU不可用时自动切换到API模式
5. **不要过度设计** - MVP优先，P1功能后续迭代
6. **环境变量** - API Key放.env，不要硬编码
7. **日志要详细** - 方便调试检索质量和降级逻辑

---

## 当前开发阶段

**v3.0 开发中**

查看以下文档了解详细信息：
- `docs/generate/09_ManuScript_v3.0_PRD_重新设计.md` - 产品需求
- `docs/generate/11_ManuScript_v3.0_数据结构设计.md` - 数据结构
- `docs/generate/12_ManuScript_v3.0_接口定义.md` - API接口
- `docs/generate/13_ManuScript_v3.0_模块设计.md` - 模块设计
- `docs/generate/14_ManuScript_v3.0_开发计划.md` - 开发计划
