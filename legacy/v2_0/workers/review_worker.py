# -*- coding: utf-8 -*-
"""
ManuScript v2.0 Review Worker

Quality audit and revision worker
Validates citations, checks for hallucinations, and improves content
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workers.base import BaseWorker
from config import config
from models import (
    WorkerInput, WorkerOutput, TaskStatus,
    SectionDraft, Citation, RankedChunk,
    ReviewResult, ReviewIssue
)


class ReviewWorker(BaseWorker):
    """
    Review Worker - quality audit and revision

    Pipeline:
    1. Validate citation accuracy
    2. Check for potential hallucinations
    3. Assess writing quality
    4. Suggest or apply revisions

    Used for: Post-processing all generated drafts
    """

    @property
    def name(self) -> str:
        return "ReviewWorker"

    @property
    def worker_type(self) -> str:
        return "review"

    async def process(self, input_data: WorkerInput) -> WorkerOutput:
        """Process review for a section"""

        task = input_data.task
        self.log_start(task)

        if not task.draft:
            task.error = "No draft to review"
            return WorkerOutput(success=False, task=task, error="No draft to review")

        try:
            # Step 1: Validate citations
            citation_result = await self._validate_citations(
                draft=task.draft,
                source_chunks=task.ranked_chunks
            )

            # Step 2: Check for hallucinations
            hallucination_issues = await self._check_hallucinations(
                draft=task.draft,
                source_chunks=task.ranked_chunks
            )

            # Step 3: Assess writing quality
            quality_issues = await self._assess_quality(
                draft=task.draft,
                section_type=task.section.section_type
            )

            # Combine all issues
            all_issues = citation_result["issues"] + hallucination_issues + quality_issues

            # Calculate accuracy score
            accuracy_score = self._calculate_accuracy_score(
                valid_citations=citation_result["valid"],
                total_citations=citation_result["total"],
                hallucination_count=len(hallucination_issues),
                quality_issues=len(quality_issues)
            )

            # Determine if revision is needed
            needs_revision = (
                accuracy_score < 7.0 or
                len(hallucination_issues) > 0 or
                any(i.severity == "high" for i in all_issues)
            )

            # Step 4: Apply revision if needed
            revised_content = None
            if needs_revision and config.REVIEW_MAX_ITERATIONS > 0:
                revised_content = await self._revise_draft(
                    draft=task.draft,
                    issues=all_issues,
                    source_chunks=task.ranked_chunks
                )

            # Create review result
            review = ReviewResult(
                section_title=task.section.title,
                accuracy_score=accuracy_score,
                issues=all_issues,
                valid_citations=citation_result["valid"],
                total_citations=citation_result["total"],
                needs_revision=needs_revision,
                revised_content=revised_content
            )

            # Update draft if revised
            if revised_content:
                task.draft.content = revised_content
                task.draft.word_count = len(revised_content)

            task.status = TaskStatus.COMPLETED

            self.log_end(task)
            self.logger.info(
                f"Review complete: score={accuracy_score:.1f}, "
                f"citations={citation_result['valid']}/{citation_result['total']}, "
                f"issues={len(all_issues)}"
            )

            return WorkerOutput(success=True, task=task)

        except Exception as e:
            self.log_error(e, task)
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return WorkerOutput(success=False, task=task, error=str(e))

    async def review_draft(
        self,
        draft: SectionDraft,
        source_chunks: list[RankedChunk]
    ) -> ReviewResult:
        """Review a draft and return detailed results"""

        # Validate citations
        citation_result = await self._validate_citations(draft, source_chunks)

        # Check hallucinations
        hallucination_issues = await self._check_hallucinations(draft, source_chunks)

        # Assess quality
        quality_issues = await self._assess_quality(draft, "general")

        all_issues = citation_result["issues"] + hallucination_issues + quality_issues

        accuracy_score = self._calculate_accuracy_score(
            valid_citations=citation_result["valid"],
            total_citations=citation_result["total"],
            hallucination_count=len(hallucination_issues),
            quality_issues=len(quality_issues)
        )

        needs_revision = accuracy_score < 7.0 or len(hallucination_issues) > 0

        return ReviewResult(
            section_title=draft.section_title,
            accuracy_score=accuracy_score,
            issues=all_issues,
            valid_citations=citation_result["valid"],
            total_citations=citation_result["total"],
            needs_revision=needs_revision
        )

    async def _validate_citations(
        self,
        draft: SectionDraft,
        source_chunks: list[RankedChunk]
    ) -> dict:
        """Validate that citations match source content"""

        issues = []

        # Extract citation markers from text
        cited_ids = set(re.findall(r'\[(\d+)\]', draft.content))

        # Build source map
        source_map = {str(i + 1): chunk for i, chunk in enumerate(source_chunks)}

        valid_count = 0
        total_count = len(cited_ids)

        for cid in cited_ids:
            if cid not in source_map:
                issues.append(ReviewIssue(
                    issue_type="citation_error",
                    description=f"Citation [{cid}] has no corresponding source",
                    location=f"[{cid}]",
                    suggestion=f"Remove citation [{cid}] or add source",
                    severity="high"
                ))
            else:
                valid_count += 1

        # Check for proper citation distribution
        if total_count == 0 and len(source_chunks) > 0:
            issues.append(ReviewIssue(
                issue_type="missing_citations",
                description="No citations found despite available sources",
                location="entire section",
                suggestion="Add citations to support claims",
                severity="medium"
            ))

        return {
            "valid": valid_count,
            "total": total_count,
            "issues": issues
        }

    async def _check_hallucinations(
        self,
        draft: SectionDraft,
        source_chunks: list[RankedChunk]
    ) -> list[ReviewIssue]:
        """Check for potential hallucinations using LLM"""

        if not source_chunks:
            return []

        # Prepare source content summary
        sources_text = "\n".join([
            f"[{i+1}] {chunk.document_name}: {chunk.content[:300]}..."
            for i, chunk in enumerate(source_chunks[:5])
        ])

        prompt = f"""Analyze this academic text for potential hallucinations or unsupported claims.

