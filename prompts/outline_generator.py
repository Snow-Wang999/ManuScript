"""
大纲生成 Prompt 模板
用于根据论文题目生成带写作提示的结构化大纲

版本说明：
- 目标版本：v2.0
- 配合改动：v2_0/models.py 的 Section 模型需新增 hints 字段
- 使用位置：大纲引擎（Outline Engine）生成大纲时调用
- 状态：待集成（保留在根目录作为参考模板）
"""

OUTLINE_GENERATOR_PROMPT = """
你是一位学术论文结构专家。请根据用户提供的论文题目，生成一份结构化的论文大纲。

## 输入
论文题目：{topic}
{abstract_section}

## 任务
1. 首先判断这篇论文最可能的类型（实证研究/综述/理论研究/案例研究）
2. 根据论文类型，生成合适的章节结构
3. 为每个章节提供简短的写作要点提示

## 输出格式（JSON）
```json
{{
  "paper_type": "empirical|review|theoretical|case_study",
  "sections": [
    {{
      "id": "section_001",
      "title": "章节标题",
      "section_type": "introduction|literature_review|methodology|results|discussion|conclusion",
      "level": 1,
      "hints": ["写作要点1", "写作要点2"],
      "word_limit": 500,
      "children": []
    }}
  ]
}}
```

## 论文类型与推荐结构

### 实证研究 (empirical)
适用于：有数据收集、实验、调查的研究
结构：引言 → 文献综述 → 研究方法 → 结果 → 讨论 → 结论

### 综述论文 (review)
适用于：系统性文献综述、研究现状分析
结构：引言 → 检索方法 → 主题分析（多个） → 综合讨论 → 结论

### 理论研究 (theoretical)
适用于：概念分析、理论构建、框架提出
结构：引言 → 理论背景 → 核心论证 → 讨论 → 结论

### 案例研究 (case_study)
适用于：单一或多案例深度分析
结构：引言 → 文献回顾 → 研究方法 → 案例描述 → 案例分析 → 讨论 → 结论

## 各章节写作要点参考

### Introduction (引言)
- 阐述研究背景，从宏观到微观
- 指出现有研究的不足或空白
- 明确本研究的目的和意义
- 简述研究方法和论文结构

### Literature Review (文献综述)
- 梳理该领域的研究发展脉络
- 归纳现有研究的主要观点和方法
- 比较不同研究的异同
- 指出研究空白，引出本研究

### Methodology (研究方法)
- 说明研究设计和整体思路
- 描述数据来源或研究对象
- 详述具体研究步骤
- 解释分析方法的选择依据

### Results (结果)
- 客观呈现研究发现
- 用图表辅助说明
- 按逻辑顺序组织
- 不做主观解释

### Discussion (讨论)
- 解释结果的意义
- 与已有研究对比（一致/矛盾）
- 分析局限性
- 提出未来研究方向

### Conclusion (结论)
- 回应研究问题
- 总结主要发现
- 强调研究贡献
- 简述实践意义

请根据论文题目生成大纲，确保：
1. 章节结构符合论文类型
2. 每个章节有2-4条具体的写作要点提示
3. 字数限制合理（总计约8000-15000字）
"""

# 简化版（用于快速生成）
OUTLINE_GENERATOR_SIMPLE = """
根据论文题目「{topic}」生成学术论文大纲。

要求：
1. 判断论文类型（实证/综述/理论/案例）
2. 输出标准章节结构
3. 每章附2-3条写作要点

输出JSON格式：
{{
  "paper_type": "类型",
  "sections": [
    {{"title": "标题", "section_type": "类型", "hints": ["要点1", "要点2"]}}
  ]
}}
"""


def generate_outline_prompt(topic: str, abstract: str = None) -> str:
    """生成大纲生成的完整 Prompt"""
    abstract_section = ""
    if abstract:
        abstract_section = f"摘要/简介：{abstract}"

    return OUTLINE_GENERATOR_PROMPT.format(
        topic=topic,
        abstract_section=abstract_section
    )


def generate_outline_prompt_simple(topic: str) -> str:
    """生成简化版 Prompt"""
    return OUTLINE_GENERATOR_SIMPLE.format(topic=topic)
