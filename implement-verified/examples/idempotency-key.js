export const meta = {
  name: 'payments-idempotency-key',
  description: 'Add an idempotency key to the payments charge endpoint, adversarially verified',
  phases: [
    { title: 'Code', detail: 'add the key, the unique index, and the replay path' },
    { title: 'Verify', detail: 'prove a retried request charges at most once, under concurrency' },
    { title: 'Fix', detail: 'one bounded remediation round, only on blockers' },
  ],
}

const REPO = '/Users/bohdan/Projects/acme'

const SPEC = `
POST /payments/charge accepts an Idempotency-Key header. A repeat of the same key with the
same body returns the original response and does NOT create a second charge. A repeat with a
different body returns 422.

INVARIANT: for any one idempotency key, at most one charge row and at most one call to the
payment provider ever occur.
FAILURE SCENARIO: two identical requests with the same key arrive concurrently, both miss the
"already seen?" read, and both insert a charge — the customer is billed twice.
`

const GREEN = `
pnpm --filter @acme/payments build
pnpm --filter @acme/payments check-types
pnpm --filter @acme/payments test
pnpm --filter @acme/payments lint
`

const CONVENTIONS = `
- Read CLAUDE.md / AGENTS.md at the repo root and in the packages you touch before writing
  code. They are binding: YAGNI, delete dead code fully, no unnecessary comments. NEVER add
  eslint-disable / @ts-ignore / @ts-expect-error — fix the real issue.
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

const coderPrompt = `You are the CODER in ${REPO}.

## Spec
${SPEC}

The endpoint currently charges on every request. Retries from the mobile client after a
network timeout are the reported source of double charges. The decided design is a unique
index on the key plus insert-first, so the database — not a read — is what arbitrates.

${CONVENTIONS}

## Read first
- packages/payments/src/routes/charge.ts — the endpoint being changed
- packages/payments/src/routes/refund.ts — mirror its error mapping and handler shape
- packages/payments/migrations/ — follow the existing migration naming and style

## Build
1. Migration: idempotency_records(key TEXT PRIMARY KEY, request_hash TEXT NOT NULL,
   response_body JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()).
2. In the charge handler, INSERT the record BEFORE calling the provider. A unique-violation
   means the key was already used: load the stored record, compare request_hash, return the
   stored response on a match and 422 on a mismatch.
3. A missing Idempotency-Key header keeps the current behavior. Do not invent a default.
4. Tests: replay returns the stored response, mismatched body returns 422, and the provider
   is called exactly once across both requests.

## Prove green (run each SEPARATELY)
${GREEN}
- Type-checking does NOT catch lint's type-aware rules. Run lint explicitly.

Report every file added/changed/deleted and all command outputs.`

const VERDICT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['verdict', 'chargedAtMostOnce', 'provenUnderConcurrency', 'lintRun', 'findings', 'greenSummary'],
  properties: {
    verdict: { enum: ['SHIP', 'NO_SHIP'] },
    chargedAtMostOnce: {
      type: 'boolean',
      description: 'true iff one key produced at most one charge row and one provider call',
    },
    provenUnderConcurrency: {
      type: 'boolean',
      description: 'true iff you ran concurrent identical requests against a real database, not a mock',
    },
    lintRun: {
      type: 'boolean',
      description: 'true iff you personally ran lint on every touched package and it passed',
    },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['severity', 'area', 'detail', 'evidence'],
        properties: {
          severity: { enum: ['blocker', 'major', 'minor', 'nit'] },
          area: { type: 'string' },
          detail: { type: 'string' },
          evidence: { type: 'string', description: 'file:line or command output proving it' },
        },
      },
    },
    greenSummary: { type: 'string' },
  },
}

const verifierPrompt = `You are the ADVERSARIAL VERIFIER in ${REPO}. Another agent just made
changes (its report is appended). Be skeptical — verify against the SPEC below, against the
CODE, and against your OWN command output. Never against the appended report's claims.

## Spec you are verifying against (authoritative)
${SPEC}

Derive the change set YOURSELF: \`git status --porcelain\` and \`git diff\`. Do not rely on
the appended file list — an unreported change is exactly what you are looking for.
GIT: read-only only. NEVER stash/reset/checkout/restore/clean/commit/mv.

Prove each with evidence:
1. The INVARIANT holds and the FAILURE SCENARIO cannot happen. PROVE IT BY RUNNING: start the
   test database, fire at least 20 concurrent identical charge requests with one key, then
   count charge rows and provider calls. A green unit suite proves nothing here — a
   check-then-insert that passes every serial test still double-charges under concurrency.
2. A different-body replay returns 422, and a request with no Idempotency-Key still behaves
   as it did before. Refunds and the rest of the payments package are untouched and green.
3. CONVENTIONS: no suppressions; architecture rules respected; YAGNI (no speculative extras
   such as key expiry, cleanup jobs, or config knobs nobody asked for).
4. GREEN: independently run each of these and report the ACTUAL output:
${GREEN}
   Any red = NO_SHIP. Skipping lint = NO_SHIP.

Ask what would break in production, not whether the code looks good.

If you could not exercise something live (no database, no provider sandbox), SAY SO
explicitly in greenSummary and set provenUnderConcurrency false. Do NOT fabricate a pass.

Return the structured verdict; list every real problem with severity + evidence.`

const fixerPrompt = (blockers) => `You are the FIXER in ${REPO}. The verifier rejected the
change. Address every blocker below.

## Spec
${SPEC}

## Blockers
${JSON.stringify(blockers, null, 2)}

${CONVENTIONS}

Fix the ROOT CAUSE, not the symptom. If a fix would require adding more of the machinery a
finding is complaining about, the design is the problem — STOP and report that instead of
implementing it.

Re-run green (each SEPARATELY) and report the actual output:
${GREEN}`

phase('Code')
const codeReport = await agent(coderPrompt, { label: 'coder', effort: 'high' })

phase('Verify')
let verdict = await agent(
  `${verifierPrompt}\n\n=== CODER REPORT (verify, do not trust) ===\n${codeReport}`,
  { label: 'verifier', effort: 'high', schema: VERDICT_SCHEMA },
)

let fixReport = null
const blockers = verdict.findings.filter((f) => f.severity === 'blocker')
if (verdict.verdict === 'NO_SHIP' && blockers.length) {
  phase('Fix')
  fixReport = await agent(fixerPrompt(blockers), { label: 'fixer', effort: 'high' })
  verdict = await agent(
    `${verifierPrompt}\n\n=== FIXER REPORT (verify, do not trust) ===\n${fixReport}`,
    { label: 'verifier-2', phase: 'Fix', effort: 'high', schema: VERDICT_SCHEMA },
  )
}

return { codeReport, fixReport, verdict }
