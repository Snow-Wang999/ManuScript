# ManuScript v3.0 数据结构设计

> **文档版本**: 1.1
> **创建日期**: 2026-02-04
> **最后更新**: 2026-02-06
> **依据文档**: 10_ManuScript_v3.0_实体与术语对齐.md, 09_ManuScript_v3.0_PRD_重新设计.md
> **适用范围**: MVP（本地 PDF 解析 + Markdown 存储 + ripgrep 检索 + 会话摘要/笔记）

---

## 目录

1. [设计原则](#1-设计原则)
2. [核心实体 Schema](#2-核心实体-schema)
3. [会话与记忆 Schema](#3-会话与记忆-schema)
4. [检索与消息 Schema](#4-检索与消息-schema)
5. [文件存储结构](#5-文件存储结构)
6. [Pydantic 模型映射](#6-pydantic-模型映射)

---

## 1. 设计原则

### 1.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | snake_case | `metadata.json`, `content.md` |
| JSON 字段 | snake_case | `paper_id`, `created_at` |
| 类型定义 | PascalCase | `Paper`, `SessionState` |
| 常量 | UPPER_SNAKE_CASE | `MAX_SESSIONS`, `DEFAULT_TOP_K` |

### 1.2 ID 规范

| 实体 | ID 格式 | 示例 | 生成规则 |
|------|---------|------|----------|
| Paper | `{source}_{identifier}` | `arxiv_2401.12345`, `local_20240204_001` | 导入时生成 |
| Paragraph (正文) | `{section_prefix}_{content_hash[:8]}` | `abs_a1b2c3d4`, `int_e5f6g7h8` | 基于内容哈希，确保重解析稳定 |
| Paragraph (笔记) | `note_{timestamp}_{sequence}` | `note_20240204_143022_001` | 时间戳 + 序列，保证唯一 |
| Session | `session_{timestamp}` | `session_20240204_143000` | 创建时生成 |
| Message | `msg_{timestamp}` | `msg_20240204_143001` | 发送时生成 |

### 1.3 时间格式

```json
{
  "datetime": "2024-01-15T10:30:00Z",  // ISO 8601 UTC
  "date": "2024-01-15",                // YYYY-MM-DD
  "time": "10:30:00"                   // HH:MM:SS
}
```

### 1.4 通用字段

所有实体均包含以下字段（如适用）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `created_at` | string (datetime) | 是 | 创建时间 |
| `updated_at` | string (datetime) | 否 | 最后更新时间 |
| `version` | integer | 否 | 版本号，用于冲突检测 |

---

## 2. 核心 Schema

### 2.1 Paper（论文）

**定义**：单篇论文的逻辑载体，包含元数据、正文、笔记、索引。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/paper.json",
  "title": "Paper",
  "description": "论文元数据，存储于 papers/{paper_id}/metadata.json",
  "type": "object",
  "required": ["paper_id", "title", "source", "created_at"],
  "properties": {
    "paper_id": {
      "type": "string",
      "description": "论文唯一标识，格式：{source}_{identifier}",
      "pattern": "^(arxiv|local|local_upload|pubmed|crossref)_[a-zA-Z0-9._-]+$",
      "examples": ["arxiv_2401.12345", "local_20240204_001"]
    },
    "title": {
      "type": "string",
      "description": "论文标题",
      "minLength": 1,
      "maxLength": 500
    },
    "authors": {
      "type": "array",
      "description": "作者列表",
      "items": {
        "type": "string",
        "description": "作者姓名，格式：Last, F. 或 First Last"
      },
      "minItems": 1
    },
    "year": {
      "type": "integer",
      "description": "发表年份",
      "minimum": 1900,
      "maximum": 2100
    },
    "source": {
      "type": "string",
      "description": "论文来源",
      "enum": ["arxiv", "local_upload", "pubmed", "crossref"]
    },
    "arxiv_id": {
      "type": "string",
      "description": "arXiv ID（仅当 source=arxiv 时）",
      "pattern": "^[0-9]{4}\\.[0-9]{5}(v[0-9]+)?$",
      "examples": ["2401.12345", "2301.12345v2"]
    },
    "doi": {
      "type": "string",
      "description": "DOI（可选）",
      "pattern": "^10\\.[0-9]{4,9}/[-._;()/:A-Z0-9]+$",
      "examples": ["10.1000/xyz123"]
    },
    "publication_venue": {
      "type": "string",
      "description": "发表 venue（会议/期刊）",
      "examples": ["CVPR", "Nature", "ICLR"]
    },
    "abstract": {
      "type": "string",
      "description": "摘要（从元数据提取，正文也有更详细版本）",
      "maxLength": 5000
    },
    "keywords": {
      "type": "array",
      "description": "关键词（可选）",
      "items": {"type": "string"},
      "maxItems": 20
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "导入/创建时间"
    },
    "parsed_at": {
      "type": "string",
      "format": "date-time",
      "description": "解析完成时间（仅当 parse_status=success/partial_failure 时必填）"
    },
    "file_path": {
      "type": "string",
      "description": "原始 PDF 文件路径"
    },
    "file_size": {
      "type": "integer",
      "description": "文件大小（字节）",
      "minimum": 0
    },
    "total_paragraphs": {
      "type": "integer",
      "description": "正文段落数量",
      "minimum": 0
    },
    "total_notes": {
      "type": "integer",
      "description": "笔记条数",
      "minimum": 0,
      "default": 0
    },
    "parse_status": {
      "type": "string",
      "description": "解析状态",
      "enum": ["pending", "parsing", "success", "partial_failure", "failed"],
      "default": "pending"
    },
    "parse_warnings": {
      "type": "array",
      "description": "解析警告信息",
      "items": {"type": "string"},
      "default": []
    },
    "tags": {
      "type": "array",
      "description": "用户标签（P1 功能）",
      "items": {"type": "string"},
      "default": []
    },
    "embedding_status": {
      "type": "string",
      "description": "向量化状态",
      "enum": ["pending", "processing", "success", "failed", "skipped"],
      "default": "pending"
    },
    "embedding_model": {
      "type": "string",
      "description": "使用的Embedding模型",
      "examples": ["bge-m3", "text-embedding-3-small"]
    },
    "embedded_at": {
      "type": "string",
      "format": "date-time",
      "description": "向量化完成时间"
    }
  }
}
```

### 2.2 Document（文档/正文结构）

**定义**：论文的结构化正文，存储为 Markdown 文件。

```markdown
---
title: Deep Learning for Medical Image Diagnosis
paper_id: arxiv_2401.12345
parsed_at: 2024-01-15T10:35:00Z
parse_version: 1.0
---

## Abstract [@id:abs_001]

This paper proposes a novel CNN architecture for medical image diagnosis. [@id:abs_002]
Our method achieves state-of-the-art performance on chest X-ray datasets.

## 1. Introduction [@id:int_001]

Medical image analysis has become increasingly important in clinical practice. [@id:int_002]
Deep learning models have shown remarkable progress in this field.

### 1.1 Background [@id:int_1_1_001]

Convolutional Neural Networks (CNNs) have emerged as a powerful tool... [@id:int_1_1_002]

### 1.2 Motivation [@id:int_1_2_001]

Despite the success, existing methods suffer from...

## 2. Related Work [@id:rel_001]

### 2.1 Medical Image Analysis [@id:rel_2_1_001]

Previous studies have explored...

## 3. Methodology [@id:method_001]

### 3.1 Network Architecture [@id:method_3_1_001]

We propose a multi-scale CNN architecture...

### 3.2 Training Strategy [@id:method_3_2_001]

The model is trained using...

## 4. Experiments [@id:exp_001]

### 4.1 Datasets [@id:exp_4_1_001]

We evaluate on three public datasets...

### 4.2 Results [@id:exp_4_2_001]

Table 1 shows the comparison...

## 5. Discussion [@id:disc_001]

## 6. Conclusion [@id:concl_001]

## References [@id:ref_001]
```

**段落 ID 生成规则**：

> **关键设计**：段落 ID 基于内容哈希生成，确保重解析后 ID 稳定，用户笔记关联不会失效。

```python
import hashlib

def generate_paragraph_id(section: str, content: str) -> str:
    """
    生成稳定的段落 ID

    Args:
        section: 章节名称（如 "Abstract", "1. Introduction"）
        content: 段落文本内容

    Returns:
        段落 ID，格式：{section_prefix}_{content_hash[:8]}

    Examples:
        >>> generate_paragraph_id("Abstract", "This paper proposes...")
        "abs_a1b2c3d4"
        >>> generate_paragraph_id("1. Introduction", "Medical image...")
        "int_e5f6g7h8"
    """
    # 标准化章节前缀
    section_prefix_map = {
        "Abstract": "abs",
        "Introduction": "int",
        "Related Work": "rel",
        "Methodology": "method",
        "Methods": "method",
        "Experiments": "exp",
        "Discussion": "disc",
        "Conclusion": "concl",
        "Conclusions": "concl",
        "References": "ref",
        "Appendix": "app",
    }

    # 获取或生成前缀
    prefix = section_prefix_map.get(section)
    if not prefix:
        # 通用处理：基于章节路径生成前缀
        # "1. Introduction" -> "sec_1"
        # "1.1 Background" -> "sec_1_1"
        normalized = section.replace(".", "_").replace(" ", "_")
        prefix = f"sec_{normalized}"[:20]  # 限制长度

    # 生成内容哈希
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:8]

    return f"{prefix}_{content_hash}"
```

| ID 类型 | 格式 | 示例 | 稳定性 |
|---------|------|------|--------|
| 正文段落 | `{section_prefix}_{content_hash[:8]}` | `abs_a1b2c3d4`, `int_e5f6g7h8` | ✅ 内容不变则 ID 不变 |
| 笔记段落 | `note_{timestamp}_{sequence}` | `note_20240204_143022_001` | ✅ 时间戳 + 序列保证唯一 |

**设计优势**：
- ✅ **重解析稳定**：相同内容生成相同 ID，用户笔记关联不失效
- ✅ **可追溯**：通过 `content_hash` 可以验证内容是否被篡改
- ✅ **去重**：相同内容的段落（如复制粘贴）会生成相同 ID，便于识别

### 2.3 Paragraph（段落）

**定义**：可检索、可溯源的最小内容单元。

**关键设计决策**：段落 ID 基于**内容哈希**生成，确保重解析后 ID 稳定，用户笔记关联不会失效。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/paragraph.json",
  "title": "Paragraph",
  "description": "段落数据结构，从 index.json 中读取",
  "type": "object",
  "required": ["paragraph_id", "paper_id", "type", "text"],
  "properties": {
    "paragraph_id": {
      "type": "string",
      "description": "段落唯一标识（基于内容哈希生成，确保稳定性）",
      "pattern": "^(abs|int|rel|method|exp|disc|concl|ref|app|sec)_[a-f0-9]{8}$",
      "examples": ["abs_a1b2c3d4", "int_f5e6d7c8", "sec_1_1_e3b0c4d2"]
    },
    "paper_id": {
      "type": "string",
      "description": "所属论文 ID"
    },
    "type": {
      "type": "string",
      "enum": ["content", "note"],
      "description": "段落类型：content=正文，note=笔记"
    },
    "section": {
      "type": "string",
      "description": "所属章节",
      "examples": ["Abstract", "1. Introduction", "3. Methodology"]
    },
    "text": {
      "type": "string",
      "description": "段落文本内容"
    },
    "content_hash": {
      "type": "string",
      "description": "段落内容 SHA256 哈希（前8位），用于验证 ID 一致性",
      "pattern": "^[a-f0-9]{8}$"
    },
    "offset": {
      "type": "integer",
      "description": "在 content.md/notes.md 中的字节偏移量"
    },
    "length": {
      "type": "integer",
      "description": "段落长度（字节数）"
    },
    "line_number": {
      "type": "integer",
      "description": "起始行号（用于定位）",
      "minimum": 1
    },
    "context_before": {
      "type": "string",
      "description": "前一段落的文本（可选，用于展示上下文）"
    },
    "context_after": {
      "type": "string",
      "description": "后一段落的文本（可选，用于展示上下文）"
    }
  }
}
```

### 2.4 Note（笔记）

**定义**：用户在阅读/检索过程中写入的内容。

**存储格式**（Markdown）：

```markdown
---
paper_id: arxiv_2401.12345
created_at: 2024-01-15T14:30:22Z
updated_at: 2024-01-15T15:45:00Z
total_notes: 2
---

## Notes [@note:note_20240115_143022]

**创建时间**: 2024-01-15T14:30:22Z
**关联段落**: abs_001, abs_002

这篇论文的核心贡献是提出了多尺度 CNN 架构，在 ChestX-ray 数据集上达到了 SOTA。

**关键点**：
- 多尺度特征融合
- 注意力机制引入
- 在三个数据集上验证

**可引用场景**: 引言部分引用，说明深度学习在医学影像的应用进展

---

## Notes [@note:note_20240115_145630]

**创建时间**: 2024-01-15T14:56:30Z
**更新时间**: 2024-01-15T15:45:00Z
**关联段落**: method_3_1_001

方法创新点分析：

1. **架构创新**：引入了多尺度特征提取模块
2. **局限性**：数据集规模较小，泛化能力待验证

**后续工作建议**：在更大规模数据集上验证
```

**Note 数据结构**（JSON 表示）：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/note.json",
  "title": "Note",
  "description": "用户笔记数据结构",
  "type": "object",
  "required": ["note_id", "paper_id", "content", "created_at"],
  "properties": {
    "note_id": {
      "type": "string",
      "description": "笔记唯一标识",
      "pattern": "^note_[0-9]{8}_[0-9]{6}$",
      "examples": ["note_20240115_143022"]
    },
    "paper_id": {
      "type": "string",
      "description": "关联的论文 ID"
    },
    "linked_paragraphs": {
      "type": "array",
      "description": "关联的段落 ID 列表",
      "items": {"type": "string"},
      "examples": [["abs_001", "abs_002"]]
    },
    "content": {
      "type": "string",
      "description": "笔记内容（Markdown 格式）"
    },
    "tags": {
      "type": "array",
      "description": "笔记标签（P1 功能）",
      "items": {"type": "string"},
      "default": []
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "最后更新时间"
    }
  }
}
```

### 2.5 Index（段落索引）

**定义**：段落 ID → 位置/类型的映射表。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/index.json",
  "title": "ParagraphIndex",
  "description": "段落索引，存储于 papers/{paper_id}/index.json",
  "type": "object",
  "required": ["paper_id", "version", "paragraphs"],
  "properties": {
    "paper_id": {
      "type": "string",
      "description": "论文 ID"
    },
    "version": {
      "type": "integer",
      "description": "索引版本号，解析时递增",
      "minimum": 1
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "索引创建时间"
    },
    "content_hash": {
      "type": "string",
      "description": "content.md 的哈希（用于索引一致性校验）"
    },
    "notes_hash": {
      "type": "string",
      "description": "notes.md 的哈希（用于索引一致性校验）"
    },
    "encoding": {
      "type": "string",
      "description": "索引基于的文本编码（建议 UTF-8）",
      "default": "utf-8"
    },
    "line_ending": {
      "type": "string",
      "description": "索引基于的换行符（LF/CRLF）",
      "enum": ["LF", "CRLF"],
      "default": "LF"
    },
    "total_paragraphs": {
      "type": "integer",
      "description": "正文段落数"
    },
    "total_notes": {
      "type": "integer",
      "description": "笔记段落数"
    },
    "paragraphs": {
      "type": "object",
      "description": "段落 ID → 索引信息的映射",
      "patternProperties": {
        "^[a-z]+(?:_[0-9]+)+$|^note_[0-9]{8}_[0-9]{6}$": {
          "type": "object",
          "required": ["type", "offset", "length"],
          "properties": {
            "type": {
              "type": "string",
              "enum": ["content", "note"],
              "description": "content=正文段落，note=笔记段落"
            },
            "offset": {
              "type": "integer",
              "description": "在对应 md 文件中的字节偏移"
            },
            "length": {
              "type": "integer",
              "description": "段落长度（字节）"
            },
            "line_number": {
              "type": "integer",
              "description": "起始行号",
              "minimum": 1
            },
            "section": {
              "type": "string",
              "description": "所属章节（仅正文段落）"
            },
            "file": {
              "type": "string",
              "enum": ["content.md", "notes.md"],
              "description": "所在文件"
            }
          }
        }
      }
    }
  }
}
```

**示例**：

```json
{
  "paper_id": "arxiv_2401.12345",
  "version": 1,
  "created_at": "2024-01-15T10:35:00Z",
  "total_paragraphs": 156,
  "total_notes": 2,
  "paragraphs": {
    "abs_001": {
      "type": "content",
      "offset": 100,
      "length": 256,
      "line_number": 8,
      "section": "Abstract",
      "file": "content.md"
    },
    "abs_002": {
      "type": "content",
      "offset": 356,
      "length": 180,
      "line_number": 9,
      "section": "Abstract",
      "file": "content.md"
    },
    "int_001": {
      "type": "content",
      "offset": 536,
      "length": 320,
      "line_number": 14,
      "section": "1. Introduction",
      "file": "content.md"
    },
    "note_20240115_143022": {
      "type": "note",
      "offset": 0,
      "length": 320,
      "line_number": 1,
      "file": "notes.md"
    },
    "note_20240115_145630": {
      "type": "note",
      "offset": 320,
      "length": 280,
      "line_number": 18,
      "file": "notes.md"
    }
  }
}
```

---

## 3. 会话与记忆 Schema

### 3.1 Session（会话）

**定义**：一次对话生命周期内的状态与历史。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/session.json",
  "title": "Session",
  "description": "会话状态，存储于 memory/sessions/{session_id}.json",
  "type": "object",
  "required": ["session_id", "created_at", "status"],
  "properties": {
    "session_id": {
      "type": "string",
      "description": "会话唯一标识",
      "pattern": "^session_[0-9]{8}_[0-9]{6}$",
      "examples": ["session_20240204_143000"]
    },
    "title": {
      "type": "string",
      "description": "会话标题（用户可编辑）",
      "maxLength": 100,
      "examples": ["探索医学影像方法", "整理引言素材"]
    },
    "status": {
      "type": "string",
      "enum": ["active", "paused", "archived", "deleted"],
      "description": "active=活跃中，paused=暂停（非活跃会话），archived=已归档，deleted=已删除"
    },
    "state": {
      "type": ["string", "null"],
      "description": "用户旅程状态（可选）",
      "enum": ["exploring", "structuring", "writing", "polishing"],
      "examples": ["exploring"]
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "最后活跃时间"
    },
    "closed_at": {
      "type": "string",
      "format": "date-time",
      "description": "关闭时间（仅当 status=archived 时）"
    },
    "messages": {
      "type": "array",
      "description": "对话历史",
      "items": {
        "$ref": "#/definitions/message"
      }
    },
    "total_messages": {
      "type": "integer",
      "description": "消息总数",
      "minimum": 0
    },
    "total_tokens": {
      "type": "integer",
      "description": "累计 Token 消耗",
      "minimum": 0
    },
    "search_history": {
      "type": "array",
      "description": "搜索历史（用于回退和重新检索）",
      "items": {
        "$ref": "#/definitions/search_record"
      }
    },
    "context": {
      "type": "object",
      "description": "会话级上下文（Agent 状态）",
      "properties": {
        "current_intent": {
          "type": "string",
          "description": "当前识别的意图"
        },
        "pending_tasks": {
          "type": "array",
          "description": "待处理任务",
          "items": {"type": "string"}
        },
        "last_paper_id": {
          "type": "string",
          "description": "最后操作的论文 ID"
        },
        "last_paragraph_id": {
          "type": "string",
          "description": "最后查看的段落 ID"
        }
      }
    }
  },
  "definitions": {
    "message": {
      "type": "object",
      "required": ["message_id", "role", "content", "timestamp"],
      "properties": {
        "message_id": {
          "type": "string",
          "pattern": "^msg_[0-9]{8}_[0-9]{6}$"
        },
        "role": {
          "type": "string",
          "enum": ["user", "assistant", "system"]
        },
        "content": {
          "type": "string"
        },
        "timestamp": {
          "type": "string",
          "format": "date-time"
        },
        "token_count": {
          "type": "integer",
          "minimum": 0
        },
        "metadata": {
          "type": "object",
          "properties": {
            "search_results": {
              "type": "array",
              "description": "关联的检索结果"
            },
            "tool_calls": {
              "type": "array",
              "description": "使用的工具"
            }
          }
        }
      }
    },
    "search_record": {
      "type": "object",
      "required": ["query", "timestamp"],
      "properties": {
        "query": {
          "type": "string",
          "description": "搜索词"
        },
        "timestamp": {
          "type": "string",
          "format": "date-time"
        },
        "result_count": {
          "type": "integer",
          "description": "结果数量"
        },
        "filters": {
          "type": "object",
          "description": "应用的筛选条件"
        }
      }
    }
  }
}
```

**示例 Session 文件**：

```json
{
  "session_id": "session_20240204_143000",
  "title": "探索医学影像方法",
  "status": "active",
  "state": "exploring",
  "created_at": "2024-02-04T14:30:00Z",
  "updated_at": "2024-02-04T15:20:00Z",
  "messages": [
    {
      "message_id": "msg_20240204_143001",
      "role": "user",
      "content": "CNN 在医学影像中的应用有哪些？",
      "timestamp": "2024-02-04T14:30:01Z",
      "token_count": 15
    },
    {
      "message_id": "msg_20240204_143002",
      "role": "assistant",
      "content": "找到 3 篇相关论文...",
      "timestamp": "2024-02-04T14:30:05Z",
      "token_count": 500,
      "metadata": {
        "search_results": ["abs_001", "int_001"],
        "tool_calls": ["fulltext_search"]
      }
    }
  ],
  "total_messages": 2,
  "total_tokens": 515,
  "search_history": [
    {
      "query": "CNN 医学影像",
      "timestamp": "2024-02-04T14:30:02Z",
      "result_count": 3
    }
  ],
  "context": {
    "current_intent": "search",
    "pending_tasks": [],
    "last_paper_id": "arxiv_2401.12345"
  }
}
```

### 3.2 Summary（会话摘要）

**定义**：会话历史的压缩版本，跨会话可引用。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/summary.json",
  "title": "SessionSummary",
  "description": "会话摘要，存储于 memory/summaries/{session_id}_summary.json",
  "type": "object",
  "required": ["session_id", "created_at", "summary_type"],
  "properties": {
    "session_id": {
      "type": "string",
      "description": "源会话 ID"
    },
    "summary_id": {
      "type": "string",
      "description": "摘要唯一标识",
      "pattern": "^summary_[0-9]{8}_[0-9]{6}$"
    },
    "summary_type": {
      "type": "string",
      "enum": ["auto", "user_requested", "session_end"],
      "description": "auto=Token 触发，user_requested=用户请求，session_end=会话结束"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "original_message_count": {
      "type": "integer",
      "description": "原始消息数"
    },
    "original_token_count": {
      "type": "integer",
      "description": "原始 Token 数"
    },
    "summary": {
      "type": "string",
      "description": "摘要内容（Markdown 格式）"
    },
    "key_findings": {
      "type": "array",
      "description": "关键发现/结论",
      "items": {
        "type": "object",
        "properties": {
          "topic": {
            "type": "string",
            "description": "主题"
          },
          "finding": {
            "type": "string",
            "description": "发现内容"
          },
          "source_paragraphs": {
            "type": "array",
            "description": "来源段落 ID",
            "items": {"type": "string"}
          }
        }
      }
    },
    "referenced_papers": {
      "type": "array",
      "description": "引用的论文 ID",
      "items": {"type": "string"}
    },
    "referenced_notes": {
      "type": "array",
      "description": "引用的笔记 ID",
      "items": {"type": "string"}
    },
    "tags": {
      "type": "array",
      "description": "摘要标签（用于检索）",
      "items": {"type": "string"}
    }
  }
}
```

**示例**：

```json
{
  "session_id": "session_20240204_143000",
  "summary_id": "summary_20240204_153000",
  "summary_type": "auto",
  "created_at": "2024-02-04T15:30:00Z",
  "original_message_count": 25,
  "original_token_count": 15000,
  "summary": "## 会话总结\n\n用户探索了 CNN 在医学影像中的应用，主要发现：\n\n1. CNN 在胸部 X 光诊断中达到专家水平\n2. 多尺度架构能提升小目标检测\n3. 注意力机制有助于定位病灶\n\n### 建议\n\n用户计划在引言部分引用 Smith et al. 2024 的论文，说明深度学习在医学影像的进展。",
  "key_findings": [
    {
      "topic": "CNN 胸部 X 光",
      "finding": "CNN 模型在胸部 X 光解读上达到与人类专家相当的准确率",
      "source_paragraphs": ["abs_001", "int_001"]
    },
    {
      "topic": "多尺度架构",
      "finding": "多尺度 CNN 能更好地处理不同尺寸的病灶",
      "source_paragraphs": ["method_3_1_001"]
    }
  ],
  "referenced_papers": ["arxiv_2401.12345", "arxiv_2401.23456"],
  "referenced_notes": ["note_20240115_143022"],
  "tags": ["CNN", "医学影像", "胸部X光"]
}
```

### 3.3 ProjectState（项目状态）

**定义**：全局共享的进度与全局上下文。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/project_state.json",
  "title": "ProjectState",
  "description": "项目全局状态，存储于 memory/project_state.json",
  "type": "object",
  "required": ["version", "created_at"],
  "properties": {
    "version": {
      "type": "integer",
      "description": "状态版本号"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "项目创建时间"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "最后更新时间"
    },
    "research_topic": {
      "type": "string",
      "description": "研究主题",
      "examples": ["深度学习在医学影像诊断中的应用"]
    },
    "research_stage": {
      "type": "string",
      "enum": ["literature_review", "proposal", "experiment", "writing", "revision"],
      "description": "当前研究阶段"
    },
    "total_papers": {
      "type": "integer",
      "description": "论文总数",
      "minimum": 0
    },
    "total_sessions": {
      "type": "integer",
      "description": "会话总数",
      "minimum": 0
    },
    "total_notes": {
      "type": "integer",
      "description": "笔记总数",
      "minimum": 0
    },
    "active_session_id": {
      "type": "string",
      "description": "当前活跃会话 ID"
    },
    "recent_papers": {
      "type": "array",
      "description": "最近导入/访问的论文",
      "items": {"type": "string"},
      "maxItems": 10
    },
    "statistics": {
      "type": "object",
      "description": "使用统计",
      "properties": {
        "total_searches": {
          "type": "integer",
          "minimum": 0
        },
        "total_tokens_used": {
          "type": "integer",
          "minimum": 0
        },
        "last_activity": {
          "type": "string",
          "format": "date-time"
        }
      }
    }
  }
}
```

**示例**：

```json
{
  "version": 1,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-02-04T15:30:00Z",
  "research_topic": "深度学习在医学影像诊断中的应用",
  "research_stage": "literature_review",
  "total_papers": 23,
  "total_sessions": 3,
  "total_notes": 15,
  "active_session_id": "session_20240204_143000",
  "recent_papers": [
    "arxiv_2401.12345",
    "arxiv_2401.23456",
    "local_20240204_001"
  ],
  "statistics": {
    "total_searches": 47,
    "total_tokens_used": 25000,
    "last_activity": "2024-02-04T15:30:00Z"
  }
}
```

### 3.4 UserPreferences（用户偏好）

**定义**：与用户相关的静态偏好与配置。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/user_preferences.json",
  "title": "UserPreferences",
  "description": "用户偏好设置，存储于 memory/user_preferences.json",
  "type": "object",
  "required": ["version"],
  "properties": {
    "version": {
      "type": "integer",
      "description": "配置版本号"
    },
    "privacy_mode": {
      "type": "string",
      "enum": ["local_only", "local_with_cloud_option"],
      "description": "local_only=纯本地，local_with_cloud_option=本地+可选云端",
      "default": "local_only"
    },
    "cloud_enabled": {
      "type": "boolean",
      "description": "是否启用云端处理",
      "default": false
    },
    "max_sessions": {
      "type": "integer",
      "description": "最大会话数",
      "default": 3,
      "minimum": 1,
      "maximum": 10
    },
    "search_preferences": {
      "type": "object",
      "properties": {
        "default_top_k": {
          "type": "integer",
          "description": "默认返回结果数",
          "default": 10,
          "minimum": 1,
          "maximum": 50
        },
        "source_priority": {
          "type": "string",
          "enum": ["content_first", "note_first", "mixed"],
          "description": "来源优先级",
          "default": "content_first"
        },
        "case_sensitive": {
          "type": "boolean",
          "description": "是否区分大小写",
          "default": false
        }
      }
    },
    "ui_preferences": {
      "type": "object",
      "properties": {
        "theme": {
          "type": "string",
          "enum": ["light", "dark", "auto"],
          "default": "auto"
        },
        "font_size": {
          "type": "integer",
          "description": "字体大小",
          "default": 14,
          "minimum": 10,
          "maximum": 24
        },
        "sidebar_width": {
          "type": "integer",
          "description": "侧边栏宽度（像素）",
          "default": 400,
          "minimum": 300,
          "maximum": 800
        }
      }
    },
    "llm_settings": {
      "type": "object",
      "properties": {
        "provider": {
          "type": "string",
          "enum": ["openai", "anthropic", "local"],
          "default": "openai"
        },
        "model": {
          "type": "string",
          "default": "gpt-4o-mini"
        },
        "temperature": {
          "type": "number",
          "default": 0.7,
          "minimum": 0,
          "maximum": 1
        },
        "max_tokens": {
          "type": "integer",
          "default": 2000
        },
        "api_key_configured": {
          "type": "boolean",
          "description": "API Key 是否已配置"
        }
      }
    },
    "summary_settings": {
      "type": "object",
      "properties": {
        "auto_trigger_threshold": {
          "type": "number",
          "description": "自动触发摘要的 Token 阈值（百分比）",
          "default": 0.8,
          "minimum": 0.5,
          "maximum": 0.95
        },
        "summary_detail_level": {
          "type": "string",
          "enum": ["brief", "medium", "detailed"],
          "default": "medium"
        }
      }
    },
    "notifications": {
      "type": "object",
      "properties": {
        "parse_complete": {
          "type": "boolean",
          "description": "解析完成通知",
          "default": true
        },
        "summary_ready": {
          "type": "boolean",
          "description": "摘要生成完成通知",
          "default": true
        },
        "session_limit_warning": {
          "type": "boolean",
          "description": "会话数量限制警告",
          "default": true
        }
      }
    }
  }
}
```

---

## 4. 检索与消息 Schema

### 4.1 Message（消息）

**定义**：对话中的单条消息。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/message.json",
  "title": "Message",
  "description": "对话消息",
  "type": "object",
  "required": ["message_id", "role", "content", "timestamp"],
  "properties": {
    "message_id": {
      "type": "string",
      "pattern": "^msg_[0-9]{8}_[0-9]{6}$",
      "examples": ["msg_20240204_143001"]
    },
    "role": {
      "type": "string",
      "enum": ["user", "assistant", "system"],
      "description": "user=用户，assistant=系统助手，system=系统消息"
    },
    "content": {
      "type": "string",
      "description": "消息内容（Markdown 格式）"
    },
    "content_type": {
      "type": "string",
      "enum": ["text", "search_results", "summary", "error"],
      "description": "内容类型",
      "default": "text"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "token_count": {
      "type": "integer",
      "description": "Token 计数",
      "minimum": 0
    },
    "metadata": {
      "type": "object",
      "description": "元数据",
      "properties": {
        "search_results": {
          "type": "array",
          "description": "关联的检索结果",
          "items": {
            "$ref": "https://manuscript.dev/schemas/search_result.json"
          }
        },
        "tool_calls": {
          "type": "array",
          "description": "使用的工具调用",
          "items": {
            "type": "object",
            "properties": {
              "tool": {
                "type": "string"
              },
              "parameters": {
                "type": "object"
              },
              "duration_ms": {
                "type": "integer"
              }
            }
          }
        },
        "error": {
          "type": "object",
          "description": "错误信息（如有）",
          "properties": {
            "code": {
              "type": "string"
            },
            "message": {
              "type": "string"
            },
            "details": {
              "type": "object"
            }
          }
        }
      }
    }
  }
}
```

### 4.2 SearchResult（检索结果）

**定义**：检索返回的单个结果项。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/search_result.json",
  "title": "SearchResult",
  "description": "检索结果项",
  "type": "object",
  "required": ["paragraph_id", "paper_id", "type", "text", "score"],
  "properties": {
    "paragraph_id": {
      "type": "string",
      "description": "段落 ID"
    },
    "paper_id": {
      "type": "string",
      "description": "论文 ID"
    },
    "type": {
      "type": "string",
      "enum": ["content", "note"],
      "description": "content=正文段落，note=笔记段落"
    },
    "text": {
      "type": "string",
      "description": "段落文本"
    },
    "highlighted_text": {
      "type": "string",
      "description": "高亮匹配关键词的文本（用于显示）"
    },
    "final_score": {
      "type": "number",
      "description": "融合后最终得分",
      "minimum": 0,
      "maximum": 1
    },
    "keyword_score": {
      "type": "number",
      "description": "关键词匹配得分",
      "minimum": 0,
      "maximum": 1
    },
    "vector_score": {
      "type": "number",
      "description": "向量相似度得分",
      "minimum": 0,
      "maximum": 1
    },
    "match_source": {
      "type": "string",
      "enum": ["keyword", "vector", "hybrid"],
      "description": "匹配来源",
      "default": "hybrid"
    },
    "section": {
      "type": "string",
      "description": "所属章节（仅正文）"
    },
    "paper_title": {
      "type": "string",
      "description": "论文标题（冗余存储，便于显示）"
    },
    "paper_authors": {
      "type": "array",
      "description": "论文作者（冗余存储，便于显示）",
      "items": {"type": "string"}
    },
    "paper_year": {
      "type": "integer",
      "description": "论文年份（冗余存储，便于显示）"
    },
    "context": {
      "type": "object",
      "description": "上下文信息",
      "properties": {
        "before": {
          "type": "string",
          "description": "前一段落（用于展示上下文）"
        },
        "after": {
          "type": "string",
          "description": "后一段落（用于展示上下文）"
        }
      }
    },
    "offset": {
      "type": "integer",
      "description": "在源文件中的偏移量（用于溯源）"
    },
    "line_number": {
      "type": "integer",
      "description": "行号（用于溯源）"
    }
  }
}
```

### 4.3 SearchQuery（检索查询）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/search_query.json",
  "title": "SearchQuery",
  "description": "检索查询参数",
  "type": "object",
  "required": ["query"],
  "properties": {
    "query": {
      "type": "string",
      "description": "搜索词/自然语言问题",
      "minLength": 1
    },
    "query_type": {
      "type": "string",
      "enum": ["keyword", "natural_language", "auto"],
      "description": "keyword=关键词搜索，natural_language=自然语言处理，auto=自动识别",
      "default": "auto"
    },
    "top_k": {
      "type": "integer",
      "description": "返回结果数量",
      "default": 10,
      "minimum": 1,
      "maximum": 100
    },
    "source_filter": {
      "type": "string",
      "enum": ["all", "content_only", "note_only"],
      "description": "来源筛选",
      "default": "all"
    },
    "paper_ids": {
      "type": "array",
      "description": "限定搜索的论文 ID 列表",
      "items": {"type": "string"}
    },
    "sections": {
      "type": "array",
      "description": "限定搜索的章节",
      "items": {"type": "string"},
      "examples": [["Abstract", "Introduction"]]
    },
    "year_range": {
      "type": "object",
      "description": "年份范围筛选",
      "properties": {
        "min": {
          "type": "integer",
          "minimum": 1900,
          "maximum": 2100
        },
        "max": {
          "type": "integer",
          "minimum": 1900,
          "maximum": 2100
        }
      }
    },
    "case_sensitive": {
      "type": "boolean",
      "description": "是否区分大小写",
      "default": false
    },
    "include_context": {
      "type": "boolean",
      "description": "是否包含上下文",
      "default": true
    }
  }
}
```

### 4.4 SearchResponse（检索响应）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/search_response.json",
  "title": "SearchResponse",
  "description": "检索响应",
  "type": "object",
  "required": ["results", "total", "query"],
  "properties": {
    "results": {
      "type": "array",
      "description": "检索结果列表",
      "items": {
        "$ref": "https://manuscript.dev/schemas/search_result.json"
      }
    },
    "total": {
      "type": "integer",
      "description": "总结果数"
    },
    "returned": {
      "type": "integer",
      "description": "返回的结果数"
    },
    "query": {
      "type": "string",
      "description": "原始查询"
    },
    "rewritten_query": {
      "type": "string",
      "description": "改写后的查询（如有）"
    },
    "search_duration_ms": {
      "type": "integer",
      "description": "检索耗时（毫秒）"
    },
    "papers_searched": {
      "type": "integer",
      "description": "搜索的论文数量"
    },
    "filters_applied": {
      "type": "object",
      "description": "应用的筛选条件"
    }
  }
}
```

