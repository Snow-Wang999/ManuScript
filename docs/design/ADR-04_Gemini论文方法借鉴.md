# Gemini 论文写作方法借鉴 - ManuScript 落实方案

> **文档目的**：将 Gemini 论文写作 7+3 模型中的可借鉴点，落实到 ManuScript 项目中
>
> **创建日期**：2026-01-19
>
> **适用版本**：v2.0 增强 + v2.5 新功能

---

## 一、借鉴来源分析

### Gemini 7步核心流程

| 步骤 | Gemini 方法 | ManuScript 现状 | 借鉴价值 |
|------|-------------|-----------------|---------|
| 1. 明确主题与结构 | 论文结构设计 | v1.0 SectionPlanner | ⭐⭐⭐ 可增强 |
| 2. 文献综述收集 | 推荐+综述生成 | RAGFlow 检索 | ⭐⭐⭐⭐⭐ 核心优势 |
| 3. 方法部分描述 | 专业化重写 | ComplexWorker | ⭐⭐⭐ 可增强 |
| 4. 结果可视化 | 图表建议 | 未覆盖 | ⭐ 低优先级 |
| 5. 讨论部分拓展 | 多角度展开 | ComplexWorker | ⭐⭐⭐⭐ 可增强 |
| 6. 首尾呼应检查 | 引言结论一致性 | **缺失** | ⭐⭐⭐⭐⭐ 新增 |
| 7. 学术语言润色 | 语言+引用规范 | ReviewWorker | ⭐⭐⭐ 可增强 |

### Gemini 3个进阶技巧

| 技巧 | 描述 | ManuScript 对应 | 借鉴价值 |
|------|------|-----------------|---------|
| 分段输入 | 章节级处理 | 已实现（分 Section） | ✅ 已有 |
| 迭代优化 | 多轮对话完善 | **可增强** | ⭐⭐⭐⭐ |
| 角色扮演 | 审稿人视角 | ReviewWorker 部分覆盖 | ⭐⭐⭐⭐ 可增强 |

---

## 二、落实分阶段规划

```
┌─────────────────────────────────────────────────────────────────────┐
│                        落实路线图                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   v2.0 增强          v2.5 新功能          v3.0 完整版               │
│   (1-2天)            (3-5天)              (未来)                    │
│                                                                     │
│   • 提示词模板化      • CoherenceChecker   • Web Search 补充        │
│   • 迭代优化循环      • 多角度审查          • 完整论文生成           │
│   • 讨论部分增强      • 章节类型专用prompt                           │
│                                                                     │
│   ────────────────────────────────────────────────────────────────  │
│   当前位置 ▲                                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、Phase 1: v2.0 增强方案

### 3.1 提示词模板化系统

**目标**：为不同章节类型设计专用 Prompt 模板，提高生成质量

**新增文件**：`v2_0/prompts/templates.py`

```python
"""
章节类型专用 Prompt 模板
借鉴自 Gemini 论文写作方法的结构化提示词设计
"""

from enum import Enum
from typing import Dict

class SectionType(Enum):
    INTRODUCTION = "introduction"
    LITERATURE_REVIEW = "literature_review"
    METHODOLOGY = "methodology"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"

