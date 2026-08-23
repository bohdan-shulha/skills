---
name: repo-wiki
description: 'Generate and maintain a living repo wiki, specs, PRDs, and architecture docs in .repo-wiki/ so coding agents can navigate the codebase with strong context. Use for codebase discovery, PR-driven documentation updates, module docs, architecture maps, domain models, feature specs, and deleting stale knowledge when code changes.'
argument-hint: 'Scope, e.g. "this PR", "payments module", or "backend refresh"'
---

# Repo Wiki

## Overview

Create and maintain a structured knowledge base from the codebase.
Primary goal: help LLMs and coding agents work faster, with less searching, less repeated explanation, and better architectural grounding.
Output should work as lightweight context engine: concise enough to scan, specific enough to act on, and kept in sync as repository changes.

This skill is for LLM-facing internal engineering knowledge such as architecture notes, module pages, domain models, PRD-style specs, integration maps, and change-aware wiki upkeep.
Human readability matters, but agent efficiency comes first.
It is not for public marketing docs or end-user documentation.

## When to Use

- Generate an initial wiki for a repository, package, service, or app
- Refresh docs after a PR, commit, refactor, migration, or incident fix
- Create or maintain architecture notes, module pages, domain models, feature specs, and PRD-style docs
- Delete stale knowledge when code, routes, jobs, packages, or configs disappear
- Prepare better navigation context, retrieval context, and domain context for coding agents and LLMs

## Workflow

1. Choose the documentation root.
   - Use `.repo-wiki/` as the canonical root for generated knowledge.
   - Do not repurpose `docs/`, `spec/`, or `wiki/` as the primary output location for this skill.
   - If those folders contain relevant human-written documentation, reference them from `.repo-wiki/` instead of merging into them.
