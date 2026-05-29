<!-- SAP Datasphere MCP Server -->
<!-- File: MCP_TestPrompts_v0.2.md -->
<!-- Version: v1 -->

# Test Prompts – SAP Datasphere MCP Server v0.2

This file contains **example natural-language prompts** to exercise each MCP tool exposed by the SAP Datasphere MCP server, plus a few **combined scenarios**.

You can use these directly in Claude Desktop (or any MCP client) to sanity-check the integration and explore behaviours.

> Where a prompt mentions specific space/asset names (e.g. `HR_SPACE`, `EMP_View_Test`), substitute values from your own tenant or the mock dataset.

---

## 1. Health & Diagnostics

### 1.1 `datasphere_ping`

1. `Run a quick health check on the SAP Datasphere MCP server and tell me if it's reachable.`
2. `Call the ping tool and confirm whether the connection to Datasphere looks OK.`
3. `Is the Datasphere MCP backend alive? Use whatever "ping" tool you have and summarise the result.`

### 1.2 `datasphere_diagnostics`

1. `Run a full diagnostics check for the Datasphere MCP server and summarise what you find, including any failed steps.`
2. `Use your diagnostics tool to verify client configuration and list any warnings about connectivity or permissions.`
3. `Before we do anything else, run diagnostics and tell me: are you in mock mode or talking to a real Datasphere tenant, and how healthy does the connection look?`

### 1.3 `datasphere_get_tenant_info`

1. `Show me a redacted overview of the configured Datasphere tenant: base URL, region hint, TLS verification settings, but no secrets.`
2. `Use your tenant-info tool to summarise which Datasphere endpoints you’re configured to talk to.`
3. `Tell me, in a safe redacted way, which Datasphere environment you are connected to (URLs, region, TLS flags).`

### 1.4 `datasphere_get_current_user`

1. `Describe the current Datasphere identity context: are you using a technical user, and are you in mock mode or real mode?`
2. `Use your "current user" tool to explain who you're acting as when you call Datasphere APIs.`
3. `Are you running against a mock client or a real tenant right now? Call the identity helper and explain in plain language.`

---

## 2. Spaces & Catalog

### 2.1 `datasphere_list_spaces`

1. `List all Datasphere spaces you can see, with their IDs and descriptions, and suggest which ones look interesting for analytics.`
2. `Call your list-spaces tool and summarise how the tenant is organised (number of spaces and a sample of them).`
3. `Show me the available Datasphere spaces and highlight any that look like sandbox or test spaces.`

### 2.2 `datasphere_list_assets`

1. `For the space called "HR_SPACE" (or the closest match), list the catalog assets you can see with type and description.`
2. `Pick one of the spaces you listed earlier and show me its assets, grouped by type (views, tables, etc.).`
3. `List assets in the space "FINANCE_SPACE" and call out anything that looks like a main fact table or consolidated view.`

### 2.3 `datasphere_search_assets`

1. `Search across all spaces for assets related to "employee" and show me the top 10 matches with their spaces and descriptions.`
2. `Within the space "HR_SPACE", search for assets whose name or description mentions "salary" and list a few candidates.`
3. `Find assets related to "sales" across the tenant, and recommend one that looks suitable for exploratory analysis.`

### 2.4 `datasphere_space_summary`

1. `Give me a summary of the "HR_SPACE" space: total asset count, counts by type, and a small sample list.`
2. `Pick one space that looks interesting and run a space summary, then explain what kind of data lives there.`
3. `Show a high-level breakdown of asset types for the space "SALES_SPACE" and suggest where to start exploring.`

### 2.5 `datasphere_get_asset_metadata`

1. `For the asset "EMP_View_Test" in the HR space, fetch its catalog metadata and explain what it represents and how it can be queried.`
2. `Pick one asset that looks like a core sales view and show its asset metadata, including whether relational and analytical APIs are available.`
3. `Given an asset of your choice, call the metadata tool and summarise its label, description, type, and key URLs you can use.`

---

## 3. Data Preview & Relational Queries

### 3.1 `datasphere_preview_asset`

1. `Preview the first 10 rows from the main employee view in HR and show me the columns and sample data.`
2. `Take any asset you think is interesting and show a small preview of its data, mentioning if the result is truncated.`
3. `In mock mode (if enabled), preview data from your demo dataset and explain what each column likely means.`

### 3.2 `datasphere_describe_asset_schema`

1. `Describe the schema of "EMP_View_Test" using a sample: list columns, rough Python types, null counts, and a few example values.`
2. `Pick an asset with numeric measures and describe its schema, highlighting which columns look like IDs, dates, or measures.`
3. `For the asset you just previewed, call the schema description tool and summarise how an analyst should think about its columns.`

