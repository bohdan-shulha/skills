---
name: repo-wiki
description: 'Generate and maintain a living repo wiki, specs, PRDs, and architecture docs in .repo-wiki/ so coding agents can navigate the codebase with strong context. Use for codebase discovery, PR-driven documentation updates, module docs, architecture maps, feature specs, and deleting stale knowledge when code changes.'
argument-hint: 'Scope, e.g. "this PR", "payments module", or "backend refresh"'
---

# Repo Wiki

## Overview

Create and maintain a structured knowledge base from the codebase.
Primary goal: help LLMs and coding agents work faster, with less searching, less repeated explanation, and better architectural grounding.
Output should work as lightweight context engine: concise enough to scan, specific enough to act on, and kept in sync as repository changes.

This skill is for LLM-facing internal engineering knowledge such as architecture notes, module pages, PRD-style specs, integration maps, and change-aware wiki upkeep.
Human readability matters, but agent efficiency comes first.
It is not for public marketing docs or end-user documentation.

## When to Use

- Generate an initial wiki for a repository, package, service, or app
- Refresh docs after a PR, commit, refactor, migration, or incident fix
- Create or maintain architecture notes, module pages, feature specs, and PRD-style docs
- Delete stale knowledge when code, routes, jobs, packages, or configs disappear
- Prepare better navigation context, retrieval context, and decision context for coding agents and LLMs

## Workflow

1. Choose the documentation root.
   - Use `.repo-wiki/` as the canonical root for generated knowledge.
   - Do not repurpose `docs/`, `spec/`, or `wiki/` as the primary output location for this skill.
   - If those folders contain relevant human-written documentation, reference them from `.repo-wiki/` instead of merging into them.
2. Determine scope.
   - For PR or commit workflows, inspect the diff and update changed areas first.
   - For a first run, do a broader repository survey.
3. Read the current knowledge base before editing it.
   - Reuse existing filenames, section names, and conventions when they are still coherent.
   - Treat code, config, and tests as source of truth.
4. Build or refresh the minimum useful knowledge set.
   - Repo purpose and major entry points
   - System architecture and boundaries
   - Module, package, or service pages
   - Important flows, integrations, data paths, and operational constraints
   - Feature specs or PRD-style pages for active product areas
5. Update surgically.
   - Create pages for new systems or concepts.
   - Revise pages affected by changed code.
   - Delete or rename pages when the underlying code is removed or renamed.
6. Add navigation and evidence.
   - Link related pages.
   - Reference concrete files, directories, APIs, or commands in prose.
   - Mark unknowns explicitly instead of guessing.
7. Validate the result with the [recommended layout](./references/structure.md) and [update policy](./references/update-policy.md).

## Default Output Set

- `.repo-wiki/architecture/overview.md` for boundaries and major dependencies
- `.repo-wiki/architecture/data-flow.md` for request paths, events, pipelines, or state transitions
- `.repo-wiki/modules/<name>.md` for major packages, services, or subsystems
- `.repo-wiki/features/<name>.md` or `.repo-wiki/prd/<name>.md` for feature intent and implementation status
- `.repo-wiki/decisions/<name>.md` for notable design decisions when those can be inferred responsibly
- `.repo-wiki/glossary.md` for domain terms and internal vocabulary when needed

## Content Rules

- Prefer explicit observations from code, config, tests, and diffs over speculation.
- Keep pages skimmable: lead with purpose, responsibilities, entry points, dependencies, and risks.
- Write generated docs using the [writing style guide](./references/writing-style.md).
- Use diagrams only when they materially improve navigation; simple Mermaid is enough.
- Separate current behavior from planned behavior.
- Avoid copying large code blocks into docs.
- Highlight mismatches between docs and code instead of silently rewriting product intent.

## PR and Commit Update Loop

1. Inspect changed files and map them to existing wiki pages.
2. Update overview pages if system boundaries, dependencies, or major flows changed.
3. Update or create module and feature pages for the touched areas.
4. Delete or rename stale pages for removed or renamed code.
5. Refresh the root index so new pages are discoverable.
6. Call out unresolved questions at the end of the affected page when needed.

## Completion Checks

- Every changed subsystem in the PR or commit is reflected in at least one page.
- Removed code no longer has live documentation pretending it still exists.
- Specs distinguish shipped behavior, intended behavior, and unknowns.
- The result makes the codebase easier for an agent to traverse.

## Boundaries

- Do not document every file individually unless the repository is tiny.
- Do not restate source code line by line.
- Do not leave empty placeholders without context.
- Do not invent undocumented behavior to make the wiki feel complete.

## References

- [recommended layout](./references/structure.md)
- [writing style guide](./references/writing-style.md)
- [update policy](./references/update-policy.md)
