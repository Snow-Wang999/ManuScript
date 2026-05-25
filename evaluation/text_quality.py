"""
ManuScript 文本质量评估

使用 LLM 或规则评估生成文本的质量
"""
import re
from dataclasses import dataclass
from openai import OpenAI


@dataclass
class TextQualityScore:
    """文本质量评分详情"""
    coherence: float       # 连贯性 (0-1)
    academic_style: float  # 学术风格 (0-1)
    citation_usage: float  # 引用使用 (0-1)
    overall: float         # 综合分数 (0-1)


def evaluate_with_rules(text: str) -> TextQualityScore:
    """
    基于规则评估文本质量（快速，无需 API）

    Args:
        text: 生成的文本

    Returns:
        文本质量评分
    """
    if not text or len(text.strip()) < 10:
        return TextQualityScore(0.0, 0.0, 0.0, 0.0)

    # 1. 连贯性：检查句子数量和平均长度
    sentences = re.split(r'[。！？.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)

    if sentence_count == 0:
        coherence = 0.0
    else:
        avg_length = len(text) / sentence_count
        # 理想句子长度 30-80 字符
        if 30 <= avg_length <= 80:
            coherence = 1.0
        elif avg_length < 30:
            coherence = avg_length / 30
        else:
            coherence = max(0.5, 1 - (avg_length - 80) / 100)

    # 2. 学术风格：检查学术词汇
    academic_words = [
        "研究", "表明", "分析", "方法", "结果", "实验", "数据",
        "提出", "验证", "证明", "模型", "算法", "系统", "框架",
        "显著", "有效", "相关", "基于", "通过", "采用"
    ]
    word_count = sum(1 for word in academic_words if word in text)
    academic_style = min(1.0, word_count / 5)

    # 3. 引用使用：检查引用标记
    citations = re.findall(r'\[\d+\]', text)
    citation_count = len(set(citations))
    # 期望每 200 字符至少 1 个引用
    expected_citations = max(1, len(text) / 200)
    citation_usage = min(1.0, citation_count / expected_citations)

    # 4. 计算综合分数
    overall = (coherence * 0.3 + academic_style * 0.3 + citation_usage * 0.4)

    return TextQualityScore(
        coherence=round(coherence, 3),
        academic_style=round(academic_style, 3),
        citation_usage=round(citation_usage, 3),
        overall=round(overall, 3)
    )


def evaluate_with_llm(
    text: str,
    api_key: str,
    base_url: str | None = None,
    model: str = "gpt-4o-mini"
) -> TextQualityScore:
    """
    使用 LLM 评估文本质量

    Args:
        text: 生成的文本
        api_key: OpenAI API Key
        base_url: API Base URL
        model: 模型名称

    Returns:
        文本质量评分
    """
    if not text or len(text.strip()) < 10:
        return TextQualityScore(0.0, 0.0, 0.0, 0.0)

    client = OpenAI(api_key=api_key, base_url=base_url)

    prompt = f"""请评估以下学术文本的质量，从三个维度打分（0-10分）：

1. 连贯性（coherence）：段落逻辑是否清晰，句子之间是否衔接自然
2. 学术风格（academic_style）：语言是否符合学术写作规范，用词是否准确
3. 引用使用（citation_usage）：引用标记是否恰当，是否有效支撑观点

文本内容：
{text}

请仅返回 JSON 格式的评分结果，例如：
{{"coherence": 7, "academic_style": 8, "citation_usage": 6}}
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )

        result_text = response.choices[0].message.content
        # 提取 JSON
        import json
        match = re.search(r'\{[^}]+\}', result_text)
        if match:
            scores = json.loads(match.group())
            coherence = scores.get("coherence", 5) / 10
            academic_style = scores.get("academic_style", 5) / 10
            citation_usage = scores.get("citation_usage", 5) / 10
            overall = (coherence * 0.3 + academic_style * 0.3 + citation_usage * 0.4)

            return TextQualityScore(
                coherence=round(coherence, 3),
                academic_style=round(academic_style, 3),
                citation_usage=round(citation_usage, 3),
                overall=round(overall, 3)
            )
    except Exception:
        pass

    # 失败时回退到规则评估
    return evaluate_with_rules(text)


def create_evaluator(
    use_llm: bool = False,
    api_key: str | None = None,
    base_url: str | None = None
):
    """
    创建评估函数

    Args:
        use_llm: 是否使用 LLM
        api_key: OpenAI API Key
        base_url: API Base URL

    Returns:
        评估函数 (text: str) -> float
    """
    if use_llm and api_key:
        def evaluator(text: str) -> float:
            score = evaluate_with_llm(text, api_key, base_url)
            return score.overall
        return evaluator
    else:
        def evaluator(text: str) -> float:
            score = evaluate_with_rules(text)
            return score.overall
        return evaluator


if __name__ == "__main__":
    # 测试
    sample_text = """
    深度学习技术在医学图像分析领域取得了显著进展[1]。研究表明，
    卷积神经网络能够有效提取医学图像的特征，实现高精度的病灶检测[2]。
    通过大规模数据训练，这些模型在多种诊断任务中展现出优于传统方法的性能[3]。
    然而，数据标注成本和模型可解释性仍是该领域面临的主要挑战。
    """

    score = evaluate_with_rules(sample_text)
    print(f"规则评估结果:")
    print(f"  连贯性: {score.coherence}")
    print(f"  学术风格: {score.academic_style}")
    print(f"  引用使用: {score.citation_usage}")
    print(f"  综合分数: {score.overall}")
