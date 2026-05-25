我已经阅读完三份设计文档。现在让我基于你确认的决策，分析需要对齐修改的内容：

---

## 📋 文档对齐分析

### 已确认的决策

| 决策点 | 选择 |
|--------|------|
| MVP检索方式 | **混合检索（ripgrep + FTS5 + 向量）** |
| Embedding模型 | **本地+API都支持，用户可选** |
| PDF解析 | **Marker + PyMuPDF** |
| 脱敏处理 | **P1做，MVP不做** |

---

## 🔴 11_数据结构设计.md 需要修改

### 修改1：5. 文件存储结构（约第193行之后）

**当前**：只有 `papers/` 目录

**需要新增**：向量索引存储结构

```markdown
### 5.2 索引存储结构（新增）

```
data/
├── papers/                          # 论文存储（保持不变）
│   └── {paper_id}/
│       ├── metadata.json
│       ├── content.md
│       ├── notes.md
│       └── index.json
│
├── indexes/                         # 全局索引层（新增）
│   ├── fts.db                      # SQLite FTS5 全文索引
│   └── vectors/                    # 向量索引
│       └── chroma/                 # ChromaDB 持久化
│           ├── chroma.sqlite3
│           └── embeddings/
│
└── config/
    └── embedding_config.json       # Embedding配置
```

### 5.3 embedding_config.json

```json
{
  "mode": "local",                    // "local" | "api" | "auto"
  "local": {
    "model_name": "BAAI/bge-m3",
    "device": "cuda",                 // "cuda" | "cpu" | "auto"
    "batch_size": 32
  },
  "api": {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "api_key_env": "OPENAI_API_KEY"
  },
  "auto_detect_gpu": true
}
```
```

---

### 修改2：2.1 Paper Schema - 补充向量化状态

**当前**（第169-180行）：只有 `parse_status`

**新增字段**：

```json
"embedding_status": {
  "type": "string",
  "description": "向量化状态",
  "enum": ["pending", "processing", "success", "failed", "skipped"],
  "default": "pending"
},
"embedding_model": {
  "type": "string",
  "description": "使用的Embedding模型",
  "examples": ["bge-m3", "text-embedding-3-small"]
},
"embedded_at": {
  "type": "string",
  "format": "date-time",
  "description": "向量化完成时间"
}
```

---

### 修改3：6.1 Pydantic模型 - 补充Embedding相关

**在 `models/paper.py` 中新增**：

```python
class EmbeddingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class EmbeddingMode(str, Enum):
    LOCAL = "local"
    API = "api"
    AUTO = "auto"


class EmbeddingConfig(BaseModel):
    """Embedding配置"""
    mode: EmbeddingMode = EmbeddingMode.AUTO
    local_model: str = "BAAI/bge-m3"
    local_device: Literal["cuda", "cpu", "auto"] = "auto"
    api_provider: str = "openai"
    api_model: str = "text-embedding-3-small"
```

---

### 修改4：SearchResult 补充向量检索字段

**当前**（第1810-1825行）：只有 `score`

**新增**：

```python
class SearchResult(BaseModel):
    """检索结果"""
    paragraph_id: str
    paper_id: str
    type: ParagraphType
    text: str
    highlighted_text: Optional[str] = None
    
    # 评分（修改）
    final_score: float = Field(..., ge=0, le=1, description="融合后最终得分")
    keyword_score: Optional[float] = Field(None, ge=0, le=1, description="关键词匹配得分")
    vector_score: Optional[float] = Field(None, ge=0, le=1, description="向量相似度得分")
    match_source: Literal["keyword", "vector", "hybrid"] = "hybrid"
    
    # 其他字段保持不变
    section: Optional[str] = None
    paper_title: Optional[str] = None
    # ...
```

---

## 🔴 12_接口定义.md 需要修改

### 修改1：4. 工具层接口 - 新增向量检索接口

**在 `4.1 ISearchTool` 之后新增**：

```python
# tools/interface.py

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

---

### 修改2：4.1 ISearchTool - 修改为混合检索

**当前**（约第400行）：只有 `search` 方法

**修改为**：

```python
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
```

---

### 修改3：6.1.2 检索API - 补充模式参数

**当前**（约第1200行）：

```yaml
POST /api/v1/search
Request:
  { query, top_k, source_filter, ... }
