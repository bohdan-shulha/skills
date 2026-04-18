# Recommended Layout

Use `.repo-wiki/` as the dedicated root for the generated knowledge base.
This keeps agent-facing repository knowledge separate from broader human docs while making the location predictable.

## Suggested Tree

```text
.repo-wiki/
  architecture/
    overview.md
    data-flow.md
  modules/
    <module>.md
  features/
    <feature>.md
  prd/
    <feature>.md
  decisions/
    <decision>.md
  glossary.md
```

Do not create every folder on day one.
Only materialize sections that the repository actually needs.

## Module Page Template

Use a compact structure like this:

```markdown
# <Module Name>

## Purpose

## Responsibilities

## Key Entry Points

## Dependencies

## Data Contracts or State

## Change Hotspots

## Related Docs
```

## Feature or PRD Page Template

Use a compact structure like this:

```markdown
# <Feature Name>

## Goal

## User or Business Problem

## Current Implementation State

## Constraints

## Related Code

## Open Questions
```

## Architecture Page Guidance

- `architecture/overview.md` should explain boundaries, major components, and external systems.
- `architecture/data-flow.md` should explain important request, event, or job paths.
- Add Mermaid only when a reader would understand the system faster with a diagram than with prose.

## Writing Style

- Use terse, direct prose for generated docs.
- Apply the detailed [writing style guide](./writing-style.md).
- Use repository terminology exactly as it appears in code and config.
- Keep page titles stable so agents and humans can find them again.
- Avoid timestamps unless the repository explicitly wants audit history inside docs.
