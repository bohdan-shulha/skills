# skills

Local Copilot skills for this workspace.

## Skills

- `commit` — Create Conventional Commits with a required body after a pre-commit safety guard passes.
- `commit-jira` — Create ticket-prefixed commits with a required body after the same safety guard passes.
- `repo-wiki` — Generate and maintain a living codebase wiki, architecture docs, specs, and PRDs in `.repo-wiki/` so agents have better repository context.

## Repository layout

- Each skill lives in its own folder with a `SKILL.md`, `agents/`, and any supporting assets such as `scripts/`.
- Resolve any relative paths mentioned by a skill from that skill folder, not from the repository root.

## How to use

- Refer to a skill by name (for example, “use commit”) or ask for a task that matches its description.
- Open the skill's `SKILL.md` for the full workflow and requirements.
