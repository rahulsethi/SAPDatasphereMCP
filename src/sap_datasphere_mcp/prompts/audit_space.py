# SAP Datasphere MCP Server
# File: prompts/audit_space.py
# Version: v1 (1.0)

"""Walk every asset in a space and produce an inventory/governance report."""

from __future__ import annotations

PROMPT = {
    "name": "audit_space",
    "description": "Walk every asset in a Datasphere space and produce an inventory + governance report (asset counts by type, exposure flags, naming patterns).",
}


def render(space_id: str) -> str:
    return (
        f"Please audit the SAP Datasphere space `{space_id}`. Build a governance-quality report.\n\n"
        "Steps:\n\n"
        f"1. Call `datasphere_catalog_space_overview` for `{space_id}` to get the headline composition.\n"
        f"2. Call `datasphere_catalog_list_assets` for `{space_id}` and group the assets by type (table, view, model).\n"
        "3. For each unique asset type, call `datasphere_catalog_get_asset` on up to 3 representative assets to "
        "capture how exposure flags (relational / analytical) and labels are typically populated.\n"
        f"4. Call `datasphere_summarize_space` for a deterministic structured summary.\n"
        "5. If the space has any analytical assets, pick the most central one and call "
        "`datasphere_catalog_list_columns` on it to verify the column-level metadata is healthy.\n\n"
        "Then produce a markdown report with these sections:\n"
        "- **Composition** — asset counts by type, total count\n"
        "- **Naming patterns** — observed prefixes/suffixes, capitalization, any obvious convention drift\n"
        "- **Exposure hygiene** — fraction of assets exposed relationally / analytically; any orphans\n"
        "- **Recommendations** — 3-5 concrete next steps for the data steward\n\n"
        "Keep the report under 600 words. Don't speculate beyond what the tool calls returned."
    )
