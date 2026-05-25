# ManuScript 开发计划

> **创建日期**: 2026-01-18
> **状态**: 待确认

---

## 1. 项目结构设计（待确认）

```
ManuScript/
├── README.md                      # 项目总说明（技术栈、目录结构、开发规范）
├── LICENSE
├── .gitignore
├── .env.example                   # API Key 等配置示例
│
├── # ===== Vibe Coding 核心文件 =====
├── CLAUDE.md                      # 🆕 AI 规则文件（技术栈、代码风格、开发规范）
├── TODO.md                        # 本文件（任务清单）
├── current_task.md                # 🆕 当前任务切片（每次只放当前版本内容）
├── Makefile                       # 常用命令
│
├── docs/                          # 文档（已有）
│   ├── generate/
│   │   ├── 07_ManuScript_v2.0_PRD.md
│   │   ├── 05_架构版本规划与实现路径.md
│   │   └── ...
│   └── ...
│
├── v0_1/                          # ===== v0.1 最小原型 =====
│   ├── README.md                  # 版本说明
│   ├── requirements.txt           # 独立依赖
│   ├── prototype.py               # 🔄 核心脚本（先无 UI）
│   ├── main.py                    # 入口（Gradio UI，后加）
│   ├── config.py                  # 配置
│   ├── logger.py                  # 日志
│   └── tests/
│       └── test_prototype.py
│
├── v0_2/                          # ===== v0.2 基础流程 =====
│   ├── README.md
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── pipeline.py
│   ├── query_generator.py
│   ├── citation_formatter.py
│   ├── logger.py
│   └── tests/
│
├── v1_0/                          # ===== v1.0 Agent 链 =====
│   ├── README.md
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── planner.py             # 一个 Agent 一个文件
│   │   ├── query_generator.py
│   │   ├── retrieval.py
│   │   ├── ranker.py
│   │   ├── writer.py
│   │   └── verifier.py
│   ├── workflow.py                # 🔄 Agent 编排（用 LangGraph）
│   ├── logger.py
│   └── tests/
│
├── v2_0/                          # ===== v2.0 动态调度 =====
│   ├── README.md
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── orchestrator.py
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── simple_worker.py
│   │   ├── complex_worker.py
│   │   └── review_worker.py
│   ├── agents/                    # 复用的 Agent 组件
│   ├── logger.py
│   └── tests/
│
├── evaluation/                    # ===== 跨版本评测 =====
│   ├── __init__.py
│   ├── test_cases.yaml            # 统一测试用例（3个真实论文题目）
│   ├── metrics.py                 # 评测指标
│   ├── compare.py                 # 对比脚本
│   └── results/                   # 评测结果（.gitignore）
│
└── logs/                          # 日志目录（.gitignore）
    ├── v0_1/
    ├── v0_2/
    ├── v1_0/
    └── v2_0/
```

---

## 2. 设计决策说明

### 2.1 为什么版本完全独立？

| 优点 | 说明 |
|------|------|
| **开发隔离** | Claude Code 可同时编辑不同版本，无冲突 |
| **独立运行** | 每个版本可单独启动、测试 |
| **依赖隔离** | 版本间可以用不同的库版本 |
| **易于理解** | 每个版本是完整的小项目 |

| 缺点 | 缓解方案 |
|------|---------|
| 代码重复 | 接受适度重复，保持独立性 |
| 维护成本 | 只维护当前开发的版本 |

### 2.2 共享 vs 独立的权衡

```
完全共享 ◄─────────────────────► 完全独立
   │                                  │
   │  修改共享代码影响所有版本        │  代码重复但互不影响
   │  适合：稳定的基础设施            │  适合：实验性项目
   │                                  │
   └──────────── 当前选择 ────────────┘
                    ↓
              偏向独立，仅评测共享
```

### 2.3 日志设计

```
每个版本独立日志配置：
- 文件：logs/{version}/app.log
- 格式：{timestamp} | {level} | {version} | {message}
- 级别：DEBUG/INFO/WARNING/ERROR
```

---

## 3. 开发任务清单

> **Vibe Coding 原则**: 一次只做一个版本，先跑通逻辑再做 UI

### Phase 0: 项目骨架 + Vibe Coding 基础设施
- [x] 确认项目结构
- [x] 创建目录结构
- [x] 创建 .gitignore
- [x] 创建 .env.example
- [x] **创建 CLAUDE.md**（AI 规则文件，从技术选型文档提取）
- [x] **创建 current_task.md**（初始内容：v0.1 任务）
- [ ] 创建 Makefile
- [ ] 创建 README.md
- [x] **准备 3 个真实论文题目作为测试用例**

