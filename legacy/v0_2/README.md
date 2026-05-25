# ManuScript v0.2 - 基础流程版本

## 目标

在 v0.1 基础上增加：
1. JSON 格式的大纲管理
2. Query Generator（从大纲生成检索查询）
3. 2步 Prompt Chain（检索 → 生成）
4. 引用格式化

## 运行方式

```bash
pip install -r requirements.txt
python main.py
```

## 核心数据流

```
Outline JSON → Query Generator → List[Query]
                                     ↓
                              RAGFlow 检索
                                     ↓
                              List[Chunks]
                                     ↓
                           Prompt Chain (2步)
                                     ↓
                              Draft + Citations
```

## 文件说明

| 文件 | 说明 |
|------|------|
| config.py | 配置管理 |
| logger.py | 日志配置 |
| pipeline.py | 核心流程编排 |
| query_generator.py | Query 生成器 |
| citation_formatter.py | 引用格式化 |
| main.py | Gradio UI |

## 前置依赖

- v0.1 验证通过（RAGFlow/OpenAI 连通性已确认）
