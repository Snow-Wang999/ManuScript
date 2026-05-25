# -*- coding: utf-8 -*-
"""
ManuScript v0.2 Pipeline

完整的 2 步 Prompt Chain 流程编排
数据流: 大纲 -> Query生成 -> RAG检索 -> Step1筛选 -> Step2生成 -> 格式化输出
"""
import httpx
from openai import OpenAI

from config import config
from logger import get_logger
from query_generator import Outline, Section, generate_queries
from citation_formatter import CitationFormatter

logger = get_logger(__name__)


# ============== RAGFlow 检索 ==============

async def search_ragflow(query: str, top_k: int = None) -> list[dict]:
    """
    调用 RAGFlow API 检索文献

    Args:
        query: 检索查询
        top_k: 返回结果数量

    Returns:
        检索到的 chunks 列表
    """
    if top_k is None:
        top_k = config.TOP_K_CHUNKS

    logger.info(f"RAGFlow 检索: {query}")

    url = f"{config.RAGFLOW_API_BASE}/api/v1/retrieval"
    headers = {
        "Authorization": f"Bearer {config.RAGFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "question": query,
        "top_k": top_k
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    chunks = data.get("data", {}).get("chunks", [])
    logger.info(f"检索到 {len(chunks)} 个 chunks")

    return chunks


async def batch_search(queries: list[str]) -> list[dict]:
    """
    批量检索并去重合并

    Args:
        queries: 查询列表

    Returns:
        去重后的 chunks 列表
    """
    all_chunks = []
    seen_contents = set()

    for query in queries:
        chunks = await search_ragflow(query)
        for chunk in chunks:
            content = chunk.get("content", "")
            # 简单去重：基于内容前100字符
            content_key = content[:100]
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                all_chunks.append(chunk)

    logger.info(f"批量检索完成，共 {len(all_chunks)} 个去重 chunks")
    return all_chunks


# ============== OpenAI 调用 ==============

def call_openai(prompt: str, temperature: float = 0.7) -> str:
    """
    调用 OpenAI API

    Args:
        prompt: 提示词
        temperature: 温度参数

    Returns:
        生成的文本
    """
    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_API_BASE
    )

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=2000
    )

    return response.choices[0].message.content


# ============== 2 步 Prompt Chain ==============

def format_chunks_for_prompt(chunks: list[dict]) -> str:
    """将 chunks 格式化为 prompt 可用的字符串"""
    if not chunks:
        return "(No relevant documents retrieved)"

    parts = []
    for i, chunk in enumerate(chunks, 1):
        content = chunk.get("content", "")
        doc_name = chunk.get("document_name", "Unknown")
        score = chunk.get("score", 0)
        parts.append(f"[{i}] Source: {doc_name} (relevance: {score:.2f})\n{content}")

    return "\n\n".join(parts)


def step1_filter_chunks(
    topic: str,
    section_title: str,
    chunks: list[dict]
) -> list[dict]:
    """
    Step 1: 筛选相关 chunks

    Args:
        topic: 论文主题
        section_title: 章节标题
        chunks: 检索到的 chunks

    Returns:
        筛选后的相关 chunks
    """
    logger.info(f"Step 1: 筛选相关 chunks")

    if not chunks:
        return []

    # 格式化 chunks
    chunks_text = format_chunks_for_prompt(chunks)

    prompt = f"""你是一位学术文献筛选专家。请根据论文主题和章节标题，从以下检索到的文献片段中筛选出最相关的内容。

论文主题：{topic}
章节标题：{section_title}

检索到的文献片段：
{chunks_text}

请分析每个文献片段与论文主题和章节的相关性，返回相关文献的编号列表。
只返回编号，用逗号分隔，例如: 1,3,5
如果都不相关，返回: 无

相关文献编号："""

    response = call_openai(prompt, temperature=0.3)
    logger.debug(f"Step 1 响应: {response}")

    # 解析响应
    if "无" in response or not response.strip():
        logger.info("Step 1: 没有相关文献")
        return []

    try:
        # 提取数字
        import re
        numbers = re.findall(r'\d+', response)
        indices = [int(n) for n in numbers]

        # 筛选 chunks（索引从1开始）
        filtered = [chunks[i-1] for i in indices if 0 < i <= len(chunks)]
        logger.info(f"Step 1: 筛选出 {len(filtered)} 个相关 chunks")
        return filtered

    except Exception as e:
        logger.warning(f"Step 1 解析失败: {e}，使用原始 chunks")
        return chunks[:5]  # 回退：返回前5个