### Phase 1: v0.1 最小原型

> **目标**: 验证 RAGFlow API 连通性 + OpenAI 单次调用
> **状态**: ✅ 完成 (2026-01-18)
> **Vibe Coding**: 先写脚本，后加 UI

#### Step 1.1: 核心逻辑（无 UI）
- [x] 创建 v0_1/README.md
- [x] 创建 v0_1/requirements.txt
- [x] 实现 v0_1/config.py
- [x] 实现 v0_1/logger.py（详细日志，方便调试）
- [x] **实现 v0_1/prototype.py**（核心脚本，直接打印结果）
  - 接收固定的 topic 和 section_title
  - 调用 RAGFlow API 检索
  - 调用 OpenAI 生成草稿
  - 在 main 函数打印结果
- [x] 用 3 个测试用例验证

#### Step 1.2: 添加 UI
- [x] 实现 v0_1/main.py（Gradio UI：3 输入框 + 1 输出框）
- [x] 编写 v0_1/tests/test_prototype.py
- [x] 验收：配置有效 API Key 后 3 秒内显示文献列表

### Phase 2: v0.2 基础流程

> **目标**: 引入 JSON 大纲和 Prompt Chain
> **状态**: ⏭️ 跳过（被 v1.0 取代）
> **Vibe Coding**: 只关注数据流，不优化 UI

- [x] 更新 current_task.md 为 v0.2 内容
- [x] 创建 v0_2 基础文件
- [ ] ~~实现 Query 生成器（Outline JSON -> List[Query]）~~ (v1.0 已实现)
- [ ] ~~实现 2步 Prompt Chain（List[Chunks] -> Draft Text）~~ (v1.0 已实现)
- [ ] ~~实现引用格式化~~ (v1.0 已实现)
- [ ] ~~实现大纲管理（JSON）~~ (v1.0 已实现)
- [ ] ~~用 3 个测试用例验证~~
- [ ] ~~对比 v0.1 的引用准确率~~

### Phase 3: v1.0 Agent 链

> **目标**: Chain-of-Agents 架构
> **状态**: ✅ 完成 (2026-01-18)
> **Vibe Coding**: 一个 Agent 一个文件，一次只写一个

- [x] 更新 current_task.md 为 v1.0 内容
- [x] 创建 v1_0 基础文件
- [x] 实现 agents/base.py（BaseAgent 抽象类）
- [x] **逐个实现 Agent**（每个都单独测试后再继续）:
  - [x] agents/planner.py + 测试
  - [x] agents/query_generator.py + 测试
  - [x] agents/retrieval.py + 测试
  - [x] agents/ranker.py + 测试
  - [x] agents/writer.py + 测试
  - [x] agents/verifier.py + 测试
- [x] 实现 workflow.py（用 LangGraph 编排）
- [x] 实现三栏 UI
- [ ] 用 3 个测试用例验证（待真实数据集）
- [ ] 对比 v0.2 的各项指标

### Phase 4: v2.0 动态调度

> **前提**: v1.0 稳定运行后再开始
> **状态**: 🔵 代码完成，待功能测试
> **Vibe Coding**: 在 v1.0 稳定前，不要把 v2.0 文档喂给 AI

- [x] 更新 current_task.md 为 v2.0 内容
- [x] 创建 v2_0 基础文件
- [x] 实现 Orchestrator
- [x] 实现 3 种 Worker (SimpleWorker, ComplexWorker, ReviewWorker)
- [x] 实现并行处理
- [x] 实现 workflow.py (LangGraph 编排)
- [x] 实现 main.py (Gradio 3列 UI)
- [ ] 安装依赖并测试
- [ ] 用 3 个测试用例验证
- [ ] 对比所有版本的指标

### Phase 5: 评测系统
- [ ] 设计评测指标（检索相关性、引用准确率、生成延迟）
- [ ] 创建 evaluation/test_cases.yaml（3 个真实论文题目）
- [ ] 实现对比脚本
- [ ] 生成评测报告

---

## 4. 待确认问题

### Q1: 项目结构是否 OK？
- [x] 是，开始创建
- [ ] 需要调整：_______________

### Q2: AI 规则文件命名？
- [x] CLAUDE.md（Claude Code 推荐）
- [ ] .cursorrules（Cursor 推荐）
- [ ] 两者都创建（内容相同）

