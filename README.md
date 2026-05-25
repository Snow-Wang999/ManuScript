# ManuScript

对话式文献研究助手（v3.0 主线）— 本地可控、可追溯检索与笔记管理

## 项目简介

ManuScript 帮助研究人员通过对话探索本地文献库，定位可追溯的原文段落并管理笔记，形成可信检索闭环。

**核心特点**：
- 本地解析 + 全文检索（ripgrep）+ 段落级溯源
- 对话式检索 + 会话摘要 + 笔记可检索
- 本地优先，云端可选（MVP）

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| 前端 | Gradio |
| 检索 | ripgrep + index.json |
| LLM | OpenAI API（可选） |
| 后端 | FastAPI |

## 版本规划

| 版本 | 目标 | 状态 |
|------|------|------|
| v3.0 | 对话式文献研究助手（主线） | 进行中 |
| v2.0 | Orchestrator-Worker（实验/对比基线） | 归档 |
| v1.0 | Chain-of-Agents（历史版本） | 弃用 |
| v0.2 | 基础流程：JSON 大纲 + Prompt Chain | 归档 |
| v0.1 | 最小原型：RAGFlow + OpenAI 连通 | 归档 |

## 版本定位（简述）

- **v3.0（主线）**：当前开发与交付目标，所有新功能以此为准。  
- **v2.0（基线）**：保留为对比与实验参考，不作为当前实现目标。  
- **v1.0 / v0.x（历史）**：仅用于回溯与说明，不再维护。

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repo_url>
cd ManuScript

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 RAGFlow 和 OpenAI 的 API Key
```

### 2. 运行 v0.1（历史）

```bash
# 安装依赖
make install-v01

# 运行核心脚本（无 UI）
make proto-v01

# 运行 Gradio UI
make run-v01
```

## 目录结构

```
ManuScript/
├── CLAUDE.md             # AI 开发规则
├── current_task.md       # 当前任务（上下文切片）
├── TODO.md               # 任务清单
├── Makefile              # 常用命令
│
├── v3_0/                 # v3.0 主线代码
│   ├── app/              # FastAPI/Gradio/React
│   ├── core/             # parser/index/search/memory
│   ├── models/           # Pydantic
│   ├── schemas/          # JSON Schema
│   ├── services/         # 工具/路由逻辑
│   └── tests/
│
├── legacy/               # 历史版本归档
│   ├── v0_1/             # v0.1 最小原型
│   ├── v0_2/             # v0.2 基础流程
│   ├── v1_0/             # v1.0 Agent 链
│   └── v2_0/             # v2.0 动态调度
├── data/                 # 运行数据（gitignore）
│   ├── manuscript_data/
│   └── logs/
├── evaluation/           # 评测系统
│
└── docs/                 # 设计文档
    └── generate/         # PRD、架构等
```

## 开发指南

详见 [CLAUDE.md](CLAUDE.md) 和 [TODO.md](TODO.md)

## 文档导航

| 文档 | 说明 |
|------|------|
| [PRD](docs/generate/09_ManuScript_v3.0_PRD_重新设计.md) | v3.0 产品需求 |
| [技术架构](docs/design/ADR-11_ManuScript_v3.0_技术架构.md) | v3.0 技术架构 |
| [数据结构设计](docs/generate/11_ManuScript_v3.0_数据结构设计.md) | v3.0 数据结构 |

## 历史文档（v0.1–v2.0 记录）

| 文档 | 说明 |
|------|------|
| [架构版本规划](docs/generate/05_架构版本规划与实现路径.md) | v0.1-v2.0 详细设计 |
| [PRD](docs/generate/07_ManuScript_v2.0_PRD.md) | v2.0 产品需求 |
| [技术选型](docs/generate/06_技术选型与AI能力评估.md) | RAG/LLM/Agent 评估 |

## License

MIT