---

## 5. 文件存储结构

### 5.1 完整目录结构

```
manuscript_data/
├── papers/                          # 论文存储
│   ├── {paper_id}/
│   │   ├── metadata.json            # 论文元数据
│   │   ├── content.md               # 正文内容（带段落 ID）
│   │   ├── notes.md                 # 用户笔记
│   │   ├── index.json               # 段落索引
│   │   └── original.pdf             # 原始 PDF（可选）
│   │
│   └── _papers_index.json           # 全局论文索引
│
├── memory/                          # 记忆存储
│   ├── sessions/                    # 会话历史
│   │   ├── session_20240204_143000.json
│   │   ├── session_20240204_150000.json
│   │   └── ...
│   │
│   ├── summaries/                   # 会话摘要
│   │   ├── session_20240204_143000_summary.json
│   │   └── ...
│   │
│   ├── project_state.json           # 项目状态
│   └── user_preferences.json        # 用户偏好
│
├── cache/                           # 缓存（可选）
│   ├── search_cache.json
│   └── llm_cache.json
│
├── exports/                         # 导出文件
│   └── backup_20240204.zip
│
├── logs/                            # 日志文件
│   └── manuscript.log
│
└── config.json                      # 全局配置
```

### 5.2 索引存储结构（新增）

```
data/
├── papers/                          # 论文存储（保持不变）
│   └── {paper_id}/
│       ├── metadata.json
│       ├── content.md
│       ├── notes.md
│       └── index.json
│
├── indexes/                         # 全局索引层（新增）
│   ├── fts.db                      # SQLite FTS5 全文索引
│   └── vectors/                    # 向量索引
│       └── chroma/                 # ChromaDB 持久化
│           ├── chroma.sqlite3
│           └── embeddings/
│
└── config/
    └── embedding_config.json       # Embedding配置
```

