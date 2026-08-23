# Writing Style Guide

Use this style for generated prose in `.repo-wiki/` pages.
Goal: keep full technical meaning. Kill fluff.

## Precedence

The repository's own writing convention wins over this guide.
When a `CLAUDE.md`, an `AGENTS.md`, or a style guide in the repository sets a rule, follow that rule.
Without this, each run adjudicates the conflict in private and the pages diverge.

## Default Mode

Default mode is terse, direct prose.
Keep this mode active across generated pages unless a clarity exception applies.

Terse means fewer sentences, not broken ones.
A dropped article makes ownership ambiguous: `Runner owns refund` and `the runner owns the refund` differ when two parties can issue the refund.

## Core Rules

- Keep the article, the subject, and the verb.
- Write one idea in each sentence.
- Drop filler words such as `just`, `really`, `basically`, `actually`, and `simply`.
- Drop pleasantries and conversational padding.
- Drop hedging unless uncertainty is real and important.
- Do not restate what the code already shows.
- Use short words when they preserve meaning.
- Keep technical terms exact.
- Keep code blocks unchanged.
- Quote errors exactly.

## Preferred Shape

Prefer this pattern when it fits:

```text
[thing] [action] [reason]. [next step].
```

Examples:

- `The auth middleware rejects an expired token. The session refresh path retries.`
- `The worker enqueues a billing event after the invoice write. The retry path uses a dead-letter queue.`
- `A feature flag gates the new checkout flow. The old path stays live for rollback.`

## Word Choice

Prefer shorter wording:

- `fix` not `implement a solution for`
- `big` not `extensive`
- `use` not `make use of`
- `help` not `facilitate`

Do not shorten domain terms, identifiers, protocol names, or API names.

## Good vs Bad

Bad:

```text
This subsystem is basically responsible for handling the authentication process in a way that ensures users are properly validated.
```

Good:

```text
The subsystem handles auth. It validates the user identity before it issues a session.
```

Bad:

```text
The issue is likely caused by the middleware creating a new object on each render.
```

Good:

```text
The middleware creates a new object on each render. The new reference triggers a re-run.
```

## Example Transformations

Question: Why does the React component re-render?

- Preferred style: `The component creates a new object reference on each render. An inline object prop is a new reference, so React re-renders. Wrap the object in useMemo.`

Question: Explain database connection pooling.

- Preferred style: `The pool reuses open database connections. The server does not open a connection for each request. This skips the handshake overhead.`

Question: Explain the queue retry path.

- Preferred style: `The worker fails. The queue retries with backoff. At the maximum retry count the message goes to the dead-letter queue.`

## Clarity Exceptions

Use fuller prose for these cases, then resume the terse style:

- security warnings
- irreversible action confirmations
- multi-step sequences where the order could be misread
- places where the reader already showed confusion and needs an explicit answer

Example:

```text
Warning: This operation permanently deletes all rows in `users` and cannot be undone.
```

After a clear warning, resume the terse style.

## Boundaries

- Keep code, commands, identifiers, and quoted errors exact.
- Do not shorten a sentence when the shorter form becomes ambiguous.
- Do not use compressed abbreviations unless the repository already uses them.
- Do not apply this style to commit messages, PR titles, or code samples unless explicitly asked.
