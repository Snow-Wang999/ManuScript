# -*- coding: utf-8 -*-
"""
ManuScript v2.0 Data Models

Pydantic models for Orchestrator-Worker architecture
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum


class SectionComplexity(str, Enum):
    """Section complexity levels"""
    SIMPLE = "simple"
    COMPLEX = "complex"
    UNKNOWN = "unknown"


class WorkerType(str, Enum):
    """Worker types"""
    SIMPLE = "simple"
    COMPLEX = "complex"
    REVIEW = "review"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


# ============ Input Models ============

class Section(BaseModel):
    """Section input from user outline"""
    title: str = Field(..., description="Section title")
    section_type: str = Field(..., description="Section type (e.g., introduction, method)")
    keywords: List[str] = Field(default_factory=list, description="Keywords for retrieval")
    description: str = Field(default="", description="Section description or requirements")
    word_limit: int = Field(default=500, description="Target word count")


class Outline(BaseModel):
    """Paper outline input"""
    topic: str = Field(..., description="Paper topic")
    sections: List[Section] = Field(..., description="List of sections")
    dataset_ids: List[str] = Field(default_factory=list, description="RAGFlow dataset IDs")


# ============ Retrieval Models ============

class SearchQuery(BaseModel):
    """Search query for RAGFlow"""
    query_text: str = Field(..., description="Query text")
    section_title: str = Field(..., description="Target section")
    query_type: str = Field(default="semantic", description="Query type")
    priority: int = Field(default=1, description="Query priority (1=highest)")


class DocumentChunk(BaseModel):
    """Retrieved document chunk"""
    chunk_id: str = Field(default="", description="Chunk ID")
    content: str = Field(..., description="Chunk content")
    document_name: str = Field(default="", description="Source document name")
    score: float = Field(default=0.0, description="Relevance score")
    section_title: str = Field(default="", description="Associated section")
    query_text: str = Field(default="", description="Original query")


class RankedChunk(BaseModel):
    """Chunk with ranking information"""
    chunk_id: str
    content: str
    document_name: str
    original_score: float = 0.0
    relevance_score: float = 0.0
    section_title: str = ""
    relevance_reason: str = ""


# ============ Writing Models ============

class Citation(BaseModel):
    """Citation information"""
    citation_id: str = Field(..., description="Citation ID like [1]")
    document_name: str = Field(..., description="Source document name")
    cited_content: str = Field(default="", description="Cited content excerpt")


class SectionDraft(BaseModel):
    """Generated section draft"""
    section_title: str
    content: str = Field(..., description="Generated text content")
    citations: List[Citation] = Field(default_factory=list)
    word_count: int = 0
    worker_type: str = Field(default="", description="Which worker generated this")


# ============ Task Models ============

class SectionTask(BaseModel):
    """Task for processing a single section"""
    section: Section
    complexity: SectionComplexity = SectionComplexity.UNKNOWN
    assigned_worker: Optional[WorkerType] = None
    status: TaskStatus = TaskStatus.PENDING

    # Intermediate results
    queries: List[SearchQuery] = Field(default_factory=list)
    chunks: List[DocumentChunk] = Field(default_factory=list)
    ranked_chunks: List[RankedChunk] = Field(default_factory=list)

    # Output
    draft: Optional[SectionDraft] = None
    error: Optional[str] = None


class TaskBatch(BaseModel):
    """Batch of tasks for parallel processing"""
    tasks: List[SectionTask] = Field(default_factory=list)
    paper_topic: str = ""
    dataset_ids: List[str] = Field(default_factory=list)


# ============ Worker I/O Models ============

class WorkerInput(BaseModel):
    """Base input for workers"""
    task: SectionTask
    paper_topic: str
    dataset_ids: List[str] = Field(default_factory=list)


class WorkerOutput(BaseModel):
    """Base output from workers"""
    success: bool = True
    task: SectionTask
    error: Optional[str] = None


# ============ Review Models ============

class ReviewIssue(BaseModel):
    """Issue found during review"""
    issue_type: str = Field(..., description="Type: citation_error, hallucination, style, etc.")
    description: str
    location: str = Field(default="", description="Where in text")
    suggestion: str = Field(default="", description="How to fix")
    severity: str = Field(default="medium", description="low, medium, high")


class ReviewResult(BaseModel):
    """Result of review process"""
    section_title: str
    accuracy_score: float = Field(default=0.0, description="0-10 score")
    issues: List[ReviewIssue] = Field(default_factory=list)
    valid_citations: int = 0
    total_citations: int = 0
    needs_revision: bool = False
    revised_content: Optional[str] = None


# ============ Orchestrator Models ============

class OrchestratorInput(BaseModel):
    """Input for the orchestrator"""
    outline: Outline
    parallel: bool = Field(default=True, description="Enable parallel processing")


class OrchestratorOutput(BaseModel):
    """Output from the orchestrator"""
    success: bool = True
    paper_topic: str
    drafts: List[SectionDraft] = Field(default_factory=list)
    all_citations: List[Citation] = Field(default_factory=list)
    reviews: List[ReviewResult] = Field(default_factory=list)
    total_words: int = 0
    error: Optional[str] = None

    # Execution stats
    tasks_completed: int = 0
    tasks_failed: int = 0
    simple_sections: int = 0
    complex_sections: int = 0


# ============ Workflow State ============

class WorkflowState(BaseModel):
    """State for LangGraph workflow"""
    # Input
    paper_topic: str = ""
    sections: List[dict] = Field(default_factory=list)
    dataset_ids: List[str] = Field(default_factory=list)

    # Task management
    tasks: List[dict] = Field(default_factory=list)
    pending_tasks: List[str] = Field(default_factory=list)
    completed_tasks: List[str] = Field(default_factory=list)

    # Results
    drafts: List[dict] = Field(default_factory=list)
    citations: List[dict] = Field(default_factory=list)
    reviews: List[dict] = Field(default_factory=list)

    # Status
    current_step: str = "initial"
    error: Optional[str] = None

    class Config:
        extra = "allow"
