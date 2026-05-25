# RAGFlow 表格处理限制与解决方案

> 记录 ManuScript 项目中 RAGFlow 表格解析的已知限制和应对策略

---

## 问题描述

### 表格解析现状

在使用 RAGFlow 处理学术论文 PDF 时，表格解析效果不理想：

| 解析器 | 表格处理效果 | 问题 |
|-------|-------------|------|
| DeepDOC | 较差 | 宽表格列对齐混乱，内容错位 |
| VLM (qwen3-vl-plus) | 较差 | 实验性功能，复杂表格解析不稳定 |
| Docling | 待测试 | 可能相对较好 |

### 典型问题示例

原始表格（学术论文中的系统对比表）：
```
Table 2. Environmental Interaction Capabilities of Deep Research Systems
System | Web Interaction | API Integration | Document Processing | GUI Navigation
-------|-----------------|-----------------|---------------------|----------------
Nanobrowser | Headless browsing... | REST API... | Basic HTML... | Not implemented
```

RAGFlow 解析结果：
```
Table 4. Knowledge Synthesis Capabilities...
System	Source Evaluation Mechanisms	Output Structuring	UserInteractionFeatures
Template-l
,recencyfilterir	emicformat,headingorganization	citation	vigation
grapeot/dep.rese	search_aent 263]Evidenceclassicatio	sentatic...
```

**问题**：列对齐完全错乱，内容无法理解。

---

## 重要性分析

### 表格在论文写作中的占比

| 内容类型 | 重要性占比 | 说明 |
|---------|-----------|------|
| **正文段落** | 70-80% | 核心论述、方法描述、结果分析 |
| **表格** | 10-15% | 数据对比、参数配置 |
| **图片** | 10-15% | 架构图、流程图、结果可视化 |

### 关键认知

1. **表格信息通常有正文对应**：作者在正文中会描述表格的关键内容
2. **检索正文可覆盖大部分需求**：论文写作时，正文检索往往能找到表格相关信息
3. **表格主要用于精确数据引用**：如需引用具体数值，可手动补充

---

## 解决方案

### 分层处理策略

```
┌─────────────────────────────────────────────────────────┐
│ 第一层（当前阶段）                                        │
│ - 忽略表格解析问题                                        │
│ - 依赖正文段落检索                                        │
│ - 接受已知限制，先跑通主流程                               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 第二层（按需补充）                                        │
│ - 遇到关键表格时，手动转 Markdown                         │
│ - 创建 tables.md 文件上传到知识库                         │
│ - 不改动 v2.0 架构代码                                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 第三层（后期优化）                                        │
│ - 评估 Marker/Docling 等工具                             │
│ - 考虑 PDF 预处理管道                                    │
│ - 架构稳定后再做大改动                                    │
└─────────────────────────────────────────────────────────┘
```

### 第一层：当前做法

直接使用 RAGFlow，配置如下：
- **Built-in 模式**：Paper
- **PDF parser**：DeepDOC（比 VLM 更稳定）
- **其他参数**：保持默认

接受表格解析不完美的现实，优先保证正文检索质量。

### 第二层：手动补充关键表格

当遇到必须引用的重要表格时：

1. **手动转换为 Markdown**：
```markdown
## Table 2: Deep Research Systems Comparison

### Nanobrowser [184]
- Web Interaction: Headless browsing, JavaScript execution, dynamic content rendering
- API Integration: REST API connectors
- Document Processing: Basic HTML parsing
- GUI Navigation: Not implemented

### AutoGLM [330]
- Web Interaction: Full browser automation, form interaction
- API Integration: RESTful and GraphQL support
- Document Processing: PDF, Office formats, JSON
- GUI Navigation: Element identification, click/input automation
```

2. **上传到 RAGFlow**：
   - 创建 `supplementary_tables.md` 文件
   - 上传到同一个知识库
   - 使用 General 模式解析

3. **优势**：
   - 不修改任何代码
   - 表格内容可被准确检索
   - 按需添加，工作量可控

### 第三层：后期优化方向

架构稳定后可考虑的优化：

| 方案 | 描述 | 复杂度 |
|-----|------|-------|
| **Marker 预处理** | 用 Marker 将 PDF 转 Markdown 后再上传 | 中 |
| **混合知识库** | 正文用 Paper 模式，表格用 Table 模式 | 中 |
| **多模态 RAG** | 支持图片存储和检索 | 高 |

---

## RAGFlow 配置建议

### 知识库设置

```yaml
# Ingestion Pipeline
Parse Type: Built-in
Built-in: Paper
PDF parser: DeepDOC  # 不用 VLM，更稳定

# 自动增强
Auto-keyword: 5
Auto-question: 0-1  # 可以关闭，节省成本

# RAPTOR（可选）
Generation Scope: Single File
Max token: 512
Threshold: 0.2
```

### 检索设置

```yaml
Similarity threshold: 0.2-0.3
Vector similarity weight: 0.3-0.5  # 平衡语义和关键词
Rerank model: gte-rerank
Top-K: 50-100  # 不需要太大
```

---

## 已知限制记录

| 限制 | 影响 | 缓解措施 |
|-----|------|---------|
| 宽表格解析错乱 | 无法检索表格数据 | 手动转 Markdown |
| 小字体表格 OCR 不准 | 内容丢失或错误 | 依赖正文描述 |
| 表格返回纯文本 | 无法获取原图 | 接受限制 |
| VLM 解析不稳定 | 实验性功能 | 使用 DeepDOC |

---

## 总结

**核心原则**：先跑通主流程，表格作为已知限制，按需手动补充。

**当前状态**：
- [x] 识别问题
- [x] 制定分层方案
- [ ] 主流程开发验证
- [ ] 按需补充关键表格
- [ ] 后期架构优化（可选）

---

*文档创建时间：2025-01*
*RAGFlow 版本：v0.22.1*
