# claude-cli-agent-protocol

Guidance for integrating Claude Code CLI in agent/headless mode, including NDJSON streaming and tool approval handling.

## When to use

- Building a host that drives Claude CLI via stream-json.
- Troubleshooting permission prompts, control_request/control_response, or long-lived process handling.

## What it covers

- Required CLI flags for stream-json I/O and approvals.
- NDJSON message types and tool approval protocol.
- Permission modes and process lifecycle guidance.

## Source

See `claude-cli-agent-protocol/SKILL.md` for full instructions and examples.
