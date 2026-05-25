# -*- coding: utf-8 -*-
"""
ManuScript v2.0 LangGraph Workflow

Orchestrates the Orchestrator-Worker pattern using LangGraph
"""
from typing import TypedDict, List, Dict, Optional, Any
import asyncio

from langgraph.graph import StateGraph, END

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from logger import get_logger
from models import (
    Section, Outline, SectionTask, TaskStatus,
    SectionComplexity, WorkerType, WorkerInput,
    SectionDraft, Citation, OrchestratorInput, OrchestratorOutput
)
from orchestrator import Orchestrator

logger = get_logger("Workflow")


class WorkflowState(TypedDict):
    """LangGraph workflow state"""
    # Input
    paper_topic: str
    sections: List[dict]
    dataset_ids: List[str]
    parallel: bool

    # Processing state
    outline: Optional[dict]
    tasks: List[dict]
    current_phase: str

    # Output
    drafts: List[dict]
    citations: List[dict]
    reviews: List[dict]

    # Stats
    tasks_completed: int
    tasks_failed: int
    simple_sections: int
    complex_sections: int
    total_words: int

    # Status
    error: Optional[str]


# Initialize orchestrator
orchestrator = Orchestrator()


async def prepare_node(state: WorkflowState) -> WorkflowState:
    """Prepare node - validate input and create outline"""
    logger.info("Executing prepare node")

    try:
        # Create sections from input
        sections = [Section(**s) for s in state["sections"]]

        # Create outline
        outline = Outline(
            topic=state["paper_topic"],
            sections=sections,
            dataset_ids=state.get("dataset_ids", [])
        )

        return {
            **state,
            "outline": outline.model_dump(),
            "current_phase": "prepared"
        }

    except Exception as e:
        logger.error(f"Prepare failed: {e}")
        return {**state, "error": str(e), "current_phase": "prepare_failed"}


async def orchestrate_node(state: WorkflowState) -> WorkflowState:
    """Orchestrate node - run the full orchestration pipeline"""
    logger.info("Executing orchestrate node")

    if state.get("error"):
        return state

    try:
        # Reconstruct outline
        outline = Outline(**state["outline"])

        # Create orchestrator input
        input_data = OrchestratorInput(
            outline=outline,
            parallel=state.get("parallel", True)
        )

        # Run orchestration
        output = await orchestrator.process(input_data)

        if not output.success:
            return {
                **state,
                "error": output.error,
                "current_phase": "orchestration_failed"
            }

        # Convert outputs to dicts
        drafts = [d.model_dump() for d in output.drafts]
        citations = [c.model_dump() for c in output.all_citations]

        return {
            **state,
            "drafts": drafts,
            "citations": citations,
            "tasks_completed": output.tasks_completed,
            "tasks_failed": output.tasks_failed,
            "simple_sections": output.simple_sections,
            "complex_sections": output.complex_sections,
            "total_words": output.total_words,
            "current_phase": "completed"
        }

    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        return {**state, "error": str(e), "current_phase": "orchestration_failed"}


def should_continue(state: WorkflowState) -> str:
    """Determine next step based on state"""
    if state.get("error"):
        return "error"
    return "continue"


def build_workflow() -> StateGraph:
    """Build the LangGraph workflow"""

    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("prepare", prepare_node)
    workflow.add_node("orchestrate", orchestrate_node)

    # Set entry point
    workflow.set_entry_point("prepare")

    # Add edges
    workflow.add_edge("prepare", "orchestrate")
    workflow.add_edge("orchestrate", END)

    return workflow


def create_app():
    """Create compiled workflow application"""
    workflow = build_workflow()
    return workflow.compile()


