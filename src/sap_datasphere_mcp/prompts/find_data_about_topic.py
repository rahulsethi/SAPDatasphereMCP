# SAP Datasphere MCP Server
# File: prompts/find_data_about_topic.py
# Version: v1 (1.0)

"""Multi-space discovery to surface candidate assets for an analytic question."""

from __future__ import annotations

from typing import List, Optional


PROMPT = {
    "name": "find_data_about_topic",
    "description": "Search across spaces for assets that answer an analytic question about a topic; rank and present the top candidates.",
}


def render(topic: str, space_ids: Optional[List[str]] = None) -> str:
    space_scope = (
        f"limit your search to these spaces: {', '.join(f'`{s}`' for s in space_ids)}"
        if space_ids
        else "search across all spaces visible to the OAuth client"
    )
    return (
        f"A user wants to answer this question: **\"{topic}\"**\n\n"
        f"Find the most useful SAP Datasphere assets that could answer it. Please {space_scope}.\n\n"
        "Steps:\n\n"
        "1. Decompose the topic into 2-4 key search terms (entities, metrics, or column names a Datasphere modeler would have used).\n"
        "2. For each term, call `datasphere_discover_assets` to find matching assets by name/id/description.\n"
        "3. For any column-like terms (e.g. an entity name that would plausibly be a column), additionally call "
        "`datasphere_discover_assets_by_column` across the in-scope spaces with a reasonable cap (max_spaces=5, max_assets_per_space=50).\n"
        "4. Dedupe results across the search and column-discover calls.\n"
        "5. For the top 5 candidates, call `datasphere_catalog_get_asset` to grab labels + descriptions for ranking.\n"
        "6. (Optional) For the single best candidate, call `datasphere_summarize_asset` to give the user a head start.\n\n"
        "Then present a ranked list (1-5) with this shape per item:\n\n"
        "1. **`{space}` / `{asset}`** — *(short label or description)*\n"
        "   - Why this matches: <1 line>\n"
        "   - What it would let you answer: <1 line>\n\n"
        "Close with a one-line recommendation: \"Start with X because Y.\" Keep total response under 400 words."
    )
