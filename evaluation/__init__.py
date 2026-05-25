"""
ManuScript 评测模块

提供跨版本评测和对比功能，支持 Langfuse 追踪和 LLM-as-Judge

使用方式:
    # 命令行
    python -m evaluation.cli run --versions v0_1,v0_2 --llm-judge
    python -m evaluation.cli compare --versions v0_1,v0_2

    # 代码调用
    from evaluation import run_evaluation, compare_versions
    results = await run_evaluation(["v0_1", "v0_2"], use_llm_judge=True)
"""
from evaluation.metrics import (
    EvaluationResult,
    calculate_citation_accuracy,
    calculate_retrieval_relevance,
    calculate_overall_score,
    calculate_citation_count,
    check_min_requirements,
    aggregate_results,
)
from evaluation.compare import (
    load_test_cases,
    save_results,
    compare_versions,
    print_comparison,
)
from evaluation.text_quality import (
    TextQualityScore,
    evaluate_with_rules,
    evaluate_with_llm,
    create_evaluator,
)
from evaluation.runner import (
    TestCase,
    ExtendedEvaluationResult,
    run_evaluation,
    quick_test,
    evaluate_single,
    VERSION_RUNNERS,
)
from evaluation.langfuse_client import (
    LangfuseTracer,
    LangfuseConfig,
    get_tracer,
    get_langfuse_config,
    observe,
)
from evaluation.llm_judge import (
    LLMJudge,
    SupportLevel,
    CitationWithContext,
    JudgeResult,
    FaithfulnessReport,
    create_judge,
    extract_citations_with_context,
    quick_evaluate,
)

__all__ = [
    # metrics
    "EvaluationResult",
    "calculate_citation_accuracy",
    "calculate_retrieval_relevance",
    "calculate_overall_score",
    "calculate_citation_count",
    "check_min_requirements",
    "aggregate_results",
    # compare
    "load_test_cases",
    "save_results",
    "compare_versions",
    "print_comparison",
    # text_quality
    "TextQualityScore",
    "evaluate_with_rules",
    "evaluate_with_llm",
    "create_evaluator",
    # runner
    "TestCase",
    "ExtendedEvaluationResult",
    "run_evaluation",
    "quick_test",
    "evaluate_single",
    "VERSION_RUNNERS",
    # langfuse_client
    "LangfuseTracer",
    "LangfuseConfig",
    "get_tracer",
    "get_langfuse_config",
    "observe",
    # llm_judge
    "LLMJudge",
    "SupportLevel",
    "CitationWithContext",
    "JudgeResult",
    "FaithfulnessReport",
    "create_judge",
    "extract_citations_with_context",
    "quick_evaluate",
]