# 章节类型专用模板
SECTION_TEMPLATES: Dict[SectionType, str] = {

    SectionType.INTRODUCTION: """
你是学术论文写作专家。请基于以下文献片段，撰写论文引言部分。

## 论文主题
{topic}

## 章节标题
{section_title}

## 文献片段
{chunks}

## 写作要求
1. 阐述研究背景和重要性
2. 指出当前研究的不足或空白
3. 明确本研究的目的和贡献
4. 每个关键论点必须标注来源 [文献名:页码]
5. 保持学术写作的客观性和严谨性

## 输出格式
直接输出段落内容，包含内联引用。
""",

    SectionType.LITERATURE_REVIEW: """
你是学术论文写作专家。请基于以下文献片段，撰写文献综述部分。

## 论文主题
{topic}

## 章节标题
{section_title}

## 文献片段
{chunks}

## 写作要求
1. 按主题或时间线组织文献
2. 总结现有研究的核心发现和方法
3. 指出研究现状中的问题和空白
4. 建立文献之间的对话关系
5. 每句话必须有文献支撑，标注 [文献名:页码]
6. 避免简单罗列，要有综合分析

## 输出格式
直接输出段落内容，包含内联引用。
""",

    SectionType.METHODOLOGY: """
你是学术论文写作专家。请基于以下文献片段，撰写研究方法部分。

## 论文主题
{topic}

## 章节标题
{section_title}

## 文献片段
{chunks}

## 写作要求
1. 详细描述研究方法的实施步骤
2. 说明数据收集过程和分析工具
3. 解释方法选择的依据（引用相关文献）
4. 讨论方法的局限性
5. 使用专业学术术语
6. 引用格式 [文献名:页码]

## 输出格式
直接输出段落内容，包含内联引用。
""",

    SectionType.DISCUSSION: """
你是学术论文写作专家。请基于以下文献片段，撰写讨论部分。

## 论文主题
{topic}

## 章节标题
{section_title}

## 文献片段
{chunks}

## 写作要求
从以下五个角度展开讨论：
1. **与现有文献的对话**：研究发现如何与已有研究呼应或冲突
2. **理论意义**：对该领域理论的贡献
3. **实践价值**：对实际应用的启示
4. **意外发现**：解释任何出乎意料的结果
5. **局限性**：诚实讨论研究的不足

每个论点必须有文献支撑，标注 [文献名:页码]

## 输出格式
直接输出段落内容，包含内联引用。
""",

    SectionType.CONCLUSION: """
你是学术论文写作专家。请基于以下文献片段，撰写结论部分。

## 论文主题
{topic}

## 章节标题
{section_title}

## 引言中提出的研究问题
{research_questions}

## 文献片段
{chunks}

## 写作要求
1. 直接回应引言中的研究问题
2. 总结主要研究发现
3. 强调研究贡献
4. 指出未来研究方向
5. 保持与引言的首尾呼应
6. 引用格式 [文献名:页码]

## 输出格式
直接输出段落内容，包含内联引用。
""",
}

def get_template(section_type: SectionType) -> str:
    """获取章节类型对应的 Prompt 模板"""
    return SECTION_TEMPLATES.get(section_type, SECTION_TEMPLATES[SectionType.INTRODUCTION])

def detect_section_type(section_title: str) -> SectionType:
    """根据章节标题推断章节类型"""
    title_lower = section_title.lower()

    keywords_map = {
        SectionType.INTRODUCTION: ["introduction", "引言", "背景", "background"],
        SectionType.LITERATURE_REVIEW: ["literature", "review", "综述", "相关工作", "related work"],
        SectionType.METHODOLOGY: ["method", "methodology", "方法", "实验设计", "approach"],
        SectionType.RESULTS: ["result", "finding", "结果", "发现", "experiment"],
        SectionType.DISCUSSION: ["discussion", "讨论", "分析", "analysis"],
        SectionType.CONCLUSION: ["conclusion", "结论", "总结", "summary"],
    }

    for section_type, keywords in keywords_map.items():
        if any(kw in title_lower for kw in keywords):
            return section_type

    return SectionType.INTRODUCTION  # 默认
```

### 3.2 迭代优化循环

**目标**：实现 "生成 → 检查 → 优化 → 再检查" 的循环

**修改文件**：`v2_0/workflow.py`

**新增状态和节点**：

```python
# 在 WorkflowState 中添加
class WorkflowState(TypedDict):
    # ... 现有字段
    iteration_count: int           # 迭代次数
    max_iterations: int            # 最大迭代次数（默认2）
    needs_revision: bool           # 是否需要修订
    revision_feedback: str         # 修订反馈

# 新增迭代优化节点
async def iterative_optimize_node(state: WorkflowState) -> WorkflowState:
    """
    迭代优化节点
    - 检查 ReviewWorker 的反馈
    - 决定是否需要再次修订
    - 控制迭代次数防止无限循环
    """
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 2)

    if iteration >= max_iter:
        state["needs_revision"] = False
        return state

    # 分析 review 结果
    review_result = state.get("review_result", {})

    # 如果引用准确率低于阈值，触发修订
    citation_accuracy = review_result.get("citation_accuracy", 1.0)
    if citation_accuracy < 0.9:  # 90% 阈值
        state["needs_revision"] = True
        state["revision_feedback"] = review_result.get("issues", [])
        state["iteration_count"] = iteration + 1
    else:
        state["needs_revision"] = False

    return state

