---
name: claude-cli-agent-protocol
description: >-
  Guidance for integrating Claude Code CLI in agent/headless mode: required stream-json flags, NDJSON protocol, control_request/control_response tool approvals, and process management. Use when building a host that drives Claude CLI or troubleshooting permission prompts and tool approvals.
---

# Claude CLI Agent Protocol

## Overview

Enable reliable, bidirectional integration with Claude Code CLI via NDJSON, including tool approval handling, permission mode control, and long-lived process management.

## Required CLI Flags

```bash
claude \
  --output-format stream-json \
  --input-format stream-json \
  --verbose \
  --permission-prompt-tool stdio
```

Notes:
- `--permission-prompt-tool stdio` enables control_request/control_response for tool approvals
- `--verbose` includes system messages, hook events, and stream events
- `--replay-user-messages` echoes user messages back on stdout for acknowledgment
- Do not use `-p` with a prompt; send user messages via stdin

## Message Protocol (NDJSON)

All stdin/stdout messages are newline-delimited JSON with a `type` field.

---

# Request Lifecycles

## Normal Request (Init → Result)

```
Host                                      CLI
  │                                         │
  │  ──── Start process with flags ────►    │
  │                                         │
  │  ◄──── system {subtype: "init"} ──────  │
  │                                         │
  │  ──── user message ───────────────►     │
  │                                         │
  │  ◄──── stream_event (deltas) ─────────  │
  │  ◄──── assistant ─────────────────────  │
  │                                         │
  │  ◄──── control_request ───────────────  │  (tool approval)
  │        {subtype: "can_use_tool"}        │
  │                                         │
  │  ──── control_response ───────────►     │
  │       {behavior: "allow"}               │
  │                                         │
  │  ◄──── user {tool_result} ────────────  │
  │  ◄──── assistant (final) ─────────────  │
  │                                         │
  │  ◄──── result {subtype: "success"} ───  │
  │                                         │
  │  ──── user message (next turn) ────►    │  (process stays alive)
```

**Sequence:**
1. `system` (init) — session info, tools, model
2. Host sends `user` message
3. `stream_event` messages (real-time deltas)
4. `assistant` message (complete response with tool_use blocks)
5. `control_request` for each tool needing approval
6. Host sends `control_response` (allow/deny)
7. `user` message (tool results echoed back)
8. More `assistant` messages if multi-turn
9. `result` — turn complete, cost/usage data

## Interrupted Request

```
Host                                      CLI
  │                                         │
  │  ◄──── system {subtype: "init"} ──────  │
  │                                         │
  │  ──── user message ───────────────►     │
  │       "Refactor entire codebase"        │
  │                                         │
  │  ◄──── stream_event ──────────────────  │
  │  ◄──── assistant ─────────────────────  │
  │  ◄──── control_request (tool) ────────  │
  │  ──── control_response (allow) ────►    │
  │  ◄──── user {tool_result} ────────────  │
  │  ◄──── stream_event ──────────────────  │  (working...)
  │                                         │
  │  ════ USER INTERRUPTS ════              │
  │                                         │
  │  ──── control_request ────────────►     │
  │       {subtype: "interrupt"}            │
  │                                         │
  │  ◄──── control_response ──────────────  │
  │        {subtype: "success"}             │
  │                                         │
  │  ◄──── result ────────────────────────  │  (turn ends)
  │                                         │
  │  ──── user message ───────────────►     │  (new instruction)
  │       "Actually, just fix the bug"      │
  │                                         │
  │  ◄──── stream_event ──────────────────  │
  │  ◄──── assistant ─────────────────────  │
  │  ◄──── result {subtype: "success"} ───  │
```

**Key points:**
- Interrupt is graceful — process stays alive, context preserved
- CLI acknowledges with `control_response`
- `result` emitted after interrupt (partial work visible in prior messages)
- Send new `user` message to redirect agent

## Interrupt During Tool Approval

If a `control_request` (can_use_tool) is pending when you want to interrupt:

```
Host                                      CLI
  │                                         │
  │  ◄──── control_request ───────────────  │  (waiting for approval)
  │        {request_id: "req_001"}          │
  │                                         │
  │  ──── control_cancel_request ─────►     │  (cancel the approval)
  │       {request_id: "req_001"}           │
  │                                         │
  │  ──── control_request ────────────►     │  (then interrupt)
  │       {subtype: "interrupt"}            │
  │                                         │
  │  ◄──── control_response ──────────────  │
  │  ◄──── result ────────────────────────  │
```

