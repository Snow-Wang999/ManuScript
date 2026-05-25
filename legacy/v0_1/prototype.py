# -*- coding: utf-8 -*-
"""
ManuScript v0.1 Core Prototype Script

Goal: Validate RAGFlow + OpenAI technical feasibility
Run: python prototype.py
"""
import httpx
from openai import OpenAI

from config import config
from logger import get_logger

logger = get_logger(__name__)


async def search_ragflow(query: str, top_k: int = 5) -> list[dict]:
    """
    Call RAGFlow API to search documents

    Args:
        query: Search query
        top_k: Number of results to return

    Returns:
        List of retrieved chunks
    """
    logger.info(f"RAGFlow search: {query}")

    url = f"{config.RAGFLOW_API_BASE}/api/v1/retrieval"
    headers = {
        "Authorization": f"Bearer {config.RAGFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "question": query,
        "dataset_ids": ["32310c0cf44d11f0a204de7d5e8c9111"],
        "top_k": top_k
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectTimeout:
            logger.error("RAGFlow API connection timeout")
            raise Exception("RAGFlow API 连接超时，请检查网络或稍后重试")
        except httpx.HTTPStatusError as e:
            logger.error(f"RAGFlow API error: {e.response.status_code}")
            raise Exception(f"RAGFlow API 错误: {e.response.status_code}")

    chunks = data.get("data", {}).get("chunks", [])
    logger.info(f"Retrieved {len(chunks)} chunks")

    return chunks


def format_context(chunks: list[dict]) -> str:
    """
    Format chunks as LLM context

    Args:
        chunks: Chunks from RAGFlow

    Returns:
        Formatted context string
    """
    if not chunks:
        return "(No relevant documents found)"

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        content = chunk.get("content", "")
        # RAGFlow uses 'document_keyword' for doc name and 'similarity' for score
        doc_name = chunk.get("document_keyword") or chunk.get("document_name", "Unknown source")
        score = chunk.get("similarity") or chunk.get("score", 0)

        context_parts.append(f"[{i}] Source: {doc_name} (relevance: {score:.2f})\n{content}")

    return "\n\n".join(context_parts)


def generate_draft(topic: str, section_title: str, context: str, num_chunks: int = 5) -> str:
    """
    Call OpenAI to generate draft with citations

    Args:
        topic: Paper topic
        section_title: Section title
        context: Retrieved document context
        num_chunks: Number of available chunks for citation

    Returns:
        Generated paragraph text
    """
    logger.info(f"Generating draft: {section_title}")

    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_API_BASE
    )

    prompt = f"""你是一个学术写作助手。请根据以下检索到的文献内容，为论文撰写一个段落。

论文主题：{topic}
章节标题：{section_title}

检索到的文献内容：
{context}

要求：
1. 仅基于提供的文献内容写作，不要编造信息
2. 使用 [1], [2] 等标记引用对应的文献来源，**只能使用 [1] 到 [{num_chunks}] 的编号**，不要使用超出范围的编号
3. 输出语言为中文，专业术语保留英文（如 Deep Research, RAG, LLM 等）
4. 遵循学术写作规范，语言流畅
5. 段落长度约 200-300 字

请撰写："""

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )

    draft = response.choices[0].message.content
    logger.info(f"Generation complete, length: {len(draft)} chars")

    return draft


async def run_prototype(topic: str, section_title: str, use_ragflow: bool = True) -> dict:
    """
    Run complete prototype flow

    Args:
        topic: Paper topic
        section_title: Section title
        use_ragflow: Whether to use RAGFlow for retrieval

    Returns:
        Dict containing chunks and draft
    """
    # 1. Build search query
    query = f"{topic} {section_title}"
    logger.info("=== Start processing ===")
    logger.info(f"Topic: {topic}")
    logger.info(f"Section: {section_title}")

    # 2. Retrieve documents
    if use_ragflow and config.RAGFLOW_API_KEY:
        chunks = await search_ragflow(query)
    else:
        logger.info("Skipping RAGFlow (no API key), using mock data")
        chunks = [
            {
                "content": "Deep learning has revolutionized medical image analysis. CNNs achieve state-of-the-art performance in tasks like tumor detection and organ segmentation.",
                "document_name": "DL_Medical_Review_2023.pdf",
                "score": 0.92
            },
            {
                "content": "Transfer learning from ImageNet pretrained models significantly improves performance on medical imaging tasks with limited labeled data.",
                "document_name": "Transfer_Learning_Medical.pdf",
                "score": 0.87
            }
        ]

    # 3. Format context
    context = format_context(chunks)

    # 4. Generate draft (pass chunk count to limit citation range)
    draft = generate_draft(topic, section_title, context, num_chunks=len(chunks))

    logger.info("=== Processing complete ===")

    return {
        "chunks": chunks,
        "context": context,
        "draft": draft
    }


async def main():
    """Main function"""
    # Validate config (RAGFlow is optional)
    missing = config.validate(require_ragflow=False)
    if missing:
        logger.error(f"Missing required config: {missing}")
        logger.error("Please copy .env.example to .env and fill in API Key")
        return

    # Test case
    topic = "Deep learning in medical image analysis"
    section_title = "Research Background"

    result = await run_prototype(topic, section_title, use_ragflow=True)

    # Print results
    print("\n" + "=" * 60)
    print("Retrieved document chunks (first 3):")
    print("=" * 60)
    for i, chunk in enumerate(result["chunks"][:3], 1):
        doc_name = chunk.get('document_keyword') or chunk.get('document_name', 'Unknown')
        print(f"\n[{i}] {doc_name}")
        print(f"    {chunk.get('content', '')[:200]}...")

    print("\n" + "=" * 60)
    print("Generated draft:")
    print("=" * 60)
    print(result["draft"])


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
