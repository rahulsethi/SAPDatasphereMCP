# SAP Datasphere MCP Server
# File: prompts/explain_analytical_model.py
# Version: v1 (1.0)

"""Explain an analytical model in business-friendly language."""

from __future__ import annotations

PROMPT = {
    "name": "explain_analytical_model",
    "description": "For an analytical asset, return its dimensions / measures / hierarchies in plain English.",
}


def render(space_id: str, asset_name: str) -> str:
    return (
        f"Please explain the SAP Datasphere analytical model `{asset_name}` in space `{space_id}` to a "
        "business analyst who is not a data engineer.\n\n"
        "Steps:\n\n"
        f"1. Call `datasphere_catalog_get_asset` for `{space_id}` / `{asset_name}`. Confirm that the asset is "
        "exposed analytically (look at the exposure flags in the response).\n"
        f"2. Call `datasphere_catalog_list_columns` to enumerate the columns with their types and any role hints.\n"
        f"3. Call `datasphere_query_analytical` with no filter and `top=10` to see a representative slice of "
        "the model's output (this surfaces measure values).\n"
        f"4. For up to 3 obvious measures, call `datasphere_profile_column` to capture distribution and outliers.\n"
        "5. Call `datasphere_summarize_asset` for a structured baseline.\n\n"
        "Then write a plain-English explanation organized as:\n\n"
        "- **What this model answers** — the business question(s) it's designed for\n"
        "- **Dimensions** — list each dimension column with a one-line meaning, calling out any time/geo/org hierarchies\n"
        "- **Measures** — list each measure with units, typical range, and any caveats from the profile (outliers, nulls)\n"
        "- **How to slice it** — 3 example questions a business user could ask and the (dimension, measure) pairing each one maps to\n\n"
        "Avoid SAP jargon; if you have to use a technical term, define it briefly inline. Keep it under 500 words."
    )
