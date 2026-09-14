---
name: claude-sdk-expert
description: Claude Agent SDK reference and expert guidance. Trigger with /claude-sdk. Use when writing, debugging, or reviewing Python or TypeScript agents built with claude-agent-sdk or @anthropic-ai/claude-agent-sdk. Spawn the claude-sdk-expert agent for deeper analysis or implementation help.
---

# Claude Agent SDK — Expert Skill

When this skill is active, answer Claude Agent SDK questions directly using the reference below. For tasks that involve writing, editing, or reviewing actual agent code, spawn the `claude-sdk-expert` agent.

## Quick Reference

### Install

```bash
pip install claude-agent-sdk          # Python ≥ 3.10
npm install @anthropic-ai/claude-agent-sdk  # TypeScript
```

### Minimal agent

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import ResultMessage

async def main() -> None:
    async for msg in query(
        prompt="What files are in this directory?",
        options=ClaudeAgentOptions(allowed_tools=["Glob"]),
    ):
        if isinstance(msg, ResultMessage):
            print(msg.result)

asyncio.run(main())
```

### Message types

| Type | When |
|------|------|
| `SystemMessage` (subtype `"init"`) | Session start — contains `session_id` |
| `AssistantMessage` | Claude's text and tool calls |
| `ResultMessage` | Final answer — `msg.result` |
| `StreamEvent` | Low-level streaming events |
| `RateLimitEvent` | Rate limit hit |

### ClaudeAgentOptions

```python
ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Bash"],
    permission_mode="acceptEdits",   # default | acceptEdits | bypassPermissions | plan
    system_prompt="...",
    cwd="/project",
    resume="<session-id>",
    hooks={"PostToolUse": [HookMatcher(matcher="Edit", hooks=[my_hook])]},
    agents={"name": AgentDefinition(description="...", prompt="...", tools=[...])},
    mcp_servers={"pg": {"command": "npx", "args": ["@mcp/server-postgres", "...url"]}},
)
```

### Hooks

```python
from claude_agent_sdk import HookMatcher

async def my_hook(input_data, tool_use_id, context) -> dict:
    # return {} to continue
    # return {"block": True, "reason": "..."} to block (PreToolUse only)
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse":  [HookMatcher(matcher="Bash",       hooks=[my_hook])],
        "PostToolUse": [HookMatcher(matcher="Edit|Write",  hooks=[my_hook])],
    }
)
```

### Sessions (resume)

```python
from claude_agent_sdk.types import SystemMessage

session_id = None
async for msg in query(prompt="Read auth.py", options=ClaudeAgentOptions(allowed_tools=["Read"])):
    if isinstance(msg, SystemMessage) and msg.subtype == "init":
        session_id = msg.data["session_id"]

# Later — full context preserved
async for msg in query(
    prompt="Now find all callers",
    options=ClaudeAgentOptions(resume=session_id),
):
    ...
```

### Subagents

```python
from claude_agent_sdk import AgentDefinition

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Glob", "Agent"],   # Agent required
    agents={
        "reviewer": AgentDefinition(
            description="Reviews code for quality and security.",
            prompt="Analyze code quality, flag OWASP issues.",
            tools=["Read", "Glob", "Grep"],
        )
    },
)
```

### MCP servers

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]},
    }
)
```

## Spawning the claude-sdk-expert agent

Use the `claude-sdk-expert` agent when the task requires:
- Writing or reviewing actual agent files
- Debugging why an agent behaves incorrectly
- Designing a multi-agent architecture
- Integrating MCP servers or hooks

The agent has `Read`, `Write`, `Edit`, `Glob`, `Grep`, and `WebFetch` access.

## Common Pitfalls

- **Never** break out of the `async for` loop early — the agent loop won't finish
- Always include `"Agent"` in `allowed_tools` when using `agents={...}`
- Hooks must be `async` — no blocking I/O inside them
- `resume=session_id` option must not be combined with `system_prompt` or `allowed_tools` from the original call
- `claude-agent-sdk` latest stable: `0.2.x` (PyPI); docs at https://code.claude.com/docs/en/agent-sdk

## Review Checklist

- [ ] The SDK version, API surface, and runtime assumptions were verified against current official documentation.
- [ ] Agent iteration, async hooks, and cancellation can run to their intended terminal state.
- [ ] Allowed tools, MCP integrations, and subagent permissions are least-privilege and explicitly configured.
- [ ] Session resume, state, and error handling match the SDK constraints documented above.
