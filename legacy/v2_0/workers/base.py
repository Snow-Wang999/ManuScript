# -*- coding: utf-8 -*-
"""
ManuScript v2.0 Worker Base Class

All workers inherit from this base class
"""
from abc import ABC, abstractmethod
from typing import List, Optional

import httpx

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config
from logger import get_logger
from models import (
    WorkerInput, WorkerOutput, SectionTask, TaskStatus,
    SearchQuery, DocumentChunk, RankedChunk, SectionDraft, Citation
)


class BaseWorker(ABC):
    """
    Base Worker class

    All workers must implement:
    - name: Worker name
    - worker_type: Worker type identifier
    - process(): Main processing logic
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.llm_config = config.get_llm_config()

    @property
    @abstractmethod
    def name(self) -> str:
        """Worker name"""
        pass

    @property
    @abstractmethod
    def worker_type(self) -> str:
        """Worker type identifier"""
        pass

    @abstractmethod
    async def process(self, input_data: WorkerInput) -> WorkerOutput:
        """
        Main processing logic

        Args:
            input_data: Worker input containing task and context

        Returns:
            Worker output with processed task
        """
        pass

    def log_start(self, task: SectionTask) -> None:
        """Log start of processing"""
        self.logger.info(
            f"[{self.name}] Processing section: {task.section.title}"
        )

    def log_end(self, task: SectionTask) -> None:
        """Log end of processing"""
        self.logger.info(
            f"[{self.name}] Completed section: {task.section.title}"
        )

    def log_error(self, error: Exception, task: SectionTask) -> None:
        """Log error during processing"""
        self.logger.error(
            f"[{self.name}] Failed on section {task.section.title}: {error}"
        )

    # ============ Shared Capabilities ============

    async def generate_queries(
        self,
        section_title: str,
        section_type: str,
        keywords: List[str],
        paper_topic: str,
        num_queries: int = 3
    ) -> List[SearchQuery]:
        """Generate search queries for a section"""

        keywords_str = ", ".join(keywords) if keywords else "none"

        prompt = f"""You are a research query generator. Generate {num_queries} search queries for retrieving relevant academic literature.

Paper Topic: {paper_topic}
Section Title: {section_title}
Section Type: {section_type}
Keywords: {keywords_str}

Requirements:
1. Generate {num_queries} diverse search queries
2. Include both broad and specific queries
3. Consider synonyms and related terms
4. Queries should be suitable for academic database search

