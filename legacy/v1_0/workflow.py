"""
ManuScript v1.0 LangGraph Workflow

使用 LangGraph 编排 6 个 Agent 的工作流程:
Planner → QueryGenerator → Retrieval → Ranker → Writer → Verifier
"""
from typing import TypedDict, List, Dict, Optional, Annotated
from pydantic import BaseModel

from langgraph.graph import StateGraph, END

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.planner import PlannerAgent, PlannerInput, PlannerOutput, SectionInfo, SectionPlan
from agents.query_generator import QueryGeneratorAgent, QueryGeneratorInput, QueryGeneratorOutput, SearchQuery
from agents.retrieval import RetrievalAgent, RetrievalInput, RetrievalOutput, DocumentChunk
from agents.ranker import RankerAgent, RankerInput, RankerOutput, RankedChunk
from agents.writer import WriterAgent, WriterInput, WriterOutput, SectionDraft, Citation
from agents.verifier import VerifierAgent, VerifierInput, VerifierOutput

from logger import get_logger

logger = get_logger("Workflow")


class WorkflowState(TypedDict):
    """工作流状态"""
    paper_topic: str
    sections: List[dict]
    dataset_ids: List[str]

    planner_output: Optional[dict]
    query_output: Optional[dict]
    retrieval_output: Optional[dict]
    ranker_output: Optional[dict]
    writer_output: Optional[dict]
    verifier_output: Optional[dict]

    error: Optional[str]
    current_step: str
    retry_count: int


planner_agent = PlannerAgent()
query_agent = QueryGeneratorAgent()
retrieval_agent = RetrievalAgent()
ranker_agent = RankerAgent()
writer_agent = WriterAgent()
verifier_agent = VerifierAgent()


async def plan_node(state: WorkflowState) -> WorkflowState:
    """Planner 节点"""
    logger.info("执行 Planner 节点")

    sections = [SectionInfo(**s) for s in state["sections"]]
    input_data = PlannerInput(
        paper_topic=state["paper_topic"],
        sections=sections
    )

    output = await planner_agent.run(input_data)

    if not output.success:
        return {**state, "error": output.error, "current_step": "plan_failed"}

    return {
        **state,
        "planner_output": output.model_dump(),
        "current_step": "planned"
    }


async def query_node(state: WorkflowState) -> WorkflowState:
    """Query Generator 节点"""
    logger.info("执行 Query Generator 节点")

    planner_data = state["planner_output"]
    section_plans = [SectionPlan(**p) for p in planner_data["section_plans"]]

    input_data = QueryGeneratorInput(
        paper_topic=state["paper_topic"],
        section_plans=section_plans
    )

    output = await query_agent.run(input_data)

    if not output.success:
        return {**state, "error": output.error, "current_step": "query_failed"}

    return {
        **state,
        "query_output": output.model_dump(),
        "current_step": "queries_generated"
    }


async def retrieval_node(state: WorkflowState) -> WorkflowState:
    """Retrieval 节点"""
    logger.info("执行 Retrieval 节点")

    query_data = state["query_output"]
    queries = [SearchQuery(**q) for q in query_data["queries"]]

    input_data = RetrievalInput(
        queries=queries,
        dataset_ids=state.get("dataset_ids", []),
        top_k=10
    )

    output = await retrieval_agent.run(input_data)

    if not output.success:
        return {**state, "error": output.error, "current_step": "retrieval_failed"}

    return {
        **state,
        "retrieval_output": output.model_dump(),
        "current_step": "retrieved"
    }


async def ranker_node(state: WorkflowState) -> WorkflowState:
    """Ranker 节点"""
    logger.info("执行 Ranker 节点")

    retrieval_data = state["retrieval_output"]
    chunks = [DocumentChunk(**c) for c in retrieval_data["chunks"]]

    planner_data = state["planner_output"]
    section_plans = [SectionPlan(**p) for p in planner_data["section_plans"]]

    input_data = RankerInput(
        chunks=chunks,
        section_plans=section_plans,
        max_chunks_per_section=5
    )

    output = await ranker_agent.run(input_data)

    if not output.success:
        return {**state, "error": output.error, "current_step": "ranking_failed"}

    return {
        **state,
        "ranker_output": output.model_dump(),
        "current_step": "ranked"
    }


async def writer_node(state: WorkflowState) -> WorkflowState:
    """Writer 节点"""
    logger.info("执行 Writer 节点")

    planner_data = state["planner_output"]
    section_plans = [SectionPlan(**p) for p in planner_data["section_plans"]]

    ranker_data = state["ranker_output"]
    ranked_chunks = {}
    for section_title, chunks in ranker_data["ranked_chunks"].items():
        ranked_chunks[section_title] = [RankedChunk(**c) for c in chunks]

    input_data = WriterInput(
        paper_topic=state["paper_topic"],
        section_plans=section_plans,
        ranked_chunks=ranked_chunks
    )

    output = await writer_agent.run(input_data)

    if not output.success:
        return {**state, "error": output.error, "current_step": "writing_failed"}

    return {
        **state,
        "writer_output": output.model_dump(),
        "current_step": "written"
    }


