# Modified: ManuScript Reboot Pack (Section RAGFlow Integration)
## Part 1. 旧项目继承清单 (Revised for RAGFlow API)
### 1.1 ✅ 核心继承与替换策略（RAGFlow 托管模式）
架构变更核心：本地不再进行任何 PDF 解析、切分或存储。所有非结构化数据处理下沉至 RAGFlow，ManuScript 只通过 API 消费结构化数据（Chunks/Images）。

| 模块 / 资产 | 是否继承旧代码 | 新策略 (RAGFlow Adapter) | 详细说明 |
|-------------|--------------|--------------------------|---------|
| PDF 解析与 OCR | ❌ | 不继承完全托管 (API) | 直接调用 RAGFlow 解析能力。不保留任何 PyMuPDF 或本地 OCR 代码。 |
| Chunk 切分与位置 | ❌ | 不继承API | 获取不再维护切分算法。通过 API 获取 RAGFlow 解析好的 Chunks（含 Token 坐标、页码）。 |
| 本地论文库 (Storage) | ❌ | 不继承ID | 映射 (Sync)本地 DB 仅存储 RAGFlow_Document_ID 与 Title 的映射关系，不再存储全文文本。 |
| 句级证据追溯 | ⚠️ | 逻辑重写引用适配 | 核心价值保留，但实现方式改为：解析 RAGFlow 返回的 provenance 数据，回显对应的原文片段。
| 表格与图片提取 | ✅ | 新增能力API | 获取利用 RAGFlow 对 Table/Image 的解析优势，在写作时自动检索相关图表作为素材。 |

### 1.2 ⚠️ 业务逻辑层（需基于 API 重构）
模块处理方式变更重点Paper Filter (筛选)重构基于 Metadata 过滤  利用 RAGFlow 的 retrieval 接口，在特定 Document ID 范围内进行检索，而不是本地遍历。Section Writer重构Context 组装  将 API 返回的 Chunks 组装成 Prompt Context，不再从本地 VectorDB 读取。

## Part 3. 核心用户旅程 (RAGFlow Workflow)
流程定义： “以 RAGFlow 为底座的 Section 级写作流”
```graph TD
    A[用户] --> B{RAGFlow 知识库准备}
    B -->|1. 上传/解析完成| C[ManuScript (Client)]
    
    subgraph ManuScript 内部流程
    C --> D[同步论文列表]
    D -->|获取 Doc IDs| E[生成/确认 Outline]
    E --> F[选择目标 Section]
    
    F --> G[Section-driven Research]
    G -->|2. 范围检索 (Filter)| H(RAGFlow API)
    H -->|返回 Top-K Chunks| G
    G -->|筛选相关论文 & 片段| I[构建 Writing Context]
    
    I --> J[生成 Draft]
    J -->|3. 引用溯源| K[高亮引用来源]
    end
    
    K -.->|查阅原文| H
```
### 详细步骤说明：
- 准备阶段 (Prerequisite)
    - 用户在 RAGFlow 端建立 Knowledge Base (KB)。用户上传 PDF，RAGFlow 完成解析（Parsing）和切分（Chunking）。
    - ManuScript 动作：输入 RAGFlow 的 API_KEY 和 DATASET_ID，拉取当前库中的论文列表（Title + Doc_ID）。
- 大纲阶段 (Outline)
    - 用户输入题目，LLM 生成 Outline。
    - 用户选中 

3.1 Method Overview。
- 筛选阶段 (Section Filtering)
    - ManuScript 生成该节的查询关键词。
- 调用 API：向 RAGFlow 发送检索请求（限制在当前 Dataset）。
- 数据获取：获得相关的 Chunks 列表，包含：
    - content_with_weight (文本)
    - img_id / table (图表数据)
    - doc_name (来源论文)
- 逻辑筛选：LLM 快速判断哪些 Chunks 真正与本节写作目标相关。
- 写作阶段 (Drafting)
    - 将筛选后的 Chunks + 图片描述填入 Prompt。生成包含引用的段落。
- 引用格式化：[doc_name, page_num] (数据来自 RAGFlow 元数据)。

## Part 4. V1 关键数据结构变更 (Data Model)
为了适配这一改动，你的核心数据模型应精简为：

```JSON
// 以前：存储了海量文本和向量
// 现在：只存储指针

class PaperReference:
    id: str                // Local UUID
    ragflow_doc_id: str    // 远程 ID
    title: str
    authors: str
    status: str            // 'parsed' in RAGFlow

class SectionContext:
    section_id: str
    intent: str
    // 不需要存 Embedding，只需要存这一节用到了哪些 RAGFlow 的 Chunk ID
    used_chunk_ids: List[str]
``` 
这里的关键优势：你完全避开了最难的“多栏 PDF 解析”和“表格还原”问题，直接站在了 RAGFlow 的肩膀上。


