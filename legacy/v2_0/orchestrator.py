# -*- coding: utf-8 -*-
"""
ManuScript v2.0 Orchestrator

Central dispatcher for task management and worker coordination
Implements Anthropic-style Orchestrator-Worker pattern
"""
import asyncio
from typing import List, Dict, Optional

import httpx

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from logger import get_logger
from models import (
    Section, Outline, SectionTask, TaskStatus,
    SectionComplexity, WorkerType, WorkerInput, WorkerOutput,
    SectionDraft, Citation, ReviewResult,
    OrchestratorInput, OrchestratorOutput
)
from workers.simple_worker import SimpleWorker
from workers.complex_worker import ComplexWorker
from workers.review_worker import ReviewWorker


logger = get_logger("Orchestrator")


class Orchestrator:
    """
    Central Orchestrator - Dynamic task dispatcher

    Responsibilities:
    1. Analyze task complexity
    2. Assign tasks to appropriate workers
    3. Coordinate parallel execution
    4. Aggregate results
    5. Manage review process
    """

    def __init__(self):
        self.logger = get_logger("Orchestrator")
        self.llm_config = config.get_llm_config()

        # Initialize workers
        self.workers = {
            WorkerType.SIMPLE: SimpleWorker(),
            WorkerType.COMPLEX: ComplexWorker(),
            WorkerType.REVIEW: ReviewWorker()
        }

        # Execution stats
        self.stats = {
            "simple_tasks": 0,
            "complex_tasks": 0,
            "reviewed_tasks": 0,
            "failed_tasks": 0
        }

    async def process(self, input_data: OrchestratorInput) -> OrchestratorOutput:
        """
        Main processing entry point

        Args:
            input_data: Contains outline and processing options

        Returns:
            OrchestratorOutput with all results
        """
        self.logger.info(f"Starting orchestration for: {input_data.outline.topic}")
        self.logger.info(f"Sections to process: {len(input_data.outline.sections)}")

        try:
            # Step 1: Analyze and create tasks
            tasks = await self._create_tasks(input_data.outline)
            self.logger.info(f"Created {len(tasks)} tasks")

            # Step 2: Process tasks (parallel or sequential)
            if input_data.parallel:
                completed_tasks = await self._process_parallel(
                    tasks=tasks,
                    paper_topic=input_data.outline.topic,
                    dataset_ids=input_data.outline.dataset_ids
                )
            else:
                completed_tasks = await self._process_sequential(
                    tasks=tasks,
                    paper_topic=input_data.outline.topic,
                    dataset_ids=input_data.outline.dataset_ids
                )

            # Step 3: Review all drafts
            reviewed_tasks = await self._review_all(completed_tasks)

            # Step 4: Aggregate results
            return self._aggregate_results(
                tasks=reviewed_tasks,
                paper_topic=input_data.outline.topic
            )

        except Exception as e:
            self.logger.error(f"Orchestration failed: {e}")
            return OrchestratorOutput(
                success=False,
                paper_topic=input_data.outline.topic,
                error=str(e)
            )

    async def _create_tasks(self, outline: Outline) -> List[SectionTask]:
        """Create and classify tasks for each section"""

        tasks = []

        for section in outline.sections:
            # Determine complexity
            complexity = await self._analyze_complexity(section, outline.topic)

            # Assign worker type
            if complexity == SectionComplexity.SIMPLE:
                worker_type = WorkerType.SIMPLE
                self.stats["simple_tasks"] += 1
            else:
                worker_type = WorkerType.COMPLEX
                self.stats["complex_tasks"] += 1

            task = SectionTask(
                section=section,
                complexity=complexity,
                assigned_worker=worker_type,
                status=TaskStatus.PENDING
            )

            tasks.append(task)
            self.logger.info(
                f"Task created: {section.title} -> {complexity.value} -> {worker_type.value}"
            )

        return tasks

    async def _analyze_complexity(
        self,
        section: Section,
        paper_topic: str
    ) -> SectionComplexity:
        """Analyze section complexity using rules and optional LLM"""

        section_type = section.section_type.lower()

        # Rule-based classification first
        if section_type in config.SIMPLE_SECTION_TYPES:
            return SectionComplexity.SIMPLE
        elif section_type in config.COMPLEX_SECTION_TYPES:
            return SectionComplexity.COMPLEX

        # For unknown types, use LLM to classify
        complexity = await self._llm_classify_complexity(section, paper_topic)
        return complexity

    async def _llm_classify_complexity(
        self,
        section: Section,
        paper_topic: str
    ) -> SectionComplexity:
        """Use LLM to classify section complexity"""

        prompt = f"""Classify this paper section as either SIMPLE or COMPLEX.

Paper Topic: {paper_topic}
Section Title: {section.title}
Section Type: {section.section_type}
Keywords: {', '.join(section.keywords) if section.keywords else 'None'}
Description: {section.description or 'Not provided'}

Classification criteria:
- SIMPLE: Introduction, background, conclusion, summary, acknowledgement
  (Requires general context, fewer technical details)

- COMPLEX: Methodology, experiments, results, analysis, implementation
  (Requires detailed technical content, multiple sources, specific evidence)

Output only one word: SIMPLE or COMPLEX"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.llm_config['api_base']}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.llm_config['api_key']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.llm_config["model"],
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 10
                    }
                )
                response.raise_for_status()
                result = response.json()

            answer = result["choices"][0]["message"]["content"].strip().upper()

            if "COMPLEX" in answer:
                return SectionComplexity.COMPLEX
            else:
                return SectionComplexity.SIMPLE

        except Exception as e:
            self.logger.warning(f"LLM classification failed: {e}, defaulting to COMPLEX")
            return SectionComplexity.COMPLEX

    async def _process_parallel(
        self,
        tasks: List[SectionTask],
        paper_topic: str,
        dataset_ids: List[str]
    ) -> List[SectionTask]:
        """Process tasks in parallel with concurrency limit"""

        self.logger.info(f"Processing {len(tasks)} tasks in parallel (max {config.MAX_PARALLEL_WORKERS})")

        semaphore = asyncio.Semaphore(config.MAX_PARALLEL_WORKERS)

        async def process_with_semaphore(task: SectionTask) -> SectionTask:
            async with semaphore:
                return await self._process_single_task(task, paper_topic, dataset_ids)

        results = await asyncio.gather(
            *[process_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

        completed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tasks[i].status = TaskStatus.FAILED
                tasks[i].error = str(result)
                self.stats["failed_tasks"] += 1
                completed.append(tasks[i])
            else:
                completed.append(result)

        return completed

    async def _process_sequential(
        self,
        tasks: List[SectionTask],
        paper_topic: str,
        dataset_ids: List[str]
    ) -> List[SectionTask]:
        """Process tasks sequentially"""

        self.logger.info(f"Processing {len(tasks)} tasks sequentially")

        completed = []
        for task in tasks:
            result = await self._process_single_task(task, paper_topic, dataset_ids)
            completed.append(result)

        return completed

    async def _process_single_task(
        self,
        task: SectionTask,
        paper_topic: str,
        dataset_ids: List[str]
    ) -> SectionTask:
        """Process a single task with the assigned worker"""

        worker = self.workers.get(task.assigned_worker)

        if not worker:
            task.status = TaskStatus.FAILED
            task.error = f"No worker for type: {task.assigned_worker}"
            return task

        worker_input = WorkerInput(
            task=task,
            paper_topic=paper_topic,
            dataset_ids=dataset_ids
        )

        output = await worker.process(worker_input)

        if not output.success:
            self.stats["failed_tasks"] += 1

        return output.task

    async def _review_all(self, tasks: List[SectionTask]) -> List[SectionTask]:
        """Review all completed drafts"""

        review_worker = self.workers[WorkerType.REVIEW]
        reviewed = []

        for task in tasks:
            if task.status == TaskStatus.COMPLETED and task.draft:
                self.logger.info(f"Reviewing: {task.section.title}")

                # Create review input
                review_input = WorkerInput(
                    task=task,
                    paper_topic="",  # Not needed for review
                    dataset_ids=[]
                )

                # Run review
                output = await review_worker.process(review_input)
                self.stats["reviewed_tasks"] += 1
                reviewed.append(output.task)
            else:
                reviewed.append(task)

        return reviewed

    def _aggregate_results(
        self,
        tasks: List[SectionTask],
        paper_topic: str
    ) -> OrchestratorOutput:
        """Aggregate all results into final output"""

        drafts = []
        all_citations = []
        total_words = 0
        tasks_completed = 0
        tasks_failed = 0

        citation_counter = 1

        for task in tasks:
            if task.status == TaskStatus.COMPLETED and task.draft:
                # Renumber citations for consistency
                draft = task.draft
                draft_citations = []

                for citation in draft.citations:
                    new_id = f"[{citation_counter}]"
                    # Update citation ID in content
                    draft.content = draft.content.replace(
                        citation.citation_id, new_id
                    )
                    citation.citation_id = new_id
                    draft_citations.append(citation)
                    citation_counter += 1

                draft.citations = draft_citations
                drafts.append(draft)
                all_citations.extend(draft_citations)
                total_words += draft.word_count
                tasks_completed += 1
            else:
                tasks_failed += 1

        success = tasks_failed == 0

        self.logger.info(
            f"Orchestration complete: {tasks_completed} completed, "
            f"{tasks_failed} failed, {total_words} total chars"
        )

        return OrchestratorOutput(
            success=success,
            paper_topic=paper_topic,
            drafts=drafts,
            all_citations=all_citations,
            total_words=total_words,
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
            simple_sections=self.stats["simple_tasks"],
            complex_sections=self.stats["complex_tasks"]
        )


async def test_orchestrator():
    """Test the Orchestrator"""

    orchestrator = Orchestrator()

    outline = Outline(
        topic="Deep Learning in Medical Image Diagnosis",
        sections=[
            Section(
                title="Introduction",
                section_type="introduction",
                keywords=["deep learning", "medical imaging", "diagnosis"],
                description="Introduce the research background",
                word_limit=300
            ),
            Section(
                title="CNN Architectures for Medical Imaging",
                section_type="method",
                keywords=["CNN", "U-Net", "segmentation"],
                description="Describe CNN architectures used",
                word_limit=500
            ),
            Section(
                title="Experimental Results",
                section_type="results",
                keywords=["accuracy", "comparison", "evaluation"],
                description="Present experimental results",
                word_limit=400
            ),
            Section(
                title="Conclusion",
                section_type="conclusion",
                keywords=["summary", "future work"],
                description="Summarize findings",
                word_limit=200
            )
        ],
        dataset_ids=[]
    )

    input_data = OrchestratorInput(
        outline=outline,
        parallel=True
    )

    print("=" * 60)
    print("Testing Orchestrator")
    print("=" * 60)
    print(f"Topic: {outline.topic}")
    print(f"Sections: {len(outline.sections)}")
    print()

    output = await orchestrator.process(input_data)

    if output.success:
        print("Orchestration successful!")
        print()
        print(f"Tasks completed: {output.tasks_completed}")
        print(f"Tasks failed: {output.tasks_failed}")
        print(f"Simple sections: {output.simple_sections}")
        print(f"Complex sections: {output.complex_sections}")
        print(f"Total words: {output.total_words}")
        print(f"Total citations: {len(output.all_citations)}")
        print()

        for draft in output.drafts:
            print(f"【{draft.section_title}】({draft.word_count} chars, {draft.worker_type})")
            print("-" * 40)
            content = draft.content
            print(content[:400] + "..." if len(content) > 400 else content)
            print()
    else:
        print(f"Orchestration failed: {output.error}")

    return output


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
