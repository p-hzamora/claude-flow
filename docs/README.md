# claude-flow docs

Per-plugin reference for the `claude-flow` marketplace. For install/update commands,
the dependency graph, and the non-negotiable regexes, see the root [README](../README.md).

## Plugins

| Plugin | Version | Depends on |
|---|---|---|
| [skills](./skills.md) | 0.1.0 | — |
| [python-suite](./python-suite.md) | 0.1.0 | `skills` |
| [jira-dev-workflow](./jira-dev-workflow.md) | 0.1.0 | `skills`, `python-suite` |
