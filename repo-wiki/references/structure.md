# Recommended Layout

Use `.repo-wiki/` as the dedicated root for the generated knowledge base.
This keeps agent-facing repository knowledge separate from broader human docs while making the location predictable.

## Suggested Tree

```text
.repo-wiki/
  index.md
  architecture/
    overview.md
    data-flow.md
  modules/
    <module>.md
  domain/
    model.md
  features/
    <feature>.md
  prd/
    <feature>.md
  business-rules/
    <topic>.md
  glossary.md
```

Do not create every folder on day one.
Only materialize sections that the repository actually needs.

`index.md` is the exception. Always write it. An unpredictable entry point defeats the purpose.

## Index Template

Shape the index as a task router, not a table of contents.
An agent arrives with a task, not a browsing intent. A contents list only repeats `ls`.

```markdown
# <Repo Name> Wiki

## What this repo does

One or two sentences.

## Start here

| Task | Read |
|---|---|
| Add or change an HTTP endpoint | `modules/api.md`, `domain/model.md` |
| Add a background job | `architecture/data-flow.md`, `modules/worker.md` |
| Change a business constraint | `business-rules/<topic>.md` |

## Commands

Name the build, test, and lint commands, or link the file that holds them.
```

Link the commands instead of copying them, so they cannot go stale.

## Module Page Template

Use a compact structure like this:

```markdown
# <Module Name>

## Purpose

## Responsibilities

## Key Entry Points

## Dependencies

## Data Contracts or State

## Invariants and Constraints

## Change Hotspots

## Related Docs
```

## Domain Model Template

Write this page only when the repository has a real business domain.

```markdown
# Domain Model

## Entities

| Entity | Code | Storage | Id prefix | Lifecycle |
|---|---|---|---|---|
| Invoice | `src/billing/invoice.ts` | `invoices` | `inv_` | draft -> issued -> paid -> void |
| Order | `src/orders/order.ts` | `orders` | `ord_` | draft -> confirmed -> shipped |

## Relations

| From | To | Cardinality | Enforced by |
|---|---|---|---|
| Invoice | Order | N:1 | FK `invoices.order_id` |
| Order | LineItem | 1:N | FK `line_items.order_id` |

## Lifecycle transitions

| Entity | Transition | Moved by |
|---|---|---|
| Invoice | issued -> paid | `src/billing/settle.ts` |

## Aliases and collisions

| Term | Real entity | Note |
|---|---|---|

## Cross-entity invariants
```

Rules for this page:

- Do not list fields. Field lists go stale and the schema is right there.
- Take the `Lifecycle` values from the enum or the union in code.
- `Moved by` names the job, route, or function that performs the transition.
  Without it a reader learns the jobs and never learns that a state machine exists.
- `Aliases and collisions` catches one entity under two names, and one word that means two entities in two tables.
- Add a Mermaid `erDiagram` only when the relations table gets hard to follow as text.

A term with a backing type or table belongs on this page.
The glossary holds only vocabulary that has no code entity.

## Business Rule Template

Both gates in the [skill](../SKILL.md) must pass before the page exists.

```markdown
# <Rule Topic>

## Rules

### <rule name>

Statement in present tense.
Enforced: `path/to/file`
Applies to: <entities or flows>

## Exceptions
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
- Apply the durability rule in the [skill](../SKILL.md). A page states what stays true between runs.
