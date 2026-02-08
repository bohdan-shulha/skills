---
name: claude-cli-agent-protocol
description: >-
  Guidance for integrating Claude Code CLI in headless/agent mode using stream-json NDJSON: required flags, replay semantics, partial stream_event handling, control_request/control_response approvals, control cancellation/interrupt flows, and runtime liveness mapping. Use when building or debugging hosts that drive Claude CLI and must keep UI state accurate (thinking/pending/streaming/approval/result).
---

# Claude CLI Agent Protocol

## Overview

Integrate Claude Code CLI via NDJSON in a way that preserves true runtime state in the host UI:
- parse all relevant stdout message types
- send correctly shaped stdin control messages
- handle replay and partial-stream behavior explicitly
- keep interrupt and approval flows consistent

This skill is optimized for host builders who need reliable liveness, queueing, replay dedup, and approval UX.

## Required CLI Flags

```bash
claude \
  -p \
  --output-format stream-json \
  --input-format stream-json \
  --verbose \
  --permission-prompt-tool stdio
```

Optional but important:
- `--replay-user-messages`
  - Re-emits user stdin messages on stdout for acknowledgment.
  - Echoed user messages include `isReplay`, `uuid`, and `parent_tool_use_id`.
- `--include-partial-messages`
  - Required if your host expects `stream_event` partial deltas (`message_start`, `content_block_delta`, etc.).
  - Without this flag, many runs emit only final `assistant` + `result` turn outputs.

Important flag constraints:
- `--input-format=stream-json` requires `--output-format=stream-json`.
- `--replay-user-messages` requires stream-json input and output.
- `--include-partial-messages` works with `--print` and stream-json output.
- Do not rely on prompt positional arg when building a long-lived host; send `user` envelopes via stdin.

## Protocol Shape (NDJSON)

All messages are newline-delimited JSON objects with top-level `type`.

For streaming, the runtime envelope is:

```json
{
  "type": "stream_event",
  "event": {
    "type": "content_block_delta",
    "index": 0,
    "delta": {"type": "text_delta", "text": "chunk"}
  }
}
```

Do not assume top-level `content_block_delta` envelopes in host parsing.

---

# Emission Semantics (Critical)

## Partial output behavior

- With `--include-partial-messages`: host receives `stream_event` payloads.
- Without it: host often receives only final `assistant` and `result` messages.

Host impact:
- If UI "Thinking/Writing" depends only on partial deltas, it may appear idle/blank unless `--include-partial-messages` is enabled.

## Replay behavior

With `--replay-user-messages`, echoed user messages include replay markers:

```json
{
  "type": "user",
  "message": {"role": "user", "content": [{"type": "text", "text": "ping"}]},
  "session_id": "...",
  "parent_tool_use_id": null,
  "uuid": "...",
  "isReplay": true
}
```

Host rule:
- Deduplicate using `uuid` (plus turn/session context if needed).

## Result semantics

`result.subtype == "success"` does not mean no error by itself.
Always evaluate `is_error` as authoritative:

```json
{
  "type": "result",
  "subtype": "success",
  "is_error": true,
  "result": "Not logged in - Please run /login"
}
```

This can also accompany non-zero process exit status.

---

# Request Lifecycles

## Normal request (init -> response -> result)

1. Host starts process.
2. CLI emits `system` `subtype:init`.
3. Host sends `user` stdin message.
4. CLI may emit `stream_event` messages (if partial enabled).
5. CLI emits `assistant` message(s).
6. CLI may emit `control_request` (tool approval).
7. Host sends `control_response`.
8. CLI emits `user` tool_result echoes.
9. CLI emits terminal `result`.

## Interrupted request

Preferred:
1. Host sends stdin `control_request` with `request.subtype: "interrupt"`.
2. CLI emits `control_response` success.
3. CLI emits `result` for terminated turn.
4. Host sends next queued `user` message.

## Interrupt during pending tool approval

Two valid strategies:

1. Cancel then interrupt:
- Send `control_cancel_request` for pending `request_id`.
- Send `control_request` interrupt.

2. Deny + interrupt in one response:
- Send `control_response` with `behavior: "deny"` and `interrupt: true`.

Pick one strategy and apply it consistently.

---

# Stdout Message Types (CLI -> Host)

These are the host-relevant types to parse.

## `system`

