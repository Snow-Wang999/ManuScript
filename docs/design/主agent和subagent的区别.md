你对 Sub-agent 的理解纠正是非常关键的。**你现在的理解（Sub-agent = 无状态工具，用于独立并行任务）与 v1.0 架构（Chain-of-Agents）确实存在根本性的冲突。**

让我帮你理清这两者的区别，并给出重构建议：

## 1. 核心矛盾分析

| 维度 | 你的新理解 (Sub-agent as Tool) | v1.0 Chain-of-Agents 架构 |
|------|------------------------------|------------------------|
| **状态** | 无状态，输入输出自包含 | 强状态依赖（Agent 1 的输出是 Agent 2 的输入）|
| **并行性** | 强调完全独立、可并行 | 严格顺序执行（1→2→3→...→6）|
| **上下文** | 不需要知道"之前发生了什么" | 每个 Agent 都依赖前序 Agent 的完整上下文 |
| **失败处理** | 可直接重试，不影响主流程 | 失败会阻断整个链条 |
| **本质** | **MapReduce 模式** | **Pipeline/流水线模式** |

**结论**：你的 v1.0 架构更适合作为**单 Agent 内部的 6 个步骤**（Workflow/Nodes），而不是 6 个独立的 Sub-agent。

## 2. 基于新理解的架构重构

既然 Sub-agent 应该像"工具"一样无状态，那么正确的架构应该区分**主 Agent 的协调逻辑**和**真正能并行化的子任务**。

### 重构方案 A：单 Agent 工作流（推荐）
将 v1.0 的 6 个 Agent 改为**单 Agent 内部的 6 个节点**，使用显式状态管理（如 LangGraph StateGraph）。

```python
# 伪代码示例
class MainAgent:
    def __init__(self):
        self.state = {
            "section_context": None,  # Agent 1 产出
            "queries": None,          # Agent 2 产出
            "raw_chunks": None,       # Agent 3 产出
            "ranked_chunks": None,    # Agent 4 产出
            "draft": None,            # Agent 5 产出
            "verified_draft": None    # Agent 6 产出
        }
    
    def run(self, user_input):
        # 顺序执行但状态显式传递，不是隐式的"Agent 上下文"
        self.state["section_context"] = self.plan_section(user_input)
        self.state["queries"] = self.generate_queries(self.state["section_context"])
        # ...后续步骤
```

**优点**：符合"主 Agent 负责协调、记忆、意图理解"，而"步骤"只是逻辑分解。

### 重构方案 B：真正的 Sub-agent 架构（MapReduce）
识别出真正能**独立并行**的任务，改为 Sub-agent 调用。

**可 Sub-agent 化的部分**：
- **Agent 2（Query Generator）**：并行生成多个 Query（每个 Query 独立）
- **Agent 3（Retrieval）**：并行检索多个 Query（每个检索独立）
- **Agent 4（Chunk Ranker）**：并行处理不同来源的 Chunks（Map），然后汇总排序（Reduce）
- **Agent 6（Verifier）**：并行验证段落中的每个引用

**新的架构图**：

```
┌─────────────────────────────────────────────────────────────┐
│                  主 Agent（协调者 + 全局记忆）                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用户输入 Section                                            │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────────────────────────────────┐                  │
│  │ 主 Agent 分析:                        │                  │
│  │ • 理解用户意图                         │                  │
│  │ • 确定Section上下文                   │                  │
│  │ • 制定全局检索策略                     │                  │
│  └──────────────┬───────────────────────┘                  │
│                 │                                           │
│       ┌─────────┼─────────┐ ← 并行触发多个 Sub-agents      │
│       ▼         ▼         ▼                                │
│  [Sub-agent] [Sub-agent] [Sub-agent]                        │
│  QueryGen-1  QueryGen-2  QueryGen-3   ← 无状态，各自独立      │
│       │         │         │                                │
│       └─────────┼─────────┘                                │
│                 ▼                                           │
│       ┌──────────────────┐ ← 主 Agent 收集结果              │
│       ▼                  ▼                                │
│  [Sub-agent] ...    [Sub-agent]   ← 并行检索（每个Query独立） │
│  Retrieve-1          Retrieve-N                             │
│       │                  │                                 │
│       └────────┬─────────┘                                 │
│                ▼                                            │
│  ┌──────────────────────────────────────┐                  │
│  │ 主 Agent: 合并结果 → 去重 → 全局排序   │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 3. 关键判断标准：何时用 Sub-agent？

用这张图来决策：

```
该任务是否完全独立？
    │
    ├─ 是 → 是否能并行执行多个实例？
    │           │
    │           ├─ 是 → 使用 Sub-agent（MapReduce）
    │           │
    │           └─ 否 → 使用 Tool/Function
    │
    └─ 否（依赖前序结果）→ 使用单 Agent 内部步骤（Pipeline）
