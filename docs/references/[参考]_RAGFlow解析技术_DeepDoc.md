根据我对ragflow deepdoc代码的详细分析，现在可以给你一个完整的总结：

  RAGFlow DeepDoc 文档解析技术分析
  项目位置
  RAGFlow项目位于：D:\HandDeepResearch_AI\ragflow

  # DeepDoc 核心架构

  DeepDoc主要采用传统的深度学习视觉方法来解析文档，同时也支持可选的多模态大模型增强。

  ---
  ## 1. 传统方法（默认/核心）

  ### OCR（光学字符识别）

  - 文件：deepdoc/vision/ocr.py
  - 使用 ONNX Runtime 加载预训练模型进行文字检测和识别
  - 模型来自 HuggingFace: InfiniFlow/deepdoc

  ### 布局识别（Layout Recognition）

  - 文件：deepdoc/vision/layout_recognizer.py
  - 使用 ONNX 模型 或 华为昇腾（Ascend）模型 进行布局检测
  - 识别10种布局元素：
    - Text（文本）
    - Title（标题）
    - Figure（图片）
    - Figure caption（图片说明）
    - Table（表格）
    - Table caption（表格说明）
    - Header（页眉）
    - Footer（页脚）
    - Reference（参考文献）
    - Equation（公式）

  ### 表格结构识别（TSR）

  - 文件：deepdoc/vision/table_structure_recognizer.py
  - 使用传统深度学习模型识别表格结构
  - 识别5种表格元素：Column、Row、Column header、Projected row header、Spanning cell

  ### 文本合并决策

  - 使用 XGBoost 模型 (updown_concat_xgb.model) 判断上下文本块是否应该合并

  ---
  ## 2. 多模态大模型支持（可选增强）

  ### VisionParser（视觉解析器）

  - 文件：deepdoc/parser/pdf_parser.py 第1448-1500行
  - 继承自 RAGFlowPdfParser
  - 使用多模态大模型（IMAGE2TEXT类型）对每页PDF进行描述
  - 调用 picture_vision_llm_chunk 函数处理

  ### VisionFigureParser（图片增强解析）

  - 文件：deepdoc/parser/figure_parser.py
  - 使用多模态大模型增强图片描述
  - 支持上下文感知的图片描述生成
  - 可用于PDF、DOCX、Excel中的图片解析

  ### MinerU 集成

  - 文件：deepdoc/parser/mineru_parser.py
  - 支持多种后端：
    - pipeline：传统多模型管道（默认）
    - vlm-transformers：使用HuggingFace Transformers的视觉语言模型
    - vlm-vllm-engine：本地vLLM引擎
    - vlm-http-client：远程vLLM服务器

  ---
  ## 3. 技术总结
  ```txt
  ┌──────────────┬──────────────────┬───────────────────┐
  │     功能     │     默认方法      │     可选增强       │
  ├──────────────┼──────────────────┼───────────────────┤
  │ OCR          │ ONNX深度学习模型  │ -                 │
  ├──────────────┼──────────────────┼───────────────────┤
  │ 布局识别      │ ONNX/Ascend模型  │ -                 │
  ├──────────────┼──────────────────┼───────────────────┤
  │ 表格结构识别  │ 深度学习模型      │ -                 │
  ├──────────────┼──────────────────┼───────────────────┤
  │ 文本合并      │ XGBoost模型      │ -                 │
  ├──────────────┼──────────────────┼───────────────────┤
  │ 图片描述      │ 提取caption文本  │  多模态LLM描述     │
  ├──────────────┼──────────────────┼───────────────────┤
  │ 整页解析      │ 传统OCR+布局     │ VisionParser(LLM) │
  └──────────────┴──────────────────┴───────────────────┘
  ```
  # 结论

  RAGFlow的DeepDoc 默认使用传统的深度学习视觉方法（OCR、布局识别、表格结构识别），这些都是基于ONNX的预训练模型。但它也提
  供了可选的多模态大模型增强功能，用户可以配置使用视觉语言模型来：
  1. 增强图片/图表的描述
  2. 使用VisionParser进行整页PDF解析
  3. 通过MinerU集成使用VLM后端

  这种设计使得系统既能高效处理大量文档（传统方法速度快、成本低），又能在需要时利用多模态大模型获得更好的语义理解。

  # Sources:
  - https://github.com/infiniflow/ragflow
  - https://ragflow.io/docs/dev/faq
  - https://llms.reducto.ai/best-llm-ready-document-parsers-2025

✶ Crunching… (Esc to interrupt · 2m 27s · ↓ 922 tokens)                                                             ✻ Worked for 2m 28s