# 在 workflow 中添加条件边
def should_iterate(state: WorkflowState) -> str:
    """决定是否继续迭代"""
    if state.get("needs_revision", False):
        return "revise"
    return "complete"
```

### 3.3 讨论部分多角度展开

**目标**：借鉴 Gemini 的"5角度讨论法"，增强 ComplexWorker

**修改文件**：`v2_0/workers/complex_worker.py`

**增强 `_generate_draft` 方法**：

```python
async def _generate_discussion_draft(
    self,
    section: Section,
    chunks: List[RetrievedChunk]
) -> str:
    """
    讨论部分专用生成方法 - 5角度展开
    借鉴自 Gemini 论文写作方法
    """
    prompt = f"""
你是学术论文写作专家。请基于以下文献，撰写讨论部分。

## 章节标题
{section.title}

## 文献片段
{self._format_chunks(chunks)}

## 写作要求 - 五角度展开法

请从以下5个角度展开讨论，每个角度2-3个要点：

### 1. 与现有文献的对话
- 本研究发现如何与已有研究呼应？
- 有哪些与现有研究不一致的发现？如何解释？

### 2. 理论意义
- 对该领域理论框架的贡献是什么？
- 是否支持、扩展或挑战了现有理论？

### 3. 实践应用价值
- 研究发现对实践有什么启示？
- 谁能从这些发现中受益？如何应用？

### 4. 意外发现的解释
- 是否有出乎意料的结果？
- 如何解释这些意外发现？

### 5. 研究局限性
- 本研究存在哪些局限？
- 这些局限如何影响结果的解释？

## 引用要求
- 每个论点必须有文献支撑
- 引用格式：[文献名:页码]

## 输出格式
直接输出讨论段落，自然整合以上5个角度，不要显式分点。
"""

    response = await self._call_llm(prompt)
    return response
```

---

## 四、Phase 2: v2.5 新功能方案

### 4.1 CoherenceChecker - 首尾呼应检查器

**目标**：检查引言和结论的逻辑一致性，确保研究问题被回应

**新增文件**：`v2_5/workers/coherence_checker.py`

```python
"""
CoherenceChecker Worker
检查论文各部分之间的逻辑一致性

借鉴自 Gemini 论文写作方法的"首尾呼应检查"
"""

from typing import List, Dict
from dataclasses import dataclass
from ..workers.base import BaseWorker
from ..models import Section, SectionDraft

@dataclass
class CoherenceReport:
    """一致性检查报告"""
    is_coherent: bool
    introduction_questions: List[str]      # 引言中的研究问题
    conclusion_answers: List[str]          # 结论中的回应
    missing_answers: List[str]             # 未被回应的问题
    suggestions: List[str]                 # 改进建议
    coherence_score: float                 # 一致性得分 0-1

class CoherenceCheckerWorker(BaseWorker):
    """
    首尾呼应检查器

    功能：
    1. 提取引言中的研究问题/目标
    2. 分析结论是否回应了这些问题
    3. 检查论点是否前后一致
    4. 提供修改建议
    """

    async def check_coherence(
        self,
        introduction: SectionDraft,
        conclusion: SectionDraft
    ) -> CoherenceReport:
        """检查引言和结论的一致性"""

        # Step 1: 提取引言中的研究问题
        questions = await self._extract_research_questions(introduction.content)

        # Step 2: 分析结论的回应情况
        answers = await self._analyze_conclusion_answers(conclusion.content, questions)

        # Step 3: 识别缺失的回应
        missing = self._find_missing_answers(questions, answers)

        # Step 4: 生成改进建议
        suggestions = await self._generate_suggestions(missing, conclusion.content)

        # 计算一致性得分
        if len(questions) > 0:
            score = (len(questions) - len(missing)) / len(questions)
        else:
            score = 1.0

        return CoherenceReport(
            is_coherent=len(missing) == 0,
            introduction_questions=questions,
            conclusion_answers=answers,
            missing_answers=missing,
            suggestions=suggestions,
            coherence_score=score
        )

    async def _extract_research_questions(self, intro_content: str) -> List[str]:
        """从引言中提取研究问题"""
        prompt = f"""
分析以下引言，提取其中明确或隐含的研究问题/研究目标。

## 引言内容
{intro_content}

## 输出格式
以 JSON 列表形式输出研究问题：
["研究问题1", "研究问题2", ...]

只输出 JSON，不要其他内容。
"""
        response = await self._call_llm(prompt)
        # 解析 JSON
        import json
        try:
            return json.loads(response)
        except:
            return []

    async def _analyze_conclusion_answers(
        self,
        conclusion_content: str,
        questions: List[str]
    ) -> List[str]:
        """分析结论对研究问题的回应"""
        prompt = f"""
分析以下结论是否回应了这些研究问题。

## 研究问题
{questions}

## 结论内容
{conclusion_content}

## 输出格式
以 JSON 列表形式输出被回应的问题及其回应：
[{{"question": "问题1", "answer": "结论中的回应"}}, ...]

只输出 JSON，不要其他内容。
"""
        response = await self._call_llm(prompt)
        import json
        try:
            return json.loads(response)
        except:
            return []

    async def _generate_suggestions(
        self,
        missing: List[str],
        conclusion: str
    ) -> List[str]:
        """生成改进建议"""
        if not missing:
            return ["结论与引言呼应良好，无需修改。"]

        prompt = f"""
以下研究问题在结论中未得到充分回应：
{missing}

当前结论：
{conclusion}

请提供具体的修改建议，说明如何在结论中补充对这些问题的回应。

输出格式：以编号列表形式给出建议。
"""
        response = await self._call_llm(prompt)
        return response.split("\n")