Common subtypes:
- `init`
- `status`
- `informational`
- `api_error`
- `hook_started`
- `hook_progress`
- `hook_response`
- `stop_hook_summary`
- `task_notification`
- `turn_duration`
- `compact_boundary`
- `microcompact_boundary`
- `local_command`

Typical `init` fields include: `cwd`, `session_id`, `tools`, `mcp_servers`, `model`, `permissionMode`, `slash_commands`, `claude_code_version`, `agents`, `skills`, `plugins`, `uuid`.

## `assistant`

Contains complete assistant message blocks:
- `text`
- `tool_use`
- `thinking` (if enabled)

May include `parent_tool_use_id` for subagent/tool-threaded messages.

## `user`

Used for:
- tool result echo blocks (`type: tool_result`)
- replayed user echo events when replay flag is enabled (`isReplay: true`)

## `stream_event`

Contains nested `event` payload.

Event types:
- `message_start`
- `content_block_start`
- `content_block_delta`
- `content_block_stop`
- `message_delta`
- `message_stop`

Observed delta types:
- `text_delta`
- `input_json_delta`
- `thinking_delta`
- `signature_delta`
- `citations_delta`

## `control_request`

Approval or control prompt from CLI, including:
- `request.subtype: "can_use_tool"`
- `request_id`
- tool details (`tool_name`, `input`, `tool_use_id`, optional `decision_reason`)

## `control_response`

Control command acknowledgment emitted by CLI (for host-issued control requests like interrupt/set mode/model).

## `control_cancel_request`

Cancellation signal path exists in protocol surface for pending control requests.
Treat as control-plane event.

## `result`

Terminal turn summary with:
- `subtype`
- `is_error`
- token/cost/turn metadata

Result subtypes:
- `success`
- `error_during_execution`
- `error_max_turns`
- `error_max_budget_usd`
- `error_max_structured_output_retries`

## `keep_alive`

Heartbeat ping message.

## `tool_use_summary`

Optional summarized tool-use event stream for condensed status rendering.

## `auth_status`

Optional authentication status updates.

## `streamlined_text` and `streamlined_tool_use_summary`

Optional condensed output channels. Useful for thin UIs; safe to ignore in fully structured hosts.

## Observed Type and Subtype Surface (2.1.37)

Observed host-facing top-level `type` values (runtime + binary scan):
- `system`
- `assistant`
- `user`
- `stream_event`
- `result`
- `control_request`
- `control_response`
- `control_cancel_request`
- `keep_alive`
- `tool_use_summary`
- `auth_status`
- `streamlined_text`
- `streamlined_tool_use_summary`

Observed protocol-relevant `subtype` values from local 2.1.37 binary:
- `api_error`
- `can_use_tool`
- `compact_boundary`
- `error`
- `error_during_execution`
- `error_max_budget_usd`
- `error_max_structured_output_retries`
- `error_max_turns`
- `hook_callback`
- `hook_progress`
- `hook_response`
- `hook_started`
- `informational`
- `init`
- `interrupt`
- `local_command`
- `mcp_message`
- `microcompact_boundary`
- `status`
- `stop_hook_summary`
- `success`
- `task_notification`
- `turn_duration`

---

# Stdin Message Types (Host -> CLI)

## `user`

```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [{"type": "text", "text": "Your prompt"}]
  },
  "uuid": "optional-client-uuid"
}
```

## `control_request`

```json
{
  "type": "control_request",
  "request_id": "req_123",
  "request": {
    "subtype": "interrupt"
  }
}
```

Supported subtypes (host-facing):
- `interrupt`
- `initialize`
- `set_permission_mode`
- `set_model`
- `set_max_thinking_tokens`
- `mcp_status`
- `mcp_message`
- `mcp_set_servers`
- `mcp_reconnect`
- `mcp_toggle`
- `rewind_files`

## `control_response`

Use for answering `can_use_tool` approval requests.

Allow:

```json
{
  "type": "control_response",
  "response": {
    "subtype": "success",
    "request_id": "req_abc123",
    "response": {
      "behavior": "allow",
      "updatedInput": {"command": "ls -la"}
    }
  }
}
```

Deny:

```json
{
  "type": "control_response",
  "response": {
    "subtype": "success",
    "request_id": "req_abc123",
    "response": {
      "behavior": "deny",
      "message": "User denied"
    }
  }
}
```

