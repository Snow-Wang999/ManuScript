# -*- coding: utf-8 -*-
"""
ManuScript v2.0 Simple Worker

Handles simple sections: background, conclusion, abstract, introduction
Uses fewer queries and simpler processing pipeline
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workers.base import BaseWorker
from config import config
from models import (
    WorkerInput, WorkerOutput, TaskStatus,
    SearchQuery, DocumentChunk, RankedChunk
)


class SimpleWorker(BaseWorker):
    """
    Simple Worker - for straightforward sections

    Pipeline:
    1. Generate 2 queries
    2. Retrieve chunks
    3. Basic ranking (top by score)
    4. Generate draft

    Suitable for: background, introduction, conclusion, abstract
    """

    @property
    def name(self) -> str:
        return "SimpleWorker"

    @property
    def worker_type(self) -> str:
        return "simple"

    async def process(self, input_data: WorkerInput) -> WorkerOutput:
        """Process a simple section"""

        task = input_data.task
        self.log_start(task)
        task.status = TaskStatus.IN_PROGRESS

        try:
            # Step 1: Generate queries (fewer for simple sections)
            queries = await self.generate_queries(
                section_title=task.section.title,
                section_type=task.section.section_type,
                keywords=task.section.keywords,
                paper_topic=input_data.paper_topic,
                num_queries=config.SIMPLE_WORKER_QUERIES
            )
            task.queries = queries

            # Step 2: Retrieve chunks
            chunks = await self.retrieve_chunks(
                queries=queries,
                dataset_ids=input_data.dataset_ids,
                top_k=config.TOP_K_CHUNKS
            )
            task.chunks = chunks

            # Step 3: Simple ranking (use original scores, take top 5)
            ranked = self._simple_rank(chunks, max_chunks=5)
            task.ranked_chunks = ranked

            # Step 4: Generate draft
            draft, _ = await self.write_section(
                paper_topic=input_data.paper_topic,
                section_title=task.section.title,
                section_type=task.section.section_type,
                writing_goal=self._get_writing_goal(task.section),
                word_limit=task.section.word_limit,
                chunks=ranked,
                citation_start=1
            )
            task.draft = draft
            task.status = TaskStatus.COMPLETED

            self.log_end(task)
            return WorkerOutput(success=True, task=task)

        except Exception as e:
            self.log_error(e, task)
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return WorkerOutput(success=False, task=task, error=str(e))

    def _simple_rank(
        self,
        chunks: list[DocumentChunk],
        max_chunks: int = 5
    ) -> list[RankedChunk]:
        """Simple ranking based on original retrieval scores"""

        # Sort by original score
        sorted_chunks = sorted(chunks, key=lambda x: x.score, reverse=True)

        ranked = []
        for chunk in sorted_chunks[:max_chunks]:
            ranked.append(RankedChunk(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                document_name=chunk.document_name,
                original_score=chunk.score,
                relevance_score=chunk.score * 10,  # Scale to 0-10
                section_title=chunk.section_title,
                relevance_reason="Top retrieval score"
            ))

        return ranked

    def _get_writing_goal(self, section) -> str:
        """Generate writing goal based on section type"""

        section_type = section.section_type.lower()
        title = section.title

        goals = {
            "introduction": f"Introduce the research topic, establish context and significance, and outline the paper structure for '{title}'",
            "background": f"Provide background information and literature context for '{title}'",
            "conclusion": f"Summarize key findings and contributions, discuss implications for '{title}'",
            "abstract": f"Provide a concise summary of the research including problem, method, and findings for '{title}'",
            "acknowledgement": f"Express gratitude to contributors and funding sources",
            "appendix": f"Provide supplementary information for '{title}'"
        }

        return goals.get(
            section_type,
            f"Write academic content for section: {title}"
        )


async def test_simple_worker():
    """Test SimpleWorker"""
    from models import Section, SectionTask, SectionComplexity

    worker = SimpleWorker()

    section = Section(
        title="Introduction",
        section_type="introduction",
        keywords=["deep learning", "medical imaging", "diagnosis"],
        description="Introduce the research background",
        word_limit=300
    )

    task = SectionTask(
        section=section,
        complexity=SectionComplexity.SIMPLE
    )

    test_input = WorkerInput(
        task=task,
        paper_topic="Deep Learning in Medical Image Diagnosis",
        dataset_ids=[]
    )

    print("=" * 60)
    print("Testing SimpleWorker")
    print("=" * 60)
    print(f"Section: {section.title}")
    print(f"Type: {section.section_type}")
    print()

    output = await worker.process(test_input)

    if output.success:
        print("Processing successful!")
        print(f"Status: {output.task.status}")
        print(f"Queries generated: {len(output.task.queries)}")
        print(f"Chunks retrieved: {len(output.task.chunks)}")
        print(f"Chunks ranked: {len(output.task.ranked_chunks)}")
        print()

        if output.task.draft:
            print(f"Draft ({output.task.draft.word_count} chars):")
            print("-" * 40)
            content = output.task.draft.content
            print(content[:500] + "..." if len(content) > 500 else content)
            print()
            print(f"Citations: {len(output.task.draft.citations)}")
            for c in output.task.draft.citations:
                print(f"  {c.citation_id}: {c.document_name}")
    else:
        print(f"Processing failed: {output.error}")

    return output


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_simple_worker())