```

### 4.2 MultiPerspectiveReviewer - 多角度审查器

**目标**：模拟不同角色（审稿人、领域专家、批评者）审查论文

**新增文件**：`v2_5/workers/multi_perspective_reviewer.py`

```python
"""
MultiPerspectiveReviewer Worker
多角度审查器 - 模拟不同角色审查论文

借鉴自 Gemini 论文写作方法的"角色扮演"技巧
"""

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

class ReviewerRole(Enum):
    """审查者角色"""
    METHODOLOGIST = "methodologist"      # 方法论专家
    DOMAIN_EXPERT = "domain_expert"      # 领域专家
    SKEPTIC = "skeptic"                  # 批判性审稿人
    PRACTITIONER = "practitioner"        # 实践者

@dataclass
class PerspectiveReview:
    """单一视角的审查结果"""
    role: ReviewerRole
    strengths: List[str]
    weaknesses: List[str]
    questions: List[str]
    improvement_suggestions: List[str]

@dataclass
class MultiPerspectiveReport:
    """多角度审查报告"""
    reviews: List[PerspectiveReview]
    consensus_issues: List[str]          # 多个角色都指出的问题
    overall_score: float
    priority_improvements: List[str]      # 优先改进项

class MultiPerspectiveReviewerWorker:
    """
    多角度审查器

    模拟以下角色审查论文：
    1. 方法论专家 - 关注研究方法的严谨性
    2. 领域专家 - 关注专业知识的准确性
    3. 批判性审稿人 - 寻找逻辑漏洞
    4. 实践者 - 关注实际应用价值
    """

    ROLE_PROMPTS = {
        ReviewerRole.METHODOLOGIST: """
你是一位方法论专家，请从以下角度审查这篇论文：
- 研究设计是否合理？
- 样本选择是否有代表性？
- 数据分析方法是否恰当？
- 是否存在方法论上的漏洞？
""",

        ReviewerRole.DOMAIN_EXPERT: """
你是该领域的资深专家，请从以下角度审查这篇论文：
- 专业术语使用是否准确？
- 是否遗漏了重要的相关研究？
- 理论框架是否完整？
- 对领域的贡献是否清晰？
""",

        ReviewerRole.SKEPTIC: """
你是一位批判性很强的审稿人，请挑战这篇论文：
- 论证逻辑是否存在漏洞？
- 结论是否被数据充分支持？
- 是否存在过度概括？
- 有哪些替代解释被忽视？
""",

        ReviewerRole.PRACTITIONER: """
你是一位实际工作者，请从应用角度审查这篇论文：
- 研究发现是否有实际应用价值？
- 建议是否可操作？
- 是否考虑了实施的限制条件？
- 对从业者有什么启示？
""",
    }

    async def review_from_all_perspectives(
        self,
        draft: str,
        roles: List[ReviewerRole] = None
    ) -> MultiPerspectiveReport:
        """从多个角度审查论文"""

        if roles is None:
            roles = list(ReviewerRole)

        reviews = []
        for role in roles:
            review = await self._review_from_perspective(draft, role)
            reviews.append(review)

        # 找出共识问题
        consensus = self._find_consensus_issues(reviews)

        # 计算综合得分
        score = self._calculate_overall_score(reviews)

        # 确定优先改进项
        priorities = self._prioritize_improvements(reviews, consensus)

        return MultiPerspectiveReport(
            reviews=reviews,
            consensus_issues=consensus,
            overall_score=score,
            priority_improvements=priorities
        )

    async def _review_from_perspective(
        self,
        draft: str,
        role: ReviewerRole
    ) -> PerspectiveReview:
        """从特定角度审查"""

        role_instruction = self.ROLE_PROMPTS[role]

        prompt = f"""
{role_instruction}

## 待审查的论文内容
{draft}

## 输出格式（JSON）
{{
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["不足1", "不足2"],
    "questions": ["疑问1", "疑问2"],
    "improvement_suggestions": ["建议1", "建议2"]
}}

只输出 JSON，不要其他内容。
"""

        response = await self._call_llm(prompt)
        import json
        try:
            data = json.loads(response)
            return PerspectiveReview(
                role=role,
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                questions=data.get("questions", []),
                improvement_suggestions=data.get("improvement_suggestions", [])
            )
        except:
            return PerspectiveReview(
                role=role,
                strengths=[],
                weaknesses=["审查解析失败"],
                questions=[],
                improvement_suggestions=[]
            )
