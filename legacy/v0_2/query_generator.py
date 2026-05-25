# -*- coding: utf-8 -*-
"""
ManuScript v0.2 Query Generator

从大纲 JSON 生成检索查询
"""
from pydantic import BaseModel
from config import config
from logger import get_logger

logger = get_logger(__name__)


# 章节类型及其对应的查询数量配置
SECTION_TYPE_QUERIES = {
    "introduction": 2,      # 引言：较少查询
    "background": 3,        # 背景：较多查询
    "related_work": 3,      # 相关工作：较多查询
    "method": 2,            # 方法：中等查询
    "experiment": 2,        # 实验：中等查询
    "result": 2,            # 结果：中等查询
    "discussion": 2,        # 讨论：中等查询
    "conclusion": 1,        # 结论：较少查询
    "default": 2,           # 默认
}

# 关键词扩展词典（学术领域常用同义词）
KEYWORD_EXPANSIONS = {
    "深度学习": ["deep learning", "神经网络", "neural network"],
    "机器学习": ["machine learning", "ML", "统计学习"],
    "自然语言处理": ["NLP", "natural language processing", "文本分析"],
    "计算机视觉": ["computer vision", "CV", "图像识别"],
    "医学图像": ["medical imaging", "医学影像", "临床图像"],
}


class Section(BaseModel):
    """章节模型"""
    title: str
    description: str = ""
    keywords: list[str] = []
    section_type: str = "default"  # 章节类型


class Outline(BaseModel):
    """大纲模型"""
    topic: str
    sections: list[Section]


def expand_keywords(keywords: list[str]) -> list[str]:
    """
    扩展关键词（添加同义词）

    Args:
        keywords: 原始关键词列表

    Returns:
        扩展后的关键词列表
    """
    expanded = list(keywords)  # 保留原始关键词

    for kw in keywords:
        if kw in KEYWORD_EXPANSIONS:
            # 添加扩展词（最多添加2个）
            for exp in KEYWORD_EXPANSIONS[kw][:2]:
                if exp not in expanded:
                    expanded.append(exp)

    return expanded


def get_query_count(section_type: str) -> int:
    """
    根据章节类型获取查询数量

    Args:
        section_type: 章节类型

    Returns:
        建议的查询数量
    """
    count = SECTION_TYPE_QUERIES.get(section_type, SECTION_TYPE_QUERIES["default"])
    # 不超过配置的最大值
    return min(count, config.MAX_QUERIES_PER_SECTION)


def generate_queries(outline: Outline, section_index: int) -> list[str]:
    """
    为指定章节生成检索查询

    Args:
        outline: 论文大纲
        section_index: 章节索引

    Returns:
        检索查询列表
    """
    section = outline.sections[section_index]
    logger.info(f"为章节 '{section.title}' (类型: {section.section_type}) 生成查询")

    queries = []
    max_queries = get_query_count(section.section_type)

    # 1. 基础查询：主题 + 章节标题
    queries.append(f"{outline.topic} {section.title}")

    # 2. 扩展关键词
    expanded_keywords = expand_keywords(section.keywords)
    logger.debug(f"关键词扩展: {section.keywords} -> {expanded_keywords}")

    # 3. 关键词查询
    for keyword in expanded_keywords:
        if len(queries) >= max_queries:
            break
        query = f"{outline.topic} {keyword}"
        if query not in queries:
            queries.append(query)

    # 4. 描述查询（如果还有空间且有描述）
    if len(queries) < max_queries and section.description:
        desc_query = f"{outline.topic} {section.description[:50]}"
        if desc_query not in queries:
            queries.append(desc_query)

    logger.info(f"生成了 {len(queries)} 个查询: {queries}")
    return queries


def generate_all_queries(outline: Outline) -> dict[int, list[str]]:
    """
    为所有章节生成检索查询

    Args:
        outline: 论文大纲

    Returns:
        章节索引到查询列表的映射
    """
    all_queries = {}
    for i in range(len(outline.sections)):
        all_queries[i] = generate_queries(outline, i)
    return all_queries
