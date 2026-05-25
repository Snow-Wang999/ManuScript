"""
ManuScript v1.0 Writer Agent

职责: 根据筛选后的文献片段生成带引用的学术文本
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.ranker import RankedChunk
from agents.planner import SectionPlan
from config import config

import httpx


class Citation(BaseModel):
    """引用信息"""
    citation_id: str = Field(..., description="引用ID，如 [1]")
    document_name: str = Field(..., description="文档名称")
    cited_content: str = Field(default="", description="被引用的内容摘要")


class SectionDraft(BaseModel):
    """章节草稿"""
    section_title: str
    content: str = Field(..., description="生成的文本内容")
    citations: List[Citation] = Field(default_factory=list, description="引用列表")
    word_count: int = 0


class WriterInput(AgentInput):
    """Writer Agent 输入"""
    paper_topic: str = Field(..., description="论文主题")
    section_plans: List[SectionPlan] = Field(..., description="章节规划")
    ranked_chunks: Dict[str, List[RankedChunk]] = Field(..., description="按章节分组的文献片段")


class WriterOutput(AgentOutput):
    """Writer Agent 输出"""
    drafts: List[SectionDraft] = Field(default_factory=list)
    all_citations: List[Citation] = Field(default_factory=list)
    total_words: int = 0


class WriterAgent(BaseAgent):
    """
    Writer Agent - 生成带引用的学术文本

    输入: 论文主题 + 章节规划 + 筛选后的文献
    输出: 章节草稿 + 引用列表
    """

    @property
    def name(self) -> str:
        return "Writer"

    async def run(self, input_data: WriterInput) -> WriterOutput:
        """执行写作"""
        self.log_start(input_data)

        try:
            drafts = []
            all_citations = []
            citation_counter = 1

            for plan in input_data.section_plans:
                chunks = input_data.ranked_chunks.get(plan.section_title, [])

                draft, citations, citation_counter = await self._write_section(
                    paper_topic=input_data.paper_topic,
                    section_plan=plan,
                    chunks=chunks,
                    citation_start=citation_counter
                )

                drafts.append(draft)
                all_citations.extend(citations)

            total_words = sum(d.word_count for d in drafts)

            output = WriterOutput(
                success=True,
                drafts=drafts,
                all_citations=all_citations,
                total_words=total_words
            )

            self.log_end(output)
            return output

        except Exception as e:
            self.log_error(e)
            return WriterOutput(success=False, error=str(e))

    async def _write_section(
        self,
        paper_topic: str,
        section_plan: SectionPlan,
        chunks: List[RankedChunk],
        citation_start: int
    ) -> tuple:
        """生成单个章节的文本"""

        sources_text = ""
        citation_map = {}

        for i, chunk in enumerate(chunks):
            cid = citation_start + i
            citation_map[cid] = chunk
            sources_text += f"\n[{cid}] 来源: {chunk.document_name}\n{chunk.content[:600]}\n"

        if not sources_text:
            sources_text = "（无可用文献）"

        prompt = f"""你是一个学术论文写作专家。请根据以下信息撰写论文章节。

论文主题: {paper_topic}
章节标题: {section_plan.section_title}
写作目标: {section_plan.writing_goal}
字数要求: 约 {section_plan.word_limit} 字

可用文献:
{sources_text}

写作要求:
1. 使用学术论文的正式语言风格
2. 必须在适当位置插入引用标记，如 [1]、[2]
3. 引用必须准确对应上面提供的文献
4. 不要编造文献中没有的信息
5. 确保逻辑连贯，段落之间有良好的过渡
6. 如果文献不足，可以适当概述但要标注需要补充引用

请直接输出章节内容，不要添加标题或其他说明。"""

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{config.OPENAI_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            result = response.json()

        content = result["choices"][0]["message"]["content"]

        import re
        cited_ids = set(map(int, re.findall(r'\[(\d+)\]', content)))

        citations = []
        for cid in sorted(cited_ids):
            if cid in citation_map:
                chunk = citation_map[cid]
                citations.append(Citation(
                    citation_id=f"[{cid}]",
                    document_name=chunk.document_name,
                    cited_content=chunk.content[:200]
                ))

        word_count = len(content)

        draft = SectionDraft(
            section_title=section_plan.section_title,
            content=content,
            citations=citations,
            word_count=word_count
        )

        self.logger.info(
            f"章节 [{section_plan.section_title}] 生成完成: {word_count} 字, {len(citations)} 个引用"
        )

        next_citation = citation_start + len(chunks)
        return draft, citations, next_citation


async def test_writer():
    """测试 Writer Agent"""
    from agents.ranker import RankedChunk
    from agents.planner import SectionPlan

    agent = WriterAgent()

    test_input = WriterInput(
        paper_topic="深度学习在医学影像诊断中的应用",
        section_plans=[
            SectionPlan(
                section_title="引言",
                writing_goal="介绍深度学习在医学影像领域的重要性和发展背景",
                query_strategy="检索综述性文献",
                num_queries=2,
                expected_source_types=["综述论文"],
                key_concepts=["深度学习", "医学影像", "自动诊断"],
                word_limit=300
            )
        ],
        ranked_chunks={
            "引言": [
                RankedChunk(
                    chunk_id="1",
                    content="深度学习在医学影像分析中取得了显著进展。卷积神经网络（CNN）能够自动从图像中提取层次化特征，在肺结节检测、眼底疾病筛查等任务上已达到甚至超越人类专家的诊断水平。",
                    document_name="深度学习医学影像综述.pdf",
                    original_score=0.85,
                    relevance_score=9.0,
                    section_title="引言",
                    relevance_reason="直接讨论深度学习在医学影像中的应用"
                ),
                RankedChunk(
                    chunk_id="2",
                    content="医学影像数据量的快速增长给放射科医生带来了巨大压力。人工智能辅助诊断系统的引入可以有效提高诊断效率，减少漏诊率，并为偏远地区提供专家级的诊断服务。",
                    document_name="AI辅助诊断系统评估.pdf",
                    original_score=0.80,
                    relevance_score=8.5,
                    section_title="引言",
                    relevance_reason="讨论AI辅助诊断的必要性"
                )
            ]
        }
    )

    print("=" * 60)
    print("测试 Writer Agent")
    print("=" * 60)
    print(f"论文主题: {test_input.paper_topic}")
    print(f"章节数: {len(test_input.section_plans)}")
    print()

    output = await agent.run(test_input)

    if output.success:
        print(f"写作成功! 总字数: {output.total_words}")
        print(f"总引用数: {len(output.all_citations)}")
        print()
        for draft in output.drafts:
            print(f"【{draft.section_title}】({draft.word_count} 字)")
            print("-" * 40)
            print(draft.content)
            print()
            print("引用列表:")
            for c in draft.citations:
                print(f"  {c.citation_id} {c.document_name}")
            print()
    else:
        print(f"写作失败: {output.error}")

    return output


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_writer())