Text to analyze:
{draft.content[:1500]}

Available sources:
{sources_text}

Identify any claims that:
1. Are not supported by the provided sources
2. Contain specific numbers/statistics without citation
3. Make strong assertions without evidence

For each issue found, output in this format:
ISSUE|description|quoted_text|severity(low/medium/high)

If no issues found, output: NO_ISSUES"""

        response = await self._call_llm(prompt)

        issues = []
        if "NO_ISSUES" not in response.upper():
            for line in response.strip().split("\n"):
                if line.startswith("ISSUE|"):
                    parts = line.split("|")
                    if len(parts) >= 4:
                        issues.append(ReviewIssue(
                            issue_type="hallucination",
                            description=parts[1].strip(),
                            location=parts[2].strip()[:100],
                            suggestion="Verify claim or add citation",
                            severity=parts[3].strip().lower() if len(parts) > 3 else "medium"
                        ))

        return issues

    async def _assess_quality(
        self,
        draft: SectionDraft,
        section_type: str
    ) -> list[ReviewIssue]:
        """Assess writing quality"""

        prompt = f"""Assess the academic writing quality of this text.

Section type: {section_type}
Text:
{draft.content[:1500]}

Check for:
1. Clarity and coherence
2. Academic tone and style
3. Logical flow between ideas
4. Grammar and language issues
5. Appropriate depth for the section type

For each significant issue, output:
QUALITY|issue_description|severity(low/medium/high)

