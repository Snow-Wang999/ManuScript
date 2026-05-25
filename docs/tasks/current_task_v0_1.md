# Current Task: v0.1 Minimal Prototype

> **Status**: ✅ Complete
> **Prerequisites**: None
> **Goal**: Validate RAGFlow + LLM technical feasibility
> **Updated**: 2026-01-18

---

## Version Goals

Implement Minimal Viable Prototype (MVP):
1. Call RAGFlow API to retrieve documents
2. Call LLM API (Qwen/DeepSeek/OpenRouter) to generate cited paragraphs
3. Simple Gradio UI to validate the flow

---

## Data Flow

```
User Input (Topic + Section Title)
       |
Build Search Query
       |
RAGFlow API Retrieval
       |
List[Chunks]
       |
Format Context
       |
LLM API Generate Draft
       |
Paragraph with Citations Output
```

---

## File List

| File | Status | Description |
|------|--------|-------------|
| v0_1/config.py | [x] | Config management, reads .env (UTF-8) |
| v0_1/logger.py | [x] | Logging setup (UTF-8) |
| v0_1/prototype.py | [x] | Core script (RAGFlow + LLM) (UTF-8) |
| v0_1/main.py | [x] | Gradio UI (UTF-8) |
| v0_1/requirements.txt | [x] | Dependencies |
| v0_1/tests/test_prototype.py | [x] | Unit tests |
| .env | [x] | API config (Qwen + DeepSeek + OpenRouter + RAGFlow) |

---

## Current Progress

### Completed
- [x] Code written
- [x] Virtual environment created
- [x] Dependencies installed (python-dotenv, httpx, openai, gradio, pytest)
- [x] Fixed huggingface_hub version compatibility
- [x] All packages import successfully
- [x] .env configured with:
  - Qwen API (primary): qwen-plus model
  - DeepSeek (backup): deepseek-chat model
  - OpenRouter (backup): gpt-4o-mini model
  - RAGFlow: https://ragflow2.excelmaster.ai
- [x] Fixed Windows encoding issues (UTF-8 + English strings in all .py files)
- [x] **prototype.py LLM generation test PASSED** (2026-01-18)
  - Used mock data (skipped RAGFlow)
  - Qwen API called successfully
  - Generated academic paragraph with [1], [2] citations
- [x] **RAGFlow API connection test PASSED** (2026-01-18)
  - API responds with code: 0
  - Dataset list: empty (waiting for user to create)
- [x] **Gradio UI startup test PASSED** (2026-01-18)
  - Runs on http://127.0.0.1:7862 (auto port selection)
  - UI loads correctly

### Pending
- [x] Create RAGFlow dataset: "deep research thesis" (ID: 32310c0cf44d11f0a204de7d5e8c9111)
- [x] **End-to-end test PASSED** (2026-01-18)
  - RAGFlow returned 20 real chunks
  - Qwen generated 2240 chars with citations [1][2][3][9][10][14]
- [ ] Full Gradio UI interactive test (optional)

---

## Environment Config

### LLM API (Priority: Qwen > DeepSeek > OpenRouter)

Project root `.env` file:

```
# LLM API (Qwen - Primary)
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_API_KEY=sk-xxx
QWEN_MODEL=qwen-plus

# Backup: DeepSeek
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_MODEL=deepseek-chat

# Backup: OpenRouter
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=sk-or-xxx
OPENROUTER_MODEL=openai/gpt-4o-mini

# RAGFlow API
RAGFLOW_API_BASE=https://ragflow2.excelmaster.ai
RAGFLOW_API_KEY=ragflow-xxx

# Logging
LOG_LEVEL=INFO
```

---

## Acceptance Criteria

- [x] RAGFlow retrieval returns relevant chunks (20 chunks from 6 documents)
- [x] LLM generates paragraphs with [1], [2] citations
- [x] Gradio UI can start and display
- [x] End-to-end flow runs with real data

---

## Test Results

### 2026-01-18 LLM Generation Test
```
Topic: Deep learning in medical image analysis
Section: Research Background

Result: SUCCESS
- Qwen API responded in ~8 seconds
- Generated 1878 chars academic paragraph
- Citations [1], [2] correctly referenced mock sources
```

### 2026-01-18 RAGFlow Connection Test
```
API: https://ragflow2.excelmaster.ai/api/v1/datasets
Result: {"code":0,"data":[...],"total_datasets":1}
Dataset: "deep research thesis" (ID: 32310c0cf44d11f0a204de7d5e8c9111)
Documents: 6, Chunks: 545
```

### 2026-01-18 End-to-End Test (FINAL)
```
Topic: Deep learning in medical image analysis
Section: Research Background

RAGFlow: Retrieved 20 chunks in ~5 seconds
LLM: Generated 2240 chars in ~17 seconds
Citations: [1][2][3][9][10][14] correctly referenced

Result: SUCCESS - v0.1 MVP COMPLETE
```

---

## Notes

1. **LLM first** - Can skip RAGFlow, test generation with mock data
2. **API Key security** - .env is in .gitignore
3. **Detailed logging** - Helps debug RAG retrieval quality
4. **Windows encoding** - All .py files use UTF-8 declaration and English strings
5. **Port conflict** - Use auto port selection, Gradio finds available port
