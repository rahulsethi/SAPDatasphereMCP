---
name: release
description: Cut a new version of the SAP Datasphere MCP server — bump the version in pyproject.toml, sync CHANGELOG.md and README, and prepare the release commit. Use when asked to release, cut a version, or bump the version.
disable-model-invocation: true
---

# release — version bump for the SAP Datasphere MCP server

The version is the single source of truth in `pyproject.toml` but is echoed in
`CHANGELOG.md` and `README.md`. Keep all three in lockstep.

## Steps

1. **Determine the new version.** Read the current `version` in `pyproject.toml`
   (latest was `0.3.1`). Ask the user for the target if not given, or infer
   patch/minor/major from the scope of changes. Follow semver.

2. **Gather what changed.** Run `git log <last-tag-or-prev-release>..HEAD --oneline`
   (or diff against the previous release commit) and group commits into
   Added / Changed / Fixed.

3. **Bump `pyproject.toml`.** Update the `version = "..."` line only.

4. **Update `CHANGELOG.md`.** Add a new section at the top following the existing
   voice and format (match how `0.3.0` / `0.3.1` entries are written). Use today's
   date. Don't rewrite past entries.

5. **Sync `README.md`.** Update any version strings / "what's new" references so they
   match the new version. Only touch version-related lines (surgical changes).

6. **Verify before committing.**
   ```powershell
   ruff check . ; ruff format .
   pytest -q
   ```

7. **Prepare the commit.** Stage the changed files and propose a commit message like
   `Release vX.Y.Z`. Do NOT push or tag unless the user explicitly asks.

## Guardrails

- Never bump version without updating CHANGELOG in the same change.
- Don't invent changelog entries — base them on real commits/diffs.
- Confirm the version number with the user before committing.
