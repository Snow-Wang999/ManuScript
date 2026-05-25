# 当前任务：v2.0 Orchestrator-Worker

> **状态**: ✅ 代码开发完成，模块测试通过
> **前置**: v1.0 稳定运行
> **目标**: 实现 Anthropic 风格的动态调度系统
> **更新日期**: 2025-01-18

---

## 版本目标

实现 Orchestrator-Worker 架构：
- Orchestrator 动态分配任务
- 根据章节复杂度选择 Worker
- 支持并行处理多个章节

---

## 架构设计

```
                    ┌─────────────────┐
                    │   Orchestrator  │
                    │   (中央调度器)   │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │   Simple    │     │   Complex   │     │   Review    │
  │   Worker    │     │   Worker    │     │   Worker    │
  │             │     │             │     │             │
  │ - 背景      │     │ - 方法      │     │ - 质量审核  │
  │ - 结论      │     │ - 实验      │     │ - 一致性检查│
  │ - 摘要      │     │ - 结果      │     │ - 引用验证  │
  └─────────────┘     └─────────────┘     └─────────────┘
```

---

## 已实现的功能

### 1. orchestrator.py ✅
**职责**: 中央调度器
```python
class Orchestrator:
    async def analyze_complexity(self, section: Section) -> str  # 复杂度分析
    async def create_tasks(self, outline: Outline) -> List[SectionTask]  # 任务创建
    async def dispatch(self, input: OrchestratorInput) -> OrchestratorOutput  # 并行调度
    async def aggregate_results(self, results: List[WorkerOutput]) -> OrchestratorOutput  # 结果聚合
```

### 2. workers/simple_worker.py ✅
**职责**: 处理简单章节（introduction, background, conclusion, abstract）
- 2个检索查询
- 基于分数的简单排序
- 流程: Query → Retrieve → Draft

### 3. workers/complex_worker.py ✅
**职责**: 处理复杂章节（method, experiment, results, discussion）
- 5个检索查询
- LLM 辅助排序
- 流程: Analyze → Query → Retrieve → Rank → Draft

### 4. workers/review_worker.py ✅
**职责**: 质量审核
- 引用验证（检查是否有对应检索内容）
- 幻觉检测（检查无来源的声明）
- 质量评估（0-100分）
- 自动修订（如质量分低于阈值）

### 5. workflow.py ✅
**职责**: LangGraph 工作流编排
- StateGraph 集成
- prepare → orchestrate → END 流程
- ManuScriptV2Workflow 封装类

### 6. main.py ✅
**职责**: Gradio 3列 UI
- 左栏: JSON 大纲输入
- 中栏: 执行日志
- 右栏: 生成内容 + 引用列表

---

## 并行处理设计

```python
async def dispatch(self, input: OrchestratorInput) -> OrchestratorOutput:
    """并行调度所有任务"""
    semaphore = asyncio.Semaphore(config.MAX_PARALLEL_WORKERS)

    async def process_with_semaphore(task: SectionTask) -> WorkerOutput:
        async with semaphore:
            worker = self._get_worker(task.complexity)
            return await worker.process(task.to_worker_input())

    results = await asyncio.gather(
        *[process_with_semaphore(task) for task in tasks],
        return_exceptions=True
    )
    return self.aggregate_results(results)
```

---

## 文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| v2_0/config.py | ✅ | LLM 提供商回退链 (Qwen→DeepSeek→OpenRouter) |
| v2_0/logger.py | ✅ | 日志配置 |
| v2_0/models.py | ✅ | Pydantic 数据模型 |
| v2_0/workers/base.py | ✅ | Worker 基类，共享检索/写作能力 |
| v2_0/workers/simple_worker.py | ✅ | 简单章节处理 |
| v2_0/workers/complex_worker.py | ✅ | 复杂章节处理 |
| v2_0/workers/review_worker.py | ✅ | 质量审核 |
| v2_0/workers/__init__.py | ✅ | 模块导出 |
| v2_0/orchestrator.py | ✅ | 中央调度器 |
| v2_0/workflow.py | ✅ | LangGraph 编排 |
| v2_0/main.py | ✅ | Gradio UI |
| v2_0/requirements.txt | ✅ | 依赖列表 |
| v2_0/README.md | ✅ | 文档 |

---

## 模块测试结果 (2025-01-18)

```bash
# 所有模块导入测试通过
✅ config.py - Config loaded: []  (无缺失配置)
✅ models.py - Models imported successfully
✅ workers/* - Workers imported successfully
✅ orchestrator.py - Orchestrator imported successfully
✅ workflow.py - Workflow imported successfully
```

---

## 验收标准

- [x] 所有模块代码完成
- [x] 模块导入测试通过
- [ ] Orchestrator 能正确分析大纲（待UI测试）
- [ ] 根据章节类型分配正确的 Worker（待UI测试）
- [ ] 支持 3 个章节并行处理（待UI测试）
- [ ] Review Worker 能发现质量问题（待UI测试）
- [ ] 对比 v1.0，处理速度提升 30%+（待性能测试）

---

## 下一步

1. 启动 Gradio UI 进行功能测试
   ```bash
   cd v2_0
   .venv/Scripts/python main.py
   ```
2. 使用示例大纲测试生成流程
3. 验证并行处理效果
4. 与 v1.0 进行性能对比

---

## 与 v1.0 的关键区别

| 特性 | v1.0 | v2.0 |
|------|------|------|
| 架构 | 固定 Agent 链 | 动态任务分配 |
| 并行 | 串行执行 | 支持并行 (MAX_PARALLEL_WORKERS=3) |
| 复杂度适配 | 统一处理 | 按复杂度选择 Worker |
| 全局审核 | 无 | Review Worker |
| Worker 类型 | 6个专用 Agent | 3种 Worker 类型 |
| 错误处理 | 链式失败 | 隔离任务失败 |

---

## 未来开发计划

### 1. 大纲生成优化（优先级：中）

**目标**：根据论文题目自动生成带写作提示的结构化大纲

**改动内容**：
1. `v2_0/models.py` - Section 模型新增 `hints` 字段
   ```python
   hints: List[str] = Field(default_factory=list, description="写作要点提示")
   ```
2. 集成大纲生成 Prompt（参考模板：`prompts/outline_generator.py`）
3. UI 大纲区显示 hints 提示

**功能说明**：
- 识别论文类型（实证/综述/理论/案例）
- 根据类型推荐合适的章节结构
- 每个章节附带 2-4 条写作要点提示

**参考文件**：
- `prompts/outline_generator.py` - Prompt 模板（待集成）