#### 5.2.1 embedding_config.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://manuscript.dev/schemas/embedding_config.json",
  "title": "EmbeddingConfig",
  "description": "Embedding服务配置，支持本地/API双模式",
  "type": "object",
  "required": ["mode"],
  "properties": {
    "mode": {
      "type": "string",
      "enum": ["local", "api", "auto"],
      "description": "local=本地模式，api=API模式，auto=自动检测GPU"
    },
    "local": {
      "type": "object",
      "description": "本地Embedding配置",
      "properties": {
        "model_name": {
          "type": "string",
          "default": "BAAI/bge-m3",
          "description": "模型名称"
        },
        "device": {
          "type": "string",
          "enum": ["cuda", "cpu", "auto"],
          "default": "auto"
        },
        "batch_size": {
          "type": "integer",
          "default": 32,
          "minimum": 1
        }
      }
    },
    "api": {
      "type": "object",
      "description": "API Embedding配置",
      "properties": {
        "provider": {
          "type": "string",
          "default": "openai"
        },
        "model": {
          "type": "string",
          "default": "text-embedding-3-small"
        },
        "api_key_env": {
          "type": "string",
          "description": "API Key环境变量名",
          "default": "OPENAI_API_KEY"
        }
      }
    },
    "auto_detect_gpu": {
      "type": "boolean",
      "default": true,
      "description": "是否自动检测GPU"
    }
  }
}
```

### 5.3 _papers_index.json（全局论文索引）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PapersIndex",
  "description": "全局论文索引，加速列表加载",
  "type": "object",
  "required": ["version", "papers"],
  "properties": {
    "version": {
      "type": "integer"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    },
    "total_papers": {
      "type": "integer"
    },
    "papers": {
      "type": "array",
      "description": "论文简略信息列表",
      "items": {
        "type": "object",
        "required": ["paper_id", "title", "created_at"],
        "properties": {
          "paper_id": {
            "type": "string"
          },
          "title": {
            "type": "string"
          },
          "authors": {
            "type": "array",
            "items": {"type": "string"}
          },
          "year": {
            "type": "integer"
          },
          "source": {
            "type": "string"
          },
          "created_at": {
            "type": "string",
            "format": "date-time"
          },
          "total_paragraphs": {
            "type": "integer"
          },
          "total_notes": {
            "type": "integer"
          },
          "tags": {
            "type": "array",
            "items": {"type": "string"}
          }
        }
      }
    }
  }
}
```