Deny + interrupt:

```json
{
  "type": "control_response",
  "response": {
    "subtype": "success",
    "request_id": "req_abc123",
    "response": {
      "behavior": "deny",
      "message": "User denied and wants to stop",
      "interrupt": true
    }
  }
}
```

## `control_cancel_request`

Cancel pending control request by `request_id`.

```json
{
  "type": "control_cancel_request",
  "request_id": "req_abc123"
}
```

---

# Tool Names and Input Fields

Common tool names and key inputs:

| Tool | Input Fields |
|------|--------------|
| `Bash` | `command`, `description`, `timeout`, `run_in_background` |
| `Read` | `file_path`, `offset`, `limit` |
| `Write` | `file_path`, `content` |
| `Edit` | `file_path`, `old_string`, `new_string`, `replace_all` |
| `Glob` | `pattern`, `path` |
| `Grep` | `pattern`, `path`, `glob`, `type`, `output_mode`, `-A`, `-B`, `-C`, `-i`, `-n` |
| `WebFetch` | `url`, `prompt` |
| `WebSearch` | `query`, `allowed_domains`, `blocked_domains` |
| `Task` | `subagent_type`, `description`, `prompt`, `model`, `run_in_background`, `resume` |
| `TaskOutput` | `task_id`, `block`, `timeout` |
| `TaskStop` | `task_id` |
| `NotebookEdit` | `notebook_path`, `new_source`, `cell_id`, `cell_type`, `edit_mode` |
| `AskUserQuestion` | `questions` |
| `EnterPlanMode` | no params |
| `ExitPlanMode` | `allowedPrompts`, `pushToRemote` |
| `Skill` | `skill`, `args` |
| `TaskCreate` | `subject`, `description`, `activeForm`, `metadata` |
| `TaskGet` | `taskId` |
| `TaskUpdate` | `taskId`, `status`, `subject`, `description`, `owner`, `addBlocks`, `addBlockedBy` |
| `TaskList` | no params |

---

# Liveness Mapping for Host UI

Recommended runtime state mapping:
- `process started` -> `starting`
- `system:init` -> `ready`
- `stream_event` or in-flight assistant turn -> `thinking/streaming`
- `control_request can_use_tool` -> `awaiting_approval`
- `result` -> `idle` (or `error` if `is_error=true`)
- process exit / fatal stderr / repeated auth failures -> `disconnected/error`

Always expose last event timestamp so users can trust the session is alive.

---

# Process Interruption

Preferred: protocol interrupt (`control_request` `subtype:interrupt`).

Fallback: OS signal only if protocol interrupt path fails or times out.

```cpp
kill(processId, SIGINT);
process.terminate();
process.waitForFinished(500);
if (process.state() != NotRunning) process.kill();
```

---

# Replay and Partial Handling Rules for Hosts

1. Treat replayed user messages as acknowledgments, not new user intent.
2. Deduplicate by `uuid` before rendering persistent chat bubbles.
3. Merge `stream_event` deltas into one in-progress assistant draft per turn.
4. Replace/complete draft on final `assistant` or `result`.
5. Do not infer completion from lack of partial events if partial streaming is disabled.

---

# Debugging

```bash
DEBUG_CLAUDE_AGENT_SDK=1 claude --debug ...
```

Capture debug logs:

```bash
claude ... --debug --debug-file /tmp/claude-debug.log
```

---

# Protocol Discovery (Installed Binary)

Inspect local type and subtype surfaces for the exact installed version:

```bash
strings /path/to/claude | grep -o 'type:"[a-z_][a-z_]*"' | sort -u
strings /path/to/claude | grep -o 'subtype:"[a-z_][a-z_]*"' | sort -u
```

Sanity-check stream-json runtime quickly:

```bash
tmpid=$(uuidgen | tr '[:upper:]' '[:lower:]')
printf '%s\n' '{"type":"user","message":{"role":"user","content":[{"type":"text","text":"ping"}]},"uuid":"'"$tmpid"'"}' \
| claude -p --output-format stream-json --input-format stream-json --verbose --replay-user-messages --permission-prompt-tool stdio --session-id "$tmpid"
```

---

# References

- Headless mode: https://docs.anthropic.com/en/docs/claude-code/headless
- CLI reference: https://docs.anthropic.com/en/docs/claude-code/cli
