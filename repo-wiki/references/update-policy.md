# Update Policy

This skill should behave like a change-aware repo wiki, not a one-shot document dump.

## Source Priority

Prefer information in this order:

1. Source code and configuration
2. Tests and fixtures
3. Existing engineering docs and ADRs
4. Recent diffs and commit context
5. Issue or PR discussion when explicitly available

If sources conflict, document the conflict instead of guessing.

## Full Refresh vs Incremental Refresh

- Use a full refresh for the first run, major reorganizations, or when the docs are obviously stale.
- Use an incremental refresh for normal PRs and commits.
- In incremental mode, start from changed files, then widen scope only when architecture or shared contracts changed.

## Create, Update, Rename, Delete Rules

Create a page when:

- a new subsystem, package, service, or major feature appears
- a previously undocumented flow becomes important to current work
- a feature needs product intent separated from implementation details

Update a page when:

- public APIs, schemas, jobs, routes, commands, or user-visible behavior change
- responsibilities or dependencies change
- a page is correct in spirit but stale in detail

Rename a page when:

- the underlying module or feature was renamed and readers would otherwise lose the trail

Delete a page when:

- the represented code or feature was removed
- the page duplicates another page with no unique value
- the page is misleading and cannot be salvaged by a simple rewrite

## Diff Mapping Heuristics

- Changed top-level package or service: update its module page and usually architecture overview.
- Changed API or schema: update feature docs and any relevant flow or contract docs.
- Changed shared library or platform config: update the consuming module pages if behavior changed.
- File move or rename: preserve continuity by renaming docs or backlinks, not by creating duplicates.

## Quality Bar

Each update should make navigation easier.
That means:

- stable filenames and headings
- direct links between related pages
- explicit mention of unknowns, risks, and assumptions
- no stale references to removed code
- no speculative details presented as facts

## Churn Control

- Avoid rewriting the entire wiki for small diffs.
- Avoid noisy cosmetic edits when nothing meaningful changed.
- Avoid adding generated timestamps, badges, or summary blocks unless the repository already uses them.

## Final Validation

Before finishing, check that:

- the changed code paths are documented
- stale pages or stale links were removed
- the wiki remains concise enough for agents to scan quickly