2. Determine scope.
   - For PR or commit workflows, inspect the diff and update changed areas first.
   - For a first run, follow the [first run sequence](#first-run) below.
3. Inventory the documentation already in the repository.
   - Find nested `CLAUDE.md`, `AGENTS.md`, `README.md`, and `docs/` files across the tree.
   - Classify each file as current or stale against the code.
   - Link a current file. Do not restate it. The people who hit the bugs wrote it.
   - Report a stale file that contradicts the code. A stale map sends an agent to build the wrong thing.
4. Read the current knowledge base before editing it.
   - Reuse existing filenames, section names, and conventions when they are still coherent.
   - Treat code, config, and tests as source of truth.
5. Choose page granularity, then keep it.
   - Under about ten modules, write one page for each module.
   - Above that, group pages by role and state which modules each page covers.
   - Thin pages that nobody maintains are worse than fewer complete pages.
6. Build or refresh the minimum useful knowledge set.
   - Repo purpose and major entry points
   - System architecture and boundaries
   - Module, package, or service pages
   - Domain entities, relations, and lifecycles, when the repository has persistent entities
   - Important flows, integrations, data paths, and operational constraints
   - Feature specs or PRD-style pages for active product areas
7. Update surgically.
   - Create pages for new systems or concepts.
   - Revise pages affected by changed code.
   - Delete or rename pages when the underlying code is removed or renamed.
8. Add navigation and evidence.
   - Link related pages.
   - Reference concrete files, directories, APIs, or commands in prose.
   - Mark unknowns explicitly instead of guessing.
   - Ensure the agent entry file (`CLAUDE.md` or `AGENTS.md`) links `.repo-wiki/index.md`. A wiki that no agent loads is dead weight.
9. Run the [verification](#verification) pass. Prose has no compiler.
10. Validate the result with the [recommended layout](./references/structure.md) and [update policy](./references/update-policy.md).

## First Run

A first run costs the most and needs the most structure. Follow this order:

1. Inventory the documentation already in the repository, as in workflow step 3.
2. Map the workspaces, packages, or services.
3. Choose page granularity, as in workflow step 5.
4. Write `domain/model.md` when the repository has persistent entities.
   Module boundaries are visible from `ls`. A lifecycle spread across a jobs directory and an enum is not.
   This page pays for itself first, so it comes before the module pages.
5. Write the module and architecture pages.
6. Write `index.md` last, when you know which pages exist.
7. Link `.repo-wiki/index.md` from the agent entry file, as in workflow step 8.

## Default Output Set

- `.repo-wiki/index.md` as the entry point, shaped as a task router
- `.repo-wiki/architecture/overview.md` for boundaries and major dependencies
- `.repo-wiki/architecture/data-flow.md` for request paths, events, pipelines, or state transitions
- `.repo-wiki/modules/<name>.md` for major packages, services, or subsystems
- `.repo-wiki/domain/model.md` whenever the repository has persistent entities: a schema directory, a migrations directory, or an ORM model set. Skip it only for a CLI or a pure library with no store.
- `.repo-wiki/features/<name>.md` or `.repo-wiki/prd/<name>.md` for feature intent and implementation status
- `.repo-wiki/glossary.md` for domain terms and internal vocabulary when needed

Create this one only when the repository earns it:

- `.repo-wiki/business-rules/<topic>.md` for a domain constraint that spans modules. Both gates below must pass.

## Business Rules

A business rule is a domain constraint that the code enforces, and that a reader cannot derive from the shape of the code alone.

A rule needs both gates:

1. It names the file that enforces it. No path, no rule.
2. It changes what a reader would write. A rule that changes nothing is trivia.

Removals, renames, migrations, and dependency changes are never business rules.
Git holds history. The wiki holds current truth.

A tooling choice is not a business rule. `We use pnpm workspaces` does not belong here.

A rule visible inside one module goes on that module page.
Only a rule that spans modules earns a page in `business-rules/`.

When a deleted thing still misleads a reader, put one warning line on the page that the reader opens, not on a page of its own:

```text
Older docs route this through a shared server package. That package no longer exists.
```

The warning fires at the moment of confusion. A separate page does not.

## Content Rules

Apply one test to every line: the line changes what an agent writes, or it saves the agent a search.
Delete a line that an agent can rebuild with one grep.
A hazard that the code hides is worth more than an inventory that the code shows.
Every rule below follows from this test.

- Prefer explicit observations from code, config, tests, and diffs over speculation.
  An observation must be durable. A measurement that you took is not a property of the code.
- Keep pages skimmable: lead with purpose, responsibilities, entry points, dependencies, and risks.
- Write generated docs using the [writing style guide](./references/writing-style.md).
- Use diagrams only when they materially improve navigation; simple Mermaid is enough.
- Separate current behavior from planned behavior.
- Avoid copying large code blocks into docs.
- Highlight mismatches between docs and code instead of silently rewriting product intent.

### Durability

A page states what stays true between runs. Write the shape, not the census.

Do not write:

- counts and sizes: files, lines, modules, tables, rows, tests
- rankings and comparatives: `largest`, `most`, `busiest`, `the one you edit most`
- dependency and package versions
- volatility words: `currently`, `recently`, `now`, `for now`
- change narration: `removed X`, `migrated from Y`, `previously Z`, `replaced W`
- timestamps, dates, author names, ticket IDs, pull request numbers

A ranking is worse than a count, because a count is at least checkable.
A ranking inverts in silence and no reader can tell.

A number stays only when the repository does not already store it.
If a file holds the value, name the file and state the rule. Never copy the value.
A port an agent must dial, a fixed protocol constant, or an external service limit qualifies.
A coverage percentage, a memory measurement, a timing measurement, a file count, and a dependency version never qualify. Each one is already in a file or already stale.

`git log` tells you where work happened. It does not tell you what the code is.
Never write a ranking or a comparative from history.

```text
Bad:
Every use case. 771 source files, 36 feature areas, one function for each file.
No classes, no dependency-injection container. It is the largest package and the
one you edit most.

Good:
Hold every use case. One exported function per file. No classes.
No dependency-injection container. Feature area per directory under `src/`.
```

Numbers hide in tables. A number inside a table cell counts.

```text
Bad:
| Package | Statements | Branches |
|---|---|---|
| worker  | 3.9 %      | 2.1 %    |

Good:
Each package pins its coverage ratchet in its `vitest.config.ts`.
Raise the ratchet in that file when coverage rises.
```

Every durable fact survives. Every perishable one goes.

## Verification

Run this pass before you finish. Nothing type-checks prose.

1. Run the verify script. Resolve the script path from this skill directory, not from the repository:

   ```bash
   python3 <skill_dir>/scripts/verify.py <repo_root>
   ```

   The script confirms that every backticked path and every relative link resolves.
   It sweeps every page for percentages, decimals, counts, rankings, volatility words, change narration, dates, and issue references.
   It skips fenced code, glob patterns, route templates, and image tags.
2. Fix every error. A path that matches two files is a defect. Name the file exactly.
   To keep a reference to a path that is absent on purpose, write `deliberately absent` on the same line.
   The script then skips the paths on that line.
3. Justify every warning against the number rule in [Durability](#durability), or delete the line.
   A number inside a table cell counts. A rare warning is a false positive; say so and move on.
4. Spot-check three claims against the code. Prefer a claim that carries a number.
   Then apply the durability rule to that number: verify it, and also ask if it may stay at all.

## Incremental Update Loop

1. Inspect changed files and map them to existing wiki pages.
2. Update overview pages if system boundaries, dependencies, or major flows changed.
3. Update or create module and feature pages for the touched areas.
4. Update `domain/model.md` when an entity, a relation, or a lifecycle state changed.
5. Delete or rename stale pages for removed or renamed code.
6. Refresh `index.md` so new pages are discoverable.
7. Call out unresolved questions at the end of the affected page when needed.

## Completion Checks

- Every changed subsystem in the PR or commit is reflected in at least one page.
- Removed code no longer has live documentation pretending it still exists.
- Every path named in the wiki exists, or is marked as deliberately absent.
- No number copies a value that a repository file stores.
- No page states a count, a version, or a ranking. The verify script ran, reports zero errors, and every warning has a justification.
- Specs distinguish shipped behavior, intended behavior, and unknowns.
- The result makes the codebase easier for an agent to traverse.

## Boundaries

- Do not document every file individually unless the repository is tiny.
- Do not restate source code line by line.
- Do not restate a repository doc that is already current. Link it.
- Do not leave empty placeholders without context.
- Do not invent undocumented behavior to make the wiki feel complete.

## References

- [recommended layout](./references/structure.md)
- [writing style guide](./references/writing-style.md)
- [update policy](./references/update-policy.md)
