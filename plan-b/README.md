# plan-b

Planning skill that produces a single concise plan by synthesizing multiple subagent plan variants.

## When to use

- The user explicitly asks for a plan related to a coding/build task.
- The task needs structure, risks, and validation steps.

## What it does

- Scans context read-only and asks minimal follow-ups.
- Spawns 3+ subagents for independent plan variants.
- Synthesizes a single best plan and includes an ASCII diagram.

## Source

See `plan-b/SKILL.md` for the full workflow and plan template.
