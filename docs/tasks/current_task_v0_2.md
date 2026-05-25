# 当前任务：v0.2 基础流程

> **状态**: 待开始
> **前置**: v0.1 验证通过
> **目标**: 引入 JSON 大纲和 Prompt Chain

---

## 版本目标

在 v0.1 基础上增加：
1. JSON 格式的大纲管理
2. Query Generator（从大纲生成检索查询）
3. 2步 Prompt Chain（检索 → 生成）
4. 引用格式化

---

## 数据流设计

```
用户输入大纲 (JSON)
       ↓
Query Generator
       ↓
List[Query]（每个章节 2-3 个查询）
       ↓
RAGFlow 检索
       ↓
List[Chunks]
       ↓
Step 1: 筛选相关 chunks
       ↓
Step 2: 生成带引用的段落
       ↓
Citation Formatter
       ↓
最终输出（草稿 + 引用列表）
```

---

## 要实现的功能

### 1. query_generator.py（已有骨架）
- 完善 `generate_queries()` 函数
- 支持根据章节类型调整 query 数量
- 支持关键词扩展

### 2. citation_formatter.py（新建）
- 将引用标记 [1], [2] 转换为完整引用格式
- 支持 APA/MLA 等格式（可选）
- 生成引用列表

### 3. pipeline.py（新建）
- 编排完整流程
- 2步 Prompt Chain：
  - Step 1: 根据 chunks 判断相关性
  - Step 2: 基于筛选后的 chunks 生成段落

### 4. main.py（新建）
- Gradio UI
- 支持大纲 JSON 输入
- 显示生成进度

---

## 文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| v0_2/config.py | [x] | 已完成 |
| v0_2/logger.py | [x] | 已完成 |
| v0_2/query_generator.py | [ ] | 需完善 |
| v0_2/citation_formatter.py | [ ] | 需创建 |
| v0_2/pipeline.py | [ ] | 需创建 |
| v0_2/main.py | [ ] | 需创建 |

---

## 验收标准

- [ ] 支持 JSON 格式大纲输入
- [ ] 每个章节生成 2-3 个检索查询
- [ ] 2步 Prompt Chain 正常工作
- [ ] 引用格式正确，有完整引用列表
- [ ] 对比 v0.1，引用准确率有提升

---

## 注意事项

1. **不要引入 Agent 概念** - 这是 v1.0 的事
2. **专注于数据流** - Prompt Chain 是核心
3. **复用 v0.1 的 RAGFlow/OpenAI 调用逻辑**
