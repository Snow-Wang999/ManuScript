# 本地论文写作助手 PRD v1

## 1. 产品愿景（一句话）

**帮助硕博生围绕既定论文大纲，高效完成“分节研究 → 分节写作”的文献综述写作过程，显著减少无效阅读与结构性思考成本。**

> 关键不是“帮用户做研究”，而是**让每一节论文都能被顺利写出来**。

---

## 2. 目标用户与核心场景

### 2.1 目标用户（V1 唯一聚焦）

- 硕士 / 博士研究生
- 正在撰写：
  - 文献综述（Related Work）
  - 论文前两章（Introduction / Background）
  - Proposal / Survey 初稿

### 2.2 核心使用场景

> 用户已经：
> - 有一个**明确研究方向**
> - 下载或收集了一批论文（本地 PDF）
> - 但**不知道如何组织结构、筛选材料并写成段落**

系统需要解决的不是“找论文”，而是：

> **“围绕某一节，我该引用哪些论文，用什么结构，把话写清楚？”**

---

## 3. 核心写作流程（产品主线）

```text
Step 1: 上传 / 管理论文（本地论文库）
Step 2: 生成论文大纲（Outline）
Step 3: 用户确认并选择某一节（Section）
Step 4: 针对该 Section 进行 Research + 论文筛选
Step 5: 生成该 Section 的写作草稿
Step 6: 用户确认 / 编辑 / 进入下一节
```

> **所有 Research 行为，必须绑定到某一个 Section**。

---

## 4. MVP 功能范围（V1）

### 4.1 必须包含（P0）

#### A. 本地论文库
- PDF 上传（多篇）
- 基础解析：标题、作者、年份、摘要（自动/修正）
- 论文全文切分（chunk，保留 section 信息）

#### B. 论文大纲生成与管理（核心）
- 输入：研究主题 / 初步问题描述
- 输出：论文结构大纲（如 Introduction / Related Work / Method 分类）
- 用户可：
  - 编辑
  - 删除
  - 调整顺序

> **Outline 是后续一切行为的起点**。

#### C. Section-driven Research（核心）

- 用户选择某一 Section
- 系统生成 Section Research Brief：
  - 本节写作目标
  - 需要回答的关键问题

#### D. 论文筛选（作为子能力）

- 基于 Section Research Brief：
  - 对本地论文库进行语义检索
  - 返回“与本节相关的论文排序列表”
- 每篇论文提供：
  - 推荐级别：Read / Skim / Skip
  - 命中依据（abstract / intro / method 片段）

#### E. Section 写作草稿生成

- 输入：
  - Section 目标
  - 筛选后的论文 + 证据
- 输出：
  - 可直接写进论文的一段或多段综述文本
  - 自动引用标注（作者 + 年份）

---

### 4.2 明确不做（Anti-goals）

- ❌ 通用 Deep Research（自由探索）
- ❌ 无大纲的随意研究
- ❌ 一次性生成整篇长论文
- ❌ 多 Agent 自主决策研究轮数
- ❌ 聊天式“随便问论文”入口

---

## 5. Section-driven Research 机制设计

### 5.1 核心思想

> **Research 不再是探索未知，而是为“写这一节”收集足够材料。**

### 5.2 Research 单元定义

```json
{
  "section_title": "Related Work: Diffusion Models in Medical Imaging",
  "writing_goal": "总结主要方法流派及代表性工作",
  "key_questions": [
    "有哪些主流方法？",
    "各方法的核心差异是什么？"
  ]
}
```

### 5.3 Research 输出（Writing Pack）

```json
{
  "key_points": ["方法流派A", "方法流派B"],
  "evidence_clusters": [
    {
      "theme": "Transformer-based diffusion",
      "papers": ["Paper1", "Paper2"]
    }
  ],
  "draft_paragraph": "..."
}
```

> **输出目标不是“报告”，而是“段落可写”。**

---

## 6. 数据与状态流转（简化）

```text
Outline
  ↓
Section (selected)
  ↓
Section Research Brief
  ↓
Local Paper Retrieval & Filtering
  ↓
Writing Pack
  ↓
Section Draft
```

每一节是**独立可完成、可回退的最小单元**。

---

## 7. 技术架构原则（V1）

- RAG 用于：
  - 本地论文检索
  - 证据定位
- LLM 用于：
  - Section Research Brief
  - 写作草稿生成
- ❌ 不引入 Supervisor 无限循环
- ❌ 不做 Agent 自主拆题

> **约束比能力更重要。**

---

## 8. 成功标准（V1 验收）

- 用户能在 1 小时内：
  - 生成清晰论文大纲
  - 完成至少 1 个 Section 的初稿
- 用户明确感知：
  - 少读了不相关论文
  - 写作更有结构感

---

## 9. 后续版本方向（V2+，不进入 MVP）

- 单篇论文深度对话
- Section 之间的逻辑一致性检查
- 引文自动规范化（BibTeX / LaTeX）
- 写作风格控制

---

**PRD v1 结论：**

> 这是一个“以写作为中心”的 Research 系统，
> 而不是一个“以研究为中心”的写作工具。

