"""
ManuScript v1.0 Retrieval Agent

职责: 执行 RAGFlow API 调用进行文献检索
"""
from typing import List, Optional
from pydantic import BaseModel, Field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.query_generator import SearchQuery
from config import config

import httpx


class RetrievalInput(AgentInput):
    """Retrieval Agent 输入"""
    queries: List[SearchQuery] = Field(..., description="检索查询列表")
    dataset_ids: List[str] = Field(default_factory=list, description="数据集ID列表")
    top_k: int = Field(default=10, description="每个查询返回的文档数")


class DocumentChunk(BaseModel):
    """文档片段"""
    chunk_id: str = Field(default="", description="片段ID")
    content: str = Field(..., description="文本内容")
    document_name: str = Field(default="", description="来源文档名")
    score: float = Field(default=0.0, description="相关性分数")
    section_title: str = Field(default="", description="对应章节")
    query_text: str = Field(default="", description="检索查询")


class RetrievalOutput(AgentOutput):
    """Retrieval Agent 输出"""
    chunks: List[DocumentChunk] = Field(default_factory=list)
    total_chunks: int = 0
    queries_executed: int = 0


class RetrievalAgent(BaseAgent):
    """
    Retrieval Agent - 执行文献检索

    输入: 检索查询列表
    输出: 文档片段列表
    """

    @property
    def name(self) -> str:
        return "Retrieval"

    async def run(self, input_data: RetrievalInput) -> RetrievalOutput:
        """执行检索"""
        self.log_start(input_data)

        try:
            all_chunks = []
            queries_executed = 0

            for query in input_data.queries:
                chunks = await self._retrieve(
                    query=query,
                    dataset_ids=input_data.dataset_ids,
                    top_k=input_data.top_k
                )
                all_chunks.extend(chunks)
                queries_executed += 1

            all_chunks = self._deduplicate_chunks(all_chunks)

            output = RetrievalOutput(
                success=True,
                chunks=all_chunks,
                total_chunks=len(all_chunks),
                queries_executed=queries_executed
            )

            self.log_end(output)
            return output

        except Exception as e:
            self.log_error(e)
            return RetrievalOutput(success=False, error=str(e))

    async def _retrieve(
        self,
        query: SearchQuery,
        dataset_ids: List[str],
        top_k: int
    ) -> List[DocumentChunk]:
        """执行单个查询的检索"""

        self.logger.info(f"检索: {query.query_text[:50]}...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{config.RAGFLOW_API_BASE}/api/v1/retrieval",
                headers={
                    "Authorization": f"Bearer {config.RAGFLOW_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "question": query.query_text,
                    "dataset_ids": dataset_ids,
                    "top_k": top_k
                }
            )
            response.raise_for_status()
            result = response.json()

        chunks = []
        raw_chunks = result.get("data", {}).get("chunks", [])

        for i, chunk in enumerate(raw_chunks):
            chunks.append(DocumentChunk(
                chunk_id=chunk.get("id", f"{query.section_title}_{i}"),
                content=chunk.get("content", ""),
                document_name=chunk.get("document_name", "unknown"),
                score=chunk.get("score", 0.0),
                section_title=query.section_title,
                query_text=query.query_text
            ))

        self.logger.info(
            f"查询返回 {len(chunks)} 个片段",
            extra={"section": query.section_title}
        )

        return chunks

    def _deduplicate_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """去重文档片段"""
        seen_content = set()
        unique_chunks = []

        for chunk in chunks:
            content_hash = hash(chunk.content[:200])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_chunks.append(chunk)

        if len(chunks) != len(unique_chunks):
            self.logger.info(
                f"去重: {len(chunks)} -> {len(unique_chunks)} 个片段"
            )

        return unique_chunks


async def test_retrieval():
    """测试 Retrieval Agent"""
    from agents.query_generator import SearchQuery

    agent = RetrievalAgent()

    test_input = RetrievalInput(
        queries=[
            SearchQuery(
                section_title="引言",
                query_text="deep learning medical image diagnosis survey",
                query_type="semantic",
                priority=1
            ),
            SearchQuery(
                section_title="方法",
                query_text="convolutional neural network CT image segmentation",
                query_type="semantic",
                priority=1
            )
        ],
        dataset_ids=[],
        top_k=5
    )

    print("=" * 60)
    print("测试 Retrieval Agent")
    print("=" * 60)
    print(f"查询数量: {len(test_input.queries)}")
    print(f"每查询 top_k: {test_input.top_k}")
    print()

    output = await agent.run(test_input)

    if output.success:
        print(f"检索成功!")
        print(f"执行查询数: {output.queries_executed}")
        print(f"总片段数: {output.total_chunks}")
        print()
        for chunk in output.chunks[:5]:
            print(f"[{chunk.section_title}] {chunk.document_name}")
            print(f"  Score: {chunk.score:.3f}")
            print(f"  Content: {chunk.content[:100]}...")
            print()
    else:
        print(f"检索失败: {output.error}")

    return output


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_retrieval())