### Q3: 是否需要 Docker？
- [ ] 是，每个版本一个 Dockerfile
- [x] 否，先用本地 Python 环境

### Q4: 前端选择？
- [x] Gradio（简单，MVP 优先）
- [ ] Streamlit
- [ ] React（后期考虑）

### Q5: 评测指标优先级？
- [x] 引用准确率（最重要）
- [x] 检索相关性
- [ ] 生成延迟
- [ ] 其他：_______________

### Q6: 3 个测试用例的论文题目？
> 暂未确定，可在 v0.1 开发时再定
- [ ] 待确定
- [ ] 待确定
- [ ] 待确定

---

## 5. Vibe Coding 核心文件说明

### 5.1 CLAUDE.md / .cursorrules

**作用**: 告诉 AI 项目的技术规范和开发规则

**内容模板**:
```markdown
# ManuScript 开发规则

## 技术栈
- Python 3.10+
- FastAPI（后端）
- Gradio（前端 UI）
- RAGFlow API（文献检索）
- OpenAI API（文本生成）
- Pydantic v2（数据模型）
- SQLite（本地存储）

## 代码风格
- 使用 async/await 异步编程
- 函数名使用 snake_case
- 类名使用 PascalCase
- 日志使用 logger.py

## 开发规范
- 每个版本独立目录，互不影响
- 先写脚本验证逻辑，再加 UI
- 每次只开发一个版本
```

### 5.2 current_task.md

**作用**: 上下文切片，每次只放当前版本的任务

**使用方法**:
1. 开发 v0.1 时，只放 v0.1 的内容
2. 开发 v0.2 时，替换为 v0.2 的内容
3. 避免把所有版本文档同时喂给 AI

**示例内容**:
```markdown
# 当前任务：v0.1 最小原型

## 目标
验证 RAGFlow API 连通性 + OpenAI 单次调用

## 要实现的功能
1. 接收 topic 和 section_title
2. 调用 RAGFlow 检索相关文献
3. 调用 OpenAI 生成草稿
4. 打印结果

## 验收标准
- 配置有效 API Key 后能正常运行
- 检索结果包含相关文献
- 生成的草稿包含引用标记
```

### 5.3 TODO.md

**作用**: 任务清单，跟踪进度

**更新时机**:
- 完成一个任务后立即打勾
- 发现新问题时添加任务
- 版本切换时回顾进度

---

## 6. 参考文档

### 6.1 核心设计参考（必读）

| 文档 | 路径 | 用途 |
|------|------|------|
| **架构版本规划** | [05_架构版本规划与实现路径.md](docs/generate/05_架构版本规划与实现路径.md) | v0.1-v3.0 架构设计、代码结构、实现清单 |
| **PRD 文档** | [07_ManuScript_v2.0_PRD.md](docs/generate/07_ManuScript_v2.0_PRD.md) | 完整产品需求、功能规格、数据模型 |
| **架构迭代记录** | [01_架构迭代实践记录.md](docs/generate/01_架构迭代实践记录.md) | 迭代模板、问题记录、升级决策模板 |

### 6.2 技术选型参考

| 文档 | 路径 | 用途 |
|------|------|------|
| **技术选型评估** | [06_技术选型与AI能力评估.md](docs/generate/06_技术选型与AI能力评估.md) | RAG/LLM/Agent 技术评估、幻觉控制策略 |
| **架构选型分析** | [ManuScript v2.0 架构选型与项目定位.md](docs/ManuScript%20v2.0%20架构选型与项目定位.md) | Material Assembly vs Deep Research、Chain-of-Agents 详细设计 |

### 6.3 项目背景参考

| 文档 | 路径 | 用途 |
|------|------|------|
| **项目概览** | [00_项目概览与求职说明.md](docs/generate/00_项目概览与求职说明.md) | 项目定位、能力展示、文档导航 |
| **用户调研** | [02_用户调研与痛点洞察.md](docs/generate/02_用户调研与痛点洞察.md) | 用户画像、痛点分析 |
| **竞品分析** | [03_竞品分析与市场定位.md](docs/generate/03_竞品分析与市场定位.md) | 竞品对比、差异化定位 |

### 6.4 外部参考

| 文档 | 路径 | 用途 |
|------|------|------|
| **Anthropic 多智能体** | [How we built our multi-agent research system.md](docs/How%20we%20built%20our%20multi-agent%20research%20system.md) | Orchestrator-Worker 模式参考 |

---

> **下一步**: 请确认上述结构和计划，我将开始创建项目骨架。
