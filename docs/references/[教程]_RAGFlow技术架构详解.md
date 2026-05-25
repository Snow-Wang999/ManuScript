# RAGFlow 深度技术架构解读

> 面向 AI 产品经理训练营的企业级 RAG 系统技术教材

---

## 关于 Paper 论文解析

对于 Paper 论文的解析，RAGFlow 的做法：

- **DeepDoc 模式**：OCR 文字、版面识别、双栏检测、图表检测 + 大模型转录图表的具体文字内容
- **Experimental 纯大模型解析**：直接把 PDF 转成图片，让 VLM 解读为 markdown

---

## 目录

1. [第一部分：RAG 系统基础与 RAGFlow 整体架构](#第一部分rag-系统基础与-ragflow-整体架构)
2. [第二部分：文档解析引擎深度解读](#第二部分文档解析引擎深度解读)
3. [第三部分：14种解析模式全景分析](#第三部分14种解析模式全景分析)
4. [第四部分：文档切片策略深度解读](#第四部分文档切片策略深度解读)
5. [第五部分：可选增强模块深度解读](#第五部分可选增强模块深度解读)
6. [第六部分：检索模块深度解读](#第六部分检索模块深度解读)
7. [第七部分：重排序模块深度解读](#第七部分重排序模块深度解读)
8. [第八部分：生成模块深度解读](#第八部分生成模块深度解读)
9. [第九部分：Agentic RAG 专题](#第九部分agentic-rag-专题)
10. [第十部分：Prompt 工程汇总](#第十部分prompt-工程汇总)
11. [第十一部分：最佳实践与选型指南](#第十一部分最佳实践与选型指南)

---

## 第一部分：RAG 系统基础与 RAGFlow 整体架构

### 1.1 什么是 RAG

**RAG（Retrieval-Augmented Generation）** 是一种结合检索与生成的 AI 架构范式，其核心思想是：

> 在大模型生成回答之前，先从知识库中检索相关信息，将其作为上下文注入 Prompt，从而让模型基于真实数据生成回答。

**RAG 解决的核心问题：**

| 问题 | 说明 |
|------|------|
| 知识过时 | LLM 训练数据有截止日期 |
| 幻觉问题 | LLM 可能"编造"看似合理但错误的信息 |
| 领域知识缺失 | 通用 LLM 缺乏企业私有数据 |
| 可溯源性 | 回答需要引用来源，便于验证 |

### 1.2 RAGFlow 完整架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RAGFlow 系统架构全景图                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    阶段一：离线索引 (Offline Indexing)                │   │
│  │                                                                       │   │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────────┐ │   │
│  │   │ 文档上传  │──▶│ 文档解析  │──▶│ 文档切片  │──▶│  可选增强处理     │ │   │
│  │   │          │   │          │   │          │   │                  │ │   │
│  │   │ PDF/Word │   │ OCR      │   │ 层级识别  │   │ - 关键词抽取     │ │   │
│  │   │ Excel    │   │ 版面分析  │   │ 树形构建  │   │ - 问题生成       │ │   │
│  │   │ 图片/音频│   │ 表格检测  │   │ Token控制│   │ - RAPTOR        │ │   │
│  │   │ ...      │   │ 多栏检测  │   │          │   │ - GraphRAG      │ │   │
│  │   └──────────┘   └──────────┘   └──────────┘   └──────────────────┘ │   │
│  │                                                        │              │   │
│  │                                                        ▼              │   │
│  │                                            ┌──────────────────────┐  │   │
│  │                                            │  Embedding + 索引    │  │   │
│  │                                            │                      │  │   │
│  │                                            │  - 向量化            │  │   │
│  │                                            │  - ES/Infinity 存储  │  │   │
│  │                                            │  - 倒排索引          │  │   │
│  │                                            └──────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    阶段二：在线查询 (Online Query)                    │   │
│  │                                                                       │   │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────────┐ │   │
│  │   │ 用户提问  │──▶│ Query    │──▶│ 混合检索  │──▶│    重排序         │ │   │
│  │   │          │   │ 预处理    │   │          │   │                  │ │   │
│  │   │          │   │          │   │ BM25     │   │ - 混合相似度     │ │   │
│  │   │          │   │ - 分词    │   │    +     │   │ - Rerank模型    │ │   │
│  │   │          │   │ - 同义词  │   │ 向量检索  │   │ - RankFeature   │ │   │
│  │   │          │   │ - 问题补全│   │    ↓     │   │                  │ │   │
│  │   │          │   │ - 权重    │   │ 0.05:0.95│   │                  │ │   │
│  │   └──────────┘   └──────────┘   └──────────┘   └──────────────────┘ │   │
│  │                                                        │              │   │
│  │                                                        ▼              │   │
│  │   ┌──────────────────────────────────────────────────────────────┐  │   │
│  │   │                        生成阶段                                │  │   │
│  │   │                                                                │  │   │
│  │   │   ┌────────────┐    ┌────────────┐    ┌────────────────────┐ │  │   │
│  │   │   │ 上下文组装  │───▶│  LLM 生成   │───▶│  引用标注 + 输出   │ │  │   │
│  │   │   │            │    │            │    │                    │ │  │   │
│  │   │   │ kb_prompt  │    │ 流式输出    │    │ [ID:x] 格式引用   │ │  │   │
│  │   │   │ Token限制  │    │            │    │                    │ │  │   │
│  │   │   └────────────┘    └────────────┘    └────────────────────┘ │  │   │
│  │   └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 核心目录结构解读

| 目录 | 职责 | 关键文件 |
|------|------|----------|
| `deepdoc/parser/` | 文档解析引擎 | `pdf_parser.py` - PDF解析核心 |
| `rag/app/` | 14种解析模式适配器 | `naive.py`, `laws.py`, `manual.py` 等 |
| `rag/nlp/` | NLP处理模块 | `__init__.py` - 切片与层级识别<br>`search.py` - 检索核心<br>`query.py` - Query处理 |
| `rag/llm/` | LLM模型封装 | `embedding_model.py`, `rerank_model.py` |
| `rag/prompts/` | Prompt模板库 | 32个 `.md` 模板文件 |
| `graphrag/` | 知识图谱模块 | `general/extractor.py` - 子图抽取 |
| `agentic_reasoning/` | Agentic RAG | `deep_research.py` - 深度推理 |
| `api/db/services/` | 业务服务层 | `dialog_service.py` - 对话核心 |

---

## 第二部分：文档解析引擎深度解读

### 2.1 为什么文档解析是 RAG 的"地基"

> **PM 决策要点**：文档解析质量直接决定了 RAG 系统的上限。再好的检索算法和 LLM，也无法弥补解析阶段丢失的信息。

RAGFlow 的核心竞争力之一就是其 **"Deep Document Understanding"** 理念——不只是简单提取文本，而是理解文档的结构、版面、表格、图表。

### 2.2 RAGFlowPdfParser 核心架构

**文件位置**: `deepdoc/parser/pdf_parser.py`

```
┌─────────────────────────────────────────────────────────────┐
│                    RAGFlowPdfParser                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   OCR 模块    │    │  版面分析     │    │  表格检测     │  │
│  │              │    │              │    │              │  │
│  │ PaddleOCR   │    │LayoutRecognizer│   │TableStructure│  │
│  │ __ocr()     │    │ _layouts_rec()│    │Recognizer    │  │
│  │              │    │              │    │              │  │
│  │ 字符级定位   │    │ ONNX模型     │    │ 行列识别      │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  多栏检测     │    │  文本合并     │    │  图表提取     │  │
│  │              │    │              │    │              │  │
│  │ KMeans      │    │ XGBoost      │    │ 裁剪+标题    │  │
│  │_assign_column│   │_text_merge() │    │关联          │  │
│  │              │    │_concat_down()│    │              │  │
│  │ 聚类列检测   │    │ 30+特征判断  │    │_extract_     │  │
│  │              │    │              │    │table_figure()│  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 核心子模块技术要点

| 子模块 | 方法 | 技术实现 | PM 关注点 |
|--------|------|----------|-----------|
| OCR | `__ocr()` | PaddleOCR | 字符级精确定位，支持中英混合 |
| 版面分析 | `_layouts_rec()` | ONNX LayoutRecognizer | 识别 text/title/table/figure/equation |
| 表格结构 | `_table_transformer_job()` | TableStructureRecognizer | 行列识别，支持复杂合并单元格 |
| 多栏检测 | `_assign_column()` | KMeans 聚类 | 自动检测单栏/双栏/多栏布局 |
| 文本合并 | `_text_merge()`, `_concat_downward()` | XGBoost 模型 | 30+特征判断是否合并相邻文本块 |
| 图表提取 | `_extract_table_figure()` | 几何运算 | 图表裁剪、标题关联 |
| 位置标记 | `_line_tag()` | 自定义格式 | `@@page\tx0\tx1\ttop\tbottom##` |

### 2.4 关键技术决策：PaddleOCR vs Vision LLM

这是 RAGFlow 中一个极其重要的架构决策，也是 AI PM 必须理解的技术权衡。

#### 2.4.1 两者的定位差异

```
┌─────────────────────────────────────────────────────────────┐
│                    文档理解技术栈分层                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            层级 3: 语义理解 (Semantic)               │   │
│  │                                                       │   │
│  │   Vision LLM (GPT-4V, Claude Vision, Qwen-VL...)    │   │
│  │                                                       │   │
│  │   职责: 图表语义解读、复杂表格理解、图文关系推理      │   │
│  │   特点: 高智能、高成本、高延迟                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ▲                                   │
│                          │ 调用                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            层级 2: 结构识别 (Structure)              │   │
│  │                                                       │   │
│  │   LayoutRecognizer + TableStructureRecognizer        │   │
│  │                                                       │   │
│  │   职责: 版面分割、表格行列识别、标题检测             │   │
│  │   特点: ONNX推理、本地部署、中等精度                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ▲                                   │
│                          │ 依赖                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            层级 1: 字符识别 (Character)              │   │
│  │                                                       │   │
│  │   PaddleOCR                                          │   │
│  │                                                       │   │
│  │   职责: 字符识别、位置坐标、文字行检测               │   │
│  │   特点: 高精度、低成本、快速、本地部署               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 2.4.2 协作流程（以 manual 模式为例）

**文件位置**: `rag/app/manual.py`

```python
# 协作流程核心代码逻辑
def chunk(filename, binary, ..., callback, vision_model):
    # 步骤1: PaddleOCR + 版面分析 (基础层)
    pdf_parser = RAGFlowPdfParser()
    sections, tbls = pdf_parser(filename, binary, ...)

    # 步骤2: 对检测到的图表调用 Vision LLM (语义层)
    if vision_model:
        for img_data in images:
            # Vision LLM 生成图表描述
            description = vision_model.describe(img_data)
            chunk["content"] += f"\n{description}"
```

#### 2.4.3 技术互补性对比

| 维度 | PaddleOCR | Vision LLM |
|------|-----------|------------|
| 核心能力 | 字符识别 + 位置定位 | 语义理解 + 推理 |
| 处理对象 | 所有文本 | 仅图表/复杂表格 |
| 调用频率 | 每页必调 | 可选调用 |
| 成本 | 极低（本地推理） | 较高（API调用） |
| 延迟 | ~100ms/页 | ~2-5s/图 |
| 精度 | 字符级精确 | 语义级理解 |
| 典型输出 | `{"text": "销售额", "bbox": [100, 200, 150, 220]}` | "该柱状图展示了2023年Q1-Q4的销售额增长趋势，Q4达到峰值120万元" |

#### 2.4.4 PM 决策指南：何时启用 Vision LLM？

| 场景 | 推荐策略 | 理由 |
|------|----------|------|
| 纯文字 PDF | 不启用 | PaddleOCR 足够，无需额外成本 |
| 含简单表格的文档 | 不启用 | TableStructureRecognizer 可处理 |
| 技术手册（含架构图） | 启用 | 需要理解图表含义 |
| 学术论文（含复杂图表） | 启用 | 需要解读实验结果图 |
| 金融报表 | 视情况 | 简单表格不需要，复杂图表需要 |
| 批量处理（>1000文档） | 谨慎启用 | 成本考量，可抽样启用 |

> **核心结论**：PaddleOCR 和 Vision LLM 不是替代关系，而是**分层协作关系**。PaddleOCR 负责"看清字"，Vision LLM 负责"理解意思"。

---

## 第三部分：14种解析模式全景分析

### 3.1 解析模式设计哲学

RAGFlow 采用**策略模式**设计，针对不同文档类型提供特化的解析逻辑。这是一个关键的产品架构决策：

> "没有万能的解析器，只有最适合特定场景的解析器"

### 3.2 14种解析模式全景表

| 模式 | 文件 | 适用场景 | 核心特点 | 技术亮点 |
|------|------|----------|----------|----------|
| naive | `naive.py` | 通用文档 | 通用切片 + 层级识别 | `Node.build_tree()` 树形结构 |
| laws | `laws.py` | 法律法规、合同 | 保持条文层级 | `BULLET_PATTERN` 识别中文法律编号 |
| manual | `manual.py` | 技术手册、产品文档 | PDF书签 + Vision图表描述 | Outline优先、section_id合并 |
| paper | `paper.py` | 学术论文 | 元数据提取 + 双栏处理 | `sort_X_by_page()` 双栏排序 |
| book | `book.py` | 书籍 | 页码范围控制 | 目录移除、章节识别 |
| resume | `resume.py` | 简历 | 结构化字段抽取 | 远程解析服务、字段映射 |
| qa | `qa.py` | FAQ文档 | Q&A对识别 | Excel格式或文本Q/A分隔 |
| picture | `picture.py` | 图片、视频帧 | OCR + Vision描述 | 支持视频抽帧 |
| one | `one.py` | 短文档 | 整文档单chunk | 适合<2000字小文档 |
| table | `table.py` | Excel/CSV | 行级结构化 | 动态类型推断、列名识别 |
| audio | `audio.py` | 音频文件 | Speech2Text | ASR模型集成 |
| presentation | `presentation.py` | PPT/PDF演示 | 按页切分 + 缩略图 | 每页生成预览图 |
| tag | `tag.py` | 标签数据 | 标签模式 | 特殊标签处理 |
| email | `email.py` | 邮件文件 | 邮件结构解析 | 收发件人、附件处理 |

### 3.3 重点模式深度解读

#### 3.3.1 naive 模式（通用基线）

**文件**: `rag/app/naive.py`

**设计理念**：提供一个足够好的通用解决方案，覆盖 80% 的场景。

**核心流程**：

```
原始文档 → PDF解析 → 层级识别(BULLET_PATTERN) → 树形结构构建 → Token控制切分 → Chunks
```

**关键代码逻辑**：

```python
# 核心切片逻辑
def chunk(filename, binary, chunk_token_num=128, ...):
    # 1. 解析文档获取sections
    sections = pdf_parser(filename, binary)

    # 2. 层级识别 + 树形构建
    chunks = hierarchical_merge(sections, chunk_token_num, ...)

    # 3. Token控制
    for chunk in chunks:
        if token_count(chunk) > chunk_token_num:
            # 拆分过长chunk
            sub_chunks = split_by_token(chunk, chunk_token_num)
```

**适用场景**：
- 通用文档、内部资料
- 没有明确结构要求的文档
- 快速验证 RAG 效果

#### 3.3.2 laws 模式（法律文档特化）

**文件**: `rag/app/laws.py`

**设计理念**：法律文档有严格的层级结构，必须保持条文的完整性和层级关系。

**核心技术**：

```python
# BULLET_PATTERN 定义（来自 rag/nlp/__init__.py）
BULLET_PATTERN = [
    # 中文法律条文编号
    r"第[零一二三四五六七八九十百千0-9]+[编章节条款项目]",  # 第一章、第二条
    r"[零一二三四五六七八九十百千]+[、\.]",                 # 一、二、
    r"[（\(][零一二三四五六七八九十百千]+[）\)]",           # （一）（二）

    # 数字编号
    r"[0-9]{1,2}[\.、]",                                   # 1. 2.
    r"[0-9]{1,2}\.[0-9]{1,2}[\.、]?",                     # 1.1 2.3

    # 英文层级
    r"Chapter\s+\d+",
    r"Section\s+\d+",
]
```

**核心流程**：

```
法律文档 → PDF解析 → BULLET_PATTERN匹配 → 树形层级构建 → 条文完整性切分
```

**关键算法**：
1. `bullets_category()` - 识别编号模式类型
2. `title_frequency()` - 统计标题出现频率，判断层级
3. `Node.build_tree()` - 栈算法构建层级树
4. `make_colon_as_title()` - 识别"定义：内容"格式

**PM 关注点**：
- 法律文档切片必须保持条文完整性
- "第一条"和其下的"(一)(二)"必须关联
- 跨页条文必须合并

#### 3.3.3 manual 模式（技术手册特化）

**文件**: `rag/app/manual.py`

**设计理念**：技术手册有两个特点：(1) 通常有完善的目录结构（PDF Outline），(2) 包含大量需要理解的图表。

**核心流程**：

```
技术手册 → 提取PDF Outline → 按章节切分 → Vision LLM描述图表 → section_id合并
```

**关键技术**：

```python
def chunk(filename, binary, ..., vision_model):
    # 1. 优先使用 PDF Outline（书签）
    doc = fitz.open(stream=binary)
    outlines = doc.get_toc()  # [(level, title, page_num), ...]

    if outlines:
        # 基于书签进行切分
        sections = split_by_outline(doc, outlines)
    else:
        # 回退到版面分析
        sections = pdf_parser(filename, binary)

    # 2. 图表描述增强
    if vision_model:
        for section in sections:
            if section.has_figure:
                description = vision_model.describe(section.figure_image)
                section.content += f"\n[图表描述]: {description}"

    # 3. 基于 section_id 合并相邻小节
    return merge_by_section_id(sections, chunk_token_num)
```

**PM 关注点**：
- PDF 书签质量直接影响切分效果
- 需要引导用户上传带书签的 PDF
- Vision LLM 成本较高，建议按需启用

#### 3.3.4 paper 模式（学术论文特化）

**文件**: `rag/app/paper.py`

**设计理念**：学���论文有固定结构（Abstract、Introduction、Methods、Results、Discussion），且常见双栏排版。

**核心技术**：

```python
def chunk(filename, binary, ...):
    # 1. 元数据提取
    metadata = extract_metadata(binary)  # title, authors, abstract

    # 2. 双栏处理
    sections = pdf_parser(filename, binary)
    sorted_sections = sort_X_by_page(sections)  # 双栏从左到右排序

    # 3. Abstract 作为关键词加权
    if metadata.get("abstract"):
        for chunk in chunks:
            chunk["important_kwd"] = extract_keywords(metadata["abstract"])

    # 4. 图表描述
    if vision_model:
        for figure in figures:
            description = vision_model.describe(figure)
```

**双栏排序算法 `sort_X_by_page()`**：

```
原始顺序（PDF提取顺序）：     排序后（阅读顺序）：
┌─────┬─────┐                 ┌─────┬─────┐
│  1  │  5  │                 │  1  │  2  │
│  2  │  6  │       →         │  3  │  4  │
│  3  │  7  │                 │  5  │  6  │
│  4  │  8  │                 │  7  │  8  │
└─────┴─────┘                 └─────┴─────┘
```

#### 3.3.5 table 模式（Excel/CSV 特化）

**文件**: `rag/app/table.py`

**设计理念**：表格数据需要保持行的完整性，同时支持结构化查询。

**核心技术**：

```python
def chunk(filename, binary, ...):
    # 1. 动态类型推断
    df = pd.read_excel(binary)
    column_types = infer_column_types(df)  # 数值/文本/日期

    # 2. 行级切分
    for idx, row in df.iterrows():
        chunk_content = format_row_as_text(row, columns)
        # 格式: "列名1: 值1; 列名2: 值2; ..."
        chunks.append({
            "content": chunk_content,
            "metadata": {"row_index": idx}
        })

    # 3. 可选: 生成 Schema 描述
    schema_chunk = generate_schema_description(df)
```

**PM 关注点**：
- 每行独立成chunk，适合精确检索
- 列名会作为语义信息保留
- 大表格会生成大量chunks

### 3.4 解析模式选型决策树

```
                    ┌─────────────────┐
                    │   文档类型判断   │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
    ┌─────────┐        ┌─────────┐         ┌─────────┐
    │  PDF?   │        │ Office? │         │  其他?  │
    └────┬────┘        └────┬────┘         └────┬────┘
         │                  │                    │
    ┌────┴────┐        ┌────┴────┐         ┌────┴────┐
    │内容类型?│        │  类型?  │         │  类型?  │
    └────┬────┘        └────┬────┘         └────┬────┘
         │                  │                    │
    ┌────┼────┬────┐   ┌───┴───┐          ┌────┼────┐
    ▼    ▼    ▼    ▼   ▼       ▼          ▼    ▼    ▼
法律  论文  手册  书籍  PPT   Excel      图片  音频  邮件
 │     │     │    │     │      │          │     │    │
 ▼     ▼     ▼    ▼     ▼      ▼          ▼     ▼    ▼
laws paper manual book present. table   picture audio email
```

---

## 第四部分：文档切片策略深度解读

### 4.1 为什么切片策略如此重要

> **PM 必知**：切片是 RAG 中最容易被低估、但影响最大的环节。

| 切片问题 | 后果 |
|----------|------|
| 切得太大 | 检索精度下降，噪音增多 |
| 切得太小 | 上下文丢失，LLM 理解困难 |
| 切断语义 | 关键信息被分到不同 chunk |
| 层级丢失 | 无法回答"第X章讲了什么" |

### 4.2 层级识别机制（BULLET_PATTERN）

**文件**: `rag/nlp/__init__.py`

RAGFlow 定义了 5 类层级模式，覆盖中英文主流文档格式：

```python
BULLET_PATTERN = [
    # 类型1: 中文法律条文（最严格）
    [
        r"第[零一二三四五六七八九十百千0-9]+编",     # 第一编
        r"第[零一二三四五六七八九十百千0-9]+章",     # 第一章
        r"第[零一二三四五六七八九十百千0-9]+节",     # 第一节
        r"第[零一二三四五六七八九十百千0-9]+条",     # 第一条
        r"第[零一二三四五六七八九十百千0-9]+款",     # 第一款
        r"[零一二三四五六七八九十百]+[、\.]",        # 一、
        r"[（\(][零一二三四五六七八九十百]+[）\)]", # （一）
    ],

    # 类型2: 数字层级（通用）
    [
        r"[0-9]{1,2}[\.、]",                        # 1.
        r"[0-9]{1,2}\.[0-9]{1,2}[\.、]?",          # 1.1
        r"[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}",      # 1.1.1
    ],

    # 类型3: 中文混合层级
    [
        r"[零一二三四五六七八九十百]+[、\.]",
        r"[（\(][零一二三四五六七八九十百]+[）\)]",
        r"[0-9]{1,2}[\.、]",
    ],

    # 类型4: 英文层级
    [
        r"Chapter\s+\d+",
        r"Section\s+\d+",
        r"Article\s+\d+",
    ],

    # 类型5: Markdown 层级
    [
        r"^#{1,6}\s+",                              # # ## ### 标题
    ]
]
# 手写成分很高
```

### 4.3 树形结构构建算法

**核心类**: `Node`

```python
class Node:
    def __init__(self, level, content, parent=None):
        self.level = level        # 层级深度
        self.content = content    # 节点内容
        self.parent = parent      # 父节点
        self.children = []        # 子节点列表

    @staticmethod
    def build_tree(sections):
        """
        使用栈算法构建树形结构

        输入: [("第一章 总则", 1), ("第一条 目的", 2), ("第二条 范围", 2), ...]
        输出: 树形结构的根节点
        """
        root = Node(0, "ROOT")
        stack = [root]

        for content, level in sections:
            node = Node(level, content)

            # 找到合适的父节点（栈中第一个层级更低的节点）
            while stack and stack[-1].level >= level:
                stack.pop()

            parent = stack[-1]
            node.parent = parent
            parent.children.append(node)
            stack.append(node)

        return root

    def get_tree(self):
        """
        DFS遍历，累加标题路径

        输出: [("第一章 总则 > 第一条 目的", "条文内容..."), ...]
        """
        results = []

        def dfs(node, path):
            current_path = f"{path} > {node.content}" if path else node.content

            if node.children:
                for child in node.children:
                    dfs(child, current_path)
            else:
                results.append((current_path, node.content))

        for child in self.children:
            dfs(child, "")

        return results
```

**示例**：

```
输入文档:
第一章 总则
  第一条 目的
    本法的目的是...
  第二条 范围
    本法适用于...
第二章 权利义务

输出结构:
ROOT
├── 第一章 总则
│   ├── 第一条 目的 → content: "第一章 总则 > 第一条 目的\n本法的目的是..."
│   └── 第二条 范围 → content: "第一章 总则 > 第二条 范围\n本法适用于..."
└── 第二章 权利义务
```

### 4.4 Token 控制与合并策略

**核心参数**: `chunk_token_num`

```python
def hierarchical_merge(sections, chunk_token_num=128, delimiter="\n"):
    """
    基于Token限制的智能合并
    """
    chunks = []
    current_chunk = ""

    for section in sections:
        combined = current_chunk + delimiter + section

        if token_count(combined) <= chunk_token_num:
            # 可以合并
            current_chunk = combined
        else:
            # 需要分割
            if current_chunk:
                chunks.append(current_chunk)

            if token_count(section) > chunk_token_num:
                # 单个section过长，需要拆分
                sub_sections = split_by_sentence(section, chunk_token_num)
                chunks.extend(sub_sections[:-1])
                current_chunk = sub_sections[-1]
            else:
                current_chunk = section

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
```

**PM 决策指南**：

| chunk_token_num 值 | 适用场景 | 权衡 |
|--------------------|----------|------|
| 64-128 | 精确问答、FAQ | 检索精准，但上下文少 |
| 256-512 | 通用场景（推荐） | 平衡精准度和上下文 |
| 1024+ | 长文档理解 | 上下文丰富，但噪音多 |

---

## 第五部分：可选增强模块深度解读

### 5.1 增强模块全景

RAGFlow 提供 5 大可选增强模块，用于提升检索和理解效果：

```
┌─────────────────────────────────────────────────────────────┐
│                     可选增强模块架构                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Auto Keyword │  │ Auto Question │  │   Metadata   │      │
│  │              │  │               │  │              │      │
│  │ 自动关键词    │  │  自动问题生成  │  │  元数据抽取   │      │
│  │ important_kwd│  │ question_kwd  │  │  Schema定义  │      │
│  └──────────────┘  └───────────────┘  └──────────────┘      │
│                                                              │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  │
│  │        RAPTOR           │  │       GraphRAG          │  │
│  │                         │  │                         │  │
│  │  递归摘要聚类            │  │    知识图谱构建          │  │
│  │  - UMAP降维             │  │    - 实体抽取           │  │
│  │  - GMM聚类              │  │    - 关系抽取           │  │
│  │  - 层级摘要树           │  │    - 社区发现           │  │
│  └─────────────────────────┘  └─────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Auto Keyword（自动关键词）

**Prompt 文件**: `rag/prompts/keyword_prompt.md`

```markdown
## Role
You are a text analyzer.

## Task
Extract the most important keywords/phrases of a given piece of text content.

## Requirements
- Summarize the text content, and give the top {{ topn }} important keywords/phrases.
- The keywords MUST be in the same language as the given piece of text content.
- The keywords are delimited by ENGLISH COMMA.
- Output keywords ONLY.
```

- **存储字段**: `important_kwd`
- **检索权重**: 30倍加权（`important_kwd^30`）

**PM 关注点**：
- 显著提升关键词匹配检索效果
- 每个 chunk 额外消耗一次 LLM 调用
- 推荐：重要文档启用，批量文档谨慎

### 5.3 Auto Question（自动问题生成）

**Prompt 文件**: `rag/prompts/question_prompt.md`

```markdown
## Role
You are a text analyzer.

## Task
Propose {{ topn }} questions about a given piece of text content.

## Requirements
- Understand and summarize the text content, and propose the top {{ topn }} important questions.
- The questions SHOULD NOT have overlapping meanings.
- The questions SHOULD cover the main content of the text as much as possible.
- The questions MUST be in the same language as the given piece of text content.
```

- **存储字段**: `question_kwd`, `question_tks`
- **检索权重**: 20倍加权（`question_tks^20`）

**核心价值**：

```
用户问题: "如何申请退款？"
           ↓
自动生成问题: "退款申请的流程是什么？"  ← 语义匹配！
           ↓
命中 chunk: "退款流程：1. 登录账户 2. 找到订单..."
```

### 5.4 Metadata（元数据抽取）

**Prompt 文件**: `rag/prompts/meta_data.md`

**核心特点**：基于用户定义的 Schema 严格抽取

```python
# 用户定义 Schema
schema = {
    "合同金额": "数字",
    "签约日期": "日期",
    "甲方名称": "文本",
    "乙方名称": "文本"
}

# LLM 严格抽取（只抽取明确提及的信息）
metadata = llm.extract(chunk_content, schema)
# 输出: {"合同金额": 100000, "签约日期": "2024-01-15", ...}
```

**应用场景**：
- 合同管理：抽取金额、日期、当事人
- 简历筛选：抽取学历、工作年限、技能
- 论文管理：抽取作者、机构、关键词

> **MetaData实际上是**，很多业务天然就有的关键索引信息。
> 比如欧美企业工商知识库，天然就有一些层级和索引：
> `国家 -> 城市 -> 公司名 -> 管理层`
>
> 对于已经有层次的知识，在导入RAG的时候，一定要保留索引信息。在RAG检索的时候，应该优先判断索引，再去获取具体的判断。
>
> 这部分就需要用到传统代码：
> ```
> 用户query -> 意图模块 { 意图：XX, 所属的国家/城市, 所属的行业 }
> -> 人工代码，筛选特定国家的数据库chunk
> -> 剩下来的数据，作为向量排序的结果
> ```

### 5.5 RAPTOR（递归摘要聚类）

**文件**: `rag/raptor.py`

**核心类**: `RecursiveAbstractiveProcessing4TreeOrganizedRetrieval`

**技术架构**：

```
原始Chunks
    │
    ▼
┌─────────────────────────────────────┐
│           UMAP 降维                  │
│   高维向量 → 低维空间（便于聚类）     │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│           GMM 聚类                   │
│   + BIC 选择最优簇数                 │
│   相似chunks → 同一簇                │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│        LLM 摘要生成                  │
│   每个簇 → 一个摘要chunk             │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│         迭代构建                     │
│   摘要chunks → 再聚类 → 再摘要       │
│   直到达到层数限制                   │
└─────────────────────────────────────┘
    │
    ▼
层级摘要树（Level 0: 原始, Level 1: 摘要, Level 2: 摘要的摘要...）
```

**核心代码逻辑**：

```python
class RecursiveAbstractiveProcessing4TreeOrganizedRetrieval:
    def __init__(self, max_level=3):
        self.max_level = max_level

    def build_tree(self, chunks, embeddings):
        levels = {0: chunks}
        current_embeddings = embeddings

        for level in range(1, self.max_level + 1):
            # 1. UMAP 降维
            reduced = umap.UMAP(n_components=10).fit_transform(current_embeddings)

            # 2. GMM 聚类 + BIC 选择最优簇数
            best_n_clusters = self._find_optimal_clusters(reduced)
            gmm = GaussianMixture(n_components=best_n_clusters)
            labels = gmm.fit_predict(reduced)

            # 3. 为每个簇生成摘要
            summaries = []
            for cluster_id in range(best_n_clusters):
                cluster_chunks = [c for c, l in zip(levels[level-1], labels) if l == cluster_id]
                summary = self._generate_summary(cluster_chunks)
                summaries.append(summary)

            levels[level] = summaries
            current_embeddings = self._embed(summaries)

        return levels
```

**适用场景**：
- 多跳问答：需要综合多个 chunk 信息
- 全局理解："这份文档主要讲什么？"
- 长文档摘要

### 5.6 GraphRAG（知识图谱）

**目录**: `graphrag/`

**核心流程**：

```
┌─────────────────────────────────────────────────────────────┐
│                     GraphRAG 构建流程                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │  子图抽取     │──▶│  子图合并     │──▶│  实体消歧     │    │
│  │              │   │              │   │              │    │
│  │ extractor.py │   │merge_subgraph│   │resolve_      │    │
│  │              │   │              │   │entities      │    │
│  │ LLM抽取      │   │ 同名实体合并  │   │ 相似实体合并  │    │
│  │ 实体+关系    │   │              │   │              │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│                                              │               │
│                                              ▼               │
│                                     ┌──────────────┐        │
│                                     │  社区发现     │        │
│                                     │              │        │
│                                     │extract_      │        │
│                                     │community     │        │
│                                     │              │        │
│                                     │Louvain算法   │        │
│                                     └──────────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**实体抽取 Prompt**（来自 `graphrag/light/graph_prompt.py`）：

```
---Goal---
Given a text document, identify all entities of those types from the text
and all relationships among the identified entities.

---Steps---
1. Identify all entities:
   - entity_name: Name of the entity
   - entity_type: One of [organization, person, geo, event, category]
   - entity_description: Comprehensive description

2. Identify all relationships:
   - source_entity, target_entity
   - relationship_description
   - relationship_strength (1-10)
   - relationship_keywords
```

**Gleaning 机制**：多轮抽取确保完整性

```python
# 第一轮抽取
entities_1, relations_1 = extract(chunk)

# 检查是否遗漏
if llm.check_missing(chunk, entities_1):
    # 第二轮补充抽取
    entities_2, relations_2 = extract_continue(chunk, entities_1)
    entities = merge(entities_1, entities_2)
```

**适用场景**：
- 复杂推理："A公司的CEO是谁？他的母校是哪里？"
- 实体关系问答："腾讯投资了哪些公司？"
- 多跳推理需求

### 5.7 增强模块启用建议表

| 文档类型 | Auto Keyword | Auto Question | Metadata | RAPTOR | GraphRAG |
|----------|--------------|---------------|----------|--------|----------|
| 法律法规 | ✅ 推荐 | ✅ 推荐 | ✅ 合同必备 | ❌ | ✅ 实体关系重要 |
| 学术论文 | ✅ 推荐 | ✅ 推荐 | ✅ 元数据重要 | ✅ 摘要聚合 | ⚠️ 可选 |
| 技术手册 | ✅ 推荐 | ✅ 高度推荐 | ⚠️ 可选 | ✅ 章节摘要 | ❌ |
| FAQ文档 | ⚠️ 可选 | ❌ 已有问题 | ❌ | ❌ | ❌ |
| 书籍 | ✅ 推荐 | ⚠️ 可选 | ⚠️ 可选 | ✅ 高度推荐 | ⚠️ 可选 |
| 企业制度 | ✅ 推荐 | ✅ 推荐 | ✅ 推荐 | ⚠️ 可选 | ✅ 组织关系 |
| 新闻资讯 | ✅ 推荐 | ⚠️ 可选 | ✅ 时间/人物 | ❌ | ✅ 人物事件 |

---

## 第六部分：检索模块深度解读

### 6.1 Query 预处理流程

**文件**: `rag/nlp/query.py`

> 对于非常复杂的问题，比如："我要退款小米的手机，而且我想知道小米汽车的最新价格我要买。"
> 必须做 query 的 multi query 改写：
> 1. 小米手机的退款政策
> 2. 小米汽车的价格

```
用户原始问题
    │
    ▼
┌─────────────────────────────────────┐
│       多轮问题补全（可选）            │
│                                     │
│  "他的母亲是谁？"                    │
│        ↓                            │
│  "Donald Trump的母亲是谁？"         │
│                                     │
│  Prompt: full_question_prompt.md    │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│           分词处理                   │
│                                     │
│  rag_tokenizer.tokenize()           │
│  支持中英文混合分词                  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│          同义词扩展                  │
│                                     │
│  synonym.py                         │
│  - 自定义词典                        │
│  - WordNet 同义词                   │
│                                     │
│  "RAG" → ["RAG", "检索增强生成"]    │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│          词权重计算                  │
│                                     │
│  term_weight.py                     │
│  - TF-IDF 权重                      │
│  - 命名实体加权                      │
│  - 停用词降权                        │
└─────────────────────────────────────┘
    │
    ▼
最终检索Query
```

### 6.2 混合检索（Hybrid Retrieval）

**文件**: `rag/nlp/search.py`

**核心方法**: `Dealer.retrieval()`

```python
class Dealer:
    def retrieval(self, question, embd_mdl, tenant_ids, kb_ids, ...):
        # 1. BM25 文本检索
        matchText, keywords = self.qryr.question(question)

        # 2. 向量语义检索
        matchDense = self.get_vector(question, embd_mdl, topk, similarity)

        # 3. 混合融合
        fusionExpr = FusionExpr("weighted_sum", topk, {"weights": "0.05,0.95"})

        # 执行混合检索
        matchExprs = [matchText, matchDense, fusionExpr]
        res = self.dataStore.search(src, highlightFields, filters, matchExprs, ...)
```

**字段权重配置**（来自 `query.py`）：

```python
query_fields = [
    "title_tks^10",         # 标题 10倍权重
    "title_sm_tks^5",       # 标题细粒度分词 5倍
    "important_kwd^30",     # 关键词 30倍权重（最高！）
    "important_tks^20",     # 关键词分词 20倍
    "question_tks^20",      # 自动问题 20倍
    "content_ltks^2",       # 正文 2倍
    "content_sm_ltks",      # 正文细粒度 1倍
]
```

**权重设计解读**：
- `important_kwd^30`：Auto Keyword 的价值体现，精确匹配关键词获得极高加权
- `question_tks^20`：Auto Question 的价值体现，问题与问题匹配
- `title_tks^10`：标题通常是内容的高度概括

**融合权重：0.05 : 0.95**
- BM25 权重 0.05：负责精确关键词匹配
- 向量检索权重 0.95：负责语义相似度
- 这个配置说明 RAGFlow 高度依赖语义检索

> **融合检索的策略，要根据业务场景决定。**
> 如果用户 query 有精准查找的需求，比如"GL-008零部件在哪里？"，BM25关键词检索的得到结果往往更匹配，向量检索可能会召回"GL-009零部件"（因为向量检索是相似度/模糊检索，不是精确检索）
> 对于这种 query，融合检索的权重，应该改为 BM25 - 0.9, 向量检索 0.1

### 6.3 增强检索机制

#### 6.3.1 TOC 增强检索

**方法**: `retrieval_by_toc()`

**原理**：利用目录结构辅助检索

```python
def retrieval_by_toc(self, query, chunks, tenant_ids, chat_mdl, topn=6):
    # 1. 获取文档目录
    toc = self.dataStore.search(filters={"toc_kwd": "toc"})

    # 2. LLM 评估目录与问题的相关性
    # Prompt: toc_relevance_system.md + toc_relevance_user.md
    relevant_sections = await relevant_chunks_with_toc(query, toc, chat_mdl, topn)

    # 3. 将相关章节的 chunks 提升权重
    for chunk_id, sim in relevant_sections:
        if chunk_id in chunks:
            chunks[chunk_id]["similarity"] += sim
```

#### 6.3.2 父子文档检索

**方法**: `retrieval_by_children()`

**原理**：子 chunk 命中后返回父 chunk 完整内容

```python
def retrieval_by_children(self, chunks, tenant_ids):
    """
    检索策略：用细粒度chunk检索，返回粗粒度chunk

    场景：
    - 原始chunk太大，拆成子chunks用于检索
    - 子chunk命中后，返回完整的父chunk给LLM
    """
    mom_chunks = defaultdict(list)

    for chunk in chunks:
        mom_id = chunk.get("mom_id")
        if mom_id:
            mom_chunks[mom_id].append(chunk)

    # 获取父chunk完整内容
    for mom_id, children in mom_chunks.items():
        parent_chunk = self.dataStore.get(mom_id)
        # 合并子chunk的相似度作为父chunk的分数
        parent_chunk["similarity"] = np.mean([c["similarity"] for c in children])
```

**应用场景**：
- 长段落检索：用句子级别检索，返回段落级别内容
- 精确定位后扩展上下文

#### 6.3.3 知识图谱检索

**文件**: `graphrag/search.py`

**类**: `KGSearch`

```python
class KGSearch:
    def search(self, query, kb_ids):
        # 1. Query 重写：提取关键词和实体
        keywords = self._extract_keywords(query)
        entities = self._extract_entities(query)

        # 2. 多路检索
        # - 关键词匹配
        keyword_results = self._search_by_keywords(keywords)
        # - 实体类型匹配
        type_results = self._search_by_types(entities)
        # - 关系匹配
        relation_results = self._search_by_relations(entities)

        # 3. N-hop 路径遍历
        extended_results = self._n_hop_traverse(entities, n=2)

        # 4. 社区报告检索
        community_results = self._search_communities(query)

        return merge_results(...)
```

---

## 第七部分：重排序模块深度解读

### 7.1 为什么需要重排序

**检索 vs 重排序的分工**：
- **检索（Retrieval）**：从百万级文档中快速筛选出 Top-K（如 1000 条）
- **重排序（Rerank）**：对 Top-K 结果精细排序，选出最相关的 Top-N（如 10 条）

> **类比**：检索是"海选"，重排序是"决赛"。

### 7.2 内置混合相似度重排

**方法**: `Dealer.rerank()`

**核心公式**：

```
最终分数 = token_sim × 0.3 + vector_sim × 0.7 + rank_feature
```

**关键词加权策略**：

```python
def rerank(self, sres, query, tkweight=0.3, vtweight=0.7):
    for chunk_id in sres.ids:
        # 获取各字段的分词
        content_ltks = sres.field[chunk_id]["content_ltks"].split()
        title_tks = sres.field[chunk_id].get("title_tks", "").split()
        important_kwd = sres.field[chunk_id].get("important_kwd", [])
        question_tks = sres.field[chunk_id].get("question_tks", "").split()

        # 加权组合：title×2, important_kwd×5, question_tks×6
        weighted_tokens = (
            content_ltks +
            title_tks * 2 +
            important_kwd * 5 +
            question_tks * 6
        )
```

**权重设计解读**：
- `question_tks × 6`：自动问题最高权重，问题匹配问题效果最好
- `important_kwd × 5`：关键词次高权重
- `title_tks × 2`：标题相对重要
- `content_ltks × 1`：正文基础权重

### 7.3 Rerank 模型重排

**方法**: `Dealer.rerank_by_model()`

**支持的 Rerank 模型**：

| 厂商 | 类 | 特点 |
|------|-----|------|
| Jina | `JinaRerank` | 多语言支持好 |
| Cohere | `CoHereRerank` | 效果稳定 |
| NVIDIA | `NvidiaRerank` | 高性能 |
| Voyage AI | `VoyageRerank` | 代码理解强 |
| 通义千问 | `QWenRerank` | 中文效果好 |
| HuggingFace | `HuggingfaceRerank` | 本地部署 |
| Xinference | `XInferenceRerank` | 本地部署 |
| OpenAI-Compatible | `OpenAI_APIRerank` | 兼容接口 |

**调用逻辑**：

```python
def rerank_by_model(self, rerank_mdl, sres, query, tkweight=0.3, vtweight=0.7):
    # 1. 计算 token 相似度（保留）
    tksim = self.qryr.token_similarity(keywords, ins_tw)

    # 2. 调用外部 Rerank 模型
    vtsim, _ = rerank_mdl.similarity(
        query,
        [" ".join(tks) for tks in ins_tw]
    )

    # 3. 加权融合
    return tkweight * np.array(tksim) + vtweight * vtsim + rank_fea
```

### 7.4 RankFeature 加权机制

**两个额外加权信号**：

1. **PageRank 分数**：文档被引用/链接的重要性
2. **Tag Feature 分数**：用户标签匹配度

```python
def _rank_feature_scores(self, query_rfea, search_res):
    # 1. PageRank 分数
    pageranks = [sres.field[id].get(PAGERANK_FLD, 0) for id in sres.ids]

    # 2. Tag 匹配分数
    for chunk_id in search_res.ids:
        chunk_tags = eval(search_res.field[chunk_id].get(TAG_FLD, "{}"))
        for tag, score in chunk_tags.items():
            if tag in query_rfea:
                nor += query_rfea[tag] * score

    return np.array(rank_fea) * 10. + pageranks
```

---

## 第八部分：生成模块深度解读

### 8.1 对话服务完整流程

**文件**: `api/db/services/dialog_service.py`

**核心方法**: `async_chat()`

```
用户消息
    │
    ▼
┌─────────────────────────────────────┐
│          模型加载                    │
│                                     │
│  - Embedding 模型                   │
│  - Chat 模型                        │
│  - Rerank 模型（可选）              │
│  - TTS 模型（可选）                 │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│        Query 预处理                  │
│                                     │
│  - 多轮问题补全                      │
│  - 跨语言处理                        │
│  - 关键词抽取                        │
│  - 元数据过滤                        │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│          检索阶段                    │
│                                     │
│  - 基础混合检索                      │
│  - TOC增强检索（可选）              │
│  - 父子文档检索（可选）             │
│  - 知识图谱检索（可选）             │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│          重排序                      │
│                                     │
│  - 内置混合重排                      │
│  - 或 Rerank模型重排                │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│        上下文组装                    │
│                                     │
│  kb_prompt() 方法                   │
│  - Token 限制控制                   │
│  - 格式化 chunk 内容                │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│        LLM 生成                      │
│                                     │
│  - 流式输出                          │
│  - 引用标注                          │
│  - TTS 转换（可选）                 │
└─────────────────────────────────────┘
    │
    ▼
最终回答（带引用）
```

### 8.2 上下文组装

**方法**: `kb_prompt()`

```python
def kb_prompt(kbinfos, max_tokens):
    """
    将检索结果组装成 Prompt 上下文
    """
    context_parts = []
    current_tokens = 0

    for i, chunk in enumerate(kbinfos["chunks"]):
        chunk_text = f"ID: {i}\n└── Content: {chunk['content_with_weight']}\n"
        chunk_tokens = num_tokens_from_string(chunk_text)

        if current_tokens + chunk_tokens > max_tokens:
            break

        context_parts.append(chunk_text)
        current_tokens += chunk_tokens

    return "\n".join(context_parts)
```

### 8.3 Citation 引用机制

**Prompt 文件**: `rag/prompts/citation_prompt.md`

**引用格式**：`[ID:x]` 或 `[ID:x][ID:y]`

**引用规则**：

```markdown
## What MUST Be Cited:
1. **Quantitative data**: Numbers, percentages, statistics
2. **Temporal claims**: Dates, timeframes
3. **Causal relationships**: Cause and effect claims
4. **Comparative statements**: Rankings, comparisons
5. **Technical definitions**: Specialized terms
6. **Direct attributions**: What someone said or did
7. **Predictions/forecasts**: Future projections
8. **Controversial claims**: Disputed facts

## What Should NOT Be Cited:
- Common knowledge (e.g., "The sun rises in the east")
- Transitional phrases
- General introductions
- Your own analysis (unless from source)
```

**内置引用算法 `insert_citations()`**：

```python
def insert_citations(self, answer, chunks, chunk_v, embd_mdl, tkweight=0.1, vtweight=0.9):
    """
    基于句子级相似度的引用标注
    """
    # 1. 将回答切分成句子
    sentences = split_into_sentences(answer)

    # 2. 对每个句子计算与 chunks 的相似度
    for i, sentence in enumerate(sentences):
        sim = self.hybrid_similarity(
            sentence_embedding,
            chunk_embeddings,
            sentence_tokens,
            chunk_tokens,
            tkweight, vtweight
        )

        # 3. 超过阈值的 chunk 作为引用
        if max(sim) > 0.63:
            cited_chunks = [j for j in range(len(chunks)) if sim[j] > max(sim) * 0.99]
            sentence += f" [ID:{cited_chunks[0]}]"
```

---

## 第九部分：Agentic RAG 专题

### 9.1 什么是 Agentic RAG

**传统 RAG**：
```
问题 → 单次检索 → 生成回答
```

**Agentic RAG**：
```
问题 → 分析问题 → 检索1 → 分析结果 → 检索2 → ... → 综合生成
```

> **核心差异**：Agentic RAG 让 LLM 自主决定"需要检索什么"和"何时停止检索"。

### 9.2 RAGFlow 的 DeepResearcher

**文件**: `agentic_reasoning/deep_research.py`

**核心类**: `DeepResearcher`

```python
class DeepResearcher:
    def __init__(self, chat_mdl, prompt_config, kb_retrieve=None, kg_retrieve=None):
        self.chat_mdl = chat_mdl
        self._kb_retrieve = kb_retrieve  # 知识库检索函数
        self._kg_retrieve = kg_retrieve  # 知识图谱检索函数
```

### 9.3 推理流程详解

```
┌─────────────────────────────────────────────────────────────┐
│                    DeepResearcher 推理流程                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   STEP 1: 问题分析                     │  │
│  │                                                        │  │
│  │   用户问题: "Jaws和Casino Royale的导演是同一国籍吗？"  │  │
│  │                                                        │  │
│  │   LLM思考: 需要分步查询                               │  │
│  │   1. Jaws的导演是谁？                                 │  │
│  │   2. 该导演的国籍？                                   │  │
│  │   3. Casino Royale的导演是谁？                        │  │
│  │   4. 该导演的国籍？                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   STEP 2: 生成查询                     │  │
│  │                                                        │  │
│  │   <|begin_search_query|>                              │  │
│  │   who is the director of Jaws?                        │  │
│  │   <|end_search_query|>                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   STEP 3: 执行检索                     │  │
│  │                                                        │  │
│  │   _retrieve_information():                            │  │
│  │   - 知识库检索 (self._kb_retrieve)                   │  │
│  │   - Web检索 (Tavily API, 可选)                       │  │
│  │   - 知识图谱检索 (self._kg_retrieve, 可选)           │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   STEP 4: 信息提取                     │  │
│  │                                                        │  │
│  │   _extract_relevant_info():                           │  │
│  │   LLM从检索结果中提取相关信息                         │  │
│  │                                                        │  │
│  │   <|begin_search_result|>                             │  │
│  │   Jaws is directed by Steven Spielberg.               │  │
│  │   <|end_search_result|>                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   STEP 5: 迭代判断                     │  │
│  │                                                        │  │
│  │   是否需要更多信息？                                  │  │
│  │   - 是 → 返回 STEP 2                                  │  │
│  │   - 否 → 进入 STEP 6                                  │  │
│  │                                                        │  │
│  │   最大迭代次数: MAX_SEARCH_LIMIT = 6                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   STEP 6: 综合回答                     │  │
│  │                                                        │  │
│  │   基于所有收集的信息生成最终回答:                     │  │
│  │                                                        │  │
│  │   "No, the directors are not from the same country.   │  │
│  │   Steven Spielberg (Jaws) is from the USA, while      │  │
│  │   Martin Campbell (Casino Royale) is from New Zealand"│  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 9.4 核心 Prompt 设计

**推理 Prompt (REASON_PROMPT)**：

```
You are an advanced reasoning agent. Your goal is to answer the user's
question by breaking it down into a series of verifiable steps.

**Your Task:**
1. Analyze the user's question.
2. If you need information, issue a search query to find a specific fact.
3. Review the search results.
4. Repeat until you have all facts needed.
5. Synthesize and provide the final answer.

**Tool Usage:**
- To search: <|begin_search_query|>your query<|end_search_query|>
- Results will be: <|begin_search_result|>results<|end_search_result|>
- Maximum {MAX_SEARCH_LIMIT} search attempts.

**Important Rules:**
- One fact at a time
- Be precise in queries
- Synthesize at the end
```

**信息提取 Prompt (RELEVANT_EXTRACTION_PROMPT)**：

```
You are a highly efficient information extraction module.

**Your Task:**
1. Read the Current Search Query
2. Scan the Searched Web Pages
3. Extract only essential, factual information

**Output Format:**
1. If relevant answer found:
   Final Information
   [Extracted facts]

2. If no relevant answer:
   Final Information
   No helpful information found.
```

### 9.5 Agentic RAG vs 传统 RAG 对比

| 维度 | 传统 RAG | Agentic RAG (DeepResearcher) |
|------|----------|------------------------------|
| 检索次数 | 1次 | 1-6次（自适应） |
| 问题分解 | 不支持 | 自动分解复杂问题 |
| 信息整合 | 简单拼接 | LLM 智能综合 |
| 适用场景 | 简单问答 | 多跳推理、复杂分析 |
| 延迟 | 低（1-2秒） | 高（10-30秒） |
| 成本 | 低 | 高（多次 LLM 调用） |
| 可解释性 | 一般 | 好（有推理过程） |

### 9.6 PM 决策指南：何时启用 Agentic RAG

| 场景 | 推荐策略 | 理由 |
|------|----------|------|
| FAQ 问答 | 不启用 | 简单问题，传统 RAG 足够 |
| 多跳问题 | 启用 | "A的B的C是什么" |
| 复杂分析 | 启用 | 需要综合多个信息源 |
| 实时性要求高 | 不启用 | 延迟过高 |
| 成本敏感 | 不启用 | 多次 LLM 调用成本高 |
| 高价值咨询 | 启用 | 质量优先于成本 |

---

## 第十部分：Prompt 工程汇总

### 10.1 Prompt 模板全景表

| Prompt 文件 | 用途 | 调用位置 | 核心变量 |
|-------------|------|----------|----------|
| `keyword_prompt.md` | 关键词抽取 | `task_executor.py` | `{{ topn }}`, `{{ content }}` |
| `question_prompt.md` | 问题生成 | `task_executor.py` | `{{ topn }}`, `{{ content }}` |
| `meta_data.md` | 元数据抽取 | `task_executor.py` | Schema 定义 |
| `citation_prompt.md` | 引用标注 | `dialog_service.py` | 引用规则 |
| `full_question_prompt.md` | 多轮问题补全 | `generator.py` | `{{ today }}`, `{{ conversation }}` |
| `cross_languages_*.md` | 跨语言处理 | `generator.py` | 目标语言 |
| `toc_relevance_*.md` | TOC相关性评估 | `search.py` | 目录内容、问题 |
| `vision_llm_*.md` | 图表描述 | `figure_parser.py` | 图片内容 |
| `analyze_task_*.md` | Agentic任务分析 | `deep_research.py` | 任务描述 |
| `reflect.md` | 反思机制 | Agent模块 | 推理历史 |
| `next_step.md` | 下一步规划 | Agent模块 | 当前状态 |

### 10.2 GraphRAG Prompt 设计

**实体抽取** (`graphrag/light/graph_prompt.py`)：

```
---Goal---
Given a text document and entity types, identify:
1. All entities with name, type, description
2. All relationships with source, target, description, strength, keywords
3. High-level content keywords

---Output Format---
("entity"{tuple_delimiter}<name>{tuple_delimiter}<type>{tuple_delimiter}<description>)
("relationship"{tuple_delimiter}<source>{tuple_delimiter}<target>{tuple_delimiter}<description>{tuple_delimiter}<keywords>{tuple_delimiter}<strength>)
("content_keywords"{tuple_delimiter}<keywords>)
```

**实体类型**：`["organization", "person", "geo", "event", "category"]`

### 10.3 Prompt 设计最佳实践

RAGFlow 的 Prompt 设计特点：

1. **结构化输出**：明确的输出格式要求
2. **Few-shot 示例**：提供具体例子
3. **约束清晰**：明确什么该做、什么不该做
4. **语言一致**：要求输出与输入语言一致
5. **可解析**：输出格式便于代码解析

---

## 第十一部分：最佳实践与选型指南

### 11.1 解析模式选型决策表

| 文档类型 | 推荐模式 | 推荐配置 | 注意事项 |
|----------|----------|----------|----------|
| 法律法规 | `laws` | chunk_token: 256-512 | 必须保持条文完整性 |
| 合同协议 | `laws` | + Metadata抽取 | 启用关键字段抽取 |
| 学术论文 | `paper` | + Vision LLM | 图表描述很重要 |
| 技术手册 | `manual` | + Vision LLM | 确保PDF有书签 |
| 企业制度 | `laws` 或 `naive` | + Auto Question | 视结构化程度选择 |
| FAQ文档 | `qa` | 默认配置 | Excel格式最佳 |
| 书籍 | `book` | + RAPTOR | 长文档需要摘要聚合 |
| PPT演示 | `presentation` | 默认配置 | 每页独立chunk |
| Excel数据 | `table` | 默认配置 | 注意行数限制 |
| 简历 | `resume` | 默认配置 | 需要远程服务支持 |
| 图片/扫描件 | `picture` | + Vision LLM | OCR质量关键 |
| 音频 | `audio` | ASR模型配置 | 依赖语音识别质量 |

### 11.2 增强功能启用决策流程

```
                    ┌─────────────────┐
                    │   文档已切片     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ 是否需要精确检索？│
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              │              ▼
         ┌────────┐         │         ┌────────┐
         │   是   │         │         │   否   │
         └────┬───┘         │         └────┬───┘
              │             │              │
              ▼             │              ▼
    ┌─────────────────┐     │     ┌─────────────────┐
    │启用 Auto Keyword│     │     │   跳过此步骤    │
    │启用 Auto Question│    │     └─────────────────┘
    └─────────────────┘     │
                            │
                    ┌───────▼───────┐
                    │是否需要全局理解？│
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             │             ▼
         ┌────────┐        │        ┌────────┐
         │   是   │        │        │   否   │
         └────┬───┘        │        └────┬───┘
              │            │             │
              ▼            │             ▼
    ┌─────────────────┐    │    ┌─────────────────┐
    │   启用 RAPTOR    │    │    │   跳过此步骤    │
    └─────────────────┘    │    └─────────────────┘
                           │
                    ┌──────▼──────┐
                    │是否有实体关系？│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            │            ▼
         ┌────────┐       │       ┌────────┐
         │   是   │       │       │   否   │
         └────┬───┘       │       └────┬───┘
              │           │            │
              ▼           │            ▼
    ┌─────────────────┐   │   ┌─────────────────┐
    │  启用 GraphRAG   │   │   │   跳过此步骤    │
    └─────────────────┘   │   └─────────────────┘
                          │
                    ┌─────▼─────┐
                    │   完成     │
                    └───────────┘
```

### 11.3 性能与效果权衡参考

| 模块 | 处理延迟 | API成本 | 效果提升 | 推荐优先级 |
|------|----------|---------|----------|------------|
| Auto Keyword | ~2s/chunk | 低 | 中等 | 高 |
| Auto Question | ~3s/chunk | 低 | 高 | 高 |
| Metadata | ~2s/chunk | 低 | 场景相关 | 中 |
| Vision LLM | ~3-5s/图 | 中 | 高（图表文档） | 场景相关 |
| RAPTOR | ~10s/100chunks | 中 | 高（长文档） | 中 |
| GraphRAG | ~30s/文档 | 高 | 高（复杂推理） | 低（按需） |
| Rerank模型 | ~1s/query | 低 | 中等 | 中 |
| Agentic RAG | 10-30s/query | 高 | 很高 | 低（高价值场景） |

### 11.4 常见问题与解决方案

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 检索不到相关内容 | 切片太大/语义不匹配 | 减小chunk_token_num，启用Auto Question |
| 回答不准确 | 检索结果噪音多 | 启用Rerank模型，调高similarity_threshold |
| 表格数据丢失 | 表格解析失败 | 使用table模式，或Vision LLM增强 |
| 条文引用错误 | 切片破坏层级 | 使用laws模式 |
| 图表内容缺失 | 未启用Vision LLM | manual/paper模式+Vision LLM |
| 多跳问题答不好 | 单次检索不够 | 启用Agentic RAG |
| 处理速度慢 | 启用太多增强 | 按需启用，批量文档谨慎 |

---

## 附录：核心文件索引

| 功能 | 文件路径 |
|------|----------|
| PDF解析 | `deepdoc/parser/pdf_parser.py` |
| 版面识别 | `deepdoc/vision/layout_recognizer.py` |
| 表格识别 | `deepdoc/vision/table_structure_recognizer.py` |
| 解析模式 | `rag/app/naive.py`, `laws.py`, `manual.py`, `paper.py`, ... |
| NLP切片 | `rag/nlp/__init__.py` |
| 检索核心 | `rag/nlp/search.py` |
| Query处理 | `rag/nlp/query.py` |
| Rerank | `rag/llm/rerank_model.py` |
| Embedding | `rag/llm/embedding_model.py` |
| RAPTOR | `rag/raptor.py` |
| GraphRAG | `graphrag/general/extractor.py`, `graphrag/light/graph_prompt.py` |
| Agentic RAG | `agentic_reasoning/deep_research.py` |
| 对话服务 | `api/db/services/dialog_service.py` |
| Prompt模板 | `rag/prompts/*.md` |

---

## 结语

RAGFlow 是一个**深度文档理解为核心竞争力**的 RAG 系统。作为 AI 产品经理，理解其架构的关键在于：

1. **分层协作**：OCR → 结构识别 → 语义理解，不同技术各司其职
2. **策略模式**：14种解析模式针对不同场景特化
3. **可选增强**：按需启用，平衡效果与成本
4. **混合检索**：BM25 + 向量，各取所长
5. **Agentic 能力**：复杂场景下的深度推理

掌握这些核心架构决策，才能在实际落地中做出正确的技术选型。

---

*本教材基于 RAGFlow 开源代码分析生成，版本基于 2024 年代码库。*
