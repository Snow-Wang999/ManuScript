这份 PRD 重构版将我们刚才讨论的**“流水线组装”理念**、**RAGFlow 托管架构**以及**三大用户痛点**完全融合了进去。

它不再是一个泛泛的“AI 助手”文档，而是一个**严谨的工程实施指南**。

---

# ManuScript PRD v2.0：分节式论文写作流水线

> **核心变更 (v2.0)**：
> 1. **架构瘦身**：移除本地 PDF 解析/切分逻辑，完全基于 RAGFlow API。
> 2. **价值重塑**：从“辅助研究”转向“证据组装与写作”。
> 3. **场景聚焦**：只解决“从 Outline 到 First Draft”这一公里。
> 
> 

---

## 1. 产品定义（Product Definition）

**一句话定位**：
ManuScript 是一个**基于 RAGFlow 的学术写作流水线工具**。它不让用户面对空白文档，而是通过“大纲分节 -> 精准素材召回 -> 证据组装 -> 草稿生成”的标准流程，帮助硕博生“拼装”出有据可依的论文初稿。

**核心隐喻**：
不是“聊天机器人”，而是**“配菜师 + 装配工”**。

* **配菜**：从 50 篇论文里把“这一节”需要的原料切好（Chunks）。
* **装配**：把原料按逻辑拼成一段话，并贴上原产地标签（Citation）。

---

## 2. 解决的核心痛点（The "Why"）

我们只解决导致用户“写不出来”的三个具体崩溃瞬间：

| 痛点场景 | 痛苦本质 | ManuScript 解法 |
| --- | --- | --- |
| **“读了后面忘前面，脑子不够用”** | **认知过载 (Cognitive Overload)** | **Section Context Window**：只把和“当前这一节”相关的 5-10 个片段摆在桌面上，屏蔽噪音。 |
| **“不敢下笔，怕找不到出处被骂”** | **引用焦虑 (Citation Anxiety)** | **Evidence Traceability**：每一句生成的草稿都必须带 RAGFlow 的坐标（Page/Doc），鼠标一指，原文立现。 |
| **“看着空白文档发呆，不知道第一句写啥”** | **结构性卡顿 (Structural Block)** | **Draft as Verification**：用户不需要“创作”，只需要“确认”系统生成的草稿是否合理。 |

---

## 3. 核心用户旅程（User Journey）

```mermaid
graph LR
    A[准备: RAGFlow KB] --> B[1. 生成/确认大纲]
    B --> C[2. 选中某一节 (Section)]
    C --> D[3. 自动化素材配菜 (Assembly)]
    D --> E[4. 生成草稿 (Drafting)]
    E --> F[5. 验证引用 (Verification)]

```

### 3.1 关键交互细节

1. **大纲导航（The Map）**：左侧永远是树状 Outline，它是整个工作的进度条。
2. **素材区（The Mise-en-place）**：当用户点击 `3.1 Method` 时，系统**静默**调用 RAGFlow，在中间区域展示“筛选出的 Top-10 核心片段（Chunks/Tables）”。
3. **写作区（The Assembly）**：右侧生成草稿。用户无法直接“这就去写”，必须先确认素材区的内容是否满意。

---

## 4. 功能范围与需求（Functional Requirements）

### 4.1 知识库接入层 (Knowledge Layer) - **[基于 RAGFlow]**

* **KB 同步**：用户输入 RAGFlow 的 `API Key` 和 `Dataset ID`。
* **元数据拉取**：系统仅拉取论文列表（Title, Author, Doc_ID），**不下载全文**。
* **状态检查**：只有在 RAGFlow 端状态为 `Parsed` 的论文才能被使用。

### 4.2 大纲引擎 (Outline Engine)

* **输入**：研究题目 / Abstract / 粗略想法。
* **输出**：标准的树状结构（JSON）。
* **操作**：增、删、改、拖拽排序。
* **约束**：**Outline 是后续一切动作的“父级 ID”，没有 Outline 就没有 Section ID。**

### 4.3 自动化配菜系统 (Material Assembly) - **[核心]**

> *这是原来的“Deep Research”，现在降维打击为“素材筛选”。*

* **Trigger**：用户选中某个 Section。
* **Query 生成**：LLM 根据 Section 标题和父级标题，生成 3-5 个检索关键词。
* **API 检索**：调用 RAGFlow `/retrieval` 接口。
* **重排序 (Re-ranking)**：LLM 快速扫一眼返回的 Chunks，剔除完全无关的（比如参考文献列表里的噪音）。
* **展示**：在 UI 上以卡片形式展示 Chunks，**必须显示来源论文标题**。

### 4.4 写作装配工 (Draft Assembler)

* **Prompt 构造**：`System: 你是学术写作助手... Context: [Chunk 1, Chunk 2...] Task: 基于 Context 写一段关于 {Section Title} 的综述。`
* **强制引用**：要求 LLM 在输出中使用 `[Doc_ID:Page]` 格式标记每一句话的来源。
* **图表描述**：如果 RAGFlow 返回了图片/表格描述，尝试将其总结写入草稿（例如：“如表 1 所示...”）。

### 4.5 证据溯源 (Trust Layer)

* **UI 交互**：在草稿中点击 `[引用]` 标记。
* **动作**：调用 RAGFlow `/document/chunk` 接口（或利用已缓存的元数据）。
* **效果**：弹窗显示该段文字在 PDF 原文中的**切片截图**或**高亮文本**。

---

## 5. 明确不做（Anti-Goals）

* ❌ **不做 PDF 解析器**：解析不准、乱码、表格错位是 RAGFlow 要解决的问题，不是我们要解决的。
* ❌ **不做通用 Chat**：没有“这就随便聊聊”的输入框。所有对话必须挂载在某个 Section 下。
* ❌ **不做全篇一键生成**：那是垃圾内容生成器。我们做的是辅助写作。
* ❌ **不上传 PDF**：ManuScript 只是 RAGFlow 的一个**高级阅读器/编辑器客户端**。

---

## 6. 技术架构原则 (Technical Stack)

* **Backend**: Python (FastAPI / Lightweight)
* **RAG Engine**: **RAGFlow API (必须)**
* **LLM**: OpenAI Compatible API (用于组装逻辑)
* **Frontend**: Gradio (MVP) -> React (V2)
* **Storage**: 仅存储 `Project -> Outline -> Draft` 的轻量级 JSON 结构，不存向量。

---

## 7. MVP 验收标准 (Success Metrics)

1. **连通性**：用户配置好 RAGFlow Key 后，能立刻看到自己的论文列表。
2. **准确性**：点击一个 Section，能从 20 篇论文里准确捞出相关的 3-5 个段落。
3. **可溯源**：生成的草稿中，至少 80% 的句子带有正确的引用标记，且能点开查看原文。

---

> **PRD 结论**：
> 这个版本彻底剥离了“也是个 RAG 系统”的沉重包袱，转而成为一个**“利用 RAG 数据进行专业写作”的垂直应用**。工程量减少 60%，用户价值提升 100%。