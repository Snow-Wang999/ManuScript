# Current Task: v2.0 Orchestrator-Worker Dynamic Dispatch

> **Status**: Code development complete, ready for testing
> **Prerequisite**: v1.0 Chain-of-Agents verified
> **Goal**: Implement dynamic task dispatch with parallel processing
> **Updated**: 2026-01-23

---

## All Versions Status

| Version | Name | Status | Notes |
|---------|------|--------|-------|
| v0.1 | Minimal Prototype | ✅ Complete | End-to-end tested with real data (20 chunks, 2240 chars) |
| v0.2 | Basic Pipeline | ⏭️ Skipped | Superseded by v1.0 |
| v1.0 | Chain-of-Agents | ✅ Complete | 6 Agents tested, workflow integrated |
| v2.0 | Orchestrator-Worker | 🔵 Code Complete | Ready for functional testing |

---

## Version Goals

Implement Anthropic-style Orchestrator-Worker architecture:
1. **Orchestrator** - Central dispatcher, dynamic task assignment
2. **SimpleWorker** - Handles simple sections (introduction, conclusion)
3. **ComplexWorker** - Handles complex sections (method, experiment)
4. **ReviewWorker** - Quality audit and revision

---

## Architecture Design

```
                    ┌─────────────────┐
                    │   Orchestrator  │
                    │ (Central Dispatcher) │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │   Simple    │   │   Complex   │   │   Review    │
    │   Worker    │   │   Worker    │   │   Worker    │
    └─────────────┘   └─────────────┘   └─────────────┘

Parallel Processing: Up to MAX_PARALLEL_WORKERS concurrent tasks
```

---

## File Checklist

| File | Status | Description |
|------|--------|-------------|
| v2_0/config.py | ✅ Complete | Configuration with LLM provider fallback |
| v2_0/logger.py | ✅ Complete | Logging module |
| v2_0/models.py | ✅ Complete | Pydantic data models |
| v2_0/workers/base.py | ✅ Complete | BaseWorker with shared capabilities |
| v2_0/workers/simple_worker.py | ✅ Complete | SimpleWorker for basic sections |
| v2_0/workers/complex_worker.py | ✅ Complete | ComplexWorker for technical sections |
| v2_0/workers/review_worker.py | ✅ Complete | ReviewWorker for quality audit |
| v2_0/orchestrator.py | ✅ Complete | Central task dispatcher |
| v2_0/workflow.py | ✅ Complete | LangGraph workflow orchestration |
| v2_0/main.py | ✅ Complete | Gradio 3-column UI |
| v2_0/requirements.txt | ✅ Complete | Dependencies |
| v2_0/README.md | ✅ Complete | Documentation |

---

## Current Progress

### Completed
- [x] config.py - LLM provider fallback (Qwen/DeepSeek/OpenRouter)
- [x] models.py - Complete data model definitions
- [x] workers/base.py - BaseWorker with shared retrieval/writing
- [x] workers/simple_worker.py - 2 queries, basic ranking
- [x] workers/complex_worker.py - 5 queries, LLM ranking, analysis
- [x] workers/review_worker.py - Citation validation, hallucination check
- [x] orchestrator.py - Dynamic dispatch with parallel support
- [x] workflow.py - LangGraph StateGraph integration
- [x] main.py - 3-column Gradio UI

### To Do
- [ ] Install dependencies
- [ ] Test individual workers
- [ ] Test orchestrator
- [ ] Test full workflow
- [ ] Validate with 3 real paper topics
- [ ] Compare with v1.0 metrics

---

## Key Features

### Dynamic Complexity Analysis
```python
# Rule-based + LLM fallback
SIMPLE_SECTION_TYPES = ["introduction", "background", "conclusion", "abstract"]
COMPLEX_SECTION_TYPES = ["method", "experiment", "results", "discussion"]
```

### Worker Pipelines

| Worker | Queries | Pipeline |
|--------|---------|----------|
| Simple | 2 | Query → Retrieve → Draft |
| Complex | 5 | Analyze → Query → Retrieve → Rank → Draft |
| Review | - | Validate → Check Hallucination → Revise |

### Parallel Processing
- `MAX_PARALLEL_WORKERS = 3` (configurable)
- Uses `asyncio.Semaphore` for concurrency control
- Failed tasks don't block other tasks

---

## Run Commands

```bash
cd v2_0
pip install -r requirements.txt

# Test individual workers
python workers/simple_worker.py
python workers/complex_worker.py
python workers/review_worker.py

# Test orchestrator
python orchestrator.py

# Test full workflow
python workflow.py

# Start UI (port 7862)
python main.py
```

---

## Comparison with v1.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Architecture | Fixed 6-Agent chain | Dynamic Orchestrator-Worker |
| Processing | Sequential | Parallel (configurable) |
| Complexity | Uniform handling | Adaptive per section |
| Worker Count | 6 specialized agents | 3 worker types |
| Error Handling | Chain failure | Isolated task failure |

---

## Acceptance Criteria

- [ ] Workers run independently
- [ ] Orchestrator dispatches correctly by complexity
- [ ] Parallel processing works with semaphore
- [ ] Review worker validates citations
- [ ] 3-column UI displays progress
- [ ] Performance improvement over v1.0 (parallel)

---

## Previous Versions

### v1.0 Chain-of-Agents
- Status: ✅ Complete and tested
- Features: 6 specialized agents, LangGraph workflow

### v0.2 Basic Pipeline
- Status: ⏭️ Skipped
- Reason: Superseded by v1.0 (Query Generator, Prompt Chain, Citation all implemented)

### v0.1 Minimal Prototype
- Status: ✅ Complete
- Features: Single retrieval + generation
- Tested: End-to-end with real RAGFlow data (20 chunks → 2240 chars with citations)

---

## Environment Setup (2026-01-23)

### Completed Tasks

#### 1. Unified Virtual Environment
- [x] Created unified `.venv` at project root
- [x] Python version: 3.9.13
- [x] All versions (v0.1, v0.2, v1.0, v2.0) now share this environment

#### 2. Unified Dependencies
- [x] Created `requirements.txt` at project root
- [x] Merged dependencies from all version subdirectories
- [x] Fixed huggingface_hub/gradio compatibility issue:
  ```
  huggingface_hub>=0.19.3,<1.0.0
  ```

#### 3. Cleanup Old Environments
- [x] Removed `v0_1/.venv`
- [x] Removed `v0_2/.venv`
- [x] Removed `v1_0/.venv`
- [x] Removed `v2_0/.venv`

### Run Commands (Updated)

All versions now use the unified environment:

```bash
# Activate unified environment
cd d:/HandDeepResearch_AI/ManuScript
.venv/Scripts/activate  # Windows CMD
source .venv/Scripts/activate  # Git Bash

# Run any version
python v0_1/main.py      # v0.1 UI (port 7860)
python v1_0/main.py      # v1.0 UI (port 7862)
python v2_0/main.py      # v2.0 UI (port 7862)
```

### Known Issues
- pip install had network issues with Chinese mirrors (python-dateutil failed)
- Core dependencies verified working: gradio, httpx, openai, pydantic, langgraph
