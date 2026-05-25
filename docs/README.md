# ManuScript 文档目录

> 项目文档结构说明与索引

---

## 目录结构

```
docs/
├── README.md                    # 本文件 - 文档索引
├── [核心]_ManuScript项目架构.md # 项目架构概览入口
│
├── design/                      # 📐 设计决策文档 (ADR)
├── generate/                    # 📄 项目核心文档（求职展示用）
├── references/                  # 📚 参考资料/笔记/教程
├── tasks/                       # 📋 当前任务追踪
└── others/                      # 📦 草稿/旧版/重复文档
```

---

## 根目录文件

| 文件 | 说明 |
|------|------|
| [[核心]_ManuScript项目架构.md]([核心]_ManuScript项目架构.md) | 项目架构概览，版本路线图 |

---

## design/ - 架构决策记录 (ADR)

存放项目架构、技术选型、方案对比等**决策性文档**，采用 ADR (Architecture Decision Record) 编号规范。

> **快速入口**：[ADR-00_决策索引.md](design/ADR-00_决策索引.md) - 所有决策的概览与导航

| 编号 | 文件 | 决策主题 |
|------|------|----------|
| ADR-00 | [ADR-00_决策索引.md](design/ADR-00_决策索引.md) | **决策索引** - 所有 ADR 的概览与导航 |
| ADR-01 | [ADR-01_v2.0整体架构与项目定位.md](design/ADR-01_v2.0整体架构与项目定位.md) | v2.0 整体架构选型与项目定位 |
| ADR-02 | [ADR-02_RAGFlow_API_vs_自建解析.md](design/ADR-02_RAGFlow_API_vs_自建解析.md) | RAGFlow API vs 自建 RAG 的决策 |
| ADR-03 | [ADR-03_三种架构路线对比.md](design/ADR-03_三种架构路线对比.md) | Dify/LangGraph/Claude SDK 架构对比 |
| ADR-04 | [ADR-04_Gemini论文方法借鉴.md](design/ADR-04_Gemini论文方法借鉴.md) | Gemini 论文写作方法借鉴落实 |
| ADR-05 | [ADR-05_RAG检索优化策略.md](design/ADR-05_RAG检索优化策略.md) | RAG 检索优化决策（重排序等） |
| ADR-06 | [ADR-06_RAGFlow表格处理限制.md](design/ADR-06_RAGFlow表格处理限制.md) | RAGFlow 表格解析限制与方案 |
| ADR-07 | [ADR-07_跳过v0.2版本决策.md](design/ADR-07_跳过v0.2版本决策.md) | 为什么跳过 v0.2 版本 |
| ADR-08 | [ADR-08_RAGFlow切片策略决策.md](design/ADR-08_RAGFlow切片策略决策.md) | RAGFlow 切片策略选择 |
| ADR-09 | [ADR-09_论文格式选择决策.md](design/ADR-09_论文格式选择决策.md) | 论文格式选型（PDF/LaTeX/Markdown） |

---

## references/ - 参考资料与笔记

存放**参考资料、学习笔记、技术教程**等文档。

### 核心教程

| 文件 | 主题 | 说明 |
|------|------|------|
| [[教程]_RAGFlow技术架构详解.md](references/[教程]_RAGFlow技术架构详解.md) | RAGFlow | 完整技术架构解读（1800行） |
| [[教程]_VibeCoding方法论.md](references/[教程]_VibeCoding方法论.md) | 方法论 | Vibe Coding 五大心法 |

### 学习笔记

| 文件 | 主题 | 说明 |
|------|------|------|
| [[笔记]_RAG检索优化技巧.md](references/[笔记]_RAG检索优化技巧.md) | RAG | 检索优化技巧总结 |
| [[笔记]_AI产品路由与Agent架构设计.md](references/[笔记]_AI产品路由与Agent架构设计.md) | Agent | AI 产品路由/Agent 架构设计 |

### RAGFlow 技术参考

| 文件 | 主题 | 内容摘要 |
|------|------|----------|
| [[参考]_RAGFlow解析技术_DeepDoc.md](references/[参考]_RAGFlow解析技术_DeepDoc.md) | 文档解析 | DeepDoc架构：OCR、布局识别、表格结构识别 |
| [[参考]_RAGFlow检索参数.md](references/[参考]_RAGFlow检索参数.md) | 检索优化 | 混合检索权重、查询字段权重、Rerank配置 |
| [[参考]_RAGFlow集成方案_GPT.md](references/[参考]_RAGFlow集成方案_GPT.md) | 架构设计 | RAGFlow API集成方案、数据模型设计 |

### 竞品分析参考

| 文件 | 主题 | 内容摘要 |
|------|------|----------|
| [[参考]_竞品分析_Gemini.md](references/[参考]_竞品分析_Gemini.md) | 竞品版图 | NotebookLM/Jenni AI/GPT-Researcher对比 |
| [[参考]_竞品分析_Kimi.md](references/[参考]_竞品分析_Kimi.md) | 技术对比 | NotebookLM vs ima.copilot深度对比 |

### 其他参考

