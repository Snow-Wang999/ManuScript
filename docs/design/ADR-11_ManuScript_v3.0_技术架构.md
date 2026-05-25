# ManuScript v3.0 技术架构（MVP）

> 目标：在本地可控的前提下，完成“可追溯检索 + 笔记检索”的可信闭环。

## 1. 架构范围（MVP）
- 本地 PDF 导入与解析
- Markdown 结构化存储（正文+笔记）
- 全文检索 + 段落级溯源
- 对话式检索 + 会话摘要
- 本地优先，云端可选

## 2. 总体架构（分层）

```
UI(Gradio/React)
  └─ API/Orchestrator (FastAPI)
       ├─ Router/Intent
       ├─ Tools
       │   ├─ Search (ripgrep + index.json)
       │   ├─ Notes (read/write)
       │   ├─ Summarizer (LLM)
       │   ├─ Query Rewrite (optional)
       │   ├─ Export (zip)
       │   └─ Hooks (format/sanitize)
       ├─ Parser Pipeline
       │   ├─ PDF Extract (pdfplumber / PyMuPDF)
       │   ├─ Structure (heading/paragraph)
       │   └─ Index Builder (index.json)
       └─ Storage (local)
           ├─ papers/{paper_id}/
           │   ├─ metadata.json
           │   ├─ content.md
           │   ├─ notes.md
           │   └─ index.json
           └─ memory/
               ├─ sessions/
               ├─ summaries/
               ├─ project_state.json
               └─ user_preferences.json
```

## 3. 关键组件说明
### 3.1 Router/Intent
- 输入：用户消息 + 当前会话状态
- 输出：路由到工具（检索/笔记/摘要/导出/闲聊）
- MVP 使用简单规则 + 轻量 LLM 判断

### 3.2 Parser Pipeline（本地）
- 目标：得到“可检索、可溯源”的段落结构
- 最低标准：章节标题、段落切分、引用标记
- 表格/公式允许降级为纯文本或占位

### 3.3 Search（检索）
- MVP：`ripgrep` + `index.json`
- 输入：关键词/自然语言（可选 query rewrite）
- 输出：命中段落 + 段落 ID + 位置偏移

### 3.4 Memory（会话与长期记忆）
- 会话历史：仅在会话内使用
- 会话摘要：跨会话可引用
- 项目状态：全局共享（大纲/阶段）

## 4. RAG 的定位
- MVP 不做向量检索
- 当前形态为“RAG-lite”：本地检索 + LLM 总结/对话
- 向量检索作为 P2 增强（语义召回）

## 5. 检索技术路线
### P0
- ripgrep 全文检索 + 段落索引

### P1
- SQLite FTS5 倒排索引（性能提升）

### P2
- 向量索引 + 全文检索融合排序

## 6. 代理/工具调用设计
- MVP 采用“单主 Agent + 工具路由”
- 不做多 Agent 编排（减少复杂度）
- 工具调用清晰可追踪（面试可解释）

## 7. 本地优先与隐私
- 原始 PDF、Markdown、笔记均本地存储
- 云端调用需显式开关
- 可选脱敏（P1）

## 8. 参考项目的可借鉴点
- open_deep_research：工具调用流程与任务规划思路
- moltbot：本地记忆与摘要持久化机制
- 但不直接复制，保持 MVP 简洁

## 9. 决策结论（简版）
- 本地解析为主，LaTeX 作为增强
- ripgrep 为主检索，向量索引作为未来升级
- 以可追溯为第一优先级