### 3.3 `datasphere_query_relational`

1. `On the main employee view, run a relational query that only returns employee ID, department, and salary for the first 20 rows, ordered by salary descending.`
2. `Filter the sales view to only show rows for country = "DE" and year >= 2023, returning a small sample with relevant columns.`
3. `Demonstrate a paged query on any asset: fetch 10 rows at a time using top/skip, and explain how the paging works.`

---

## 4. Columns, Profiling & Discovery

### 4.1 `datasphere_list_columns`

1. `For "EMP_View_Test" in HR, list all columns with their types, nullability, and whether they are keys.`
2. `Pick a core sales asset and show me its columns using relational metadata if available, falling back to sample-based inference if needed.`
3. `List the columns for one asset and highlight which ones you think are good candidates for joins or filters.`

### 4.2 `datasphere_profile_column`

1. `Profile the "EMP_ID" column in the main employee view and tell me whether it behaves like a unique identifier (based on counts, distincts, and role hint).`
2. `Profile a numeric measure column like "AMOUNT" or "SALES_VALUE" and summarise min, max, mean, percentiles, and outliers.`
3. `Find a categorical column (e.g. "COUNTRY" or "DEPARTMENT") and show its categorical summary: top values, frequencies, and concentration.`

### 4.3 `datasphere_find_assets_with_column`

1. `Within the "HR_SPACE" space, find all assets that contain a column called "EMP_ID" and summarise which asset looks most important.`
2. `Search in a single space for assets that have a "CUSTOMER_ID" column and list them with their column counts.`
3. `In the space "FINANCE_SPACE", find assets that expose a "PERIOD" column and suggest which one to analyse for monthly trends.`

### 4.4 `datasphere_find_assets_by_column`

1. `Across all spaces, find assets that have a column named "CUSTOMER_ID" and tell me how widely that identifier is used.`
2. `Search across spaces for a column called "ORDER_ID" and group the results by space, noting any patterns you see.`
3. `Find assets that share a column called "PRODUCT_ID" and propose which combination of assets would make a good star schema.`

---

## 5. Combined Scenario Prompts (Multiple Tools)

These prompts are designed to trigger **multiple tools in sequence** (spaces → assets → metadata → profiling, etc.).

1. **End-to-end asset exploration**

   > `Run diagnostics first to ensure everything is healthy. Then pick a non-empty space, list its assets, choose one interesting asset, fetch its metadata, describe its schema, preview some rows, and finally profile one numeric and one categorical column. Summarise what this dataset is about.`

2. **Key discovery for joins**

   > `Find a column that looks like a shared key across multiple assets (for example EMP_ID or CUSTOMER_ID). Use your find-assets-by-column tools to discover where it appears, list those assets, and suggest which asset should be treated as the primary source vs lookups.`

3. **Building a semantic “card” for an asset**

   > `Choose a core analytical asset (for example a main sales or employee view). Using your metadata, schema, and column profiling tools, create a concise "asset card" that explains: purpose, key dimensions, key measures, important IDs, and any data quality caveats.`

4. **Mock mode smoke test**

   > `Switch mental context to mock mode if it is enabled. Use diagnostics to confirm you are in mock mode, list the demo spaces/assets, preview a dataset, describe its schema, and profile one column. Explain how someone can safely experiment with the MCP server using mock mode.`

5. **Column-level data quality check**

   > `Pick an asset with a date column and an amount column (for example an orders or sales view). Profile the date column and the amount column, check for nulls and outliers, and then tell me if this asset looks suitable for downstream analytics or if you see any red flags.`

6. **Space-level reconnaissance**

   > `List all spaces, pick the one that looks most like a finance or sales space, run a space summary there, search for assets related to "invoice" or "order", and then preview the most promising asset. Summarise how this space could be used in an analytics project.`

7. **“What can I query?” orientation**

   > `Without assuming anything about my tenant, discover what you can: list spaces, pick one, summarise it, then show me two or three assets with metadata and quick previews that you think are good starting points for analysis.`

---

## 6. How to extend this file for future versions

For **future versions (v0.3+)**, when new tools are added:

1. Add a new section with the tool name (e.g. `### datasphere_list_analytical_models`).
2. Provide **2–3 focused prompts**:
   - one minimal (“call this tool directly”),
   - one guided (“choose an interesting object, then call the tool”),
   - one combined scenario where this tool works alongside others.
3. Add at least one **combined scenario** that uses the new tool plus existing ones.

This keeps the prompts file aligned with the MCP surface and makes it easy to regression-test behaviour every time you cut a new release.
