"""
ManuScript v1.0 Ranker Agent

职责: 对检索结果进行排序筛选，选出最相关的文档片段
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.retrieval import DocumentChunk
from agents.planner import SectionPlan
from config import config

import httpx


class RankerInput(AgentInput):
    """Ranker Agent 输入"""
    chunks: List[DocumentChunk] = Field(..., description="文档片段列表")
    section_plans: List[SectionPlan] = Field(..., description="章节规划")
    max_chunks_per_section: int = Field(default=5, description="每章节最大片段数")


class RankedChunk(BaseModel):
    """排序后的文档片段"""
    chunk_id: str
    content: str
    document_name: str
    original_score: float = Field(..., description="原始检索分数")
    relevance_score: float = Field(..., description="LLM 评估的相关性分数")
    section_title: str
    relevance_reason: str = Field(default="", description="相关性说明")


class RankerOutput(AgentOutput):
    """Ranker Agent 输出"""
    ranked_chunks: Dict[str, List[RankedChunk]] = Field(
        default_factory=dict,
        description="按章节分组的排序结果"
    )
    total_selected: int = 0
    total_filtered: int = 0


class RankerAgent(BaseAgent):
    """
    Ranker Agent - 对检索结果排序筛选

    输入: 文档片段 + 章节规划
    输出: 按章节分组的排序结果
    """

    @property
    def name(self) -> str:
        return "Ranker"

    async def run(self, input_data: RankerInput) -> RankerOutput:
        """执行排序筛选"""
        self.log_start(input_data)

        try:
            chunks_by_section: Dict[str, List[DocumentChunk]] = {}
            for chunk in input_data.chunks:
                if chunk.section_title not in chunks_by_section:
                    chunks_by_section[chunk.section_title] = []
                chunks_by_section[chunk.section_title].append(chunk)

            plan_map = {p.section_title: p for p in input_data.section_plans}

            ranked_chunks: Dict[str, List[RankedChunk]] = {}
            total_selected = 0
            total_filtered = 0

            for section_title, chunks in chunks_by_section.items():
                plan = plan_map.get(section_title)
                if not plan:
                    continue

                ranked = await self._rank_chunks(
                    chunks=chunks,
                    section_plan=plan,
                    max_chunks=input_data.max_chunks_per_section
                )

                ranked_chunks[section_title] = ranked
                total_selected += len(ranked)
                total_filtered += len(chunks) - len(ranked)

            output = RankerOutput(
                success=True,
                ranked_chunks=ranked_chunks,
                total_selected=total_selected,
                total_filtered=total_filtered
            )

            self.log_end(output)
            return output

        except Exception as e:
            self.log_error(e)
            return RankerOutput(success=False, error=str(e))

    async def _rank_chunks(
        self,
        chunks: List[DocumentChunk],
        section_plan: SectionPlan,
        max_chunks: int
    ) -> List[RankedChunk]:
        """对单个章节的片段进行排序"""

        if not chunks:
            return []

        chunks_text = ""
        for i, chunk in enumerate(chunks[:15]):
            chunks_text += f"\n[{i}] 来源: {chunk.document_name}\n{chunk.content[:500]}\n"

        prompt = f"""你是一个学术文献筛选专家。请评估以下文档片段与章节写作目标的相关性。

章节标题: {section_plan.section_title}
写作目标: {section_plan.writing_goal}
核心概念: {', '.join(section_plan.key_concepts) if section_plan.key_concepts else '无'}

文档片段:
{chunks_text}

请为每个片段评分（0-10分），并选出最相关的 {max_chunks} 个片段。

以JSON格式返回:
{{
    "rankings": [
        {{
            "index": 0,
            "score": 8.5,
            "reason": "直接讨论了核心概念X"
        }}
    ]
}}

评分标准:
- 10分: 完全匹配写作目标，可直接引用
- 7-9分: 高度相关，提供重要支撑
- 4-6分: 部分相关，可作为背景
- 1-3分: 相关性低
- 0分: 完全不相关

只返回评分最高的 {max_chunks} 个片段的JSON，不要其他内容。"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{config.OPENAI_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                }
            )
            response.raise_for_status()
            result = response.json()

        content = result["choices"][0]["message"]["content"]

        import json
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        ranking_data = json.loads(content)

        ranked = []
        for item in ranking_data.get("rankings", []):
            idx = item.get("index", 0)
            if idx < len(chunks):
                chunk = chunks[idx]
                ranked.append(RankedChunk(
                    chunk_id=chunk.chunk_id,
                    content=chunk.content,
                    document_name=chunk.document_name,
                    original_score=chunk.score,
                    relevance_score=item.get("score", 0.0),
                    section_title=chunk.section_title,
                    relevance_reason=item.get("reason", "")
                ))

        ranked.sort(key=lambda x: x.relevance_score, reverse=True)
        ranked = ranked[:max_chunks]

        self.logger.info(
            f"章节 [{section_plan.section_title}] 筛选: {len(chunks)} -> {len(ranked)} 片段"
        )

        return ranked


async def test_ranker():
    """测试 Ranker Agent"""
    from agents.retrieval import DocumentChunk
    from agents.planner import SectionPlan

    agent = RankerAgent()

    test_input = RankerInput(
        chunks=[
            DocumentChunk(
                chunk_id="1",
                content="深度学习在医学影像分析中取得了显著进展，特别是在CT和MRI图像的自动诊断方面。卷积神经网络能够有效提取图像特征...",
                document_name="深度学习医学影像综述.pdf",
                score=0.85,
                section_title="引言",
                query_text="deep learning medical imaging"
            ),
            DocumentChunk(
                chunk_id="2",
                content="本研究提出了一种基于U-Net的肝脏肿瘤分割方法，在公开数据集上达到了92%的Dice系数...",
                document_name="肝脏肿瘤分割方法.pdf",
                score=0.78,
                section_title="引言",
                query_text="deep learning medical imaging"
            ),
            DocumentChunk(
                chunk_id="3",
                content="机器学习算法在金融风控中的应用越来越广泛，包括信用评分、欺诈检测等场景...",
                document_name="机器学习金融应用.pdf",
                score=0.45,
                section_title="引言",
                query_text="deep learning medical imaging"
            )
        ],
        section_plans=[
            SectionPlan(
                section_title="引言",
                writing_goal="介绍深度学习在医学影像领域的重要性",
                query_strategy="检索综述性文献",
                num_queries=2,
                expected_source_types=["综述论文"],
                key_concepts=["深度学习", "医学影像", "自动诊断"]
            )
        ],
        max_chunks_per_section=2
    )

    print("=" * 60)
    print("测试 Ranker Agent")
    print("=" * 60)
    print(f"输入片段数: {len(test_input.chunks)}")
    print(f"每章节最大片段数: {test_input.max_chunks_per_section}")
    print()

    output = await agent.run(test_input)

    if output.success:
        print(f"排序成功!")
        print(f"选中: {output.total_selected}, 过滤: {output.total_filtered}")
        print()
        for section, chunks in output.ranked_chunks.items():
            print(f"【{section}】")
            for chunk in chunks:
                print(f"  [{chunk.relevance_score:.1f}] {chunk.document_name}")
                print(f"    原因: {chunk.relevance_reason}")
            print()
    else:
        print(f"排序失败: {output.error}")

    return output


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ranker())
