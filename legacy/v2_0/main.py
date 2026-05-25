# -*- coding: utf-8 -*-
"""
ManuScript v2.0 Gradio UI

Three-column interface for Orchestrator-Worker paper generation
"""
import json
import asyncio
import gradio as gr

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from logger import get_logger
from workflow import ManuScriptV2Workflow

logger = get_logger("GradioUI")


EXAMPLE_OUTLINE = {
    "topic": "Deep Learning in Medical Image Diagnosis",
    "sections": [
        {
            "title": "Introduction",
            "section_type": "introduction",
            "keywords": ["deep learning", "medical imaging", "AI diagnosis"],
            "description": "Introduce the research background and motivation",
            "word_limit": 300
        },
        {
            "title": "Background and Related Work",
            "section_type": "background",
            "keywords": ["CNN", "image classification", "medical AI"],
            "description": "Review existing literature and approaches",
            "word_limit": 400
        },
        {
            "title": "Methodology",
            "section_type": "method",
            "keywords": ["U-Net", "segmentation", "architecture"],
            "description": "Describe the proposed deep learning methodology",
            "word_limit": 600
        },
        {
            "title": "Experimental Setup and Results",
            "section_type": "experiment",
            "keywords": ["dataset", "evaluation metrics", "comparison"],
            "description": "Present experimental setup and results",
            "word_limit": 500
        },
        {
            "title": "Discussion",
            "section_type": "discussion",
            "keywords": ["analysis", "limitations", "implications"],
            "description": "Discuss findings and their implications",
            "word_limit": 400
        },
        {
            "title": "Conclusion",
            "section_type": "conclusion",
            "keywords": ["summary", "contributions", "future work"],
            "description": "Summarize contributions and future directions",
            "word_limit": 250
        }
    ],
    "dataset_ids": []
}


def validate_outline(outline_json: str) -> tuple[bool, str, dict]:
    """Validate the outline JSON"""
    try:
        outline = json.loads(outline_json)

        if "topic" not in outline:
            return False, "Missing 'topic' field", {}

        if "sections" not in outline or not outline["sections"]:
            return False, "Missing or empty 'sections' field", {}

        for i, section in enumerate(outline["sections"]):
            if "title" not in section:
                return False, f"Section {i+1} missing 'title'", {}
            if "section_type" not in section:
                return False, f"Section {i+1} missing 'section_type'", {}

        return True, "Valid outline", outline

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}", {}


async def generate_paper(
    outline_json: str,
    parallel: bool,
    progress=gr.Progress()
) -> tuple[str, str, str]:
    """
    Generate paper from outline

    Returns: (process_log, generated_content, citations)
    """
    log_messages = []

    def add_log(message: str):
        log_messages.append(message)
        return "\n".join(log_messages)

    # Validate outline
    add_log("[INFO] Validating outline...")
    valid, message, outline = validate_outline(outline_json)

    if not valid:
        add_log(f"[ERROR] {message}")
        return "\n".join(log_messages), "", ""

    add_log(f"[OK] Valid outline: {outline['topic']}")
    add_log(f"[INFO] Sections: {len(outline['sections'])}")

    # Validate config
    missing = config.validate()
    if missing:
        add_log(f"[ERROR] Missing configuration: {', '.join(missing)}")
        return "\n".join(log_messages), "", ""

    llm_config = config.get_llm_config()
    add_log(f"[INFO] LLM Provider: {llm_config['provider']}")
    add_log(f"[INFO] Model: {llm_config['model']}")

    # Classify sections
    add_log("[INFO] Analyzing section complexity...")
    for section in outline["sections"]:
        complexity = config.get_section_complexity(section["section_type"])
        worker = "SimpleWorker" if complexity == "simple" else "ComplexWorker"
        add_log(f"  - {section['title'][:40]}... -> {worker}")

    # Run workflow
    add_log("")
    add_log("[INFO] Starting generation...")
    add_log(f"[INFO] Parallel processing: {'enabled' if parallel else 'disabled'}")

    workflow = ManuScriptV2Workflow()

    try:
        progress(0.1, desc="Initializing...")

        result = await workflow.run(
            paper_topic=outline["topic"],
            sections=outline["sections"],
            dataset_ids=outline.get("dataset_ids", []),
            parallel=parallel
        )

        progress(0.9, desc="Finalizing...")

        if result["success"]:
            add_log("")
            add_log("[SUCCESS] Generation completed!")
            add_log(f"  - Tasks completed: {result['tasks_completed']}")
            add_log(f"  - Simple sections: {result['simple_sections']}")
            add_log(f"  - Complex sections: {result['complex_sections']}")
            add_log(f"  - Total characters: {result['total_words']}")
            add_log(f"  - Total citations: {len(result['citations'])}")

            # Format generated content
            content_parts = []
            for draft in result["drafts"]:
                content_parts.append(f"## {draft['section_title']}")
                content_parts.append(f"*Generated by {draft['worker_type']} ({draft['word_count']} chars)*")
                content_parts.append("")
                content_parts.append(draft["content"])
                content_parts.append("")

            generated_content = "\n".join(content_parts)

            # Format citations
            citation_parts = ["## References", ""]
            for i, citation in enumerate(result["citations"], 1):
                citation_parts.append(
                    f"{citation['citation_id']} {citation['document_name']}"
                )
                if citation.get("cited_content"):
                    citation_parts.append(f"   > {citation['cited_content'][:100]}...")
                citation_parts.append("")

            citations = "\n".join(citation_parts)

            progress(1.0, desc="Done!")
            return "\n".join(log_messages), generated_content, citations

        else:
            add_log(f"[ERROR] Generation failed: {result.get('error', 'Unknown error')}")
            return "\n".join(log_messages), "", ""

    except Exception as e:
        add_log(f"[ERROR] Exception: {str(e)}")
        logger.exception("Generation failed")
        return "\n".join(log_messages), "", ""