### 5.4 知识管理扩展（P1 功能）

借鉴现代知识管理系统（如 Obsidian、Foam）的设计，为长期研究项目提供上下文管理能力。

```
data/
├── context/                    # 会话上下文（新增）
│   ├── RESEARCH_TOPIC.md       # 当前研究主题
│   ├── READING_HISTORY.md      # 阅读历史
│   └── QUERIES.md              # 检索查询历史
│
├── tasks/                      # 研究任务管理（新增）
│   ├── 001_深度学习论文综述.md
│   ├── 002_Transformer架构分析.md
│   └── _archive/
│
└── papers/
    ├── README.md               # 论文库概览（新增）
    └── {category}/
        └── README.md           # 分类描述
```

#### 5.4.1 RESEARCH_TOPIC.md

当前研究主题的持久化记录，帮助 AI 跨会话保持上下文。

```markdown
# 当前研究主题

## 研究领域
深度学习在自然语言处理中的应用

## 关键问题
- Transformer 架构的演进
- 预训练语言模型的效率优化
- 多模态融合方法

## 相关论文库
- papers/attention/
- papers/transformer/
- papers/bert/
- papers/gpt/

## 研究目标
- [ ] 完成领域核心论文综述
- [ ] 识别研究缺口
- [ ] 形成个人研究观点

## 更新时间
2026-02-06
```

