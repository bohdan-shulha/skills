---
name: implement-verified
description: 'Implement, code, refactor, migrate, or delete something with an adversarial verification pass. An Opus coder writes the implementation, then an independent Opus verifier re-runs every check itself and must prove the stated invariant with its own command output before it ships. Use when implementing anything a green test suite can still hide a bug in — billing, credits or charging, concurrency and locking, idempotency and retries, data migrations, behavior-preserving refactors, or removing a guard.'
argument-hint: 'What to implement, e.g. "add an idempotency key to the payments endpoint"'
---

# Implement, Verified

## Overview

Run a change through two independent agents: a **coder** that implements it, then an
**adversarial verifier** that re-runs every check itself and tries to break the claim. The
verifier never trusts the coder's report — it is handed the report explicitly labelled as
untrusted and must produce its own command output.

This exists because a green test suite routinely hides the defects that matter. Concurrency
and billing bugs in particular pass every unit test and only surface under a concurrent probe
against a real dependency.

## When to Use

- A correctness invariant a unit suite can hide: "charged at most once", "runs exactly once",
  "no two writers", "the migration is reversible".
- Refactors that must preserve behavior exactly (moves, renames, extractions).
- Deletions — proving the removed guard is genuinely re-established elsewhere.
- Anything touching money, locks, retries, or shared mutable state.

Do **not** use it for a typo, a one-line fix, or exploratory work. It spawns two Opus agents;
the cost only pays off when being wrong is expensive.

## Workflow

1. **Scope it precisely.** Name the invariant that must hold. If you cannot state a failure
   scenario the verifier could reproduce, the task is not ready for this skill.
2. **Write the script** from the template below, filling every `«…»`. Task-specific boolean
   gates in the verdict schema are what force the verifier to commit to a claim.
3. **Run it** with the Workflow tool (both agents Opus, effort high).
4. **Judge the verdict yourself.** See *Judging* — do not rubber-stamp a SHIP.
5. **Report** the verdict, what was actually proven, and what could not be exercised.

## The script

```js
export const meta = {
  name: '«short-kebab-name»',
  description: '«what changes + that it is adversarially verified»',
  phases: [
    { title: 'Code',   detail: '«what the coder does»' },
    { title: 'Verify', detail: '«what the verifier proves»' },
  ],
}

const REPO = '«/abs/path/to/repo»'

// Keep this block. Every rule was learned from a rejected round.
const CONVENTIONS = `
- Project rules (CLAUDE.md / AGENTS.md) are binding: YAGNI, delete dead code fully, no
  unnecessary comments. NEVER add eslint-disable / @ts-ignore / @ts-expect-error — fix
  the real issue.
- Architecture rules of the repo apply to new code too (e.g. bound ports, not raw handles).
- GIT: do NOT commit. No state-mutating git (no stash/reset/checkout/restore/clean/mv).
  Read-only git only. The working tree is shared — never clobber it.
- Do NOT use \`sed -i\` on tracked files. Use real edits.
- Run package scripts SEPARATELY. Never chain script names as args to one run —
  \`pnpm --filter x build check-types\` passes the extras as ARGS to build and fails.
- Codegen is ONE command; never run its steps by hand; never hand-edit generated files.
- If a genuine blocker or a contradiction with the plan emerges, STOP and report it
  rather than hacking around it.
`

const coderPrompt = `You are the CODER for «task» in «repo».

«Context: what shipped before, why this change, the decided design.»

${CONVENTIONS}

## Read first
«exact files to mirror / the existing pattern to follow»

## Build
«numbered, concrete deliverables»

## Prove green (run each SEPARATELY)
«build, check-types, test, AND LINT for every touched package»
- Type-checking does NOT catch lint's type-aware rules. Run lint explicitly.
- «any grep that must come back empty, e.g. no references to a deleted symbol»

Report every file added/changed/deleted and all command outputs.`

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['verdict', «'taskSpecificGates'», 'lintRun', 'findings', 'greenSummary'],
  properties: {
    verdict: { enum: ['SHIP', 'NO_SHIP'] },
    // Boolean gates force a claim the verifier must back with evidence.
    «gateName»: { type: 'boolean', description: 'true iff «what was actually proven»' },
    lintRun: { type: 'boolean', description: 'true iff you personally ran lint on every touched package and it passed' },
    findings: { type: 'array', items: { type: 'object', additionalProperties: false,
      required: ['severity','area','detail','evidence'], properties: {
        severity: { enum: ['blocker','major','minor','nit'] },
        area: { type: 'string' }, detail: { type: 'string' },
        evidence: { type: 'string', description: 'file:line or command output proving it' } } } },
    greenSummary: { type: 'string' },
  },
}

const verifierPrompt = `You are the ADVERSARIAL VERIFIER for «task» in «repo». A coder just made
the changes (its report is appended). Be skeptical — verify against the CODE and against your
OWN command output, never the coder's claims.

GIT: read-only only. NEVER stash/reset/checkout/restore/clean/commit/mv.

Prove each with evidence:
1. «The core invariant. If it involves concurrency, money, or shared state, PROVE IT BY
   RUNNING a concurrent probe against a real dependency — a green unit suite hides these.»
2. «Nothing unrelated regressed: name what must still be untouched and green.»
3. CONVENTIONS: no suppressions; architecture rules respected; YAGNI (no speculative extras).
4. GREEN: independently run build + check-types + test + LINT for every touched package and
   report the ACTUAL output. Any red = NO_SHIP. Skipping lint = NO_SHIP.

If you could not exercise something live (no creds / no service), SAY SO explicitly in
greenSummary. Do NOT fabricate a pass.

Return the structured verdict; list every real problem with severity + evidence.`

phase('Code')
const codeReport = await agent(coderPrompt, { label: 'coder', model: 'opus', effort: 'high' })

phase('Verify')
const verdict = await agent(
  `${verifierPrompt}\n\n=== CODER REPORT (verify, do not trust) ===\n${codeReport}`,
  { label: 'verifier', model: 'opus', effort: 'high', schema: VERDICT_SCHEMA },
)

return { codeReport, verdict }
```

## What makes it work

- **The verifier re-runs everything itself.** Every real defect this pattern has caught came
  from the verifier's own probe, not from reading the coder's report.
- **Boolean gates in the schema.** Forcing `chargedAtMostOnce: true|false` is what turns
  "looks fine" into a NO_SHIP with a reproducible probe.
- **"Prove by running, and say so if you couldn't."** Without this, a verifier that cannot
  reach a database or a model will quietly imply it tested anyway.
- **Explicit lint.** `build` + `check-types` + `test` can all pass while type-aware lint rules
  fail on the same diff.

## Judging

A SHIP is a recommendation, not a merge. Before accepting:

- **Check what the verifier could not run.** "Proven statically" is not "proven".
- **Re-check anything it declared out of scope.** Repo-integration gaps — ignore-config parity,
  a missing root lint override, whether generated output is tracked — sit outside most verifier
  briefs and are a common miss.
- **Read the diff for the thing you would have done differently.** Roughly a third of real
  issues surface here, not in either agent's output.

On NO_SHIP, judge the finding before acting: fix the root cause, not the symptom. If the fix
would add more of the machinery a finding is complaining about, the design is the problem.

## Notes

- Requires the Workflow tool and explicit multi-agent opt-in (say "use a workflow").
- Both agents share one working tree. Run one workflow at a time, or give agents isolated
  worktrees — concurrent builds contend on `dist/`, caches, and lockfiles.
- The coder does not commit. Committing is yours, after judging.