def step2_generate_draft(
    topic: str,
    section_title: str,
    chunks: list[dict]
) -> str:
    """
    Step 2: 基于筛选后的 chunks 生成带引用的段落

    Args:
        topic: 论文主题
        section_title: 章节标题
        chunks: 筛选后的 chunks

    Returns:
        生成的段落文本
    """
    logger.info(f"Step 2: 生成带引用的段落")

    if not chunks:
        return f"(No relevant documents found for section: {section_title})"

    # 格式化 chunks
    chunks_text = format_chunks_for_prompt(chunks)

    prompt = f"""你是一位学术写作助手。请根据以下筛选后的相关文献内容，为论文撰写一个段落。

论文主题：{topic}
章节标题：{section_title}

相关文献内容：
{chunks_text}

写作要求：
1. 严格基于提供的文献内容撰写，不要编造信息
2. 使用 [1], [2] 等标记引用对应的文献来源
3. 每个重要观点都必须有引用支持
4. 语言流畅，符合学术写作规范
5. 段落长度约 200-400 字

请撰写段落："""

    draft = call_openai(prompt, temperature=0.7)
    logger.info(f"Step 2: 生成完成，长度 {len(draft)} 字符")

    return draft


# ============== 完整流程 ==============

async def process_section(
    outline: Outline,
    section_index: int
) -> dict:
    """
    处理单个章节

    Args:
        outline: 论文大纲
        section_index: 章节索引

    Returns:
        处理结果
    """
    section = outline.sections[section_index]
    logger.info(f"=== 处理章节 {section_index + 1}: {section.title} ===")

    # 1. 生成查询
    queries = generate_queries(outline, section_index)

    # 2. 批量检索
    all_chunks = await batch_search(queries)

    # 3. Step 1: 筛选相关 chunks
    filtered_chunks = step1_filter_chunks(
        outline.topic,
        section.title,
        all_chunks
    )

    # 4. Step 2: 生成草稿
    draft = step2_generate_draft(
        outline.topic,
        section.title,
        filtered_chunks
    )

    # 5. 格式化引用
    formatter = CitationFormatter()
    formatter.extract_citations_from_chunks(filtered_chunks)
    validation = formatter.validate_citations_in_text(draft)

    return {
        "section_index": section_index,
        "section_title": section.title,
        "queries": queries,
        "raw_chunks_count": len(all_chunks),
        "filtered_chunks_count": len(filtered_chunks),
        "filtered_chunks": filtered_chunks,
        "draft": draft,
        "citation_validation": validation,
        "formatted_output": formatter.format_output(draft)
    }


async def process_outline(outline: Outline) -> dict:
    """
    处理完整大纲

    Args:
        outline: 论文大纲

    Returns:
        所有章节的处理结果
    """
    logger.info(f"开始处理大纲: {outline.topic}")
    logger.info(f"共 {len(outline.sections)} 个章节")

    results = []
    all_chunks = []

    for i in range(len(outline.sections)):
        result = await process_section(outline, i)
        results.append(result)
        all_chunks.extend(result["filtered_chunks"])

    # 生成完整输出
    full_draft = "\n\n".join([
        f"## {r['section_title']}\n\n{r['draft']}"
        for r in results
    ])

    # 整体引用列表（去重）
    seen_docs = set()
    unique_chunks = []
    for chunk in all_chunks:
        doc = chunk.get("document_name", "")
        if doc not in seen_docs:
            seen_docs.add(doc)
            unique_chunks.append(chunk)

    formatter = CitationFormatter()
    formatter.extract_citations_from_chunks(unique_chunks)

    logger.info(f"大纲处理完成")

    return {
        "topic": outline.topic,
        "section_results": results,
        "full_draft": full_draft,
        "reference_list": formatter.generate_reference_list(),
        "total_references": len(unique_chunks)
    }


# ============== 测试入口 ==============

async def main():
    """测试主函数"""
    # 验证配置
    missing = config.validate()
    if missing:
        logger.error(f"缺少必需的配置项: {missing}")
        return

    # 测试大纲
    outline = Outline(
        topic="深度学习在医学图像分析中的应用",
        sections=[
            Section(
                title="研究背景",
                description="医学图像分析的重要性和挑战",
                keywords=["医学图像", "深度学习"],
                section_type="background"
            ),
            Section(
                title="相关工作",
                description="现有的医学图像分析方法",
                keywords=["卷积神经网络", "图像分割"],
                section_type="related_work"
            ),
        ]
    )

    result = await process_outline(outline)

    # 打印结果
    print("\n" + "=" * 60)
    print("生成的论文草稿")
    print("=" * 60)
    print(result["full_draft"])
    print(result["reference_list"])


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