---

# Stdout Message Types (CLI → Host)

## `system` - Session and Status Messages

| Subtype | Description |
|---------|-------------|
| `init` | Session initialization with model, tools, session_id, cwd |
| `api_error` | API error occurred |
| `informational` | Informational message |
| `status` | Status update |
| `hook_started` | Hook execution started |
| `hook_progress` | Hook execution progress |
| `hook_response` | Hook execution response |
| `stop_hook_summary` | Summary when hooks are stopped |
| `task_notification` | Background task notification |
| `turn_duration` | Turn timing information |
| `compact_boundary` | Context compaction boundary |
| `microcompact_boundary` | Micro-compaction boundary |
| `local_command` | Local slash command execution |

Example `init`:
```json
{
  "type": "system",
  "subtype": "init",
  "session_id": "abc123",
  "cwd": "/path/to/project",
  "model": "claude-sonnet-4-20250514",
  "tools": [{"name": "Bash", "type": "computer_use"}, ...]
}
```

## `assistant` - Claude's Response

```json
{
  "type": "assistant",
  "message": {
    "id": "msg_xxx",
    "role": "assistant",
    "content": [
      {"type": "text", "text": "Here's the solution..."},
      {"type": "tool_use", "id": "toolu_xxx", "name": "Bash", "input": {"command": "ls"}}
    ],
    "usage": {"input_tokens": 100, "output_tokens": 50}
  },
  "parent_tool_use_id": null,
  "session_id": "abc123"
}
```

Content block types:
- `text` - Text content with `text` field
- `tool_use` - Tool invocation with `id`, `name`, `input`
- `thinking` - Extended thinking content (when enabled)

## `user` - Tool Results

Echoed when tool execution completes:
```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {"type": "tool_result", "tool_use_id": "toolu_xxx", "content": "output here"}
    ]
  }
}
```

## `stream_event` - Streaming Events

Real-time content deltas during generation:
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

Event types:
- `message_start` - Message generation started
- `content_block_start` - New content block
- `content_block_delta` - Content chunk (text_delta, input_json_delta)
- `content_block_stop` - Content block complete
- `message_delta` - Message-level updates (stop_reason, usage)
- `message_stop` - Message complete

## `result` - Completion Message

| Subtype | Description |
|---------|-------------|
| `success` | Successful completion |
| `error_during_execution` | Error during tool execution |
| `error_max_turns` | Maximum turns exceeded |
| `error_max_budget_usd` | Budget limit exceeded |
| `error_max_structured_output_retries` | Structured output validation failed |

Example:
```json
{
  "type": "result",
  "subtype": "success",
  "duration_ms": 5000,
  "duration_api_ms": 4500,
  "num_turns": 3,
  "total_cost_usd": 0.05,
  "usage": {"input_tokens": 1000, "output_tokens": 500},
  "session_id": "abc123",
  "is_error": false
}
```

## `control_request` - Approval Required

Sent when CLI needs host approval (tool execution, etc.):
```json
{
  "type": "control_request",
  "request_id": "req_abc123",
  "request": {
    "subtype": "can_use_tool",
    "tool_name": "Bash",
    "input": {"command": "rm -rf /tmp/test", "description": "Delete test files"},
    "tool_use_id": "toolu_xyz"
  }
}
```

## `keep_alive` - Connection Ping

```json
{"type": "keep_alive"}
```

---

# Stdin Message Types (Host → CLI)

## `user` - Send User Message

```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [{"type": "text", "text": "Your prompt here"}]
  },
  "uuid": "optional-unique-id"
}
```

## `control_request` - Host Control Commands

| Subtype | Description | Response |
|---------|-------------|----------|
| `interrupt` | Abort current operation | `success` |
| `initialize` | Initialize with SDK MCP servers | `success` with init info |
| `set_permission_mode` | Change mode (plan, default, etc.) | `success` |
| `set_model` | Change model | `success` |
| `set_max_thinking_tokens` | Set thinking token limit | `success` |
| `mcp_status` | Get MCP server status | `success` with `mcpServers` |
| `mcp_message` | Send message to MCP server | `success` |
| `mcp_set_servers` | Configure MCP servers | `success` with result |
| `mcp_reconnect` | Reconnect to MCP server | `success` or `error` |
| `mcp_toggle` | Enable/disable MCP server | `success` or `error` |
| `rewind_files` | Rewind file changes | `success` with result |

