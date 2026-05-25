"""
ManuScript v1.0 Query Generator Agent

职责: 根据写作计划生成文献检索查询
"""
from typing import List, Optional
from pydantic import BaseModel, Field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.planner import SectionPlan
from config import config

import httpx


class QueryGeneratorInput(AgentInput):
    """Query Generator Agent 输入"""
    paper_topic: str = Field(..., description="论文主题")
    section_plans: List[SectionPlan] = Field(..., description="章节规划列表")


class SearchQuery(BaseModel):
    """单个检索查询"""
    section_title: str = Field(..., description="所属章节")
    query_text: str = Field(..., description="查询文本")
    query_type: str = Field(default="semantic", description="查询类型: semantic/keyword")
    priority: int = Field(default=1, description="优先级 1-3")


class QueryGeneratorOutput(AgentOutput):
    """Query Generator Agent 输出"""
    queries: List[SearchQuery] = Field(default_factory=list)
    total_queries: int = 0


class QueryGeneratorAgent(BaseAgent):
    """
    Query Generator Agent - 生成文献检索查询

    输入: 论文主题 + 章节规划
    输出: 检索查询列表
    """

    @property
    def name(self) -> str:
        return "QueryGenerator"

    async def run(self, input_data: QueryGeneratorInput) -> QueryGeneratorOutput:
        """执行查询生成"""
        self.log_start(input_data)

        try:
            all_queries = []

            for plan in input_data.section_plans:
                queries = await self._generate_queries(
                    paper_topic=input_data.paper_topic,
                    section_plan=plan
                )
                all_queries.extend(queries)

            output = QueryGeneratorOutput(
                success=True,
                queries=all_queries,
                total_queries=len(all_queries)
            )

            self.log_end(output)
            return output

        except Exception as e:
            self.log_error(e)
            return QueryGeneratorOutput(success=False, error=str(e))

    async def _generate_queries(
        self,
        paper_topic: str,
        section_plan: SectionPlan
    ) -> List[SearchQuery]:
        """为单个章节生成检索查询"""

        prompt = f"""你是一个学术文献检索专家。请根据以下信息生成检索查询。

论文主题: {paper_topic}
章节标题: {section_plan.section_title}
写作目标: {section_plan.writing_goal}
检索策略: {section_plan.query_strategy}
核心概念: {', '.join(section_plan.key_concepts) if section_plan.key_concepts else '无'}
建议查询数量: {section_plan.num_queries}

请生成 {section_plan.num_queries} 个检索查询，以JSON数组格式返回:
[
    {{
        "query_text": "检索查询文本（英文或中文均可）",
        "query_type": "semantic 或 keyword",
        "priority": 1到3的整数，1最高
    }}
]

生成查询时注意:
1. 覆盖章节的核心概念
2. 混合使用宽泛查询和精确查询
3. 优先使用学术术语
4. 考虑同义词和相关概念

只返回JSON数组，不要其他内容。"""

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
                    "temperature": 0.5
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

        queries_data = json.loads(content)

        queries = []
        for q in queries_data:
            queries.append(SearchQuery(
                section_title=section_plan.section_title,
                query_text=q.get("query_text", ""),
                query_type=q.get("query_type", "semantic"),
                priority=q.get("priority", 1)
            ))

        self.logger.info(
            f"为章节 [{section_plan.section_title}] 生成了 {len(queries)} 个查询"
        )

        return queries


async def test_query_generator():
    """测试 Query Generator Agent"""
    from agents.planner import SectionPlan

    agent = QueryGeneratorAgent()

    test_input = QueryGeneratorInput(
        paper_topic="深度学习在医学影像诊断中的应用",
        section_plans=[
            SectionPlan(
                section_title="引言",
                writing_goal="介绍深度学习在医学影像领域的重要性和发展背景",
                query_strategy="检索综述性文献和领域发展里程碑",
                num_queries=2,
                expected_source_types=["综述论文", "发展史文献"],
                key_concepts=["深度学习", "医学影像", "人工智能诊断"]
            ),
            SectionPlan(
                section_title="卷积神经网络在CT图像分析中的应用",
                writing_goal="详细介绍CNN在CT图像分割和病变检测中的方法",
                query_strategy="检索方法论文和实证研究",
                num_queries=3,
                expected_source_types=["方法论文", "实证研究"],
                key_concepts=["CNN", "CT图像", "图像分割", "病变检测"]
            )
        ]
    )

    print("=" * 60)
    print("测试 Query Generator Agent")
    print("=" * 60)
    print(f"论文主题: {test_input.paper_topic}")
    print(f"章节数量: {len(test_input.section_plans)}")
    print()

    output = await agent.run(test_input)

    if output.success:
        print(f"生成成功! 总查询数: {output.total_queries}")
        print()
        current_section = ""
        for q in output.queries:
            if q.section_title != current_section:
                current_section = q.section_title
                print(f"【{current_section}】")
            print(f"  [{q.priority}] ({q.query_type}) {q.query_text}")
        print()
    else:
        print(f"生成失败: {output.error}")

    return output


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_query_generator())
