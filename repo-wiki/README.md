# repo-wiki

This skill maintains a generated knowledge base in `.repo-wiki/` so LLMs and coding agents can navigate a repository with better architectural and feature context.

## What It Does

- surveys a repository or a scoped area such as a module, service, or PR diff
- writes or updates concise architecture, module, domain, feature, and business rule pages under `.repo-wiki/`
- keeps the generated docs aligned with code changes, including deleting stale pages
- references existing human-written docs when useful instead of merging into them
- optimizes repository context so agents spend less time searching and re-deriving architecture

## When to Use It

Use `repo-wiki` when you want to:

- generate an initial codebase wiki
- refresh docs after a PR or commit
- document a subsystem before or during implementation work
- make the codebase easier for LLMs to understand before asking for changes

## How to Invoke It

Example prompts:

- `/repo-wiki this PR`
- `/repo-wiki payments module`
- `/repo-wiki backend refresh`
- `/repo-wiki initial wiki for the repository`

## Output Shape

Typical output lives under `.repo-wiki/` and may include:

- `index.md`
- `architecture/overview.md`
- `architecture/data-flow.md`
- `modules/<name>.md`
- `domain/model.md`
- `features/<name>.md`
- `prd/<name>.md`
- `business-rules/<topic>.md`
- `glossary.md`

The skill is adaptive. It should create only the pages that are useful for the repository and current scope.
Primary audience is LLMs and coding agents. Human readability is still useful, but secondary.

## Operating Rules

- `.repo-wiki/` is the canonical output root
- source code, config, and tests are the source of truth
- updates should follow diffs first, then widen only when shared contracts or architecture changed
- stale generated pages should be updated, renamed, or deleted when the underlying code changes
- generated prose should stay terse, direct, low-filler, and technically exact
- generated docs should optimize for agent retrieval, navigation, and implementation context
- pages state what stays true between runs, so no counts, versions, or rankings
- every path in a page must resolve, and the skill verifies this before it finishes

## Files In This Skill

- `SKILL.md` contains the agent-facing workflow
- `references/structure.md` defines the recommended generated layout
- `references/writing-style.md` defines the generated prose style and examples
- `references/update-policy.md` defines incremental update rules
