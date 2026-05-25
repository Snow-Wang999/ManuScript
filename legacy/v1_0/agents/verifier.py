"""
ManuScript v1.0 Verifier Agent

职责: 验证生成文本中的引用准确性
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.writer import SectionDraft, Citation
from config import config

import httpx


class CitationVerification(BaseModel):
    """单个引用的验证结果"""
    citation_id: str
    document_name: str
    is_valid: bool = Field(..., description="引用是否有效")
    accuracy_score: float = Field(..., description="准确性分数 0-10")
    issue: Optional[str] = Field(default=None, description="问题描述")
    suggestion: Optional[str] = Field(default=None, description="修改建议")


class SectionVerification(BaseModel):
    """章节验证结果"""
    section_title: str
    overall_score: float = Field(..., description="整体引用质量分数")
    citation_results: List[CitationVerification] = Field(default_factory=list)
    issues_found: int = 0
    suggestions: List[str] = Field(default_factory=list)


class VerifierInput(AgentInput):
    """Verifier Agent 输入"""
    drafts: List[SectionDraft] = Field(..., description="章节草稿列表")
    source_chunks: Dict[str, str] = Field(
        default_factory=dict,
        description="引用ID到原文内容的映射"
    )


class VerifierOutput(AgentOutput):
    """Verifier Agent 输出"""
    verifications: List[SectionVerification] = Field(default_factory=list)
    overall_accuracy: float = 0.0
    total_citations: int = 0
    valid_citations: int = 0
    needs_revision: bool = False


class VerifierAgent(BaseAgent):
    """
    Verifier Agent - 验证引用准确性

    输入: 章节草稿 + 原文引用映射
    输出: 验证结果 + 修改建议
    """

    @property
    def name(self) -> str:
        return "Verifier"

    async def run(self, input_data: VerifierInput) -> VerifierOutput:
        """执行验证"""
        self.log_start(input_data)

        try:
            verifications = []
            total_citations = 0
            valid_citations = 0

            for draft in input_data.drafts:
                verification = await self._verify_section(
                    draft=draft,
                    source_chunks=input_data.source_chunks
                )
                verifications.append(verification)

                total_citations += len(verification.citation_results)
                valid_citations += sum(
                    1 for c in verification.citation_results if c.is_valid
                )

            overall_accuracy = (
                valid_citations / total_citations * 10
                if total_citations > 0 else 0.0
            )

            needs_revision = overall_accuracy < 7.0 or any(
                v.issues_found > 0 for v in verifications
            )

            output = VerifierOutput(
                success=True,
                verifications=verifications,
                overall_accuracy=overall_accuracy,
                total_citations=total_citations,
                valid_citations=valid_citations,
                needs_revision=needs_revision
            )

            self.log_end(output)
            return output

        except Exception as e:
            self.log_error(e)
            return VerifierOutput(success=False, error=str(e))

    async def _verify_section(
        self,
        draft: SectionDraft,
        source_chunks: Dict[str, str]
    ) -> SectionVerification:
        """验证单个章节的引用"""

        if not draft.citations:
            return SectionVerification(
                section_title=draft.section_title,
                overall_score=10.0,
                citation_results=[],
                issues_found=0,
                suggestions=[]
            )

        citations_info = ""
        for citation in draft.citations:
            source_content = source_chunks.get(
                citation.citation_id,
                citation.cited_content
            )
            citations_info += f"\n{citation.citation_id} 来源: {citation.document_name}\n原文: {source_content[:400]}\n"

        prompt = f"""你是一个学术引用审核专家。请验证以下文本中的引用是否准确。

生成的文本:
{draft.content}

引用的原文:
{citations_info}

请检查每个引用是否:
1. 准确反映了原文的含义
2. 没有曲解或过度概括
3. 引用位置是否恰当

以JSON格式返回验证结果:
{{
    "overall_score": 8.5,
    "results": [
        {{
            "citation_id": "[1]",
            "is_valid": true,
            "accuracy_score": 9.0,
            "issue": null,
            "suggestion": null
        }},
        {{
            "citation_id": "[2]",
            "is_valid": false,
            "accuracy_score": 4.0,
            "issue": "引用内容与原文不符",
            "suggestion": "建议修改为..."
        }}
    ],
    "general_suggestions": ["整体建议1", "整体建议2"]
}}