async def verifier_node(state: WorkflowState) -> WorkflowState:
    """Verifier 节点"""
    logger.info("执行 Verifier 节点")

    writer_data = state["writer_output"]
    drafts = [SectionDraft(**d) for d in writer_data["drafts"]]

    source_chunks = {}
    for draft in drafts:
        for citation in draft.citations:
            source_chunks[citation.citation_id] = citation.cited_content

    input_data = VerifierInput(
        drafts=drafts,
        source_chunks=source_chunks
    )

    output = await verifier_agent.run(input_data)

    if not output.success:
        return {**state, "error": output.error, "current_step": "verification_failed"}

    return {
        **state,
        "verifier_output": output.model_dump(),
        "current_step": "completed"
    }


def should_continue(state: WorkflowState) -> str:
    """判断是否继续或结束"""
    if state.get("error"):
        return "error"
    return "continue"


def build_workflow() -> StateGraph:
    """构建工作流图"""
    workflow = StateGraph(WorkflowState)

    workflow.add_node("plan", plan_node)
    workflow.add_node("query", query_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("ranker", ranker_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("verifier", verifier_node)

    workflow.set_entry_point("plan")

    workflow.add_edge("plan", "query")
    workflow.add_edge("query", "retrieval")
    workflow.add_edge("retrieval", "ranker")
    workflow.add_edge("ranker", "writer")
    workflow.add_edge("writer", "verifier")
    workflow.add_edge("verifier", END)

    return workflow


def create_app():
    """创建可执行的工作流应用"""
    workflow = build_workflow()
    return workflow.compile()


class ManuScriptWorkflow:
    """ManuScript 工作流封装类"""

    def __init__(self):
        self.app = create_app()
        self.logger = get_logger("ManuScriptWorkflow")

    async def run(
        self,
        paper_topic: str,
        sections: List[dict],
        dataset_ids: List[str] = None
    ) -> dict:
        """
        运行完整工作流

        Args:
            paper_topic: 论文主题
            sections: 章节列表，每个章节包含 title, section_type, keywords, word_limit
            dataset_ids: RAGFlow 数据集ID列表

        Returns:
            包含所有输出的字典
        """
        self.logger.info(f"开始生成论文: {paper_topic}")

        initial_state: WorkflowState = {
            "paper_topic": paper_topic,
            "sections": sections,
            "dataset_ids": dataset_ids or [],
            "planner_output": None,
            "query_output": None,
            "retrieval_output": None,
            "ranker_output": None,
            "writer_output": None,
            "verifier_output": None,
            "error": None,
            "current_step": "initial",
            "retry_count": 0
        }

        try:
            final_state = await self.app.ainvoke(initial_state)

            if final_state.get("error"):
                self.logger.error(f"工作流失败: {final_state['error']}")
                return {
                    "success": False,
                    "error": final_state["error"],
                    "step": final_state["current_step"]
                }

            self.logger.info("工作流完成")

            return {
                "success": True,
                "paper_topic": paper_topic,
                "drafts": final_state["writer_output"]["drafts"],
                "citations": final_state["writer_output"]["all_citations"],
                "verification": final_state["verifier_output"],
                "total_words": final_state["writer_output"]["total_words"]
            }

        except Exception as e:
            self.logger.error(f"工作流异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "step": "exception"
            }


async def test_workflow():
    """测试完整工作流"""
    workflow = ManuScriptWorkflow()

    sections = [
        {
            "title": "引言",
            "section_type": "introduction",
            "keywords": ["深度学习", "医学影像", "诊断"],
            "word_limit": 300
        },
        {
            "title": "卷积神经网络在CT图像分析中的应用",
            "section_type": "body",
            "keywords": ["CNN", "CT", "图像分割"],
            "word_limit": 500
        },
        {
            "title": "结论与展望",
            "section_type": "conclusion",
            "keywords": ["未来方向", "挑战"],
            "word_limit": 200
        }
    ]

    print("=" * 60)
    print("测试 ManuScript v1.0 工作流")
    print("=" * 60)
    print(f"论文主题: 深度学习在医学影像诊断中的应用")
    print(f"章节数: {len(sections)}")
    print()

    result = await workflow.run(
        paper_topic="深度学习在医学影像诊断中的应用",
        sections=sections,
        dataset_ids=[]
    )

    if result["success"]:
        print("生成成功!")
        print(f"总字数: {result['total_words']}")
        print()

        for draft in result["drafts"]:
            print(f"【{draft['section_title']}】")
            print("-" * 40)
            print(draft["content"][:500] + "..." if len(draft["content"]) > 500 else draft["content"])
            print()

        print("引用列表:")
        for c in result["citations"]:
            print(f"  {c['citation_id']} {c['document_name']}")

        print()
        print("验证结果:")
        v = result["verification"]
        print(f"  整体准确率: {v['overall_accuracy']:.1f}/10")
        print(f"  有效引用: {v['valid_citations']}/{v['total_citations']}")
        print(f"  需要修订: {'是' if v['needs_revision'] else '否'}")
    else:
        print(f"生成失败: {result['error']}")
        print(f"失败步骤: {result['step']}")

    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_workflow())
