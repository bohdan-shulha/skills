# plan-b

Planning skill that produces a single concise plan by synthesizing multiple subagent plan variants.

## What it does
- Triggers on user intent like "I want to make..." / "I need to do..."
- Uses a read-only scan and minimal questions (same as create-plan)
- Spawns 3+ subagents to draft plan variants, then judges and merges
- Always includes an ASCII diagram (flow/architecture/UI mockup)

## How to use
Ask for a plan or describe a build task. Example prompts:
- "I want to make a CLI tool that ..."
- "I need to do a migration from ..."

The assistant returns a single plan that follows the Plan template inside `plan-b/SKILL.md`.