只返回JSON，不要其他内容。"""

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

        verification_data = json.loads(content)

        citation_results = []
        for item in verification_data.get("results", []):
            citation_results.append(CitationVerification(
                citation_id=item.get("citation_id", ""),
                document_name=next(
                    (c.document_name for c in draft.citations
                     if c.citation_id == item.get("citation_id")),
                    ""
                ),
                is_valid=item.get("is_valid", True),
                accuracy_score=item.get("accuracy_score", 0.0),
                issue=item.get("issue"),
                suggestion=item.get("suggestion")
            ))

        issues_found = sum(1 for c in citation_results if not c.is_valid)

        verification = SectionVerification(
            section_title=draft.section_title,
            overall_score=verification_data.get("overall_score", 0.0),
            citation_results=citation_results,
            issues_found=issues_found,
            suggestions=verification_data.get("general_suggestions", [])
        )

        self.logger.info(
            f"章节 [{draft.section_title}] 验证完成: "
            f"分数 {verification.overall_score:.1f}, 问题 {issues_found} 个"
        )

        return verification


async def test_verifier():
    """测试 Verifier Agent"""
    from agents.writer import SectionDraft, Citation

    agent = VerifierAgent()

    test_input = VerifierInput(
        drafts=[
            SectionDraft(
                section_title="引言",
                content="""深度学习技术在医学影像诊断领域取得了重大突破。卷积神经网络能够自动从医学图像中提取多层次特征，在肺结节检测和眼底疾病筛查等任务上已达到专家级诊断水平[1]。随着医学影像数据量的快速增长，人工智能辅助诊断系统的引入可以显著提高诊断效率，降低漏诊率[2]。""",
                citations=[
                    Citation(
                        citation_id="[1]",
                        document_name="深度学习医学影像综述.pdf",
                        cited_content="卷积神经网络能够自动从图像中提取层次化特征，在肺结节检测、眼底疾病筛查等任务上已达到甚至超越人类专家的诊断水平。"
                    ),
                    Citation(
                        citation_id="[2]",
                        document_name="AI辅助诊断系统评估.pdf",
                        cited_content="医学影像数据量的快速增长给放射科医生带来了巨大压力。人工智能辅助诊断系统的引入可以有效提高诊断效率，减少漏诊率。"
                    )
                ],
                word_count=150
            )
        ],
        source_chunks={
            "[1]": "卷积神经网络能够自动从图像中提取层次化特征，在肺结节检测、眼底疾病筛查等任务上已达到甚至超越人类专家的诊断水平。",
            "[2]": "医学影像数据量的快速增长给放射科医生带来了巨大压力。人工智能辅助诊断系统的引入可以有效提高诊断效率，减少漏诊率。"
        }
    )

    print("=" * 60)
    print("测试 Verifier Agent")
    print("=" * 60)
    print(f"待验证章节数: {len(test_input.drafts)}")
    print()

    output = await agent.run(test_input)

    if output.success:
        print(f"验证完成!")
        print(f"整体准确率: {output.overall_accuracy:.1f}/10")
        print(f"总引用数: {output.total_citations}")
        print(f"有效引用: {output.valid_citations}")
        print(f"需要修订: {'是' if output.needs_revision else '否'}")
        print()

        for v in output.verifications:
            print(f"【{v.section_title}】分数: {v.overall_score:.1f}")
            for c in v.citation_results:
                status = "[OK]" if c.is_valid else "[X]"
                print(f"  {status} {c.citation_id} ({c.accuracy_score:.1f})")
                if c.issue:
                    print(f"    问题: {c.issue}")
                if c.suggestion:
                    print(f"    建议: {c.suggestion}")
            if v.suggestions:
                print("  整体建议:")
                for s in v.suggestions:
                    print(f"    - {s}")
            print()
    else:
        print(f"验证失败: {output.error}")

    return output


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_verifier())
