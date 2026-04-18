# Writing Style Guide

Use this style for generated prose in `.repo-wiki/` pages.
Goal: keep full technical meaning. Kill fluff.

## Default Mode

Default mode is terse, direct, fragment-friendly prose.
Keep this mode active across generated pages unless a clarity exception applies.

## Core Rules

- Drop articles when sentence still reads clearly.
- Drop filler words such as `just`, `really`, `basically`, `actually`, and `simply`.
- Drop pleasantries and conversational padding.
- Drop hedging unless uncertainty is real and important.
- Fragments are fine.
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

- `Auth middleware reject expired token. Session refresh path handle retry.`
- `Worker enqueue billing event after invoice write. Retry path use dead-letter queue.`
- `Feature flag gate new checkout flow. Old path stay live for rollback.`

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
Subsystem handle auth. Validate user identity before session issue.
```

Bad:

```text
The issue is likely caused by the middleware creating a new object on each render.
```

Good:

```text
Middleware create new object each render. New ref trigger re-run.
```

## Example Transformations

Question: Why React component re-render?

- Preferred style: `New object ref each render. Inline object prop = new ref = re-render. Wrap in useMemo.`

Question: Explain database connection pooling.

- Preferred style: `Pool reuse open DB connections. No new connection per request. Skip handshake overhead.`

Question: Explain queue retry path.

- Preferred style: `Worker fail. Queue retry with backoff. Max retry hit -> dead-letter queue.`

## Clarity Exceptions

Use normal prose for these cases, then resume terse style:

- security warnings
- irreversible action confirmations
- multi-step sequences where fragment order could be misread
- places where reader already showed confusion and needs explicit clarification

Example:

```text
Warning: This operation permanently deletes all rows in `users` and cannot be undone.
```

After clear warning, resume terse style.

## Boundaries

- Keep code, commands, identifiers, and quoted errors exact.
- Do not force fragments into places where meaning gets worse.
- Do not use compressed abbreviations unless repository already uses them.
- Do not apply this style to commit messages, PR titles, or code samples unless explicitly asked.
