# ManuScript Project Architecture

> Updated: 2026-01-18

---

## Project Overview

ManuScript is an AI-powered academic writing assistant that generates manuscripts with citations from document retrieval.

**Core Goal**: User provides topic + outline → System retrieves relevant papers → Generates cited paragraphs

---

## Two Architecture Paradigms

| Dimension | **Architecture A** | **Architecture B** |
|-----------|-------------------|-------------------|
| **Name** | Low-Code Assembly | Professional Code |
| **Tech Stack** | Dify + RAGFlow | LangGraph + Python + RAGFlow |
| **Directory** | `dify_demo/` | `v0_1/` ~ `v2_0/` |
| **Difficulty** | Low | High |
| **Flexibility** | Medium | Very High |
| **Best For** | Quick demos | Production system |

---

## Version Roadmap

### Architecture B (Main Line)

| Version | Status | Goal | Key Tech |
|---------|--------|------|----------|
| v0.1 | ✅ Complete | Validate RAGFlow + LLM | Python + httpx + openai |
| v0.2 | 📋 Planned | JSON outline + Prompt Chain | Python + Query Generator |
| v1.0 | 📋 Planned | Agent chain | LangGraph basics |
| v2.0 | 📋 Planned | Orchestrator-Worker | LangGraph + LangFuse |

### Architecture A (Dify)

| Version | Status | Goal |
|---------|--------|------|
| dify_demo | 📋 Planned | DSL workflow export |

---

## Directory Structure

```
ManuScript/
├── docs/
│   ├── tasks/               # Task tracking per version
│   │   ├── current_task_v0_1.md    ✅ Complete
│   │   ├── current_task_v0_2.md    📋 Planned
│   │   └── current_task_dify.md    📋 Planned
│   ├── 架构对比.md          # Architecture comparison (原始思考)
│   └── architecture.md      # This file
│
├── v0_1/                    # ✅ Minimal prototype
│   ├── config.py
│   ├── logger.py
│   ├── prototype.py
│   └── main.py
│
├── v0_2/                    # 📋 Basic flow
│   └── ...
│
├── v1_0/                    # 📋 Agent chain
│   └── agents/
│
├── v2_0/                    # 📋 Dynamic dispatch
│   └── workers/
│
├── dify_demo/               # 📋 Dify DSL exports
│   ├── README.md
│   └── manuscript_workflow.yml (TBD)
│
├── evaluation/              # Evaluation system
│
├── .env                     # API keys (git ignored)
└── CLAUDE.md                # Dev rules
```

---

## Shared Resources

All architectures share:
- `.env` - API keys (Qwen, DeepSeek, OpenRouter, RAGFlow)
- `docs/` - Documentation
- RAGFlow dataset: "deep research thesis" (ID: `32310c0cf44d11f0a204de7d5e8c9111`)

---

## Tech Stack Summary

| Component | Choice | Notes |
|-----------|--------|-------|
| **LLM** | Qwen (primary) | Also: DeepSeek, OpenRouter |
| **RAG** | RAGFlow API | Remote: ragflow2.excelmaster.ai |
| **Agent Framework** | LangGraph | For v1.0+ |
| **Observability** | LangFuse | For v2.0+ |
| **UI** | Gradio | Quick prototyping |
| **Low-Code** | Dify | Architecture A |

---

## Development Principles

1. **Version Isolation** - Each version is independent directory
2. **One version at a time** - Complete before moving to next
3. **Script first, UI later** - Validate logic before adding Gradio
4. **UTF-8 + English** - Avoid Windows encoding issues
5. **Citation accuracy is priority** - Generated text must have traceable citations