```

---

## 五、实施检查清单

### Phase 1: v2.0 增强（预计 1-2 天）

- [ ] 创建 `v2_0/prompts/` 目录
- [ ] 实现 `templates.py` 提示词模板系统
- [ ] 在 `BaseWorker` 中集成模板选择逻辑
- [ ] 增强 `ComplexWorker` 的讨论部分生成
- [ ] 在 `workflow.py` 中添加迭代优化循环
- [ ] 测试迭代优化效果

### Phase 2: v2.5 新功能（预计 3-5 天）

- [ ] 创建 `v2_5/` 目录结构
- [ ] 实现 `CoherenceCheckerWorker`
- [ ] 实现 `MultiPerspectiveReviewerWorker`
- [ ] 集成到 LangGraph workflow
- [ ] 更新 Gradio UI 显示审查报告
- [ ] 测试完整流程

---

## 六、与 ManuScript 核心优势的结合

### 关键差异化

| 维度 | Gemini 方法 | ManuScript |
|------|-------------|------------|
| 文献来源 | AI 推荐（可能虚构） | 本地文献库（真实可追溯） |
| 引用准确性 | 无法保证 | RAGFlow 检索 + Verifier 验证 |
| 定制化 | 通用提示词 | 章节类型专用模板 |
| 质量保证 | 用户自行检查 | 多角度自动审查 |

### ManuScript 的护城河

```
┌─────────────────────────────────────────────────────────────┐
│                    ManuScript 核心价值                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   用户本地文献库                                             │
│        │                                                    │
│        ▼                                                    │
│   RAGFlow 精准检索  ──►  每句话有原文支撑                    │
│        │                                                    │
│        ▼                                                    │
│   引用可追溯验证    ──►  Verifier + CoherenceChecker         │
│        │                                                    │
│        ▼                                                    │
│   学术诚信保障      ──►  区别于 AI "编造"引用                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 七、后续规划

### v3.0 考虑项（未来）

从 Gemini 方法中，以下功能可作为 v3.0 的候选：

1. **结果可视化建议** - 自动推荐图表类型
2. **Web Search 补充** - 当本地文献不足时联网搜索（需用户确认）
3. **完整论文生成** - 一键生成全文初稿

### 评估指标

| 指标 | 描述 | 目标值 |
|------|------|--------|
| 引用准确率 | 引用可追溯到原文的比例 | ≥ 95% |
| 首尾一致性 | CoherenceChecker 得分 | ≥ 0.9 |
| 多角度审查通过率 | 无严重问题的比例 | ≥ 80% |
| 生成延迟 | 单章节端到端时间 | ≤ 30s |

---

> **总结**：Gemini 方法提供了流程分解和多角度审查的思路，但其核心弱点（引用可能虚构）正是 ManuScript 的核心优势。本方案将 Gemini 的流程优化思想与 ManuScript 的 RAG 引用能力结合，形成差异化竞争力。