class ManuScriptV2Workflow:
    """
    ManuScript v2.0 Workflow wrapper

    Provides clean interface for running the Orchestrator-Worker pipeline
    """

    def __init__(self):
        self.app = create_app()
        self.logger = get_logger("ManuScriptV2Workflow")

    async def run(
        self,
        paper_topic: str,
        sections: List[dict],
        dataset_ids: List[str] = None,
        parallel: bool = True
    ) -> dict:
        """
        Run the complete workflow

        Args:
            paper_topic: Paper topic/title
            sections: List of section dicts with title, section_type, keywords, etc.
            dataset_ids: RAGFlow dataset IDs for retrieval
            parallel: Enable parallel processing

        Returns:
            Result dict with drafts, citations, and stats
        """
        self.logger.info(f"Starting v2.0 workflow: {paper_topic}")

        initial_state: WorkflowState = {
            "paper_topic": paper_topic,
            "sections": sections,
            "dataset_ids": dataset_ids or [],
            "parallel": parallel,
            "outline": None,
            "tasks": [],
            "current_phase": "initial",
            "drafts": [],
            "citations": [],
            "reviews": [],
            "tasks_completed": 0,
            "tasks_failed": 0,
            "simple_sections": 0,
            "complex_sections": 0,
            "total_words": 0,
            "error": None
        }

        try:
            final_state = await self.app.ainvoke(initial_state)

            if final_state.get("error"):
                self.logger.error(f"Workflow failed: {final_state['error']}")
                return {
                    "success": False,
                    "error": final_state["error"],
                    "phase": final_state["current_phase"]
                }

            self.logger.info("Workflow completed successfully")

            return {
                "success": True,
                "paper_topic": paper_topic,
                "drafts": final_state["drafts"],
                "citations": final_state["citations"],
                "total_words": final_state["total_words"],
                "tasks_completed": final_state["tasks_completed"],
                "tasks_failed": final_state["tasks_failed"],
                "simple_sections": final_state["simple_sections"],
                "complex_sections": final_state["complex_sections"]
            }

        except Exception as e:
            self.logger.error(f"Workflow exception: {e}")
            return {
                "success": False,
                "error": str(e),
                "phase": "exception"
            }

    async def run_with_progress(
        self,
        paper_topic: str,
        sections: List[dict],
        dataset_ids: List[str] = None,
        parallel: bool = True,
        progress_callback=None
    ) -> dict:
        """
        Run workflow with progress callbacks for UI updates

        Args:
            progress_callback: Async function(phase, message) for progress updates
        """
        if progress_callback:
            await progress_callback("starting", f"Starting: {paper_topic}")

        # Validate config
        missing = config.validate()
        if missing:
            error_msg = f"Missing configuration: {', '.join(missing)}"
            if progress_callback:
                await progress_callback("error", error_msg)
            return {"success": False, "error": error_msg}

        if progress_callback:
            await progress_callback("analyzing", f"Analyzing {len(sections)} sections...")

        result = await self.run(
            paper_topic=paper_topic,
            sections=sections,
            dataset_ids=dataset_ids,
            parallel=parallel
        )

        if progress_callback:
            if result["success"]:
                await progress_callback(
                    "completed",
                    f"Completed: {result['tasks_completed']} sections, "
                    f"{result['total_words']} chars"
                )
            else:
                await progress_callback("error", result.get("error", "Unknown error"))

        return result


async def test_workflow():
    """Test the complete workflow"""

    workflow = ManuScriptV2Workflow()

    sections = [
        {
            "title": "Introduction",
            "section_type": "introduction",
            "keywords": ["deep learning", "medical imaging", "diagnosis"],
            "description": "Introduce the research background",
            "word_limit": 300
        },
        {
            "title": "Deep Learning Methods for Medical Image Analysis",
            "section_type": "method",
            "keywords": ["CNN", "transformer", "segmentation", "classification"],
            "description": "Describe deep learning architectures and methods",
            "word_limit": 600
        },
        {
            "title": "Experimental Evaluation",
            "section_type": "experiment",
            "keywords": ["dataset", "metrics", "comparison"],
            "description": "Evaluate the proposed methods",
            "word_limit": 500
        },
        {
            "title": "Conclusion and Future Work",
            "section_type": "conclusion",
            "keywords": ["summary", "contributions", "future directions"],
            "description": "Summarize findings and discuss future work",
            "word_limit": 250
        }
    ]

    print("=" * 60)
    print("Testing ManuScript v2.0 Workflow")
    print("=" * 60)
    print(f"Paper Topic: Deep Learning in Medical Image Diagnosis")
    print(f"Sections: {len(sections)}")
    print()

    async def progress_handler(phase: str, message: str):
        print(f"[{phase.upper()}] {message}")

    result = await workflow.run_with_progress(
        paper_topic="Deep Learning in Medical Image Diagnosis",
        sections=sections,
        dataset_ids=[],
        parallel=True,
        progress_callback=progress_handler
    )

    print()
    print("=" * 60)
    print("Results")
    print("=" * 60)

    if result["success"]:
        print(f"Status: SUCCESS")
        print(f"Tasks Completed: {result['tasks_completed']}")
        print(f"Tasks Failed: {result['tasks_failed']}")
        print(f"Simple Sections: {result['simple_sections']}")
        print(f"Complex Sections: {result['complex_sections']}")
        print(f"Total Characters: {result['total_words']}")
        print(f"Total Citations: {len(result['citations'])}")
        print()

        for draft in result["drafts"]:
            print(f"\n【{draft['section_title']}】")
            print(f"Worker: {draft['worker_type']}")
            print(f"Length: {draft['word_count']} chars")
            print(f"Citations: {len(draft['citations'])}")
            print("-" * 40)
            content = draft["content"]
            print(content[:500] + "..." if len(content) > 500 else content)
    else:
        print(f"Status: FAILED")
        print(f"Error: {result.get('error')}")

    return result


if __name__ == "__main__":
    asyncio.run(test_workflow())
