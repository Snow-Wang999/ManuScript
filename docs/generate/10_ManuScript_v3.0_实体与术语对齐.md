# ManuScript v3.0 实体与术语对齐（V0.1）

> 目的：在进入数据结构/接口/模块设计前，统一“对象是谁、边界在哪、如何命名”。
> 适用范围：MVP（本地 PDF 解析 + Markdown 存储 + ripgrep 检索 + 会话摘要/笔记）。

---

## 0. 范围与原则
- **范围**：仅覆盖 MVP 必需实体；P1/P2 以注记形式标明。
- **原则**：术语即契约，避免同义词混用；实体命名尽量与存储文件/接口字段一致。

---

## 1. 核心实体清单（MVP）

### 1.1 Paper（论文）
- **定义**：单篇论文的逻辑载体，包含元数据、正文、笔记、索引。
- **边界**：一篇 PDF 或 arXiv 论文对应一个 Paper。
- **主要文件**：`papers/{paper_id}/metadata.json` + `content.md` + `notes.md` + `index.json`
- **关键字段**：`paper_id`、`title`、`authors`、`year`、`source`、`created_at`、`parsed_at`。

### 1.2 Document（文档/正文）
- **定义**：论文的结构化正文（Markdown）。
- **边界**：仅指 `content.md`，不包含笔记。
- **职责**：承载段落 ID 与章节结构，供检索/溯源定位。

### 1.3 Paragraph（段落）
- **定义**：可检索、可溯源的最小内容单元。
- **边界**：从 `content.md` 中解析而来；笔记段落由 `notes.md` 提供。
- **ID 规范**：正文 `[@id:xxx]`，笔记 `[@note:note_yyy]`。
- **定位方式**：`index.json` 中的 `offset/length/type`。

### 1.4 Note（笔记）
- **定义**：用户在阅读/检索过程中写入的内容。
- **边界**：存放于 `notes.md`，不与正文混写。
- **ID 规范**：时间戳 ID（如 `note_YYYYMMDD_HHMMSS`）。
- **可检索性**：与正文一样参与全文检索，但标识为 `type: note`。

### 1.5 Index（段落索引）
- **定义**：段落 ID → 位置/类型的映射表。
- **文件**：`index.json`（每篇论文一份）。
- **用途**：溯源定位与高亮。

### 1.6 Session（会话）
- **定义**：一次对话生命周期内的状态与历史。
- **文件**：`memory/sessions/{session_id}.json`
- **边界**：会话历史仅在会话内使用；跨会话引用需要 Summary。

### 1.7 Summary（会话摘要）
- **定义**：会话历史的压缩版本，跨会话可引用。
- **文件**：`memory/summaries/{session_id}_summary.json`

### 1.8 ProjectState（项目状态）
- **定义**：全局共享的进度与全局上下文（如研究主题、阶段）。
- **文件**：`memory/project_state.json`

### 1.9 UserPreferences（用户偏好）
- **定义**：与用户相关的静态偏好与配置（如默认本地/云端模式）。
- **文件**：`memory/user_preferences.json`

---

## 2. 术语与命名对齐

| 术语 | 统一定义 | 说明/禁止混用 |
|------|----------|---------------|
| 论文（Paper） | 逻辑实体，含元数据+正文+笔记+索引 | 不要用“文档”指代 Paper |
| 文档/正文（Document） | `content.md` 内容 | 不含 notes |
| 段落（Paragraph） | 可检索最小单元 | 不与“chunk”混用（MVP 用 Paragraph） |
| 笔记（Note） | 用户写入内容 | 笔记不写入 `content.md` |
| 索引（Index） | 段落定位映射表 | 指 `index.json` |
| 溯源（Traceability） | 结果可定位到段落 | 以段落 ID 为主 |
| 会话（Session） | 单次对话生命周期 | 不是“项目” |
| 会话摘要（Summary） | 压缩对话历史 | 可跨会话引用 |
| 记忆（Memory） | 会话历史 + 摘要 + 项目状态 | 不是向量库 |
| 解析（Parsing） | PDF/LaTeX → Markdown | 不是检索 |
| 检索（Search） | ripgrep + index.json | 不是 LLM 生成 |

---

## 3. ID 规则对齐

### 3.1 Paper ID
- **格式**：`source_identifier`（示例：`arxiv_2401.12345` 或 `local_20240204_001`）
- **稳定性**：一篇论文固定，重解析不变。

### 3.2 Paragraph ID
- **正文**：位置型 ID（如 `abs_001`、`int_001`）
- **笔记**：时间戳型 ID（如 `note_20240204_143022`）
- **原则**：正文 ID 与段落结构强绑定，笔记 ID 与时间强绑定。

### 3.3 Session ID
- **建议格式**：`session_YYYYMMDD_HHMMSS`（可加入短随机串防冲突）

---

## 4. 生命周期与归属

| 实体 | 归属 | 生成时机 | 更新频率 | 删除策略 |
|------|------|----------|----------|----------|
| Paper | 用户 | 导入/解析时 | 解析/元数据更新 | 用户显式删除 |
| Document | 系统 | 解析完成 | 重新解析 | 随 Paper 删除 |
| Note | 用户 | 写入时 | 高频 | 用户显式删除 |
| Index | 系统 | 解析后 | 段落变更时重建/局部更新 | 随 Paper 删除 |
| Session | 用户 | 新建会话 | 高 | 可关闭/归档 |
| Summary | 系统 | 触发压缩 | 中 | 可清理 |
| ProjectState | 系统 | 初次运行 | 低 | 重置 |
| UserPreferences | 用户 | 初次配置 | 低 | 重置 |

---

## 5. 关键歧义与裁定

1. **“段落” vs “chunk”**：MVP 统一使用“段落（Paragraph）”。
2. **“文档” vs “论文”**：文档=正文（content.md），论文=Paper 实体。
3. **“记忆”**：仅指会话历史/摘要/项目状态，不包含向量库。
4. **“检索结果”**：返回段落 ID 与文本片段，不返回生成内容。

---

## 6. 未来扩展（P1/P2 注记）
- P1：SQLite FTS5 → Index 结构可能变化，但段落 ID 不变。
- P2：向量索引加入后，“检索结果”仍以段落 ID 作为溯源锚点。
- P1：LaTeX 解析引入后，Document 仍输出 Markdown，保持接口稳定。

---

## 7. 产出物对接点

- **下一步数据结构设计**：以本文件的实体与 ID 规则作为 Schema 基础。
- **接口定义**：所有 API 字段与命名遵循本文件术语。
- **模块设计**：模块边界依赖实体归属与生命周期。