```

**修改为**：

```yaml
POST /api/v1/search
Request:
  {
    query: string,
    top_k?: number,           # 默认10
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
```

---

### 修改4：7. 错误码 - 补充向量相关

**新增**（在第1434行之后）：

```python
# ========== 向量检索相关 (40351-40399) ==========
VECTOR_INDEX_NOT_FOUND = 40351       # 向量索引不存在
VECTOR_INDEX_CORRUPTED = 40352       # 向量索引损坏
EMBEDDING_FAILED = 40353             # 向量化失败
EMBEDDING_MODEL_NOT_AVAILABLE = 40354  # Embedding模型不可用
EMBEDDING_DIMENSION_MISMATCH = 40355   # 向量维度不匹配
GPU_NOT_AVAILABLE = 40356            # GPU不可用（本地模式）
```

---

## 🔴 13_模块设计.md 需要修改

### 修改1：2.1 目录结构 - 补充向量相关模块

**在 `tools/search/` 下新增**：

```
├── tools/
│   ├── search/
│   │   ├── __init__.py
│   │   ├── fulltext_search.py       # 全文检索（ripgrep + FTS5）
│   │   ├── vector_search.py         # 向量检索（新增）
│   │   ├── hybrid_search.py         # 混合检索（新增）
│   │   ├── query_rewriter.py
│   │   └── result_ranker.py         # RRF融合（修改）
│   ├── embedding/                    # 新增目录
│   │   ├── __init__.py
│   │   ├── interface.py             # Embedding接口
│   │   ├── local_embedding.py       # 本地BGE-M3
│   │   ├── api_embedding.py         # OpenAI API
│   │   └── embedding_factory.py     # 工厂类
│   ├── parse/
│   │   ├── __init__.py
│   │   ├── paper_parser.py
│   │   ├── marker_parser.py         # 新增：Marker解析器
│   │   ├── pdf_parser.py            # 修改：作为fallback
│   │   └── ...
```

**在 `repositories/` 下新增**：

```
├── repositories/
│   ├── ...
│   ├── vector_repository.py         # 向量索引存储（新增）
│   └── fts_repository.py            # FTS5索引存储（新增）
```

---

### 修改2：5.1 检索工具模块 - 重构为混合检索

**当前**（约第700行）：只有 `FulltextSearchTool`

**修改为三个子模块**：

```python
# tools/search/fulltext_search.py
class FulltextSearchTool(IFulltextSearchTool):
    """关键词检索（ripgrep + FTS5）"""
    
    def __init__(
        self,
        paper_repo: IPaperRepository,
        index_repo: IIndexRepository,
        fts_repo: IFTSRepository,      # 新增
        ripgrep: RipgrepWrapper
    ):
        ...
    
    async def search(self, query: str, top_k: int = 20) -> list[SearchResult]:
        # 1. ripgrep 精确匹配
        # 2. FTS5 模糊匹配
        # 3. 合并去重
        ...


# tools/search/vector_search.py（新增）
class VectorSearchTool(IVectorSearchTool):
    """向量检索（ChromaDB）"""
    
    def __init__(
        self,
        vector_repo: IVectorRepository,
        embedding_service: IEmbeddingService
    ):
        self._vector_repo = vector_repo
        self._embedding_service = embedding_service
    
    async def search(self, query: str, top_k: int = 20) -> list[SearchResult]:
        query_vector = await self._embedding_service.encode([query])
        results = await self._vector_repo.search(query_vector[0], top_k)
        return results


# tools/search/hybrid_search.py（新增）
class HybridSearchTool(ISearchTool):
    """混合检索（RRF融合）"""
    
    def __init__(
        self,
        fulltext_tool: IFulltextSearchTool,
        vector_tool: IVectorSearchTool,
        ranker: IResultRanker
    ):
        ...
    
    async def search(
        self, 
        query: SearchQuery,
        mode: str = "hybrid"
    ) -> SearchResponse:
        if mode == "keyword":
            return await self._fulltext_tool.search(query.query, query.top_k)
        elif mode == "vector":
            return await self._vector_tool.search(query.query, query.top_k)
        else:
            # 混合模式
            keyword_results = await self._fulltext_tool.search(query.query, query.top_k * 2)
            vector_results = await self._vector_tool.search(query.query, query.top_k * 2)
            fused = await self._ranker.rrf_fusion(keyword_results, vector_results)
            return SearchResponse(results=fused[:query.top_k], ...)
```

---

### 修改3：5.4 解析模块 - 使用Marker

**当前**（约第1100行）：`PDFParser` 使用 pdfplumber

**修改为**：

```python
# tools/parse/marker_parser.py（新增）
class MarkerParser(IPDFParser):
    """Marker PDF解析器（学术PDF专用）"""
    
    def __init__(self, use_gpu: bool = True):
        from marker.converters.pdf import PdfConverter
        self._converter = PdfConverter()
        self._use_gpu = use_gpu
    
    async def parse(self, pdf_path: str) -> ParseResult:
        """
        使用Marker解析PDF
        
        Returns:
            ParseResult: 包含Markdown内容和元数据
        """
        try:
            result = self._converter(pdf_path)
            return ParseResult(
                content=result.markdown,
                metadata=result.metadata,
                status="success"
            )
        except Exception as e:
            # Fallback到PyMuPDF
            return await self._fallback_parse(pdf_path)


# tools/parse/pdf_parser.py（修改为fallback）
class PyMuPDFParser(IPDFParser):
    """PyMuPDF解析器（Fallback）"""
    ...


# tools/parse/paper_parser.py（修改）
class PaperParser(IPaperParser):
    """论文解析器"""
    
    def __init__(
        self,
        marker_parser: MarkerParser,      # 主解析器
        pymupdf_parser: PyMuPDFParser,    # Fallback
        indexer: ParagraphIndexer,
        embedding_service: IEmbeddingService  # 新增：解析后自动向量化
    ):
        ...
    
    async def parse_and_index(self, pdf_path: str, paper_id: str) -> Paper:
        # 1. Marker解析
        result = await self._marker_parser.parse(pdf_path)
        
        # 2. 生成段落索引
        paragraphs = self._indexer.index(result.content)
        
        # 3. 向量化（异步）
        asyncio.create_task(self._embed_paragraphs(paper_id, paragraphs))
        
        return paper
```

---

### 修改4：6. 数据层 - 新增向量存储

**新增**：

```python
# repositories/vector_repository.py（新增）
class VectorRepository(IVectorRepository):
    """向量索引存储（ChromaDB）"""
    
    def __init__(self, data_dir: Path):
        import chromadb
        self._client = chromadb.PersistentClient(
            path=str(data_dir / "indexes" / "vectors" / "chroma")
        )
        self._collection = self._client.get_or_create_collection(
            name="paragraphs",
            metadata={"hnsw:space": "cosine"}
        )
    
    async def add(
        self, 
        paper_id: str,
        paragraph_ids: list[str],
        embeddings: list[list[float]],
        texts: list[str]
    ) -> bool:
        self._collection.add(
            ids=paragraph_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=[{"paper_id": paper_id} for _ in paragraph_ids]
        )
        return True
    
    async def search(
        self, 
        query_embedding: list[float],
        top_k: int = 10,
        paper_ids: Optional[list[str]] = None
    ) -> list[dict]:
        where = {"paper_id": {"$in": paper_ids}} if paper_ids else None
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )
        return results
    
    async def delete(self, paper_id: str) -> bool:
        self._collection.delete(where={"paper_id": paper_id})
        return True