#### 5.4.2 READING_HISTORY.md

记录阅读过的论文和笔记，方便回溯和引用。

```markdown
# 阅读历史

## 已阅读
| 日期 | 论文标题 | 核心观点 | 笔记数 |
|------|----------|----------|--------|
| 2026-02-05 | Attention Is All You Need | 自注意力机制替代循环 | 5 |
| 2026-02-06 | BERT: Pre-training of Deep... | 双向编码器预训练 | 3 |

## 阅读中
- GPT-3: Language Models are Few-Shot Learners

## 待阅读
- T5: Exploring the Limits of Transfer Learning
- PaLM: Scaling Language Modeling with Pathways
```

#### 5.4.3 QUERIES.md

记录有效的检索查询，构建个人查询知识库。

```markdown
# 检索查询历史

## 高效查询
- "self-attention mechanism complexity O(n^2)" → 找到5篇相关论文
- "BERT vs RoBERTa pre-training differences" → 找到3篇对比分析

## 语义搜索示例
- "如何降低Transformer的计算复杂度？" → 推荐了Linear Transformer相关论文
```

#### 5.4.4 任务文件结构

每个研究任务一个 Markdown 文件，链接相关论文。

```markdown
# 001_深度学习论文综述

## 任务状态
进行中

## 任务描述
完成深度学习在NLP领域的核心论文综述，重点关注架构演进。

## 相关论文
- [Attention Is All You Need](../papers/arxiv_1706.03762/)
- [BERT: Pre-training of Deep Bidirectional Transformers](../papers/arxiv_1810.04805/)
- [GPT-3: Language Models are Few-Shot Learners](../papers/arxiv_2005.14165/)

## 进度
- [x] 阅读Attention论文
- [x] 阅读BERT论文
- [ ] 阅读GPT-3论文
- [ ] 整理架构演进时间线

## 关键发现
- 自注意力机制是Transformer的核心
- 预训练+微调成为主流范式
- 规模扩展持续带来性能提升

## 创建时间
2026-02-01
## 最后更新
2026-02-06
```