If quality is acceptable, output: QUALITY_OK"""

        response = await self._call_llm(prompt)

        issues = []
        if "QUALITY_OK" not in response.upper():
            for line in response.strip().split("\n"):
                if line.startswith("QUALITY|"):
                    parts = line.split("|")
                    if len(parts) >= 2:
                        issues.append(ReviewIssue(
                            issue_type="quality",
                            description=parts[1].strip(),
                            severity=parts[2].strip().lower() if len(parts) > 2 else "low"
                        ))

        return issues

    def _calculate_accuracy_score(
        self,
        valid_citations: int,
        total_citations: int,
        hallucination_count: int,
        quality_issues: int
    ) -> float:
        """Calculate overall accuracy score (0-10)"""

        score = 10.0

        # Citation accuracy impact
        if total_citations > 0:
            citation_ratio = valid_citations / total_citations
            score -= (1 - citation_ratio) * 3  # Up to -3 for citation issues

        # Hallucination impact
        score -= hallucination_count * 1.5  # -1.5 per hallucination

        # Quality issues impact
        score -= quality_issues * 0.5  # -0.5 per quality issue

        return max(0.0, min(10.0, score))

    async def _revise_draft(
        self,
        draft: SectionDraft,
        issues: list[ReviewIssue],
        source_chunks: list[RankedChunk]
    ) -> str:
        """Revise draft to address identified issues"""

        # Format issues for revision prompt
        issues_text = "\n".join([
            f"- [{i.severity.upper()}] {i.issue_type}: {i.description}"
            for i in issues[:5]  # Limit issues shown
        ])

        # Format sources
        sources_text = "\n".join([
            f"[{i+1}] {chunk.document_name}: {chunk.content[:400]}..."
            for i, chunk in enumerate(source_chunks[:5])
        ])

        prompt = f"""Revise this academic text to address the identified issues.

Original text:
{draft.content}

Issues to address:
{issues_text}

Available sources:
{sources_text}

Requirements:
1. Fix citation errors - ensure all citations match available sources
2. Remove or rephrase unsupported claims
3. Maintain academic writing style
4. Keep the overall structure and main points
5. Preserve valid citations

Output the revised text only, no explanations."""

        revised = await self._call_llm(prompt, temperature=0.5, max_tokens=3000)

        self.logger.info(f"Revised draft for {draft.section_title}")
        return revised


async def test_review_worker():
    """Test ReviewWorker"""
    from models import Section, SectionTask, SectionComplexity, SectionDraft, RankedChunk

    worker = ReviewWorker()

    # Create mock draft with some issues
    draft = SectionDraft(
        section_title="Introduction",
        content="""Deep learning has revolutionized medical imaging diagnosis [1].
Studies show that CNN-based systems achieve 95% accuracy in detecting lung nodules [2].
The transformer architecture has become the dominant approach in 2024 [3].
Recent advances in federated learning enable privacy-preserving medical AI [4].
According to research, over 80% of radiologists now use AI assistance.""",
        citations=[],
        word_count=300,
        worker_type="simple"
    )

    # Create mock source chunks
    chunks = [
        RankedChunk(
            chunk_id="1",
            content="Deep learning has shown significant progress in medical image analysis...",
            document_name="DL_Medical_Survey.pdf",
            original_score=0.9,
            relevance_score=9.0,
            section_title="Introduction"
        ),
        RankedChunk(
            chunk_id="2",
            content="CNN models for lung nodule detection have achieved high sensitivity...",
            document_name="Lung_Detection_Study.pdf",
            original_score=0.85,
            relevance_score=8.5,
            section_title="Introduction"
        )
    ]

    section = Section(
        title="Introduction",
        section_type="introduction",
        keywords=["deep learning", "medical imaging"],
        word_limit=300
    )

    task = SectionTask(
        section=section,
        complexity=SectionComplexity.SIMPLE,
        draft=draft,
        ranked_chunks=chunks
    )

    test_input = WorkerInput(
        task=task,
        paper_topic="Deep Learning in Medical Image Diagnosis",
        dataset_ids=[]
    )

    print("=" * 60)
    print("Testing ReviewWorker")
    print("=" * 60)
    print(f"Section: {section.title}")
    print()

    output = await worker.process(test_input)

    if output.success:
        print("Review successful!")
        print()

        # The review result would be embedded in task processing
        # For standalone review, use review_draft method
        review = await worker.review_draft(draft, chunks)

        print(f"Accuracy Score: {review.accuracy_score:.1f}/10")
        print(f"Valid Citations: {review.valid_citations}/{review.total_citations}")
        print(f"Needs Revision: {review.needs_revision}")
        print()

        if review.issues:
            print("Issues Found:")
            for issue in review.issues:
                print(f"  [{issue.severity.upper()}] {issue.issue_type}: {issue.description}")
    else:
        print(f"Review failed: {output.error}")

    return output


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_review_worker())
