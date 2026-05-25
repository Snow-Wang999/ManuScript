现在我已经深入分析了 RAGFlow 的检索系统。让我为你总结 RAGFlow 检索技术和优化参数。

# RAGFlow 检索技术深度分析
## 一、你的 ManuScript v0.1 当前实现
你的 prototype.py 使用了最简单的检索方式：


### 当前实现 (v0_1/prototype.py:30-39)
```python
payload = {
    "question": query,
    "dataset_ids": ["32310c0cf44d11f0a204de7d5e8c9111"],
    "top_k": top_k  # 默认 5
}
```
这只使用了基础参数，还有很多高级参数可以优化。

## 二、RAGFlow 检索核心技术
### 1. 混合检索 (Hybrid Search)
从 search.py:127 看到：

```python
fusionExpr = FusionExpr("weighted_sum", topk, {"weights": "0.05,0.95"})
# 5% 全文检索 + 95% 向量检索
matchExprs = [matchText, matchDense, fusionExpr]
```

### 2. 查询字段权重
从 query.py:31-38：

```python
self.query_fields = [
    "title_tks^10",        # 标题权重 10x
    "title_sm_tks^5",      
    "important_kwd^30",    # 重要关键词权重 30x
    "important_tks^20",    
    "question_tks^20",     # 问题匹配权重 20x
    "content_ltks^2",      # 内容权重 2x
    "content_sm_ltks",
]
```
### 3. 重排序 (Rerank)
从 search.py:404-412：

- 支持多种 Rerank 模型（Jina, Cohere, BAAI/bge-reranker 等）
- 结合 token 相似度 + 向量相似度

## 三、关键可调参数（按重要性排序）

| 参数 | 默认值 | 作用 | 优化建议 |
|------|-------|------|---------|
| similarity_threshold | 0.2 | 相似度阈值，过滤低相关结果 | 论文检索建议 0.3-0.5，提高精度 |
| vector_similarity_weight | 0.3 | 向量/关键词权重比 | 学术检索建议 0.5-0.7，偏向语义 |
| top_k | 1024 | 初始检索数量 | 保持默认或增大 |
| top_n | 8 | 最终返回数量 | 根据需要调整，10-20 |
| rerank_id | 无 | 重排序模型 | 强烈建议启用，如 gte-rerank |
| chunk_token_num | 512 | 分块大小 | 学术论文建议 1024-2048 |

## 四、优化你的 ManuScript 检索
### 方案 1：增强 API 调用参数
修改 prototype.py 的检索请求：

```python
payload = {
    "question": query,
    "dataset_ids": ["32310c0cf44d11f0a204de7d5e8c9111"],
    "top_k": 20,  # 增加返回数量
    # 以下参数需要确认你的 RAGFlow 版本是否支持
    "similarity_threshold": 0.3,  # 提高阈值，过滤噪音
    "vector_similarity_weight": 0.5,  # 平衡语义和关键词
}
```
### 方案 2：在 RAGFlow 配置知识库时优化
在创建/编辑知识库时设置：

| 设置项 | 建议值 | 原因 |
|--------|-------|------|
| Chunk Token Size | 1024-2048 | 学术论文段落较长 |
| Parsing Method | "Paper" 或 "Book" | 针对论文格式优化 |
| Enable Rerank | ✅ 开启 | 二次排序提升精度 |
| Embedding Model | bge-large / gte-large | 中文建议用 bge |


### 方案 3：v0.2 中实现多查询策略
参考你的 current_task_v0_2.md，Query Generator 可以：

```python
# 一个章节生成多个检索词
queries = [
    "deep learning medical image analysis",  # 原始
    "CNN tumor detection segmentation",      # 同义扩展
    "transfer learning radiology",           # 相关概念
]
```

# 合并多次检索结果
## 五、RAGFlow 检索流程图
```txt
            用户查询
                ↓
┌───────────────────────────────┐
│  Query Processing (query.py)  │
│  - 分词 + 权重计算             │
│  - 同义词扩展                  │
│  - 字段权重 (title^10)        │
└───────────────┬───────────────┘
                ↓
        ┌───────┴───────┐
        ↓               ↓
┌─────────────┐  ┌─────────────┐
│  全文检索    │  │  向量检索    │
│  (BM25)     │  │  (cosine)   │
└──────┬──────┘  └──────┬──────┘
       └───────┬────────┘
               ↓
┌───────────────────────────────┐
│  Fusion (weighted_sum)        │
│  weights: "0.05,0.95"         │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│  Rerank (可选)                │
│  - bge-reranker / gte-rerank  │
│  - token_sim * 0.3 +          │
│    vector_sim * 0.7           │
└───────────────┬───────────────┘
                ↓
        返回 Top-N Chunks
```
## 六、快速提升效果的 3 个建议

- 启用 Rerank 模型

    - 在 RAGFlow 控制台配置 Rerank 模型（推荐 gte-rerank 或 bge-reranker-v2-m3）

- 调整 Chunk 大小

    - 学术论文建议 1024-2048 tokens，避免切断完整论述

- 增加 similarity_threshold

    - 从默认 0.2 提高到 0.3-0.4，过滤低相关结果

需要我帮你修改 v0_1 代码来添加这些优化参数吗？