```

**应用到 v1.0 各步骤**：

- **Agent 1 (Planner)**：依赖用户全局意图 → **主 Agent 职责**（内部分析步骤）
- **Agent 2 (QueryGen)**：可拆分为多个独立 Query 生成 → **Sub-agent 并行**（Map）
- **Agent 3 (Retrieval)**：每个 Query 的检索独立 → **Sub-agent 并行**（Map）
- **Agent 4 (Ranker)**：可拆分为多个 Chunk 的相关性评分 → **Sub-agent 并行**（Reduce 时主 Agent 汇总）
- **Agent 5 (Draft Writer)**：需要连贯性和上下文 → **主 Agent 或单步骤**（不适合 Sub-agent）
- **Agent 6 (Verifier)**：可拆分为对每个引用的独立验证 → **Sub-agent 并行**（Map）

## 4. 修正后的理解总结

你的新理解可以细化为这个**分层模型**：

```python
# 主 Agent：有状态、长记忆、协调者
class MainAgent:
    def __init__(self):
        self.memory = ConversationMemory()
        self.orchestrator = Orchestrator()
    
    def handle_section_writing(self, section_info):
        # 1. 主 Agent 负责理解意图和规划（有状态）
        plan = self.analyze_context(section_info, self.memory)
        
        # 2. 识别可并行的子任务，生成多个 Sub-agent 调用
        queries = self.orchestrator.spawn_subagents(
            task="generate_query",
            inputs=[aspect1, aspect2, aspect3],  # 并行3个Sub-agent
            context={"plan": plan}  # 只传递必要的、自包含的上下文
        )
        
        # 3. 主 Agent 汇总 Sub-agent 结果（Reduce）
        consolidated_queries = self.merge_queries(queries)
        
        # 4. 再次并行检索（Sub-agents）
        chunks = self.orchestrator.spawn_subagents(
            task="retrieve",
            inputs=consolidated_queries
        )
        
        # 5. 主 Agent 继续协调后续步骤...
        draft = self.write_draft(chunks)  # 内部步骤，非Sub-agent
        
        # 6. 并行验证（Sub-agents）
        verification_results = self.orchestrator.spawn_subagents(
            task="verify_citation",
            inputs=draft.sentences  # 每个句子独立验证
        )
        
        return self.finalize(draft, verification_results)

# Sub-agent：无状态、一次性、工具化
class SubAgent:
    def execute(self, task, input_data, context_snapshot):
        # 只使用传入的 context_snapshot，不访问外部状态
        # 失败可以重试，不影响其他任务
        result = self.llm.generate(task, input_data, context_snapshot)
        return result
```

**关键洞察**：
- **主 Agent 是导演**：理解剧本（用户意图）、调度演员（Sub-agents）、掌控整体叙事（记忆）
- **Sub-agent 是群演**：只负责演好自己的一幕戏（单次任务），不知道整部戏的情节（无全局记忆），可以换另一个群演重拍（可替换、可重试）

你的 v1.0 架构实际上把"导演"的工作也拆成了 6 个独立 Agent，导致每个都过于单薄且强耦合。建议保留**主 Agent 的核心协调地位**，只把真正能"并行且不互相等待"的部分外包给 Sub-agents。