def load_example():
    """Load example outline"""
    return json.dumps(EXAMPLE_OUTLINE, indent=2, ensure_ascii=False)


def create_ui():
    """Create the Gradio interface"""

    with gr.Blocks(
        title="ManuScript v2.0 - Orchestrator-Worker",
        theme=gr.themes.Soft()
    ) as demo:

        gr.Markdown("""
        # ManuScript v2.0 - Orchestrator-Worker Paper Generator

        Dynamic task dispatch with parallel processing for academic paper generation.

        **Features:**
        - 🎯 Automatic section complexity analysis
        - ⚡ Parallel processing with worker pool
        - 📝 SimpleWorker for introduction/conclusion
        - 🔬 ComplexWorker for methods/experiments
        - ✅ ReviewWorker for quality assurance
        """)

        with gr.Row():
            # Left column: Input
            with gr.Column(scale=1):
                gr.Markdown("### 📋 Paper Outline")

                outline_input = gr.Textbox(
                    label="Outline (JSON)",
                    placeholder="Enter your paper outline in JSON format...",
                    lines=20,
                    value=json.dumps(EXAMPLE_OUTLINE, indent=2, ensure_ascii=False)
                )

                with gr.Row():
                    load_btn = gr.Button("📄 Load Example", variant="secondary")
                    parallel_checkbox = gr.Checkbox(
                        label="Parallel Processing",
                        value=True,
                        info="Enable parallel section processing"
                    )

                generate_btn = gr.Button(
                    "🚀 Generate Paper",
                    variant="primary",
                    size="lg"
                )

            # Middle column: Process Log
            with gr.Column(scale=1):
                gr.Markdown("### 📊 Process Log")

                process_log = gr.Textbox(
                    label="Execution Log",
                    lines=25,
                    interactive=False,
                    placeholder="Process log will appear here..."
                )

            # Right column: Output
            with gr.Column(scale=1):
                gr.Markdown("### 📄 Generated Content")

                with gr.Tabs():
                    with gr.TabItem("Content"):
                        content_output = gr.Markdown(
                            label="Generated Paper",
                            value="Generated content will appear here..."
                        )

                    with gr.TabItem("Citations"):
                        citations_output = gr.Markdown(
                            label="References",
                            value="Citations will appear here..."
                        )

        # Event handlers
        load_btn.click(
            fn=load_example,
            outputs=outline_input
        )

        generate_btn.click(
            fn=generate_paper,
            inputs=[outline_input, parallel_checkbox],
            outputs=[process_log, content_output, citations_output]
        )

        gr.Markdown("""
        ---
        **ManuScript v2.0** | Orchestrator-Worker Architecture |
        [GitHub](https://github.com/yourusername/manuscript)
        """)

    return demo


def main():
    """Run the Gradio app"""

    # Validate configuration
    missing = config.validate()
    if missing:
        print(f"Warning: Missing configuration: {', '.join(missing)}")
        print("Some features may not work correctly.")
    else:
        llm_config = config.get_llm_config()
        print(f"LLM Provider: {llm_config['provider']}")
        print(f"Model: {llm_config['model']}")

    print("\nStarting ManuScript v2.0...")
    print("=" * 50)

    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7862,
        share=False
    )


if __name__ == "__main__":
    main()