#### 5.4.5 papers/README.md

论文库概览，统计信息和导航。

```markdown
# 论文库概览

## 统计信息
- 总论文数: 127
- 已解析: 125
- 已向量化: 120
- 笔记总数: 48

## 分类导航
- [attention/](attention/) - 15篇，注意力机制相关
- [transformer/](transformer/) - 23篇，Transformer架构
- [bert/](bert/) - 18篇，BERT系列
- [gpt/](gpt/) - 12篇，GPT系列
- [multimodal/](multimodal/) - 9篇，多模态模型

## 最近添加
1. "Mamba: Linear-Time Sequence Modeling" (2026-02-05)
2. "Retentive Network: A Successor to Transformer" (2026-02-04)

## 索引状态
- FTS5全文索引: ✅ 正常
- ChromaDB向量索引: ✅ 正常
- 向量维度: 1024 (BGE-M3)
```

#### 5.4.6 data/papers/{category}/README.md

分类级别的描述和统计。

```markdown
# Transformer 架构论文

## 分类说明
收集基于Transformer架构的核心论文，包括改进变体和应用研究。

## 统计
- 论文数: 23
- 原始Transformer: 1篇
- 编码器改进: 8篇
- 解码器改进: 5篇
- 架构变体: 9篇

## 核心论文
1. Attention Is All You Need (2017) - 原始论文
2. Transformer-XL (2019) - 长序列建模
3. Linformer (2020) - 线性复杂度

## 相关分类
- [../attention/](../attention/) - 注意力机制基础
- [../bert/](../bert/) - BERT编码器系列
- [../gpt/](../gpt/) - GPT解码器系列
```

