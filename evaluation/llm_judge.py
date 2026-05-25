"""
ManuScript LLM-as-Judge 评测模块

使用 LLM 评估生成文本的引用准确性（引用幻觉检测）

核心指标：
- Faithfulness（忠实度）: 生成的句子是否被引用的原文支撑
- Citation Hallucination Rate（引用幻觉率）: 没有被支撑的引用比例
"""
import re
import json
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx
from openai import AsyncOpenAI


class SupportLevel(Enum):
    """引用支撑程度"""
    SUPPORT = "support"          # 原文支撑该句子
    PARTIAL = "partial"          # 部分支撑
    NEUTRAL = "neutral"          # 无关
    CONTRADICT = "contradict"    # 原文与句子矛盾


@dataclass
class CitationWithContext:
    """带上下文的引用"""
    citation_index: int          # 引用编号 [1], [2] 等
    sentence: str                # 包含引用的句子
    source_content: str          # 引用对应的原文内容
    source_doc_name: str = ""    # 原文文档名


@dataclass
class JudgeResult:
    """单个引用的判断结果"""
    citation: CitationWithContext
    support_level: SupportLevel
    confidence: float            # 置信度 0-1
    reasoning: str               # 判断理由


@dataclass
class FaithfulnessReport:
    """忠实度评测报告"""
    total_citations: int         # 总引用数
    supported: int               # 被支撑的引用数
    partial: int                 # 部分支撑
    neutral: int                 # 无关
    contradicted: int            # 矛盾

    faithfulness_score: float    # 忠实度分数 (0-1)
    hallucination_rate: float    # 幻觉率 (0-1)

    details: list[JudgeResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_citations": self.total_citations,
            "supported": self.supported,
            "partial": self.partial,
            "neutral": self.neutral,
            "contradicted": self.contradicted,
            "faithfulness_score": round(self.faithfulness_score, 3),
            "hallucination_rate": round(self.hallucination_rate, 3),
            "details": [
                {
                    "citation_index": d.citation.citation_index,
                    "sentence": d.citation.sentence[:100] + "..." if len(d.citation.sentence) > 100 else d.citation.sentence,
                    "support_level": d.support_level.value,
                    "confidence": round(d.confidence, 2),
                    "reasoning": d.reasoning
                }
                for d in self.details
            ]
        }


def extract_citations_with_context(draft: str, chunks: list[dict]) -> list[CitationWithContext]:
    """
    从草稿中提取引用及其上下文

    Args:
        draft: 生成的草稿文本
        chunks: 检索到的 chunks 列表

    Returns:
        带上下文的引用列表
    """
    citations = []

    # 按句子分割（支持中英文句号）
    sentences = re.split(r'(?<=[。！？.!?])\s*', draft)

    for sentence in sentences:
        if not sentence.strip():
            continue

        # 查找句子中的引用标记 [1], [2] 等
        citation_matches = re.findall(r'\[(\d+)\]', sentence)

        for citation_num in citation_matches:
            idx = int(citation_num)

            # 检查 chunk 是否存在
            if idx <= len(chunks) and idx > 0:
                chunk = chunks[idx - 1]
                citations.append(CitationWithContext(
                    citation_index=idx,
                    sentence=sentence.strip(),
                    source_content=chunk.get("content", ""),
                    source_doc_name=chunk.get("document_name", f"chunk_{idx}")
                ))

    return citations


