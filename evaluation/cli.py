"""
ManuScript 评测命令行工具

使用方式:
    python -m evaluation.cli run --versions v0_1,v0_2 --llm-judge
    python -m evaluation.cli compare --versions v0_1,v0_2
    python -m evaluation.cli quick-test --version v0_1 --llm-judge
    python -m evaluation.cli test-langfuse
"""
import argparse
import asyncio
import sys
from pathlib import Path

# 添加根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


def cmd_run(args):
    """运行评测"""
    from evaluation.runner import run_evaluation
    from evaluation.text_quality import create_evaluator

    versions = args.versions.split(",") if args.versions else ["v0_1"]

    # 创建文本质量评估器
    evaluator = None
    if args.use_llm:
        import os
        from dotenv import load_dotenv
        load_dotenv(ROOT_DIR / ".env")
        evaluator = create_evaluator(
            use_llm=True,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE")
        )
    else:
        evaluator = create_evaluator(use_llm=False)

    print(f"开始评测版本: {versions}")
    print(f"使用 LLM 评估文本质量: {args.use_llm}")
    print(f"使用 LLM-as-Judge 评估引用: {args.llm_judge}")
    print("-" * 50)

    results = asyncio.run(run_evaluation(
        versions=versions,
        text_quality_evaluator=evaluator,
        use_llm_judge=args.llm_judge,
        verbose=True
    ))

    print("\n" + "=" * 50)
    print("评测完成！结果已保存到 evaluation/results/ 目录")

    if args.llm_judge:
        print("\n忠实度评测摘要:")
        for version, version_results in results.items():
            valid = [r for r in version_results if r.faithfulness_report]
            if valid:
                avg_faith = sum(r.faithfulness_score for r in valid) / len(valid)
                avg_halluc = sum(r.hallucination_rate for r in valid) / len(valid)
                print(f"  {version}: 忠实度={avg_faith:.3f}, 幻觉率={avg_halluc:.3f}")


def cmd_compare(args):
    """对比版本"""
    from evaluation.compare import compare_versions, print_comparison

    versions = args.versions.split(",") if args.versions else ["v0_1", "v0_2"]

    print(f"对比版本: {versions}")
    comparison = compare_versions(versions)
    print_comparison(comparison)


def cmd_quick_test(args):
    """快速测试"""
    from evaluation.runner import quick_test

    version = args.version or "v0_1"
    use_llm_judge = args.llm_judge

    print(f"快速测试 {version}...")
    print(f"LLM-as-Judge: {'启用' if use_llm_judge else '禁用'}")

    result = asyncio.run(quick_test(version, use_llm_judge))

    print(f"\n结果:")
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
        report = result.faithfulness_report
        print(f"  详情: {report.supported} 支撑, {report.partial} 部分, "
              f"{report.neutral} 无关, {report.contradicted} 矛盾")


def cmd_list_cases(args):
    """列出测试用例"""
    from evaluation.compare import load_test_cases

    cases = load_test_cases()
    print(f"共 {len(cases)} 个测试用例:\n")

    for tc in cases:
        print(f"  [{tc['id']}] {tc['topic']}")
        for section in tc.get("sections", []):
            print(f"    - {section['title']} ({section.get('type', 'default')})")
        print()


def cmd_test_langfuse(args):
    """测试 Langfuse 连接"""
    from evaluation.langfuse_client import get_tracer

    print("测试 Langfuse 连接...")
    tracer = get_tracer()

    if tracer.is_enabled():
        print("✓ Langfuse 已连接")

        # 创建测试 trace
        with tracer.trace("connection_test", "test", "test_connection") as trace:
            tracer.score(trace, "test_score", 1.0, "连接测试成功")

        print("✓ 测试 trace 已创建")
        print("\n请在 Langfuse Dashboard 中查看:")
        print(f"  {tracer.config.host}")
    else:
        print("✗ Langfuse 未配置或连接失败")
        print("\n请检查 .env 文件中的配置:")
        print("  LANGFUSE_PUBLIC_KEY=pk-lf-xxx")
        print("  LANGFUSE_SECRET_KEY=sk-lf-xxx")


def cmd_test_judge(args):
    """测试 LLM-as-Judge"""
    from evaluation.llm_judge import create_judge, LLMJudge

    print("测试 LLM-as-Judge...")
    judge = create_judge()

    if judge is None:
        print("✗ LLM Judge 未配置")
        print("\n请检查 .env 文件中的 OPENAI_API_KEY")
        return

    print("✓ LLM Judge 已配置")

    # 测试评估
    sample_draft = "深度学习在医学图像分析中取得了显著进展[1]。"
    sample_chunks = [
        {"content": "近年来深度学习技术在医学图像领域展现出巨大潜力。", "document_name": "test.pdf"}
    ]

    print("\n运行测试评估...")
    report = asyncio.run(judge.evaluate_faithfulness(sample_draft, sample_chunks))

    print(f"✓ 评估完成")
    print(f"  忠实度: {report.faithfulness_score:.3f}")
    print(f"  幻觉率: {report.hallucination_rate:.3f}")


def main():
    parser = argparse.ArgumentParser(
        description="ManuScript 评测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m evaluation.cli run --versions v0_1,v0_2          # 运行评测
  python -m evaluation.cli run --versions v0_1 --llm-judge   # 启用 LLM-as-Judge
  python -m evaluation.cli compare --versions v0_1,v0_2      # 对比版本
  python -m evaluation.cli quick-test --version v0_1         # 快速测试
  python -m evaluation.cli test-langfuse                     # 测试 Langfuse 连接
  python -m evaluation.cli test-judge                        # 测试 LLM-as-Judge
"""
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # run 命令
    run_parser = subparsers.add_parser("run", help="运行评测")
    run_parser.add_argument(
        "--versions", "-v",
        default="v0_1",
        help="要评测的版本，逗号分隔 (默认: v0_1)"
    )
    run_parser.add_argument(
        "--use-llm",
        action="store_true",
        help="使用 LLM 评估文本质量"
    )
    run_parser.add_argument(
        "--llm-judge",
        action="store_true",
        help="使用 LLM-as-Judge 评估引用准确性（检测引用幻觉）"
    )
    run_parser.set_defaults(func=cmd_run)

    # compare 命令
    compare_parser = subparsers.add_parser("compare", help="对比版本")
    compare_parser.add_argument(
        "--versions", "-v",
        default="v0_1,v0_2",
        help="要对比的版本，逗号分隔 (默认: v0_1,v0_2)"
    )
    compare_parser.set_defaults(func=cmd_compare)

    # quick-test 命令
    quick_parser = subparsers.add_parser("quick-test", help="快速测试")
    quick_parser.add_argument(
        "--version", "-v",
        default="v0_1",
        help="要测试的版本 (默认: v0_1)"
    )
    quick_parser.add_argument(
        "--llm-judge",
        action="store_true",
        help="使用 LLM-as-Judge 评估引用准确性"
    )
    quick_parser.set_defaults(func=cmd_quick_test)

    # list-cases 命令
    list_parser = subparsers.add_parser("list-cases", help="列出测试用例")
    list_parser.set_defaults(func=cmd_list_cases)

    # test-langfuse 命令
    langfuse_parser = subparsers.add_parser("test-langfuse", help="测试 Langfuse 连接")
    langfuse_parser.set_defaults(func=cmd_test_langfuse)

    # test-judge 命令
    judge_parser = subparsers.add_parser("test-judge", help="测试 LLM-as-Judge")
    judge_parser.set_defaults(func=cmd_test_judge)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
