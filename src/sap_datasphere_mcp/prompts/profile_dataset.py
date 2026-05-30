# SAP Datasphere MCP Server
# File: prompts/profile_dataset.py
# Version: v1 (1.0)

"""End-to-end profile of a Datasphere asset.

Walks: list_columns → preview → profile_column on numeric/categorical hints
→ deterministic summary. Designed for "show me what this dataset looks like"
questions.
"""

from __future__ import annotations

PROMPT = {
    "name": "profile_dataset",
    "description": "Generate a complete profile of a Datasphere dataset (schema + sample + per-column profile + summary).",
}


def render(space_id: str, asset_name: str) -> str:
    """Return the prompt text the agent should follow."""
    return (
        f"Please profile the SAP Datasphere asset `{asset_name}` in space `{space_id}`.\n\n"
        "Do this step by step, using the available tools:\n\n"
        f"1. Call `datasphere_catalog_get_asset` for ({space_id!r}, {asset_name!r}) to confirm the asset exists and grab labels.\n"
        f"2. Call `datasphere_catalog_list_columns` to get the column list with types.\n"
        f"3. Call `datasphere_query_preview` with `top=5` to see a small sample of rows.\n"
        "4. For each column that looks numeric, categorical, or like an ID, call `datasphere_profile_column` "
        "(skip columns that are obviously high-cardinality free text — use the `role_hint` returned in step 2 to decide).\n"
        "5. Call `datasphere_summarize_asset` for a deterministic compact summary.\n\n"
        "Then write a short human-readable narrative that explains: what this asset contains, what each key column "
        "represents, the data quality signals (null rates, outliers, low-cardinality dimensions), and one or two "
        "analytics this dataset would naturally support.\n\n"
        "Finish with a clear next-step suggestion (e.g. 'this asset would join cleanly with X via column Y'). Keep "
        "the whole response under 500 words and use plain markdown."
    )
