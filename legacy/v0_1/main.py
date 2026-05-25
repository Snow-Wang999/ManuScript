# -*- coding: utf-8 -*-
"""
ManuScript v0.1 Gradio UI

Run: python main.py
"""
import asyncio
import gradio as gr

from config import config
from logger import get_logger
from prototype import run_prototype

logger = get_logger(__name__)


async def generate(topic: str, section_title: str, keywords: str) -> str:
    """
    Gradio callback function

    Args:
        topic: Paper topic
        section_title: Section title
        keywords: Keywords (optional, not used yet)

    Returns:
        Generated draft text
    """
    # Validate input
    if not topic.strip():
        return "Please enter paper topic"
    if not section_title.strip():
        return "Please enter section title"

    # Validate config (RAGFlow is optional)
    missing = config.validate(require_ragflow=False)
    if missing:
        return f"Config error: missing {', '.join(missing)}, please check .env file"

    try:
        # Skip RAGFlow for now, use mock data
        result = await run_prototype(topic.strip(), section_title.strip(), use_ragflow=True)
        draft = result["draft"]
        chunks = result["chunks"]

        # Parse citation numbers from generated text
        import re
        cited_nums = set(int(m) for m in re.findall(r'\[(\d+)\]', draft))

        # Format output
        output_parts = [
            "## Generated Draft\n\n",
            draft,
            "\n\n---\n\n",
            "## References\n\n"
        ]

        # Only show cited chunks with content summary
        for num in sorted(cited_nums):
            if 1 <= num <= len(chunks):
                chunk = chunks[num - 1]
                doc_name = chunk.get("document_keyword") or chunk.get("document_name", "Unknown source")
                content = chunk.get("content", "")
                # Truncate content to ~100 chars for summary
                summary = content[:100].replace("\n", " ").strip()
                if len(content) > 100:
                    summary += "..."
                output_parts.append(f"[{num}] {doc_name}\n\n> {summary}\n\n")

        # Show unique documents summary with numbered list
        unique_docs = list(set(
            chunks[num - 1].get("document_keyword") or chunks[num - 1].get("document_name", "Unknown")
            for num in cited_nums if 1 <= num <= len(chunks)
        ))
        output_parts.append(f"**来源文档 ({len(unique_docs)} 篇)**:\n\n")
        for i, doc in enumerate(unique_docs, 1):
            output_parts.append(f"{i}. {doc}\n")

        return "".join(output_parts)

    except Exception as e:
        logger.exception("Generation failed")
        return f"Generation failed: {str(e)}"


def create_ui() -> gr.Blocks:
    """Create Gradio UI"""

    with gr.Blocks(title="ManuScript v0.1") as demo:
        gr.Markdown("# ManuScript v0.1 - Minimal Prototype")
        gr.Markdown("Generate academic paragraphs with citations based on document retrieval")

        with gr.Row():
            with gr.Column():
                topic_input = gr.Textbox(
                    label="Paper Topic",
                    placeholder="e.g., Deep learning in medical image analysis",
                    lines=1
                )
                section_input = gr.Textbox(
                    label="Section Title",
                    placeholder="e.g., Research Background",
                    lines=1
                )
                keywords_input = gr.Textbox(
                    label="Keywords (optional)",
                    placeholder="e.g., CNN, image segmentation, pathology diagnosis",
                    lines=1
                )
                generate_btn = gr.Button("Generate", variant="primary")

        output = gr.Markdown(label="Output")

        generate_btn.click(
            fn=generate,
            inputs=[topic_input, section_input, keywords_input],
            outputs=output
        )

    return demo


def main():
    """Main function"""
    logger.info("Starting ManuScript v0.1 Gradio UI")

    demo = create_ui()
    demo.launch(
        server_name="127.0.0.1",
        share=False
    )


if __name__ == "__main__":
    main()