class LLMJudge:
    """
    LLM 评判器

    使用 LLM 判断引用是否支撑生成的句子
    """

    JUDGE_PROMPT = """你是一个学术引用准确性评判专家。你的任务是判断一个学术句子是否被其引用的原文所支撑。

## 待评判的句子
{sentence}

## 引用的原文内容
{source_content}

## 评判标准
- **support**: 原文内容明确支撑该句子的观点或信息
- **partial**: 原文部分支撑该句子，但有些信息无法从原文推断
- **neutral**: 原文与该句子无直接关系，既不支撑也不矛盾
- **contradict**: 原文与该句子的观点或信息相矛盾

## 输出格式
请以 JSON 格式输出，包含以下字段：
```json
{{
    "support_level": "support/partial/neutral/contradict",
    "confidence": 0.0-1.0,
    "reasoning": "简短说明判断理由（不超过50字）"
}}
```

请直接输出 JSON，不要有其他内容。"""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str = "gpt-4o-mini"
    ):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model

    async def judge_single(self, citation: CitationWithContext) -> JudgeResult:
        """
        判断单个引用是否支撑句子

        Args:
            citation: 带上下文的引用

        Returns:
            判断结果
        """
        prompt = self.JUDGE_PROMPT.format(
            sentence=citation.sentence,
            source_content=citation.source_content[:2000]  # 限制长度
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # 低温度保证一致性
                max_tokens=200
            )

            result_text = response.choices[0].message.content

            # 解析 JSON
            json_match = re.search(r'\{[^{}]+\}', result_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                support_level = SupportLevel(data.get("support_level", "neutral"))
                confidence = float(data.get("confidence", 0.5))
                reasoning = data.get("reasoning", "")
            else:
                # 解析失败，默认 neutral
                support_level = SupportLevel.NEUTRAL
                confidence = 0.5
                reasoning = "解析失败"

        except Exception as e:
            support_level = SupportLevel.NEUTRAL
            confidence = 0.0
            reasoning = f"评判出错: {str(e)[:50]}"

        return JudgeResult(
            citation=citation,
            support_level=support_level,
            confidence=confidence,
            reasoning=reasoning
        )

    async def judge_batch(
        self,
        citations: list[CitationWithContext],
        concurrency: int = 5
    ) -> list[JudgeResult]:
        """
        批量判断引用

        Args:
            citations: 引用列表
            concurrency: 并发数

        Returns:
            判断结果列表
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def judge_with_semaphore(citation: CitationWithContext) -> JudgeResult:
            async with semaphore:
                return await self.judge_single(citation)

        tasks = [judge_with_semaphore(c) for c in citations]
        return await asyncio.gather(*tasks)

    async def evaluate_faithfulness(
        self,
        draft: str,
        chunks: list[dict],
        concurrency: int = 5
    ) -> FaithfulnessReport:
        """
        评估草稿的忠实度

        Args:
            draft: 生成的草稿
            chunks: 检索到的 chunks
            concurrency: 并发数

        Returns:
            忠实度评测报告
        """
        # 提取引用
        citations = extract_citations_with_context(draft, chunks)

        if not citations:
            return FaithfulnessReport(
                total_citations=0,
                supported=0,
                partial=0,
                neutral=0,
                contradicted=0,
                faithfulness_score=0.0,
                hallucination_rate=1.0,
                details=[]
            )

        # 批量判断
        results = await self.judge_batch(citations, concurrency)

        # 统计结果
        supported = sum(1 for r in results if r.support_level == SupportLevel.SUPPORT)
        partial = sum(1 for r in results if r.support_level == SupportLevel.PARTIAL)
        neutral = sum(1 for r in results if r.support_level == SupportLevel.NEUTRAL)
        contradicted = sum(1 for r in results if r.support_level == SupportLevel.CONTRADICT)

        total = len(results)

        # 计算分数
        # 忠实度 = (完全支撑 * 1.0 + 部分支撑 * 0.5) / 总数
        faithfulness_score = (supported + partial * 0.5) / total if total > 0 else 0.0

        # 幻觉率 = (无关 + 矛盾) / 总数
        hallucination_rate = (neutral + contradicted) / total if total > 0 else 1.0

        return FaithfulnessReport(
            total_citations=total,
            supported=supported,
            partial=partial,
            neutral=neutral,
            contradicted=contradicted,
            faithfulness_score=faithfulness_score,
            hallucination_rate=hallucination_rate,
            details=results
        )


def create_judge(
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = "gpt-4o-mini"
) -> LLMJudge | None:
    """
    创建 LLM 评判器

    Args:
        api_key: OpenAI API Key（不传则从环境变量读取）
        base_url: API Base URL
        model: 模型名称

    Returns:
        LLMJudge 实例，如果配置不完整则返回 None
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()

    api_key = api_key or os.getenv("OPENAI_API_KEY")
    base_url = base_url or os.getenv("OPENAI_API_BASE")
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        print("警告: 未配置 OPENAI_API_KEY，LLM Judge 不可用")
        return None

    return LLMJudge(api_key=api_key, base_url=base_url, model=model)


async def quick_evaluate(draft: str, chunks: list[dict]) -> FaithfulnessReport | None:
    """
    快速评估（便捷函数）

    Args:
        draft: 生成的草稿
        chunks: 检索到的 chunks

    Returns:
        忠实度报告
    """
    judge = create_judge()
    if judge is None:
        return None

    return await judge.evaluate_faithfulness(draft, chunks)


if __name__ == "__main__":
    # 测试
    sample_draft = """
    深度学习技术在医学图像分析领域取得了显著进展[1]。研究表明，
    卷积神经网络能够有效提取医学图像的特征，实现高精度的病灶检测[2]。
    通过大规模数据训练，这些模型已经超越了人类医生的诊断准确率[3]。
    """

    sample_chunks = [
        {
            "content": "近年来，深度学习在医学图像分析中展现出巨大潜力，多项研究证明其在疾病诊断方面的有效性。",
            "document_name": "paper1.pdf"
        },
        {
            "content": "卷积神经网络（CNN）通过卷积层、池化层等结构，能够自动学习图像的层次化特征表示。",
            "document_name": "paper2.pdf"
        },
        {
            "content": "虽然深度学习模型表现优异，但在某些复杂病例中仍需要专业医生的判断。",
            "document_name": "paper3.pdf"
        }
    ]

    async def test():
        judge = create_judge()
        if judge:
            report = await judge.evaluate_faithfulness(sample_draft, sample_chunks)
            print("=" * 50)
            print("忠实度评测报告")
            print("=" * 50)
            print(f"总引用数: {report.total_citations}")
            print(f"支撑: {report.supported}")
            print(f"部分支撑: {report.partial}")
            print(f"无关: {report.neutral}")
            print(f"矛盾: {report.contradicted}")
            print(f"忠实度分数: {report.faithfulness_score:.3f}")
            print(f"幻觉率: {report.hallucination_rate:.3f}")
            print("\n详细结果:")
            for detail in report.details:
                print(f"  [{detail.citation.citation_index}] {detail.support_level.value}")
                print(f"      理由: {detail.reasoning}")
        else:
            print("LLM Judge 未配置")

    asyncio.run(test())
