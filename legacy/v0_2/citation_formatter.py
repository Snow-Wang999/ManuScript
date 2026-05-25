# -*- coding: utf-8 -*-
"""
ManuScript v0.2 Citation Formatter

将引用标记转换为完整引用格式，生成引用列表
"""
import re
from dataclasses import dataclass
from logger import get_logger

logger = get_logger(__name__)


@dataclass
class Citation:
    """引用信息"""
    index: int              # 引用编号 [1], [2] 等
    document_name: str      # 文档名称
    content_snippet: str    # 内容摘要
    score: float = 0.0      # 相关度分数


class CitationFormatter:
    """引用格式化器"""

    def __init__(self, format_style: str = "simple"):
        """
        初始化格式化器

        Args:
            format_style: 引用格式风格 (simple, apa, mla)
        """
        self.format_style = format_style
        self.citations: list[Citation] = []

    def extract_citations_from_chunks(self, chunks: list[dict]) -> list[Citation]:
        """
        从 RAGFlow chunks 提取引用信息

        Args:
            chunks: RAGFlow 返回的 chunks 列表

        Returns:
            引用信息列表
        """
        self.citations = []

        for i, chunk in enumerate(chunks, 1):
            citation = Citation(
                index=i,
                document_name=chunk.get("document_name", "未知来源"),
                content_snippet=chunk.get("content", "")[:100],
                score=chunk.get("score", 0.0)
            )
            self.citations.append(citation)

        logger.info(f"提取了 {len(self.citations)} 个引用")
        return self.citations

    def format_single_citation(self, citation: Citation) -> str:
        """
        格式化单个引用

        Args:
            citation: 引用信息

        Returns:
            格式化后的引用字符串
        """
        if self.format_style == "apa":
            # APA 风格（简化版，因为我们没有完整的元数据）
            return f"[{citation.index}] {citation.document_name}"
        elif self.format_style == "mla":
            # MLA 风格（简化版）
            return f"[{citation.index}] \"{citation.document_name}\""
        else:
            # 简单风格
            return f"[{citation.index}] {citation.document_name}"

    def generate_reference_list(self) -> str:
        """
        生成完整的引用列表

        Returns:
            格式化的引用列表字符串
        """
        if not self.citations:
            return ""

        lines = ["", "参考文献：", "-" * 40]

        for citation in self.citations:
            formatted = self.format_single_citation(citation)
            lines.append(formatted)

        return "\n".join(lines)

    def validate_citations_in_text(self, text: str) -> dict:
        """
        验证文本中的引用标记

        Args:
            text: 生成的文本

        Returns:
            验证结果，包含使用的引用和缺失的引用
        """
        # 提取文本中所有的引用标记 [1], [2], [1,2], [1-3] 等
        pattern = r'\[(\d+(?:[-,]\d+)*)\]'
        matches = re.findall(pattern, text)

        used_indices = set()
        for match in matches:
            # 处理范围 [1-3]
            if '-' in match:
                start, end = map(int, match.split('-'))
                used_indices.update(range(start, end + 1))
            # 处理多个 [1,2,3]
            elif ',' in match:
                used_indices.update(map(int, match.split(',')))
            else:
                used_indices.add(int(match))

        # 检查哪些引用被使用，哪些缺失
        available_indices = {c.index for c in self.citations}
        used = used_indices & available_indices
        missing = used_indices - available_indices

        result = {
            "used_citations": sorted(used),
            "missing_citations": sorted(missing),
            "unused_citations": sorted(available_indices - used),
            "is_valid": len(missing) == 0
        }

        logger.info(f"引用验证结果: 使用={len(used)}, 缺失={len(missing)}")
        return result

    def format_output(self, draft: str) -> str:
        """
        格式化最终输出（草稿 + 引用列表）

        Args:
            draft: 生成的草稿文本

        Returns:
            包含引用列表的完整输出
        """
        reference_list = self.generate_reference_list()
        return f"{draft}\n{reference_list}"


def create_citation_mapping(chunks: list[dict]) -> dict[int, str]:
    """
    创建引用编号到文档名的映射

    Args:
        chunks: RAGFlow chunks

    Returns:
        编号到文档名的映射
    """
    return {
        i: chunk.get("document_name", "未知")
        for i, chunk in enumerate(chunks, 1)
    }
