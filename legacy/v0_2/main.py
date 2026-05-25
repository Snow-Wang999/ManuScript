# -*- coding: utf-8 -*-
"""
ManuScript v0.2 Gradio UI

支持 JSON 格式大纲输入
运行：python main.py
"""
import asyncio
import json
import gradio as gr

from config import config
from logger import get_logger
from query_generator import Outline, Section
from pipeline import process_outline, process_section

logger = get_logger(__name__)

# 示例大纲 JSON
EXAMPLE_OUTLINE = """{
    "topic": "深度学习在医学图像分析中的应用",
    "sections": [
        {
            "title": "研究背景",
            "description": "医学图像分析的重要性和挑战",
            "keywords": ["医学图像", "深度学习"],
            "section_type": "background"
        },
        {
            "title": "相关工作",
            "description": "现有的医学图像分析方法综述",
            "keywords": ["卷积神经网络", "图像分割", "目标检测"],
            "section_type": "related_work"
        },
        {
            "title": "研究方法",
            "description": "本文提出的方法",
            "keywords": ["网络架构", "训练策略"],
            "section_type": "method"
        }
    ]
}"""


def parse_outline(outline_json: str) -> Outline:
    """
    解析 JSON 格式的大纲

    Args:
        outline_json: JSON 字符串

    Returns:
        Outline 对象
    """
    data = json.loads(outline_json)

    sections = []
    for s in data.get("sections", []):
        sections.append(Section(
            title=s.get("title", ""),
            description=s.get("description", ""),
            keywords=s.get("keywords", []),
            section_type=s.get("section_type", "default")
        ))

    return Outline(
        topic=data.get("topic", ""),
        sections=sections
    )


async def generate_full(outline_json: str, progress=gr.Progress()) -> tuple[str, str, str]:
    """
    生成完整论文草稿

    Args:
        outline_json: JSON 格式的大纲
        progress: Gradio 进度条

    Returns:
        (草稿, 引用列表, 日志信息)
    """
    # 验证配置
    missing = config.validate()
    if missing:
        error_msg = f"配置错误：缺少 {', '.join(missing)}，请检查 .env 文件"
        return error_msg, "", error_msg

    # 解析大纲
    try:
        outline = parse_outline(outline_json)
    except json.JSONDecodeError as e:
        error_msg = f"JSON 解析错误：{str(e)}"
        return error_msg, "", error_msg
    except Exception as e:
        error_msg = f"大纲格式错误：{str(e)}"
        return error_msg, "", error_msg

    if not outline.sections:
        return "大纲中没有章节", "", "大纲中没有章节"

    # 处理进度
    log_lines = []
    log_lines.append(f"开始处理: {outline.topic}")
    log_lines.append(f"共 {len(outline.sections)} 个章节")

    try:
        results = []
        total_sections = len(outline.sections)

        for i, section in enumerate(outline.sections):
            progress((i + 0.5) / total_sections, desc=f"处理章节: {section.title}")
            log_lines.append(f"\n--- 处理章节 {i+1}: {section.title} ---")

            result = await process_section(outline, i)
            results.append(result)

            log_lines.append(f"  生成查询: {len(result['queries'])} 个")
            log_lines.append(f"  检索结果: {result['raw_chunks_count']} -> {result['filtered_chunks_count']} chunks")
            log_lines.append(f"  引用验证: {result['citation_validation']}")

            progress((i + 1) / total_sections, desc=f"完成章节: {section.title}")

        # 组装完整草稿
        full_draft_parts = [f"# {outline.topic}\n"]
        for r in results:
            full_draft_parts.append(f"\n## {r['section_title']}\n")
            full_draft_parts.append(r['draft'])

        full_draft = "\n".join(full_draft_parts)

        # 生成引用列表
        all_chunks = []
        seen_docs = set()
        for r in results:
            for chunk in r['filtered_chunks']:
                doc = chunk.get("document_name", "")
                if doc not in seen_docs:
                    seen_docs.add(doc)
                    all_chunks.append(chunk)

        reference_lines = ["\n## 参考文献\n"]
        for i, chunk in enumerate(all_chunks, 1):
            doc_name = chunk.get("document_name", "未知")
            reference_lines.append(f"[{i}] {doc_name}")

        reference_list = "\n".join(reference_lines)

        log_lines.append(f"\n=== 处理完成 ===")
        log_lines.append(f"总引用数: {len(all_chunks)}")

        return full_draft, reference_list, "\n".join(log_lines)

    except Exception as e:
        logger.exception("生成失败")
        error_msg = f"生成失败：{str(e)}"
        log_lines.append(f"\n错误: {error_msg}")
        return error_msg, "", "\n".join(log_lines)


def create_ui() -> gr.Blocks:
    """创建 Gradio UI"""

    with gr.Blocks(title="ManuScript v0.2", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# ManuScript v0.2 - 基础流程")
        gr.Markdown("支持 JSON 大纲输入，2步 Prompt Chain 生成带引用的论文草稿")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 输入大纲")
                outline_input = gr.Code(
                    label="大纲 JSON",
                    language="json",
                    value=EXAMPLE_OUTLINE,
                    lines=20
                )
                generate_btn = gr.Button("生成论文草稿", variant="primary", size="lg")

            with gr.Column(scale=2):
                gr.Markdown("### 生成结果")
                with gr.Tabs():
                    with gr.TabItem("草稿"):
                        draft_output = gr.Markdown(label="生成的草稿")
                    with gr.TabItem("引用列表"):
                        reference_output = gr.Markdown(label="引用列表")
                    with gr.TabItem("处理日志"):
                        log_output = gr.Textbox(label="日志", lines=15, interactive=False)

        # 绑定事件
        generate_btn.click(
            fn=generate_full,
            inputs=[outline_input],
            outputs=[draft_output, reference_output, log_output]
        )

        # 使用说明
        with gr.Accordion("使用说明", open=False):
            gr.Markdown("""
            ### JSON 大纲格式

            ```json
            {
                "topic": "论文主题",
                "sections": [
                    {
                        "title": "章节标题",
                        "description": "章节描述（可选）",
                        "keywords": ["关键词1", "关键词2"],
                        "section_type": "background"  // 可选值见下方
                    }
                ]
            }
            ```

            ### 支持的章节类型 (section_type)

            | 类型 | 说明 | 查询数量 |
            |------|------|---------|
            | introduction | 引言 | 2 |
            | background | 背景 | 3 |
            | related_work | 相关工作 | 3 |
            | method | 方法 | 2 |
            | experiment | 实验 | 2 |
            | result | 结果 | 2 |
            | discussion | 讨论 | 2 |
            | conclusion | 结论 | 1 |
            | default | 默认 | 2 |
            """)

    return demo


def main():
    """主函数"""
    logger.info("启动 ManuScript v0.2 Gradio UI")

    demo = create_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7861,  # 使用不同端口，避免与 v0.1 冲突
        share=False
    )


if __name__ == "__main__":
    main()
