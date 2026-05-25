# Current Task: Dify Demo (Architecture A)

> **Status**: Planned
> **Prerequisites**: v0.1 Complete
> **Goal**: Create low-code Dify workflow for quick demo
> **Updated**: 2026-01-18

---

## Version Goals

Create a Dify DSL workflow that:
1. Accepts user input (topic + optional outline)
2. Calls RAGFlow API for document retrieval
3. Generates manuscript sections with citations
4. Outputs formatted manuscript

---

## Deliverables

| File | Status | Description |
|------|--------|-------------|
| dify_demo/manuscript_workflow.yml | [ ] | Main Dify DSL export |
| dify_demo/README.md | [x] | Documentation |

---

## Workflow Design

```
[Start]
   ↓
[User Input] - Topic, optional outline
   ↓
[HTTP Request] - RAGFlow /retrieval (get initial context)
   ↓
[LLM] - Generate outline if not provided
   ↓
[Iterator] - For each section in outline:
   │
   ├─→ [HTTP Request] - RAGFlow /retrieval (section-specific)
   │
   ├─→ [LLM] - Generate draft with [1][2] citations
   │
   └─→ [Collect results]
   ↓
[LLM] - Format final output
   ↓
[End] - Return manuscript + references
```

---

## RAGFlow API Integration

```yaml
# HTTP Request Node Configuration
method: POST
url: https://ragflow2.excelmaster.ai/api/v1/retrieval
headers:
  Authorization: Bearer {{ragflow_api_key}}
  Content-Type: application/json
body:
  question: "{{section_query}}"
  dataset_ids: ["32310c0cf44d11f0a204de7d5e8c9111"]
  top_k: 5
```

---

## Acceptance Criteria

- [ ] DSL file imports successfully into Dify
- [ ] RAGFlow retrieval works via HTTP node
- [ ] LLM generates cited paragraphs
- [ ] Iterator handles multiple sections
- [ ] Output is properly formatted

---

## Notes

1. **Export DSL only** - No Python code in this version
2. **Use Dify variables** - For API keys and dynamic values
3. **Keep it simple** - Avoid complex branching
4. **Compare with v0.1** - Same functionality, different approach