| 文件 | 主题 | 说明 |
|------|------|------|
| [[参考]_Anthropic多智能体研究系统.md](references/[参考]_Anthropic多智能体研究系统.md) | Agent | Anthropic 多智能体系统参考文章 |
| [[参考]_VibeCoding建议_Gemini.md](references/[参考]_VibeCoding建议_Gemini.md) | 项目建议 | ManuScript架构评价、迭代策略 |
| [[参考]_Windows编码问题.md](references/[参考]_Windows编码问题.md) | 编码问题 | Windows GBK/UTF-8编码冲突解决 |
| [[实验]_LaTeX搜索实验.md](references/[实验]_LaTeX搜索实验.md) | 实验 | LaTeX公式搜索测试记录 |

---

## generate/ - 项目核心文档

存放**求职展示用**的核心项目文档，编号有序。

| 文件 | 说明 |
|------|------|
| [00_项目概览与求职说明.md](generate/00_项目概览与求职说明.md) | 项目概览入口 |
| [01_架构迭代实践记录.md](generate/01_架构迭代实践记录.md) | 架构演进记录 |
| [02_用户调研与痛点洞察.md](generate/02_用户调研与痛点洞察.md) | 用户调研 |
| [03_竞品分析与市场定位.md](generate/03_竞品分析与市场定位.md) | 竞品分析 |
| [05_架构版本规划与实现路径.md](generate/05_架构版本规划与实现路径.md) | 版本规划 |
| [06_技术选型与AI能力评估.md](generate/06_技术选型与AI能力评估.md) | 技术选型 |
| [07_ManuScript_v2.0_PRD.md](generate/07_ManuScript_v2.0_PRD.md) | v2.0 PRD |
| [08_面试解释文档.md](generate/08_面试解释文档.md) | 面试说明 |

---

## tasks/ - 任务追踪

存放各版本的**当前任务**文档。

| 文件 | 说明 |
|------|------|
| [current_task_v0_1.md](tasks/current_task_v0_1.md) | v0.1 任务 |
| [current_task_v0_2.md](tasks/current_task_v0_2.md) | v0.2 任务 |
| [current_task_v1_0.md](tasks/current_task_v1_0.md) | v1.0 任务 |
| [current_task_v2_0.md](tasks/current_task_v2_0.md) | v2.0 任务 |
| [current_task_dify.md](tasks/current_task_dify.md) | Dify 任务 |

---

## others/ - 草稿/旧版/重复

存放**非核心文档**：草稿、旧版、重复内容等。

| 文件 | 标签 | 说明 |
|------|------|------|
| [[旧版]_PRD_v1_本地论文写作助手.md](others/[旧版]_PRD_v1_本地论文写作助手.md) | 旧版 | v1版本PRD（已被v2替代） |
| [[草稿]_项目重启规划.md](others/[草稿]_项目重启规划.md) | 草稿 | 未完成的规划文档 |
| [[草稿]_早期用户需求.md](others/[草稿]_早期用户需求.md) | 草稿 | 早期需求收集（未整理） |
| [[重复]_PRD_v2_分节式论文写作流水线.md](others/[重复]_PRD_v2_分节式论文写作流水线.md) | 重复 | 与generate/07_PRD重复 |
| [[重复]_竞品调研报告_kimi.html](others/[重复]_竞品调研报告_kimi.html) | 重复 | 与竞品分析_Kimi.md重复（HTML版本） |
| [[重复]_rag的教程.md](others/[重复]_rag的教程.md) | 重复 | 与RAGFlow深度技术教程重复 |
| [[备份]_战略分析报告.md](others/[备份]_战略分析报告.md) | 备份 | 战略分析备份文件 |
| [[已整合]_战略分析报告.md](others/[已整合]_战略分析报告.md) | 已整合 | 内容已整合到generate文档 |
| [[已整合]_04_架构演进决策文档.md](others/[已整合]_04_架构演进决策文档.md) | 已整合 | 内容已整合到01_架构迭代实践记录 |
| [[内部]_文档清单.md](others/[内部]_文档清单.md) | 内部 | 文档整理工作清单 |

---

## 文档整理原则

1. **根目录**：只保留 README.md 和核心架构入口文件
2. **design/**：所有架构、技术、方案的**决策文档** (ADR)
3. **references/**：参考资料、学习笔记、技术教程
4. **generate/**：求职展示用的**正式文档**（有编号）
5. **tasks/**：各版本的**任务追踪**
6. **others/**：草稿、旧版、重复等**非核心内容**

### 标签说明

| 标签 | 说明 |
|------|------|
| `[核心]` | 项目核心入口文档 |
| `[教程]` | 技术教程、学习指南 |
| `[笔记]` | 学习笔记、总结 |
| `[参考]` | 外部参考资料 |
| `[实验]` | 实验性记录 |
| `[旧版]` | 已被新版替代 |
| `[草稿]` | 未完成的草稿 |
| `[重复]` | 与其他文档内容重复 |
| `[备份]` | 备份文件 |
| `[已整合]` | 内容已整合到其他文档 |
| `[内部]` | 内部工作文档 |

---

*最后更新：2026-01-26*
