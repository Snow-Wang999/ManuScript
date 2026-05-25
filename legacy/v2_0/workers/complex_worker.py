# -*- coding: utf-8 -*-
"""
ManuScript v2.0 Complex Worker

Handles complex sections: method, experiment, results, discussion
Uses more queries and sophisticated processing pipeline
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


class ComplexWorker(BaseWorker):
    """
    Complex Worker - for detailed technical sections

    Pipeline:
    1. Analyze section requirements
    2. Generate 5 diverse queries
    3. Retrieve chunks
    4. LLM-based relevance ranking
    5. Generate structured draft with proper citations

    Suitable for: method, methodology, experiment, results, discussion
    """

    @property
    def name(self) -> str:
        return "ComplexWorker"

    @property
    def worker_type(self) -> str:
        return "complex"

    async def process(self, input_data: WorkerInput) -> WorkerOutput:
        """Process a complex section"""

        task = input_data.task
        self.log_start(task)
        task.status = TaskStatus.IN_PROGRESS

        try:
            # Step 1: Analyze section and generate writing plan
            writing_plan = await self._analyze_section(
                section=task.section,
                paper_topic=input_data.paper_topic
            )

            # Step 2: Generate diverse queries
            queries = await self._generate_diverse_queries(
                section=task.section,
                paper_topic=input_data.paper_topic,
                writing_plan=writing_plan
            )
            task.queries = queries

            # Step 3: Retrieve chunks
            chunks = await self.retrieve_chunks(
                queries=queries,
                dataset_ids=input_data.dataset_ids,
                top_k=config.TOP_K_CHUNKS
            )
            task.chunks = chunks

            # Step 4: LLM-based ranking
            ranked = await self.rank_chunks(
                chunks=chunks,
                section_title=task.section.title,
                writing_goal=writing_plan,
                max_chunks=7  # More chunks for complex sections
            )
            task.ranked_chunks = ranked

            # Step 5: Generate structured draft
            draft, _ = await self._write_complex_section(
                paper_topic=input_data.paper_topic,
                section=task.section,
                writing_plan=writing_plan,
                chunks=ranked
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

    async def _analyze_section(self, section, paper_topic: str) -> str:
        """Analyze section requirements and create writing plan"""

        prompt = f"""Analyze this paper section and create a writing plan.

Paper Topic: {paper_topic}
Section Title: {section.title}
Section Type: {section.section_type}
Keywords: {', '.join(section.keywords) if section.keywords else 'None'}
Description: {section.description or 'Not provided'}
Word Limit: {section.word_limit}

Create a brief writing plan that includes:
1. Main points to cover
2. Key information to look for in literature
3. Structure suggestions (sub-points if needed)
4. Types of sources needed (methodology papers, empirical studies, etc.)

Keep the plan concise (100-150 words)."""

        plan = await self._call_llm(prompt)
        self.logger.info(f"Created writing plan for {section.title}")
        return plan

    async def _generate_diverse_queries(
        self,
        section,
        paper_topic: str,
        writing_plan: str
    ) -> list[SearchQuery]:
        """Generate diverse search queries for comprehensive coverage"""

        prompt = f"""Generate {config.COMPLEX_WORKER_QUERIES} diverse search queries for academic literature retrieval.

Paper Topic: {paper_topic}
Section Title: {section.title}
Section Type: {section.section_type}
Keywords: {', '.join(section.keywords) if section.keywords else 'None'}

Writing Plan:
{writing_plan}

Requirements:
1. Generate {config.COMPLEX_WORKER_QUERIES} different queries
2. Include variety:
   - Broad conceptual queries
   - Specific technical queries
   - Methodology-focused queries
   - State-of-the-art/survey queries
   - Application/case study queries
3. Each query should target different aspects of the section

Output format (one query per line, no numbering):
query 1
query 2
..."""

        response = await self._call_llm(prompt)
        queries = []

        for i, line in enumerate(response.strip().split("\n")):
            line = line.strip()
            if line and not line.startswith("#"):
                # Remove any leading numbers or bullets
                clean_line = line.lstrip("0123456789.-) ")
                if clean_line:
                    queries.append(SearchQuery(
                        query_text=clean_line,
                        section_title=section.title,
                        query_type="semantic",
                        priority=i + 1
                    ))

        self.logger.info(f"Generated {len(queries)} diverse queries for {section.title}")
        return queries[:config.COMPLEX_WORKER_QUERIES]

    async def _write_complex_section(
        self,
        paper_topic: str,
        section,
        writing_plan: str,
        chunks: list[RankedChunk]
    ) -> tuple:
        """Generate structured content for complex section"""

        # Format sources with more detail
        sources_text = ""
        citation_map = {}

        for i, chunk in enumerate(chunks):
            cid = i + 1
            citation_map[cid] = chunk
            sources_text += f"""
