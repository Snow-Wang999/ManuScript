"""
ManuScript 评测执行器

运行各版本并收集评测结果，支持 Langfuse 追踪和 LLM-as-Judge 评测

支持的版本:
- v0_1: 最小原型
- v0_2: 基础流程
- v1_0: Agent 链
- v2_0: 动态调度
- local_mcp: 本地隐私版
"""
import asyncio
import time
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Any

# 添加根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from evaluation.metrics import (
    EvaluationResult,
    calculate_citation_accuracy,
    calculate_retrieval_relevance,
    calculate_overall_score,
)
from evaluation.compare import save_results, load_test_cases
from evaluation.langfuse_client import get_tracer, LangfuseTracer
from evaluation.llm_judge import (
    LLMJudge,
    FaithfulnessReport,
    create_judge,
)


@dataclass
class TestCase:
    """测试用例"""
    id: str
    topic: str
    sections: list[dict]
    expected: dict


@dataclass
class ExtendedEvaluationResult:
    """扩展评测结果（包含 LLM-as-Judge）"""
    base_result: EvaluationResult
    faithfulness_report: FaithfulnessReport | None = None

    @property
    def version(self) -> str:
        return self.base_result.version

    @property
    def faithfulness_score(self) -> float:
        if self.faithfulness_report:
            return self.faithfulness_report.faithfulness_score
        return 0.0

    @property
    def hallucination_rate(self) -> float:
        if self.faithfulness_report:
            return self.faithfulness_report.hallucination_rate
        return 1.0

    def to_dict(self) -> dict:
        result = self.base_result.to_dict()
        result["faithfulness_score"] = self.faithfulness_score
        result["hallucination_rate"] = self.hallucination_rate
        if self.faithfulness_report:
            result["faithfulness_details"] = self.faithfulness_report.to_dict()
        return result


def parse_test_cases(raw_cases: list[dict]) -> list[TestCase]:
    """解析测试用例"""
    return [
        TestCase(
            id=tc["id"],
            topic=tc["topic"],
            sections=tc["sections"],
            expected=tc.get("expected", {})
        )
        for tc in raw_cases
    ]


async def run_v0_1(topic: str, section_title: str, keywords: list[str]) -> dict:
    """
    运行 v0.1 版本

    Returns:
        包含 chunks, draft, latency_ms 的结果
    """
    v0_1_path = str(ROOT_DIR / "v0_1")
    if v0_1_path not in sys.path:
        sys.path.insert(0, v0_1_path)

    try:
        from v0_1.prototype import run_prototype

        start_time = time.time()
        result = await run_prototype(topic, section_title)
        latency_ms = (time.time() - start_time) * 1000

        return {
            "chunks": result.get("chunks", []),
            "draft": result.get("draft", ""),
            "latency_ms": latency_ms
        }
    except ImportError as e:
        return {"error": f"导入 v0_1 失败: {e}", "chunks": [], "draft": "", "latency_ms": 0}
    except Exception as e:
        return {"error": str(e), "chunks": [], "draft": "", "latency_ms": 0}


async def run_v0_2(topic: str, section_title: str, keywords: list[str]) -> dict:
    """
    运行 v0.2 版本

    Returns:
        包含 chunks, draft, latency_ms 的结果
    """
    v0_2_path = str(ROOT_DIR / "v0_2")
    if v0_2_path not in sys.path:
        sys.path.insert(0, v0_2_path)

    try:
        from v0_2.query_generator import Outline, Section, generate_queries

        start_time = time.time()

        outline = Outline(
            topic=topic,
            sections=[Section(title=section_title, keywords=keywords)]
        )
        queries = generate_queries(outline, 0)

        # TODO: 当 v0.2 pipeline 实现后替换此占位逻辑
        latency_ms = (time.time() - start_time) * 1000

        return {
            "chunks": [],
            "draft": f"[v0.2 pipeline 未完成] 生成查询: {queries}",
            "latency_ms": latency_ms,
            "queries": queries
        }
    except ImportError as e:
        return {"error": f"导入 v0_2 失败: {e}", "chunks": [], "draft": "", "latency_ms": 0}
    except Exception as e:
        return {"error": str(e), "chunks": [], "draft": "", "latency_ms": 0}


async def run_v1_0(topic: str, section_title: str, keywords: list[str]) -> dict:
    """运行 v1.0 版本 (Agent 链)"""
    return {
        "error": "v1.0 尚未实现",
        "chunks": [],
        "draft": "",
        "latency_ms": 0
    }


async def run_v2_0(topic: str, section_title: str, keywords: list[str]) -> dict:
    """运行 v2.0 版本 (动态调度)"""
    return {
        "error": "v2.0 尚未实现",
        "chunks": [],
        "draft": "",
        "latency_ms": 0
    }


