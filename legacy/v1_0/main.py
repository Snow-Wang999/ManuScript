"""
ManuScript v1.0 Gradio UI

三栏布局:
- 左栏: 输入（论文主题、章节大纲）
- 中栏: 过程（Agent 执行状态）
- 右栏: 输出（生成的草稿、引用列表）
"""
import json
import asyncio
import gradio as gr

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from workflow import ManuScriptWorkflow
from config import config
from logger import get_logger

logger = get_logger("UI")


EXAMPLE_OUTLINE = """{
    "paper_topic": "深度学习在医学影像诊断中的应用",
    "sections": [
        {
            "title": "引言",
            "section_type": "introduction",
            "keywords": ["深度学习", "医学影像", "诊断"],
            "word_limit": 300
        },
        {
            "title": "卷积神经网络在CT图像分析中的应用",
            "section_type": "body",
            "keywords": ["CNN", "CT", "图像分割", "病变检测"],
            "word_limit": 500
        },
        {
            "title": "结论与展望",
            "section_type": "conclusion",
            "keywords": ["未来方向", "挑战", "临床应用"],
            "word_limit": 200
        }
    ]
}"""


workflow = ManuScriptWorkflow()


def validate_outline(outline_json: str) -> tuple:
    """验证大纲 JSON 格式"""
    try:
        data = json.loads(outline_json)

        if "paper_topic" not in data:
            return False, "缺少 paper_topic 字段"
        if "sections" not in data:
            return False, "缺少 sections 字段"
        if not isinstance(data["sections"], list):
            return False, "sections 必须是数组"
        if len(data["sections"]) == 0:
            return False, "sections 不能为空"

        for i, section in enumerate(data["sections"]):
            if "title" not in section:
                return False, f"第 {i+1} 个章节缺少 title"

        return True, data

    except json.JSONDecodeError as e:
        return False, f"JSON 格式错误: {e}"


async def generate_paper_async(outline_json: str, dataset_ids: str, progress_callback):
    """异步生成论文"""
    valid, result = validate_outline(outline_json)
    if not valid:
        return f"错误: {result}", "", ""

    data = result

    ids = [id.strip() for id in dataset_ids.split(",") if id.strip()]

    progress_callback("开始生成...\n")
    progress_callback(f"论文主题: {data['paper_topic']}\n")
    progress_callback(f"章节数: {len(data['sections'])}\n\n")

    progress_callback("▶ Planner Agent 分析大纲...\n")

    output = await workflow.run(
        paper_topic=data["paper_topic"],
        sections=data["sections"],
        dataset_ids=ids
    )

    if not output["success"]:
        progress_callback(f"✗ 生成失败: {output['error']}\n")
        progress_callback(f"  失败步骤: {output.get('step', 'unknown')}\n")
        return "生成失败", output["error"], ""

    progress_callback("✓ 所有 Agent 执行完成\n\n")

    draft_text = ""
    for draft in output["drafts"]:
        draft_text += f"## {draft['section_title']}\n\n"
        draft_text += draft["content"]
        draft_text += "\n\n"

    citation_text = "## 引用列表\n\n"
    for c in output["citations"]:
        citation_text += f"{c['citation_id']} {c['document_name']}\n"

    verification = output["verification"]
    citation_text += f"\n## 验证结果\n\n"
    citation_text += f"- 整体准确率: {verification['overall_accuracy']:.1f}/10\n"
    citation_text += f"- 有效引用: {verification['valid_citations']}/{verification['total_citations']}\n"
    citation_text += f"- 需要修订: {'是' if verification['needs_revision'] else '否'}\n"

    return f"生成完成! 总字数: {output['total_words']}", draft_text, citation_text


def generate_paper(outline_json: str, dataset_ids: str):
    """同步包装器"""
    progress_log = []

    def progress_callback(msg):
        progress_log.append(msg)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        status, draft, citations = loop.run_until_complete(
            generate_paper_async(outline_json, dataset_ids, progress_callback)
        )
    finally:
        loop.close()

    progress_text = "".join(progress_log)

    return status, progress_text, draft, citations


def create_ui():
    """创建 Gradio UI"""
    with gr.Blocks(
        title="ManuScript v1.0",
        theme=gr.themes.Soft()
    ) as app:
        gr.Markdown("# ManuScript v1.0 - Chain-of-Agents 论文生成")
        gr.Markdown("输入论文大纲，AI 将自动检索文献并生成带引用的草稿")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 输入")

                outline_input = gr.Textbox(
                    label="论文大纲 (JSON)",
                    placeholder="输入 JSON 格式的大纲...",
                    value=EXAMPLE_OUTLINE,
                    lines=20
                )

                dataset_input = gr.Textbox(
                    label="数据集 ID (可选，逗号分隔)",
                    placeholder="dataset_id_1, dataset_id_2",
                    lines=1
                )

                generate_btn = gr.Button(
                    "生成论文",
                    variant="primary",
                    size="lg"
                )

                status_output = gr.Textbox(
                    label="状态",
                    lines=1,
                    interactive=False
                )

            with gr.Column(scale=1):
                gr.Markdown("### 执行过程")

                progress_output = gr.Textbox(
                    label="Agent 执行日志",
                    lines=25,
                    interactive=False
                )

            with gr.Column(scale=1):
                gr.Markdown("### 输出")

                draft_output = gr.Markdown(
                    label="生成的草稿",
                    value="*等待生成...*"
                )

                citation_output = gr.Markdown(
                    label="引用列表",
                    value=""
                )

        generate_btn.click(
            fn=generate_paper,
            inputs=[outline_input, dataset_input],
            outputs=[status_output, progress_output, draft_output, citation_output]
        )

        gr.Markdown("---")
        gr.Markdown("""
        ### 使用说明
        1. 在左侧输入 JSON 格式的论文大纲
        2. (可选) 输入 RAGFlow 数据集 ID
        3. 点击"生成论文"按钮
        4. 在中间查看 Agent 执行过程
        5. 在右侧查看生成结果

        ### JSON 大纲格式
        ```json
        {
            "paper_topic": "论文主题",
            "sections": [
                {
                    "title": "章节标题",
                    "section_type": "introduction/body/conclusion",
                    "keywords": ["关键词1", "关键词2"],
                    "word_limit": 300
                }
            ]
        }
        ```
        """)

    return app


if __name__ == "__main__":
    missing = config.validate()
    if missing:
        print(f"警告: 缺少配置项: {missing}")
        print("请在项目根目录创建 .env 文件")

    app = create_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7862,
        share=False
    )
