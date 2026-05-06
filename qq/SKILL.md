---
name: qq
description: 'Manual read-only Q&A. Answer question using inspection only: no edits, writes, patches, git changes, or clarifying questions.'
disable-model-invocation: true
---

Answer directly, keep it concise, use existing context first, then read, search, or run only non-mutating inspection if needed. If something cannot be verified without changing workspace, say so and state assumptions or limits in chat.

Never edit, create, rename, or delete files. Never apply patches, write to workspace, change git state, run mutating terminal commands, ask clarifying questions, or drift from analysis into implementation unless user explicitly leaves read-only mode.