---

## 6. Pydantic 模型映射

### 6.1 核心模型定义

```python
# models/paper.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal, Optional
from enum import Enum


class SourceType(str, Enum):
    ARXIV = "arxiv"
    LOCAL_UPLOAD = "local_upload"
    PUBMED = "pubmed"
    CROSSREF = "crossref"


class ParseStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    SUCCESS = "success"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"


class EmbeddingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class EmbeddingMode(str, Enum):
    LOCAL = "local"
    API = "api"
    AUTO = "auto"


class EmbeddingConfig(BaseModel):
    """Embedding配置"""

    mode: EmbeddingMode = EmbeddingMode.AUTO
    local_model: str = "BAAI/bge-m3"
    local_device: Literal["cuda", "cpu", "auto"] = "auto"
    local_batch_size: int = Field(32, ge=1, le=128)
    api_provider: str = "openai"
    api_model: str = "text-embedding-3-small"
    api_key_env: str = "OPENAI_API_KEY"
    auto_detect_gpu: bool = True

```python
# models/paper.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal, Optional
from enum import Enum


class SourceType(str, Enum):
    ARXIV = "arxiv"
    LOCAL_UPLOAD = "local_upload"
    PUBMED = "pubmed"
    CROSSREF = "crossref"


class ParseStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    SUCCESS = "success"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"


class PaperMetadata(BaseModel):
    """论文元数据"""

    paper_id: str = Field(
        ...,
        pattern=r"^(arxiv|local|local_upload|pubmed|crossref)_[a-zA-Z0-9._-]+$",
        description="论文唯一标识"
    )
    title: str = Field(..., min_length=1, max_length=500)
    authors: list[str] = Field(..., min_length=1)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    source: SourceType
    arxiv_id: Optional[str] = Field(None, pattern=r"^[0-9]{4}\.[0-9]{5}(v[0-9]+)?$")
    doi: Optional[str] = Field(None, pattern=r"^10\.[0-9]{4,9}/[-._;()/:A-Z0-9]+$")
    publication_venue: Optional[str] = None
    abstract: Optional[str] = Field(None, max_length=5000)
    keywords: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    parsed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = Field(None, ge=0)
    total_paragraphs: int = Field(0, ge=0)
    total_notes: int = Field(0, ge=0)
    parse_status: ParseStatus = ParseStatus.PENDING
    parse_warnings: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }


# models/paragraph.py
class ParagraphType(str, Enum):
    CONTENT = "content"
    NOTE = "note"


class Paragraph(BaseModel):
    """段落数据"""

    paragraph_id: str
    paper_id: str
    type: ParagraphType
    section: Optional[str] = None
    text: str
    offset: Optional[int] = Field(None, ge=0)
    length: Optional[int] = Field(None, ge=0)
    line_number: Optional[int] = Field(None, ge=1)
    context_before: Optional[str] = None
    context_after: Optional[str] = None


# models/note.py
class Note(BaseModel):
    """用户笔记"""

    note_id: str = Field(
        ...,
        pattern=r"^note_[0-9]{8}_[0-9]{6}$"
    )
    paper_id: str
    linked_paragraphs: list[str] = Field(default_factory=list)
    content: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None


# models/index.py
class ParagraphIndexEntry(BaseModel):
    """段落索引条目"""

    type: ParagraphType
    offset: int = Field(..., ge=0)
    length: int = Field(..., ge=0)
    line_number: Optional[int] = Field(None, ge=1)
    section: Optional[str] = None
    file: Literal["content.md", "notes.md"]


class ParagraphIndex(BaseModel):
    """段落索引"""

    paper_id: str
    version: int = Field(1, ge=1)
    created_at: datetime
    total_paragraphs: int = Field(0, ge=0)
    total_notes: int = Field(0, ge=0)
    paragraphs: dict[str, ParagraphIndexEntry] = Field(default_factory=dict)


# models/session.py
class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class UserState(str, Enum):
    EXPLORING = "exploring"
    STRUCTURING = "structuring"
    WRITING = "writing"
    POLISHING = "polishing"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """对话消息"""

    message_id: str = Field(..., pattern=r"^msg_[0-9]{8}_[0-9]{6}$")
    role: MessageRole
    content: str
    timestamp: datetime
    token_count: int = Field(0, ge=0)


class SessionContext(BaseModel):
    """会话上下文"""

    current_intent: Optional[str] = None
    pending_tasks: list[str] = Field(default_factory=list)
    last_paper_id: Optional[str] = None
    last_paragraph_id: Optional[str] = None


class Session(BaseModel):
    """会话状态"""

    session_id: str = Field(..., pattern=r"^session_[0-9]{8}_[0-9]{6}$")
    title: str = Field(..., max_length=100)
    status: SessionStatus = SessionStatus.ACTIVE
    state: Optional[UserState] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    messages: list[Message] = Field(default_factory=list)
    total_messages: int = Field(0, ge=0)
    total_tokens: int = Field(0, ge=0)
    context: SessionContext = Field(default_factory=SessionContext)


# models/search.py
class SearchResult(BaseModel):
    """检索结果（支持混合检索评分）"""

    paragraph_id: str
    paper_id: str
    type: ParagraphType
    text: str
    highlighted_text: Optional[str] = None

    # 评分（修改为混合检索）
    final_score: float = Field(..., ge=0, le=1, description="融合后最终得分")
    keyword_score: Optional[float] = Field(None, ge=0, le=1, description="关键词匹配得分")
    vector_score: Optional[float] = Field(None, ge=0, le=1, description="向量相似度得分")
    match_source: Literal["keyword", "vector", "hybrid"] = "hybrid"

    # 其他字段保持不变
    section: Optional[str] = None
    paper_title: Optional[str] = None
    paper_authors: Optional[list[str]] = None
    paper_year: Optional[int] = None
    offset: Optional[int] = None
    line_number: Optional[int] = None


class SearchQuery(BaseModel):
    """检索查询"""

    query: str = Field(..., min_length=1)
    query_type: Literal["keyword", "natural_language", "auto"] = "auto"
    top_k: int = Field(10, ge=1, le=100)
    source_filter: Literal["all", "content_only", "note_only"] = "all"
    paper_ids: Optional[list[str]] = None
    case_sensitive: bool = False
    include_context: bool = True


class SearchResponse(BaseModel):
    """检索响应"""

    results: list[SearchResult]
    total: int
    returned: int
    query: str
    rewritten_query: Optional[str] = None
    search_duration_ms: int
    papers_searched: int
```

---

## 7. 修订建议（V1.1）

> 目的：将当前 Schema 调整为“可落地 + 可演进 + 易校验”的版本。

### 7.1 必改项（高优先级）
- **字段一致性**：`publication venue` 已改为 `publication_venue`，避免 JSON/Pydantic 不一致。
- **ID 规则一致性**：`paper_id` pattern 已放宽，与 `source` 枚举一致（支持 `local_upload/pubmed/crossref`）。
- **解析时间约束**：`parsed_at` 不应在 `pending` 时必填；仅在 `success/partial_failure` 时要求存在。
- **段落 ID 正则**：支持 `int_1_1_001` 等多层级格式，已放宽 regex。
- **索引一致性校验**：新增 `content_hash/notes_hash`、`encoding/line_ending`，避免偏移漂移导致溯源错误。

### 7.2 建议改进（中优先级）
- **段落 ID 生成规则**：建议用“章节路径 + 序号”的通用算法，避免硬编码章节前缀列表。
- **Note 作为单一真源**：明确“Markdown 为真源，JSON 仅运行时生成”或反之，避免双写不一致。
- **Session.state 的 JSON Schema**：已调整为 `type: [string, null]`，符合 draft-07 规范。
- **全局论文索引**：建议添加 `parse_status` / `updated_at` / `last_modified` 以提升列表与一致性检查。

### 7.3 可选增强（低优先级 / P1）
- **索引版本迁移策略**：当 `INDEX_VERSION` 升级时，提供批量重建/迁移脚本。
- **search_result display-only**：明确冗余字段仅用于展示，避免被误用为数据源。

---

## 附录 A：字段映射表

| 实体 | JSON 字段 | Pydantic 字段 | 类型 |
|------|-----------|---------------|------|
| Paper | paper_id | paper_id | str |
| Paper | parse_status | parse_status | ParseStatus (Enum) |
| Paragraph | type | type | ParagraphType (Enum) |
| Session | status | status | SessionStatus (Enum) |
| Session | state | state | UserState (Enum) |
| Message | role | role | MessageRole (Enum) |
| SearchResult | score | score | float (0-1) |

---

## 附录 B：默认值配置

```python
# config/constants.py

# 会话限制
MAX_SESSIONS = 3
MAX_MESSAGES_PER_SESSION = 1000
TOKEN_WARNING_THRESHOLD = 0.8  # 80%

# 检索配置
DEFAULT_TOP_K = 10
MAX_TOP_K = 100
DEFAULT_SEARCH_TIMEOUT = 5  # 秒

# 文件大小限制
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB
MAX_MD_SIZE = 10 * 1024 * 1024   # 10MB

# 索引配置
INDEX_VERSION = 1
MAX_PARAGRAPHS_PER_PAPER = 10000

# 缓存配置
SEARCH_CACHE_SIZE = 100
SEARCH_CACHE_TTL = 3600  # 1小时
```

---

*文档版本: 1.0 | 最后更新: 2026-02-04*
