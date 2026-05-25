"""
ManuScript v1.0 Planner Agent

职责: 分析章节结构，规划写作策略
"""
from pydantic import BaseModel, Field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import BaseAgent, AgentInput, AgentOutput
from config import config

import httpx


class SectionInfo(BaseModel):
    """章节信息"""
    title: str = Field(..., description="章节标题")
    section_type: str = Field(default="body", description="章节类型: introduction/body/conclusion")
    keywords: list[str] = Field(default_factory=list, description="关键词")
    word_limit: int = Field(default=500, description="字数限制")


class PlannerInput(AgentInput):
    """Planner Agent 输入"""
    paper_topic: str = Field(..., description="论文主题")
    sections: list[SectionInfo] = Field(..., description="章节列表")


class SectionPlan(BaseModel):
    """单个章节的写作计划"""
    section_title: str
    writing_goal: str = Field(..., description="写作目标")
    query_strategy: str = Field(..., description="检索策略说明")
    num_queries: int = Field(default=3, description="建议查询数量")
    expected_source_types: list[str] = Field(default_factory=list, description="预期文献类型")
    key_concepts: list[str] = Field(default_factory=list, description="核心概念")
    word_limit: int = Field(default=500, description="字数限制")


class PlannerOutput(AgentOutput):
    """Planner Agent 输出"""
    paper_topic: str = ""
    section_plans: list[SectionPlan] = Field(default_factory=list)
    total_estimated_sources: int = 0


class PlannerAgent(BaseAgent):
    """
    Planner Agent - 分析章节结构，规划写作策略

    输入: 论文主题 + 章节大纲
    输出: 每个章节的写作计划
    """

    @property
    def name(self) -> str:
        return "Planner"

    async def run(self, input_data: PlannerInput) -> PlannerOutput:
        """执行规划"""
        self.log_start(input_data)

        try:
            section_plans = []

            for section in input_data.sections:
                plan = await self._plan_section(
                    paper_topic=input_data.paper_topic,
                    section=section
                )
                section_plans.append(plan)

            total_sources = sum(p.num_queries * 3 for p in section_plans)

            output = PlannerOutput(
                success=True,
                paper_topic=input_data.paper_topic,
                section_plans=section_plans,
                total_estimated_sources=total_sources
            )

            self.log_end(output)
            return output

        except Exception as e:
            self.log_error(e)
            return PlannerOutput(success=False, error=str(e))

    async def _plan_section(self, paper_topic: str, section: SectionInfo) -> SectionPlan:
        """为单个章节生成写作计划"""

        prompt = f"""你是一个学术写作规划专家。请为以下章节制定写作计划。

论文主题: {paper_topic}
章节标题: {section.title}
章节类型: {section.section_type}
关键词: {', '.join(section.keywords) if section.keywords else '无'}
字数限制: {section.word_limit}

请以JSON格式返回写作计划，包含以下字段:
{{
    "writing_goal": "这个章节的写作目标（一句话）",
    "query_strategy": "文献检索策略说明",
    "num_queries": 建议的检索查询数量(整数, 2-5),
    "expected_source_types": ["预期的文献类型列表，如: 综述论文, 实证研究, 方法论文章"],
    "key_concepts": ["需要覆盖的核心概念列表"]
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
                    "temperature": 0.3
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

        plan_data = json.loads(content)

        return SectionPlan(
            section_title=section.title,
            writing_goal=plan_data.get("writing_goal", ""),
            query_strategy=plan_data.get("query_strategy", ""),
            num_queries=plan_data.get("num_queries", 3),
            expected_source_types=plan_data.get("expected_source_types", []),
            key_concepts=plan_data.get("key_concepts", []),
            word_limit=section.word_limit
        )


async def test_planner():
    """测试 Planner Agent"""
    agent = PlannerAgent()

    test_input = PlannerInput(
        paper_topic="深度学习在医学影像诊断中的应用",
        sections=[
            SectionInfo(
                title="引言",
                section_type="introduction",
                keywords=["深度学习", "医学影像", "诊断"],
                word_limit=300
            ),
            SectionInfo(
                title="卷积神经网络在CT图像分析中的应用",
                section_type="body",
                keywords=["CNN", "CT", "图像分割"],
                word_limit=600
            ),
            SectionInfo(
                title="结论与展望",
                section_type="conclusion",
                keywords=["未来方向", "挑战"],
                word_limit=200
            )
        ]
    )

    print("=" * 60)
    print("测试 Planner Agent")
    print("=" * 60)
    print(f"论文主题: {test_input.paper_topic}")
    print(f"章节数量: {len(test_input.sections)}")
    print()

    output = await agent.run(test_input)

    if output.success:
        print("规划成功!")
        print(f"预计总文献数: {output.total_estimated_sources}")
        print()
        for plan in output.section_plans:
            print(f"【{plan.section_title}】")
            print(f"  写作目标: {plan.writing_goal}")
            print(f"  检索策略: {plan.query_strategy}")
            print(f"  查询数量: {plan.num_queries}")
            print(f"  预期文献类型: {plan.expected_source_types}")
            print(f"  核心概念: {plan.key_concepts}")
            print()
    else:
        print(f"规划失败: {output.error}")

    return output


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_planner())
