# 当前任务：v1.0 Chain-of-Agents

> **状态**: ✅ 开发完成，测试通过
> **前置**: v0.2 验证通过
> **目标**: 实现 6 个专业 Agent 的协作链

---

## 版本目标

实现 Chain-of-Agents 架构：
1. **Planner Agent** - 分析章节，规划写作策略
2. **Query Generator Agent** - 生成检索查询
3. **Retrieval Agent** - 执行文献检索
4. **Ranker Agent** - 对检索结果排序筛选
5. **Writer Agent** - 生成带引用的文本
6. **Verifier Agent** - 验证引用准确性

---

## 架构设计

```
用户输入 → Planner → Query Generator → Retrieval → Ranker → Writer → Verifier → 输出
              ↑                                                           │
              └─────────────────── 反馈循环 ──────────────────────────────┘
```

---

## 文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| v1_0/config.py | ✅ 完成 | 配置管理 |
| v1_0/logger.py | ✅ 完成 | 日志模块 |
| v1_0/agents/base.py | ✅ 完成 | Agent 基类（AgentInput/AgentOutput/BaseAgent） |
| v1_0/agents/planner.py | ✅ 完成 | Planner Agent（分析大纲、生成写作计划） |
| v1_0/agents/query_generator.py | ✅ 完成 | Query Generator Agent（生成检索查询） |
| v1_0/agents/retrieval.py | ✅ 完成 | Retrieval Agent（RAGFlow API 调用） |
| v1_0/agents/ranker.py | ✅ 完成 | Ranker Agent（LLM 评估相关性排序） |
| v1_0/agents/writer.py | ✅ 完成 | Writer Agent（生成带引用的学术文本） |
| v1_0/agents/verifier.py | ✅ 完成 | Verifier Agent（验证引用准确性） |
| v1_0/workflow.py | ✅ 完成 | LangGraph 工作流编排 |
| v1_0/main.py | ✅ 完成 | Gradio 三栏 UI（输入/过程/输出） |

---

## 开发进度

### 已完成
- [x] base.py - Agent 基类定义
- [x] planner.py - 分析章节结构，生成写作计划
- [x] query_generator.py - 根据计划生成检索查询
- [x] retrieval.py - 执行 RAGFlow API 检索
- [x] ranker.py - LLM 评估相关性，筛选最相关片段
- [x] writer.py - 生成带引用的学术文本
- [x] verifier.py - 验证引用准确性，给出修改建议
- [x] workflow.py - LangGraph 编排 6 个 Agent
- [x] main.py - 三栏布局 Gradio UI
- [x] 安装依赖（langgraph, gradio, httpx, pydantic）
- [x] 单独测试每个 Agent
- [x] 集成测试工作流

### 待完成
- [ ] 验收测试（3个真实论文题目）
- [ ] 对比 v0.2 引用准确率

---

## 测试记录 (2026-01-18)

### 单独测试结果

| Agent | 状态 | 说明 |
|-------|------|------|
| Planner | ✅ 通过 | 为3个章节生成写作计划，预计文献数36 |
| QueryGenerator | ✅ 通过 | 为每个章节生成2-4个检索查询 |
| Retrieval | ✅ 通过 | RAGFlow API调用正常（无数据集返回0） |
| Ranker | ✅ 通过 | LLM评估相关性并筛选，3→2片段 |
| Writer | ✅ 通过 | 生成带引用的学术文本，431字，2个引用 |
| Verifier | ✅ 通过 | 验证引用准确性，识别1个问题并给出建议 |

### 集成测试结果

- **工作流**: Planner → QueryGenerator → Retrieval → Ranker → Writer → Verifier
- **执行状态**: ✅ 全流程通过
- **测试主题**: 深度学习在医学影像诊断中的应用
- **章节数**: 3个（引言、方法、结论）
- **生成字数**: 1486字
- **备注**: 需配置RAGFlow数据集ID才能获取真实文献

### 修复记录

1. `SectionPlan` 添加 `word_limit` 字段 - 修复 Writer Agent 字段缺失错误
2. `verifier.py` 修复Unicode字符打印问题（✓→[OK]，✗→[X]）

---

## 验收标准

- [x] 6 个 Agent 各自独立运行正常
- [x] LangGraph 工作流串联正确
- [ ] 三栏 UI 正常显示执行过程（待测试）
- [ ] 引用验证功能有效（需真实数据集验证）
- [ ] 引用准确率相比 v0.2 有提升（需真实数据集验证）

---

## 运行方式

```bash
cd v1_0
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 测试单个 Agent
python -m agents.planner
python -m agents.query_generator
python -m agents.retrieval
python -m agents.ranker
python -m agents.writer
python -m agents.verifier

# 测试工作流
python workflow.py

# 启动 UI (端口 7862)
python main.py
```

---

## 技术栈

- **Agent 框架**: LangGraph v1.0+
- **数据模型**: Pydantic v2
- **HTTP 客户端**: httpx (异步)
- **前端**: Gradio
- **LLM**: OpenAI API (gpt-4o-mini)
- **检索**: RAGFlow API

---

## Agent 接口设计

### 1. Planner Agent
```python
Input: PlannerInput { paper_topic, sections: List[SectionInfo] }
Output: PlannerOutput { section_plans: List[SectionPlan], total_estimated_sources }
```

### 2. Query Generator Agent
```python
Input: QueryGeneratorInput { paper_topic, section_plans }
Output: QueryGeneratorOutput { queries: List[SearchQuery], total_queries }
```

### 3. Retrieval Agent
```python
Input: RetrievalInput { queries, dataset_ids, top_k }
Output: RetrievalOutput { chunks: List[DocumentChunk], total_chunks }
```

### 4. Ranker Agent
```python
Input: RankerInput { chunks, section_plans, max_chunks_per_section }
Output: RankerOutput { ranked_chunks: Dict[str, List[RankedChunk]] }
```

### 5. Writer Agent
```python
Input: WriterInput { paper_topic, section_plans, ranked_chunks }
Output: WriterOutput { drafts: List[SectionDraft], all_citations, total_words }
```

### 6. Verifier Agent
```python
Input: VerifierInput { drafts, source_chunks }
Output: VerifierOutput { verifications, overall_accuracy, needs_revision }
```

---

## 注意事项

1. **一个 Agent 一个文件** - 便于单独测试
2. **先测试再集成** - 每个 Agent 测试通过后再继续
3. **日志详细** - 方便调试 Agent 协作问题
4. **引用准确性是最高优先级**
