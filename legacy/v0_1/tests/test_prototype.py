"""
ManuScript v0.1 测试
"""
import pytest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config
from prototype import format_context


class TestConfig:
    """配置测试"""

    def test_config_exists(self):
        """测试配置类存在"""
        assert config is not None

    def test_validate_returns_list(self):
        """测试 validate 返回列表"""
        result = config.validate()
        assert isinstance(result, list)


class TestFormatContext:
    """format_context 函数测试"""

    def test_empty_chunks(self):
        """测试空 chunks"""
        result = format_context([])
        assert "未检索到" in result

    def test_single_chunk(self):
        """测试单个 chunk"""
        chunks = [{
            "content": "测试内容",
            "document_name": "test.pdf",
            "score": 0.95
        }]
        result = format_context(chunks)
        assert "[1]" in result
        assert "test.pdf" in result
        assert "测试内容" in result

    def test_multiple_chunks(self):
        """测试多个 chunks"""
        chunks = [
            {"content": "内容1", "document_name": "doc1.pdf", "score": 0.9},
            {"content": "内容2", "document_name": "doc2.pdf", "score": 0.8},
        ]
        result = format_context(chunks)
        assert "[1]" in result
        assert "[2]" in result


# 集成测试（需要真实 API）
@pytest.mark.skip(reason="需要配置 API Key")
class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_search_ragflow(self):
        """测试 RAGFlow 检索"""
        from prototype import search_ragflow
        chunks = await search_ragflow("深度学习")
        assert isinstance(chunks, list)

    def test_generate_draft(self):
        """测试生成草稿"""
        from prototype import generate_draft
        draft = generate_draft(
            "测试主题",
            "测试章节",
            "[1] 测试文献内容"
        )
        assert len(draft) > 0