Output format (one query per line, no numbering):
query 1
query 2
query 3"""

        response = await self._call_llm(prompt)
        queries = []

        for i, line in enumerate(response.strip().split("\n")):
            line = line.strip()
            if line and not line.startswith("#"):
                queries.append(SearchQuery(
                    query_text=line,
                    section_title=section_title,
                    query_type="semantic",
                    priority=i + 1
                ))

        self.logger.info(f"Generated {len(queries)} queries for {section_title}")
        return queries[:num_queries]

    async def retrieve_chunks(
        self,
        queries: List[SearchQuery],
        dataset_ids: List[str],
        top_k: int = 10
    ) -> List[DocumentChunk]:
        """Retrieve document chunks from RAGFlow with optimized parameters"""

        all_chunks = []

        # Build retrieval payload with RAGFlow optimization parameters
        base_payload = {
            "dataset_ids": dataset_ids,
            "top_k": top_k,
            "similarity_threshold": config.SIMILARITY_THRESHOLD,
            "vector_similarity_weight": config.VECTOR_SIMILARITY_WEIGHT,
        }
        # Add rerank model if configured
        if config.RERANK_MODEL_ID:
            base_payload["rerank_id"] = config.RERANK_MODEL_ID

        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in queries:
                try:
                    payload = {**base_payload, "question": query.query_text}
                    response = await client.post(
                        f"{config.RAGFLOW_API_BASE}/api/v1/retrieval",
                        headers={
                            "Authorization": f"Bearer {config.RAGFLOW_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json=payload
                    )
                    response.raise_for_status()
                    result = response.json()

                    raw_chunks = result.get("data", {}).get("chunks", [])
                    for i, chunk in enumerate(raw_chunks):
                        all_chunks.append(DocumentChunk(
                            chunk_id=chunk.get("id", f"{query.section_title}_{i}"),
                            content=chunk.get("content", ""),
                            document_name=chunk.get("document_name", "unknown"),
                            score=chunk.get("score", 0.0),
                            section_title=query.section_title,
                            query_text=query.query_text
                        ))

                    self.logger.debug(
                        f"Retrieved {len(raw_chunks)} chunks for query: {query.query_text[:50]}..."
                    )

                except Exception as e:
                    self.logger.warning(f"Retrieval failed for query: {e}")
                    continue

        # Deduplicate
        unique_chunks = self._deduplicate_chunks(all_chunks)
        self.logger.info(f"Retrieved {len(unique_chunks)} unique chunks")

        return unique_chunks

    def _deduplicate_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Remove duplicate chunks based on content"""
        seen = set()
        unique = []

        for chunk in chunks:
            content_hash = hash(chunk.content[:200])
            if content_hash not in seen:
                seen.add(content_hash)
                unique.append(chunk)

        return unique

    async def rank_chunks(
        self,
        chunks: List[DocumentChunk],
        section_title: str,
        writing_goal: str,
        max_chunks: int = 5
    ) -> List[RankedChunk]:
        """Rank chunks by relevance using LLM"""

        if not chunks:
            return []

        # Format chunks for ranking
        chunks_text = ""
        for i, chunk in enumerate(chunks[:15]):  # Limit to avoid token overflow
            chunks_text += f"\n[{i+1}] Source: {chunk.document_name}\n{chunk.content[:400]}\n"

        prompt = f"""You are evaluating document chunks for relevance to a paper section.

Section Title: {section_title}
Writing Goal: {writing_goal}

Document Chunks:
{chunks_text}

For each chunk, rate its relevance from 1-10 where:
- 10: Directly addresses the section topic with key insights
- 7-9: Highly relevant, contains useful information
- 4-6: Somewhat relevant, might be useful
- 1-3: Marginally relevant or off-topic

Output format (one per line):
chunk_number|score|brief_reason

Example:
1|9|Directly discusses methodology
2|6|Related but focuses on different aspect"""

        response = await self._call_llm(prompt)

        # Parse rankings
        ranked = []
        chunk_map = {i + 1: chunk for i, chunk in enumerate(chunks[:15])}

        for line in response.strip().split("\n"):
            try:
                parts = line.strip().split("|")
                if len(parts) >= 2:
                    idx = int(parts[0].strip())
                    score = float(parts[1].strip())
                    reason = parts[2].strip() if len(parts) > 2 else ""

                    if idx in chunk_map:
                        chunk = chunk_map[idx]
                        ranked.append(RankedChunk(
                            chunk_id=chunk.chunk_id,
                            content=chunk.content,
                            document_name=chunk.document_name,
                            original_score=chunk.score,
                            relevance_score=score,
                            section_title=section_title,
                            relevance_reason=reason
                        ))
            except (ValueError, IndexError):
                continue

        # Sort by relevance score and return top N
        ranked.sort(key=lambda x: x.relevance_score, reverse=True)
        return ranked[:max_chunks]

    async def write_section(
        self,
        paper_topic: str,
        section_title: str,
        section_type: str,
        writing_goal: str,
        word_limit: int,
        chunks: List[RankedChunk],
        citation_start: int = 1
    ) -> tuple[SectionDraft, int]:
        """Generate section content with citations"""

        # Format sources
        sources_text = ""
        citation_map = {}

        for i, chunk in enumerate(chunks):
            cid = citation_start + i
            citation_map[cid] = chunk
            sources_text += f"\n[{cid}] Source: {chunk.document_name}\n{chunk.content[:600]}\n"

        if not sources_text:
            sources_text = "(No relevant sources available)"

        prompt = f"""You are an academic writing expert. Write a section for a research paper.

Paper Topic: {paper_topic}
Section Title: {section_title}
Section Type: {section_type}
Writing Goal: {writing_goal}
Word Limit: approximately {word_limit} words

Available Sources:
{sources_text}

Requirements:
1. Write in formal academic style
2. Insert citation markers [1], [2], etc. at appropriate locations
3. Citations must correspond to the provided sources
4. Do not fabricate information not found in sources
5. Ensure logical flow between sentences and paragraphs
6. If sources are insufficient, note where additional citations are needed

Write the section content directly, without any preamble or section title."""

        content = await self._call_llm(prompt, temperature=0.7)

        # Extract used citations
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

        draft = SectionDraft(
            section_title=section_title,
            content=content,
            citations=citations,
            word_count=len(content),
            worker_type=self.worker_type
        )

        next_citation = citation_start + len(chunks)
        self.logger.info(
            f"Generated {len(content)} chars for {section_title} with {len(citations)} citations"
        )

        return draft, next_citation

    async def _call_llm(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """Call LLM API"""

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.llm_config['api_base']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.llm_config['api_key']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.llm_config["model"],
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            response.raise_for_status()
            result = response.json()

        return result["choices"][0]["message"]["content"]