async def run_local_mcp(topic: str, section_title: str, keywords: list[str]) -> dict:
    """运行 local_mcp 版本 (本地隐私版)"""
    local_mcp_path = str(ROOT_DIR / "local_mcp")
    if local_mcp_path not in sys.path:
        sys.path.insert(0, local_mcp_path)

    try:
        # TODO: 当 local_mcp 版本实现后替换此占位逻辑
        from local_mcp.runner import run_local_pipeline

        start_time = time.time()
        result = await run_local_pipeline(topic, section_title, keywords)
        latency_ms = (time.time() - start_time) * 1000

        return {
            "chunks": result.get("chunks", []),
            "draft": result.get("draft", ""),
            "latency_ms": latency_ms
        }
    except ImportError:
        return {
            "error": "local_mcp 尚未实现",
            "chunks": [],
            "draft": "",
            "latency_ms": 0
        }
    except Exception as e:
        return {"error": str(e), "chunks": [], "draft": "", "latency_ms": 0}


VERSION_RUNNERS = {
    "v0_1": run_v0_1,
    "v0_2": run_v0_2,
    "v1_0": run_v1_0,
    "v2_0": run_v2_0,
    "local_mcp": run_local_mcp,
}


async def evaluate_single(
    version: str,
    test_case: TestCase,
    section: dict,
    text_quality_evaluator: Callable[[str], float] | None = None,
    use_llm_judge: bool = False,
    llm_judge: LLMJudge | None = None,
    tracer: LangfuseTracer | None = None
) -> ExtendedEvaluationResult:
    """
    评测单个测试用例的单个章节

    Args:
        version: 版本号
        test_case: 测试用例
        section: 章节信息
        text_quality_evaluator: 文本质量评估函数
        use_llm_judge: 是否使用 LLM-as-Judge 评测引用准确性
        llm_judge: LLM 评判器实例
        tracer: Langfuse 追踪器

    Returns:
        扩展评测结果
    """
    runner = VERSION_RUNNERS.get(version)
    if not runner:
        raise ValueError(f"未知版本: {version}")

    test_case_id = f"{test_case.id}_{section['title']}"
    tracer = tracer or get_tracer()

    # 使用 Langfuse 追踪
    with tracer.trace(
        name="evaluate_section",
        version=version,
        test_case_id=test_case_id,
        metadata={
            "topic": test_case.topic,
            "section_title": section["title"],
            "keywords": section.get("keywords", [])
        }
    ) as trace:
        # 执行生成
        with tracer.span("run_version", trace, input_data={"version": version}) as span:
            result = await runner(
                test_case.topic,
                section["title"],
                section.get("keywords", [])
            )
            if span:
                span.end(output={
                    "has_error": bool(result.get("error")),
                    "chunks_count": len(result.get("chunks", [])),
                    "draft_length": len(result.get("draft", "")),
                    "latency_ms": result.get("latency_ms", 0)
                })

        # 处理错误情况
        if "error" in result and result["error"]:
            base_result = EvaluationResult(
                version=version,
                test_case_id=test_case_id,
                citation_accuracy=0.0,
                retrieval_relevance=0.0,
                text_quality=0.0,
                latency_ms=result.get("latency_ms", 0),
                overall_score=0.0
            )
            return ExtendedEvaluationResult(base_result=base_result)

        chunks = result.get("chunks", [])
        draft = result.get("draft", "")

        # 计算基础指标
        citation_acc = calculate_citation_accuracy(draft, chunks)
        retrieval_rel = calculate_retrieval_relevance(
            f"{test_case.topic} {section['title']}",
            chunks
        )

        # 计算文本质量
        if text_quality_evaluator and draft:
            text_quality = text_quality_evaluator(draft)
        else:
            min_length = test_case.expected.get("min_length", 100)
            text_quality = min(1.0, len(draft) / min_length) if draft else 0.0

        # LLM-as-Judge 评测引用忠实度
        faithfulness_report = None
        if use_llm_judge and draft and chunks:
            judge = llm_judge or create_judge()
            if judge:
                with tracer.span("llm_judge", trace, input_data={"draft_length": len(draft)}) as span:
                    faithfulness_report = await judge.evaluate_faithfulness(draft, chunks)
                    if span:
                        span.end(output={
                            "faithfulness_score": faithfulness_report.faithfulness_score,
                            "hallucination_rate": faithfulness_report.hallucination_rate
                        })

        # 计算综合得分
        overall = calculate_overall_score(
            citation_acc,
            retrieval_rel,
            text_quality,
            result.get("latency_ms", 0)
        )

        base_result = EvaluationResult(
            version=version,
            test_case_id=test_case_id,
            citation_accuracy=citation_acc,
            retrieval_relevance=retrieval_rel,
            text_quality=text_quality,
            latency_ms=result.get("latency_ms", 0),
            overall_score=overall
        )

        # 记录评分到 Langfuse
        if trace:
            tracer.score(trace, "citation_accuracy", citation_acc)
            tracer.score(trace, "retrieval_relevance", retrieval_rel)
            tracer.score(trace, "text_quality", text_quality)
            tracer.score(trace, "overall_score", overall)
            if faithfulness_report:
                tracer.score(trace, "faithfulness", faithfulness_report.faithfulness_score)
                tracer.score(trace, "hallucination_rate", faithfulness_report.hallucination_rate)

        return ExtendedEvaluationResult(
            base_result=base_result,
            faithfulness_report=faithfulness_report
        )


