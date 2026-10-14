from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Optional
import logging
from src.state import State

logger = logging.getLogger(__name__)
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs"


# join results of all workers to a complete blog, and saves it as a markdown file
def reducer(state: State) -> dict:
    logger.info("Called Reducer")
    plan = state.get("plan")
    if plan is None:
        logger.error("Cannot save a blog without a generated plan.")
        raise ValueError("Cannot save a blog without a generated plan.")

    title = plan.blog_title.strip()
    if not title:
        logger.error("Cannot save a blog with an empty title.")
        raise ValueError("Cannot save a blog with an empty title.")

    sections = state.get("sections", [])

    if not sections or any(not section.strip() for _, section in sections):
        logger.error("Cannot save a blog with missing or empty sections.")
        raise ValueError("Cannot save a blog with missing or empty sections.")

    # Sort by task ID, then extract and validate Markdown.
    sorted_sections = sorted(sections, key=lambda item: item[0])

    markdown_sections = [
        markdown.strip()
        for _, markdown in sorted_sections
    ]

    if any(not section for section in markdown_sections):
        logger.error("Cannot save a blog with missing or empty sections.")
        raise ValueError("Cannot save a blog with missing or empty sections.")

    body = "\n\n".join(markdown_sections)
    final_md = f"# {title}\n\n{body}"

    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    if not slug:
        logger.error("Cannot create a Markdown filename from the blog title.")
        raise ValueError("Cannot create a Markdown filename from the blog title.")


    output_path = OUTPUT_DIR / f"{slug}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    temporary_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{slug}_",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(final_md)
            temporary_file.flush()

        temporary_path.replace(output_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    logger.info("Created the markdown file")

    return {"final": final_md}