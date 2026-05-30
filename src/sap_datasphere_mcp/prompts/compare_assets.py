# SAP Datasphere MCP Server
# File: prompts/compare_assets.py
# Version: v1 (1.0)

"""Compare two Datasphere assets structurally."""

from __future__ import annotations

PROMPT = {
    "name": "compare_assets",
    "description": "Structural comparison between two Datasphere assets — column overlap, type mismatches, naming differences, row-count delta.",
}


def render(space_a: str, asset_a: str, space_b: str, asset_b: str) -> str:
    return (
        f"Please compare these two SAP Datasphere assets:\n\n"
        f"- A: `{asset_a}` in space `{space_a}`\n"
        f"- B: `{asset_b}` in space `{space_b}`\n\n"
        "Steps:\n\n"
        "1. Call `datasphere_summarize_compare_assets` first — it does the heavy lifting and returns a structured comparison.\n"
        f"2. If anything is unclear, call `datasphere_catalog_list_columns` on each asset to confirm column-level details.\n"
        f"3. Call `datasphere_query_preview` with `top=3` on each asset to see what real rows look like.\n\n"
        "Then write a markdown report covering:\n\n"
        "- **Column overlap** — columns in A only, columns in B only, columns in both (and whether they have the same type)\n"
        "- **Naming differences** — same-meaning columns with slightly different names (use judgment, call them out)\n"
        "- **Type mismatches** — same column name, different types\n"
        "- **Sample contrasts** — one row each from the previews, side-by-side\n"
        "- **Likely relationship** — is this a parent/child, a partial copy, a different aggregation level, or unrelated?\n"
        "- **Migration / consolidation notes** — if these two should be unified, what would the merge look like?\n\n"
        "Keep it under 600 words. Use markdown tables for the column comparisons."
    )