async def run_evaluation(
    versions: list[str],
    test_cases: list[TestCase] | None = None,
    text_quality_evaluator: Callable[[str], float] | None = None,
    use_llm_judge: bool = False,
    verbose: bool = True
) -> dict[str, list[ExtendedEvaluationResult]]:
    """
    运行完整评测

    Args:
        versions: 要评测的版本列表
        test_cases: 测试用例，不传则从 yaml 加载
        text_quality_evaluator: 文本质量评估函数
        use_llm_judge: 是否使用 LLM-as-Judge 评测引用准确性
        verbose: 是否打印进度

    Returns:
        各版本的评测结果
    """
    if test_cases is None:
        raw_cases = load_test_cases()
        test_cases = parse_test_cases(raw_cases)

    all_results: dict[str, list[ExtendedEvaluationResult]] = {v: [] for v in versions}

    # 初始化 LLM Judge（如果需要）
    llm_judge = create_judge() if use_llm_judge else None
    tracer = get_tracer()

    if verbose:
        print(f"Langfuse 追踪: {'已启用' if tracer.is_enabled() else '未启用'}")
        print(f"LLM-as-Judge: {'已启用' if llm_judge else '未启用'}")

    for version in versions:
        if verbose:
            print(f"\n评测 {version}...")

        for tc in test_cases:
            for section in tc.sections:
                if verbose:
                    print(f"  - {tc.id}: {section['title']}")

                result = await evaluate_single(
                    version=version,
                    test_case=tc,
                    section=section,
                    text_quality_evaluator=text_quality_evaluator,
                    use_llm_judge=use_llm_judge,
                    llm_judge=llm_judge,
                    tracer=tracer
                )
                all_results[version].append(result)

        # 保存结果（转换为 EvaluationResult 列表）
        base_results = [r.base_result for r in all_results[version]]
        save_results(base_results, version)

        if verbose:
            avg_score = sum(r.base_result.overall_score for r in all_results[version]) / len(all_results[version])
            print(f"  {version} 平均得分: {avg_score:.3f}")

            if use_llm_judge:
                valid_reports = [r for r in all_results[version] if r.faithfulness_report]
                if valid_reports:
                    avg_faith = sum(r.faithfulness_score for r in valid_reports) / len(valid_reports)
                    avg_halluc = sum(r.hallucination_rate for r in valid_reports) / len(valid_reports)
                    print(f"  {version} 忠实度: {avg_faith:.3f}, 幻觉率: {avg_halluc:.3f}")

    # 确保 Langfuse 数据发送
    tracer.flush()

    return all_results


async def quick_test(
    version: str = "v0_1",
    use_llm_judge: bool = False
) -> ExtendedEvaluationResult:
    """
    快速测试单个版本

    Args:
        version: 版本号
        use_llm_judge: 是否使用 LLM-as-Judge

    Returns:
        扩展评测结果
    """
    test_case = TestCase(
        id="quick_test",
        topic="深度学习在医学图像分析中的应用",
        sections=[{"title": "研究背景", "keywords": ["深度学习", "医学图像"]}],
        expected={"min_citations": 2, "min_length": 200}
    )
    return await evaluate_single(
        version=version,
        test_case=test_case,
        section=test_case.sections[0],
        use_llm_judge=use_llm_judge
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="快速测试")
    parser.add_argument("--version", "-v", default="v0_1", help="版本号")
    parser.add_argument("--llm-judge", action="store_true", help="使用 LLM-as-Judge")
    args = parser.parse_args()

    result = asyncio.run(quick_test(args.version, args.llm_judge))

    print(f"\n快速测试结果:")
    print(f"  版本: {result.version}")
    print(f"  引用准确率: {result.base_result.citation_accuracy:.3f}")
    print(f"  检索相关性: {result.base_result.retrieval_relevance:.3f}")
    print(f"  文本质量: {result.base_result.text_quality:.3f}")
    print(f"  延迟: {result.base_result.latency_ms:.1f}ms")
    print(f"  综合得分: {result.base_result.overall_score:.3f}")

    if result.faithfulness_report:
        print(f"\nLLM-as-Judge 评测:")
        print(f"  忠实度: {result.faithfulness_score:.3f}")
        print(f"  幻觉率: {result.hallucination_rate:.3f}")
        print(f"  详情: {result.faithfulness_report.supported} 支撑, "
              f"{result.faithfulness_report.partial} 部分, "
              f"{result.faithfulness_report.neutral} 无关, "
              f"{result.faithfulness_report.contradicted} 矛盾")