# repositories/fts_repository.py（新增）
class FTSRepository(IFTSRepository):
    """FTS5全文索引存储"""
    
    def __init__(self, data_dir: Path):
        import sqlite3
        self._db_path = data_dir / "indexes" / "fts.db"
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS paragraphs_fts 
            USING fts5(
                paragraph_id,
                paper_id,
                section,
                text,
                tokenize='porter unicode61'
            )
        """)
        conn.close()
    
    async def search(self, query: str, top_k: int = 20) -> list[dict]:
        conn = sqlite3.connect(self._db_path)
        cursor = conn.execute("""
            SELECT paragraph_id, paper_id, section, text, 
                   bm25(paragraphs_fts) as score
            FROM paragraphs_fts
            WHERE paragraphs_fts MATCH ?
            ORDER BY score
            LIMIT ?
        """, (query, top_k))
        results = cursor.fetchall()
        conn.close()
        return results
```

---

### 修改5：8.2 模块职责矩阵 - 更新

**新增行**：

| 模块 | 职责 | 依赖 | 被依赖 |
|------|------|------|--------|
| **VectorSearchTool** | 向量语义检索 | IVectorRepository, IEmbeddingService | HybridSearchTool |
| **HybridSearchTool** | 混合检索+RRF融合 | FulltextSearchTool, VectorSearchTool | Agent |
| **EmbeddingService** | 文本向量化 | BGE-M3/OpenAI API | VectorSearchTool, PaperParser |
| **VectorRepository** | 向量索引CRUD | ChromaDB | VectorSearchTool |
| **FTSRepository** | 全文索引CRUD | SQLite FTS5 | FulltextSearchTool |
| **MarkerParser** | 学术PDF解析 | Marker库 | PaperParser |

---

## 📊 修改汇总

| 文档 | 修改数量 | 关键变更 |
|------|----------|----------|
| **11_数据结构设计.md** | 4处 | 新增向量索引存储、Embedding配置、状态字段 |
| **12_接口定义.md** | 4处 | 新增IVectorSearchTool、IEmbeddingService、混合检索API |
| **13_模块设计.md** | 5处 | 新增向量检索模块、Embedding模块、Marker解析器 |

---

## ✅ 下一步

你希望我：

1. **生成修改后的完整文档**（三份文档一起输出）
2. **先确认以上分析是否准确**，再生成文档
3. **只生成关键代码片段**，你自己合并到文档中

你选哪个？