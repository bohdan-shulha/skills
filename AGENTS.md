# Agent Instructions

## Skill-relative paths

- When a `SKILL.md` references a relative path such as `scripts/...`, resolve it from the directory that contains that `SKILL.md`.
- Do not resolve skill-relative paths from the current project working directory unless the skill explicitly says to.
- If a referenced path does not exist under the skill directory, report it as missing instead of searching other folders.

Examples:
- `commit/SKILL.md` + `scripts/precommit_guard.py` -> `commit/scripts/precommit_guard.py`
- `babysit/SKILL.md` + `scripts/pr.py` -> `babysit/scripts/pr.py`