[{cid}] Source: {chunk.document_name}
Relevance: {chunk.relevance_score:.1f}/10 - {chunk.relevance_reason}
Content:
{chunk.content[:700]}
---"""

        if not sources_text:
            sources_text = "(No relevant sources available - write based on general knowledge and note where citations are needed)"

        section_guidance = self._get_section_guidance(section.section_type)

        prompt = f"""You are an academic writing expert. Write a detailed section for a research paper.

Paper Topic: {paper_topic}
Section Title: {section.title}
Section Type: {section.section_type}
Word Limit: approximately {section.word_limit} words

Writing Plan:
{writing_plan}

{section_guidance}

Available Sources:
{sources_text}

Requirements:
1. Follow the writing plan structure
2. Write in formal academic style
3. Insert citation markers [1], [2], etc. at appropriate locations
4. Citations must correspond to the provided sources
5. Ensure logical flow and clear argumentation
6. Include technical details where appropriate
7. If sources are insufficient, note where additional citations are needed with [?]

Write the section content directly, without preamble or section title."""

        content = await self._call_llm(prompt, temperature=0.7, max_tokens=3000)

        # Extract used citations
        import re
        cited_ids = set(map(int, re.findall(r'\[(\d+)\]', content)))

        from models import Citation, SectionDraft

        citations = []
        for cid in sorted(cited_ids):
            if cid in citation_map:
                chunk = citation_map[cid]
                citations.append(Citation(
                    citation_id=f"[{cid}]",
                    document_name=chunk.document_name,
                    cited_content=chunk.content[:200]
                ))

        draft = SectionDraft(
            section_title=section.title,
            content=content,
            citations=citations,
            word_count=len(content),
            worker_type=self.worker_type
        )

        self.logger.info(
            f"Generated complex section: {len(content)} chars, {len(citations)} citations"
        )

        return draft, len(chunks) + 1

    def _get_section_guidance(self, section_type: str) -> str:
        """Get specific guidance based on section type"""

        guidance = {
            "method": """
Section-specific guidance for METHODOLOGY:
- Describe the approach/framework clearly
- Explain key algorithms or procedures
- Justify design choices with references
- Include technical details sufficient for replication
- Address limitations where appropriate""",

            "methodology": """
Section-specific guidance for METHODOLOGY:
- Present the research methodology systematically
- Explain data collection/analysis methods
- Justify methodological choices
- Reference established methods where applicable""",

            "experiment": """
Section-specific guidance for EXPERIMENTS:
- Describe experimental setup clearly
- Specify datasets, parameters, evaluation metrics
- Explain baseline comparisons
- Present experimental procedure step by step""",

            "results": """
Section-specific guidance for RESULTS:
- Present findings objectively
- Use quantitative data where available
- Compare with baselines or prior work
- Highlight key observations""",

            "discussion": """
Section-specific guidance for DISCUSSION:
- Interpret results in context
- Compare with related work
- Discuss implications and significance
- Address limitations and future directions""",

            "analysis": """
Section-specific guidance for ANALYSIS:
- Provide systematic analysis of data/results
- Support claims with evidence
- Draw connections between findings
- Consider alternative interpretations""",

            "implementation": """
Section-specific guidance for IMPLEMENTATION:
- Describe system architecture/design
- Explain key implementation details
- Discuss technical challenges and solutions
- Provide sufficient detail for understanding"""
        }

        return guidance.get(
            section_type.lower(),
            "Write detailed academic content with proper citations."
        )


async def test_complex_worker():
    """Test ComplexWorker"""
    from models import Section, SectionTask, SectionComplexity

    worker = ComplexWorker()

    section = Section(
        title="Convolutional Neural Networks for Medical Image Segmentation",
        section_type="method",
        keywords=["CNN", "segmentation", "U-Net", "medical imaging"],
        description="Describe the CNN architectures used for medical image segmentation",
        word_limit=600
    )

    task = SectionTask(
        section=section,
        complexity=SectionComplexity.COMPLEX
    )

    test_input = WorkerInput(
        task=task,
        paper_topic="Deep Learning in Medical Image Diagnosis",
        dataset_ids=[]
    )

    print("=" * 60)
    print("Testing ComplexWorker")
    print("=" * 60)
    print(f"Section: {section.title}")
    print(f"Type: {section.section_type}")
    print()

    output = await worker.process(test_input)

    if output.success:
        print("Processing successful!")
        print(f"Status: {output.task.status}")
        print(f"Queries generated: {len(output.task.queries)}")
        print()
        for q in output.task.queries:
            print(f"  - {q.query_text[:60]}...")
        print()
        print(f"Chunks retrieved: {len(output.task.chunks)}")
        print(f"Chunks ranked: {len(output.task.ranked_chunks)}")
        print()

        if output.task.draft:
            print(f"Draft ({output.task.draft.word_count} chars):")
            print("-" * 40)
            content = output.task.draft.content
            print(content[:800] + "..." if len(content) > 800 else content)
            print()
            print(f"Citations: {len(output.task.draft.citations)}")
            for c in output.task.draft.citations:
                print(f"  {c.citation_id}: {c.document_name}")
    else:
        print(f"Processing failed: {output.error}")

    return output


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_complex_worker())