### Interrupt Example

Send:
```json
{
  "type": "control_request",
  "request_id": "int_001",
  "request": {"subtype": "interrupt"}
}
```

Receive:
```json
{
  "type": "control_response",
  "response": {
    "subtype": "success",
    "request_id": "int_001",
    "response": {}
  }
}
```

### Set Permission Mode Example

```json
{
  "type": "control_request",
  "request_id": "mode_001",
  "request": {
    "subtype": "set_permission_mode",
    "mode": "plan"
  }
}
```

Modes: `default`, `plan`, `bypassPermissions`, `acceptEdits`

### Set Model Example

```json
{
  "type": "control_request",
  "request_id": "model_001",
  "request": {
    "subtype": "set_model",
    "model": "claude-opus-4-20250514"
  }
}
```

## `control_response` - Tool Approval Response

When CLI sends `control_request` with `subtype: "can_use_tool"`:

**Allow** (must include `updatedInput`):
```json
{
  "type": "control_response",
  "response": {
    "subtype": "success",
    "request_id": "req_abc123",
    "response": {
      "behavior": "allow",
      "updatedInput": {"command": "ls -la", "description": "List files"}
    }
  }
}
```

**Deny** (must include `message`):
```json
{
  "type": "control_response",
  "response": {
    "subtype": "success",
    "request_id": "req_abc123",
    "response": {
      "behavior": "deny",
      "message": "User denied this action"
    }
  }
}
```

**Error**:
```json
{
  "type": "control_response",
  "response": {
    "subtype": "error",
    "request_id": "req_abc123",
    "error": "Timeout waiting for user"
  }
}
```

## `control_cancel_request` - Cancel Pending Request

Cancels a pending `control_request` (e.g., tool approval timeout). **No response is sent.**

```json
{
  "type": "control_cancel_request",
  "request_id": "req_abc123"
}
```

---

# Tool Names and Input Fields

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
| `AskUserQuestion` | `questions` array |
| `EnterPlanMode` | (no params) |
| `ExitPlanMode` | `allowedPrompts`, `pushToRemote` |
| `Skill` | `skill`, `args` |
| `TaskCreate` | `subject`, `description`, `activeForm`, `metadata` |
| `TaskGet` | `taskId` |
| `TaskUpdate` | `taskId`, `status`, `subject`, `description`, `owner`, `addBlocks`, `addBlockedBy` |
| `TaskList` | (no params) |

---

# Process Interruption

Two mechanisms exist:

## 1. Protocol-based Interrupt (Recommended)

Send `control_request` with `subtype: "interrupt"`:
```json
{
  "type": "control_request",
  "request_id": "int_001",
  "request": {"subtype": "interrupt"}
}
```

This aborts the current operation and receives a `control_response` confirmation.

## 2. OS Signal (Fallback)

```cpp
// Send SIGINT for graceful abort
kill(m_process->processId(), SIGINT);

// Or terminate then kill
m_process->terminate();  // SIGTERM
m_process->waitForFinished(500);
if (m_process->state() != QProcess::NotRunning)
    m_process->kill();  // SIGKILL
```

---

# Subagent Protocol

The `Task` tool spawns subagents. Track responses via `parent_tool_use_id`:

```json
{
  "type": "assistant",
  "parent_tool_use_id": "toolu_abc",
  "message": {"content": [...]}
}
```

---

# Cost Tracking

The `result` message includes:
- `total_cost_usd` - Total API cost
- `usage` - Token counts (input_tokens, output_tokens, cache_read_input_tokens)
- `permission_denials` - List of denied tool actions

---

# Debugging

```bash
DEBUG_CLAUDE_AGENT_SDK=1 claude --debug ...
```

---

# SDK Protocol Discovery

Inspect the TypeScript SDK for undocumented behaviors:

```bash
cd /tmp && npm pack @anthropic-ai/claude-code && tar -xzf *.tgz

# Find message types
grep -o 'type:"[^"]*"' package/cli.js | sort -u

# Find subtypes
grep -o 'subtype:"[^"]*"' package/cli.js | sort -u

# Find control request handling
rg 'request\.subtype===' package/cli.js
```

---

# References

- Headless mode: https://docs.anthropic.com/en/docs/claude-code/headless
- CLI reference: https://docs.anthropic.com/en/docs/claude-code/cli
