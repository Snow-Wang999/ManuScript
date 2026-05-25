"""
ManuScript 版本对比脚本

对比不同版本的评测结果
"""
import yaml
import json
from pathlib import Path
from datetime import datetime

from metrics import EvaluationResult


RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_test_cases() -> list[dict]:
    """加载测试用例"""
    with open(Path(__file__).parent / "test_cases.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("test_cases", [])


def save_results(results: list[EvaluationResult], version: str) -> str:
    """
    保存评测结果

    Args:
        results: 评测结果列表
        version: 版本号

    Returns:
        保存的文件路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{version}_{timestamp}.json"
    filepath = RESULTS_DIR / filename

    data = {
        "version": version,
        "timestamp": timestamp,
        "results": [r.to_dict() for r in results]
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return str(filepath)


def compare_versions(versions: list[str]) -> dict:
    """
    对比多个版本的评测结果

    Args:
        versions: 要对比的版本列表

    Returns:
        对比结果
    """
    comparison = {}

    for version in versions:
        # 查找该版本最新的评测结果
        version_files = list(RESULTS_DIR.glob(f"{version}_*.json"))
        if not version_files:
            comparison[version] = {"error": "未找到评测结果"}
            continue

        latest_file = max(version_files, key=lambda f: f.stat().st_mtime)
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 计算平均得分
        results = data.get("results", [])
        if results:
            avg_score = sum(r["overall_score"] for r in results) / len(results)
            avg_citation = sum(r["citation_accuracy"] for r in results) / len(results)
            avg_latency = sum(r["latency_ms"] for r in results) / len(results)
        else:
            avg_score = avg_citation = avg_latency = 0

        comparison[version] = {
            "avg_overall_score": round(avg_score, 3),
            "avg_citation_accuracy": round(avg_citation, 3),
            "avg_latency_ms": round(avg_latency, 1),
            "test_count": len(results),
            "timestamp": data.get("timestamp")
        }

    return comparison


def print_comparison(comparison: dict) -> None:
    """打印对比结果"""
    print("\n" + "=" * 60)
    print("ManuScript 版本对比")
    print("=" * 60)

    # 表头
    print(f"{'版本':<10} {'综合得分':<12} {'引用准确率':<12} {'平均延迟':<12}")
    print("-" * 60)

    # 数据行
    for version, data in comparison.items():
        if "error" in data:
            print(f"{version:<10} {data['error']}")
        else:
            print(f"{version:<10} {data['avg_overall_score']:<12.3f} {data['avg_citation_accuracy']:<12.3f} {data['avg_latency_ms']:<12.1f}ms")

    print("=" * 60)


if __name__ == "__main__":
    # 示例：对比所有版本
    versions = ["v0_1", "v0_2", "v1_0", "v2_0"]
    comparison = compare_versions(versions)
    print_comparison(comparison)
