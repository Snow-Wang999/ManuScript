# ManuScript v1.0 - Chain-of-Agents 版本

## 目标

实现 6 个专业 Agent 的协作链：
1. **Planner Agent** - 分析章节，规划写作策略
2. **Query Generator Agent** - 生成检索查询
3. **Retrieval Agent** - 执行文献检索
4. **Ranker Agent** - 对检索结果排序筛选
5. **Writer Agent** - 生成带引用的文本
6. **Verifier Agent** - 验证引用准确性

## 架构

```
用户输入 → Planner → Query Generator → Retrieval → Ranker → Writer → Verifier → 输出
              ↑                                                           │
              └─────────────────── 反馈循环 ──────────────────────────────┘
```

## 运行方式

```bash
pip install -r requirements.txt
python main.py
```

## 文件说明

| 文件 | 说明 |
|------|------|
| config.py | 配置管理 |
| logger.py | 日志配置 |
| agents/base.py | Agent 基类 |
| agents/planner.py | Planner Agent |
| agents/query_generator.py | Query Generator Agent |
| agents/retrieval.py | Retrieval Agent |
| agents/ranker.py | Ranker Agent |
| agents/writer.py | Writer Agent |
| agents/verifier.py | Verifier Agent |
| workflow.py | LangGraph 编排 |
| main.py | 三栏 UI |

## 开发顺序

按照 Vibe Coding 原则，一个 Agent 一个文件，每个测试通过后再继续：

1. base.py → 测试
2. planner.py → 测试
3. query_generator.py → 测试
4. retrieval.py → 测试
5. ranker.py → 测试
6. writer.py → 测试
7. verifier.py → 测试
8. workflow.py → 集成测试

## 前置依赖

- v0.2 验证通过（Query Generator、Prompt Chain 模式已确认）
