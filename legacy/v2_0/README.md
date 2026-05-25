# ManuScript v2.0 - Orchestrator-Worker Dynamic Dispatch

## Overview

v2.0 implements an Anthropic-style multi-agent system with dynamic task dispatching:

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
```

## Features

- **Dynamic Dispatch**: Automatically classifies sections by complexity
- **Parallel Processing**: Process multiple sections concurrently
- **Specialized Workers**: Different processing pipelines for different content types
- **Quality Review**: Automatic citation validation and hallucination detection

## Architecture

### Workers

| Worker | Section Types | Queries | Pipeline |
|--------|--------------|---------|----------|
| SimpleWorker | introduction, background, conclusion | 2 | Query → Retrieve → Draft |
| ComplexWorker | method, experiment, results, discussion | 5 | Analyze → Query → Retrieve → Rank → Draft |
| ReviewWorker | All sections | - | Validate → Check → Revise |

### Processing Flow

1. **Orchestrator** receives paper outline
2. **Complexity Analysis** classifies each section
3. **Task Assignment** dispatches to appropriate workers
4. **Parallel Execution** with configurable concurrency
5. **Review Process** validates all generated content
6. **Aggregation** combines results with unified citations

## Installation

```bash
cd v2_0
pip install -r requirements.txt
```

## Configuration

Environment variables in `.env`:

```env
# LLM API (supports Qwen, DeepSeek, OpenRouter)
QWEN_API_KEY=your-api-key
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

# RAGFlow API
RAGFLOW_API_BASE=https://your-ragflow-instance
RAGFLOW_API_KEY=your-ragflow-key

# v2.0 Settings
MAX_PARALLEL_WORKERS=3
LOG_LEVEL=INFO
```

## Usage

### Gradio UI

```bash
python main.py
```

Access at `http://localhost:7862`

### Programmatic

```python
import asyncio
from workflow import ManuScriptV2Workflow

async def main():
    workflow = ManuScriptV2Workflow()

    sections = [
        {
            "title": "Introduction",
            "section_type": "introduction",
            "keywords": ["deep learning", "medical imaging"],
            "word_limit": 300
        },
        {
            "title": "Methodology",
            "section_type": "method",
            "keywords": ["CNN", "segmentation"],
            "word_limit": 600
        }
    ]

    result = await workflow.run(
        paper_topic="Deep Learning in Medical Imaging",
        sections=sections,
        parallel=True
    )

    if result["success"]:
        for draft in result["drafts"]:
            print(f"## {draft['section_title']}")
            print(draft["content"])

asyncio.run(main())
```

## Comparison with v1.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Architecture | Fixed 6-Agent chain | Dynamic Orchestrator-Worker |
| Processing | Sequential | Parallel (configurable) |
| Complexity Handling | Uniform | Adaptive per section |
| Worker Types | 6 specialized agents | 3 worker types |
| Error Recovery | Chain failure | Isolated task failure |

## File Structure

```
v2_0/
├── config.py           # Configuration management
├── logger.py           # Logging setup
├── models.py           # Pydantic data models
├── orchestrator.py     # Central dispatcher
├── workflow.py         # LangGraph orchestration
├── main.py             # Gradio UI
├── requirements.txt    # Dependencies
├── workers/
│   ├── __init__.py
│   ├── base.py         # Worker base class
│   ├── simple_worker.py
│   ├── complex_worker.py
│   └── review_worker.py
└── tests/              # Test suite
```

## Testing

```bash
# Test individual workers
python workers/simple_worker.py
python workers/complex_worker.py
python workers/review_worker.py

# Test orchestrator
python orchestrator.py

# Test full workflow
python workflow.py
```

## Development Notes

- All workers inherit from `BaseWorker` with shared retrieval/writing capabilities
- LLM provider fallback: Qwen → DeepSeek → OpenRouter
- Parallel execution respects `MAX_PARALLEL_WORKERS` limit
- Review process is automatic but can be disabled
