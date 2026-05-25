"""
ManuScript 评测指标

评估各版本的表现
"""
import re
from dataclasses import dataclass


@dataclass
class EvaluationResult:
    """评测结果"""
    version: str
    test_case_id: str
    citation_accuracy: float  # 引用准确率 (0-1)
    retrieval_relevance: float  # 检索相关性 (0-1)
    text_quality: float  # 文本质量 (0-1)
    latency_ms: float  # 响应延迟 (毫秒)
    overall_score: float  # 综合得分

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "test_case_id": self.test_case_id,
            "citation_accuracy": self.citation_accuracy,
            "retrieval_relevance": self.retrieval_relevance,
            "text_quality": self.text_quality,
            "latency_ms": self.latency_ms,
            "overall_score": self.overall_score
        }


def calculate_citation_accuracy(draft: str, chunks: list[dict]) -> float:
    """
    计算引用准确率

    检查生成文本中的引用标记 [1], [2] 等是否有对应的 chunk

    Args:
        draft: 生成的草稿
        chunks: 检索到的 chunks

    Returns:
        准确率 (0-1)
    """
    # 提取引用标记
    citations = re.findall(r'\[(\d+)\]', draft)
    if not citations:
        return 0.0

    # 去重
    unique_citations = set(int(c) for c in citations)

    # 检查每个引用是否有对应的 chunk
    valid_count = sum(1 for c in unique_citations if c <= len(chunks))

    return valid_count / len(unique_citations) if unique_citations else 0.0


def calculate_retrieval_relevance(query: str, chunks: list[dict]) -> float:
    """
    计算检索相关性

    基于 chunk 的 score 字段

    Args:
        query: 检索查询
        chunks: 检索到的 chunks

    Returns:
        平均相关性 (0-1)
    """
    if not chunks:
        return 0.0

    scores = [chunk.get("score", 0) for chunk in chunks]
    return sum(scores) / len(scores)


def calculate_overall_score(
    citation_accuracy: float,
    retrieval_relevance: float,
    text_quality: float,
    latency_ms: float,
    weights: dict | None = None
) -> float:
    """
    计算综合得分

    Args:
        citation_accuracy: 引用准确率
        retrieval_relevance: 检索相关性
        text_quality: 文本质量
        latency_ms: 响应延迟
        weights: 权重配置

    Returns:
        综合得分 (0-1)
    """
    if weights is None:
        weights = {
            "citation_accuracy": 0.4,
            "retrieval_relevance": 0.3,
            "text_quality": 0.2,
            "latency": 0.1
        }

    # 延迟转换为分数 (3秒以内得满分，超过10秒得0分)
    latency_score = max(0, 1 - (latency_ms - 3000) / 7000) if latency_ms > 3000 else 1.0

    return (
        weights["citation_accuracy"] * citation_accuracy +
        weights["retrieval_relevance"] * retrieval_relevance +
        weights["text_quality"] * text_quality +
        weights["latency"] * latency_score
    )


def calculate_citation_count(draft: str) -> int:
    """
    统计引用数量

    Args:
        draft: 生成的草稿

    Returns:
        引用数量
    """
    citations = re.findall(r'\[(\d+)\]', draft)
    return len(set(int(c) for c in citations))


def check_min_requirements(
    draft: str,
    chunks: list[dict],
    min_citations: int = 2,
    min_length: int = 100
) -> dict:
    """
    检查是否满足最低要求

    Args:
        draft: 生成的草稿
        chunks: 检索到的 chunks
        min_citations: 最少引用数
        min_length: 最少字符数

    Returns:
        检查结果
    """
    citation_count = calculate_citation_count(draft)
    text_length = len(draft)

    return {
        "citation_count": citation_count,
        "text_length": text_length,
        "meets_citation_requirement": citation_count >= min_citations,
        "meets_length_requirement": text_length >= min_length,
        "passes": citation_count >= min_citations and text_length >= min_length
    }


def aggregate_results(results: list[EvaluationResult]) -> dict:
    """
    聚合多个评测结果

    Args:
        results: 评测结果列表

    Returns:
        聚合统计
    """
    if not results:
        return {}

    n = len(results)
    return {
        "count": n,
        "avg_citation_accuracy": sum(r.citation_accuracy for r in results) / n,
        "avg_retrieval_relevance": sum(r.retrieval_relevance for r in results) / n,
        "avg_text_quality": sum(r.text_quality for r in results) / n,
        "avg_latency_ms": sum(r.latency_ms for r in results) / n,
        "avg_overall_score": sum(r.overall_score for r in results) / n,
        "min_overall_score": min(r.overall_score for r in results),
        "max_overall_score": max(r.overall_score for r in results),
    }
