# ManuScript

> 封闭域学术研究助手 — 基于本地文献库的素材组装与段落级溯源

## 项目简介

ManuScript 帮助研究人员通过对话探索本地文献库，定位可追溯的原文段落，组织素材并生成带引用的综述。

与开放域深度搜索（[research-assistant](https://github.com/Snow-Wang999/research-assistant)）互补，覆盖学术研究的"文献管理 → 素材组织 → 综述生成"环节。

**核心特点**：
- 基于 RAGFlow 的本地文献检索 + 段落级溯源
- 对话式交互，意图路由自动分流简单/复杂查询
- 渐进式架构演进：v0.1 → v2.0 共 4 个已完成版本，v3.0 设计中

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.9+ |
| 前端 | Gradio |
| RAG | RAGFlow（开源，自部署） |
| LLM | 通义千问 API（可切换） |
| 后端 | FastAPI |

## 版本状态

| 版本 | 架构 | 状态 |
|------|------|------|
| v0.1 | 最小原型：RAGFlow + OpenAI 连通 | ✅ 完成 |
| v0.2 | 基础流程：JSON 大纲 + Prompt Chain | ✅ 完成 |
| v1.0 | Chain-of-Agents（多 Agent 协作） | ✅ 完成 |
| v2.0 | Orchestrator-Worker 动态调度 | ✅ 完成 |
| v3.0 | 对话式文献研究助手（本地混合检索 + 意图路由） | 🔧 设计阶段 |

### 版本演进逻辑

- **v0.1-v0.2**：验证 RAGFlow API 可行性，跑通基本流程
- **v1.0**：引入 Agent 架构，多步协作完成文献综述
- **v2.0**：Orchestrator-Worker 模式，动态调度简单/复杂任务
- **v3.0**（设计中）：本地混合检索（ripgrep + FTS5 + ChromaDB）+ 意图路由层

## 快速开始

```bash
# 克隆项目
git clone https://github.com/Snow-Wang999/ManuScript.git
cd ManuScript

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 RAGFlow 和 LLM 的 API 配置

# 安装依赖（以 v2.0 为例）
pip install -r legacy/v2_0/requirements.txt

# 运行
python legacy/v2_0/main.py
```

> 注意：需要自部署 [RAGFlow](https://github.com/infiniflow/ragflow) 服务，并在 `.env` 中配置连接信息。

## 目录结构

```
ManuScript/
├── legacy/               # 已完成的版本归档
│   ├── v0_1/             # v0.1 最小原型
│   ├── v0_2/             # v0.2 基础流程
│   ├── v1_0/             # v1.0 Agent 链
│   └── v2_0/             # v2.0 动态调度
├── v3_0/                 # v3.0 设计阶段
├── evaluation/           # 评测系统
│   ├── llm_judge.py      # LLM 评委
│   ├── metrics.py        # 文本质量指标
│   └── text_quality.py   # 文本质量评估
├── prompts/              # Prompt 模板
├── docs/                 # 设计文档（40+ 文件）
│   ├── design/           # ADR 架构决策记录（ADR-00 至 ADR-12）
│   ├── generate/         # PRD、架构规划、竞品分析
│   └── references/       # 技术参考资料
└── tex/                  # 测试用 LaTeX 论文
```

## 文档导航

### 核心文档

| 文档 | 说明 |
|------|------|
| [项目概览与求职说明](docs/generate/00_项目概览与求职说明.md) | 项目全貌与产品定位 |
| [架构迭代实践记录](docs/generate/01_架构迭代实践记录.md) | v0.1-v2.0 迭代过程 |
| [竞品分析与市场定位](docs/generate/03_竞品分析与市场定位.md) | 9 款竞品深度对比 |
| [面试解释文档](docs/generate/08_面试解释文档.md) | 技术决策与项目亮点 |

### v3.0 设计文档

| 文档 | 说明 |
|------|------|
| [v3.0 PRD](docs/generate/09_ManuScript_v3.0_PRD_重新设计.md) | 产品需求 |
| [v3.0 技术架构](docs/design/ADR-11_ManuScript_v3.0_技术架构.md) | 技术架构设计 |
| [v3.0 数据结构](docs/generate/11_ManuScript_v3.0_数据结构设计.md) | 数据模型设计 |

### 历史文档

| 文档 | 说明 |
|------|------|
| [架构版本规划](docs/generate/05_架构版本规划与实现路径.md) | v0.1-v2.0 详细设计 |
| [v2.0 PRD](docs/generate/07_ManuScript_v2.0_PRD.md) | v2.0 产品需求 |
| [技术选型](docs/generate/06_技术选型与AI能力评估.md) | RAG/LLM/Agent 评估 |

## 相关项目

- [research-assistant](https://github.com/Snow-Wang999/research-assistant) — 开放域 Deep Research 路线（完整可运行），与 ManuScript 互补

## License

MIT
