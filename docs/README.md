# claude-flow docs

Per-plugin reference for the `claude-flow` marketplace. For install/update commands,
the dependency graph, and the non-negotiable regexes, see the root [README](../README.md).

## Plugins

| Plugin | Version | Depends on |
|---|---|---|
| [skills](./skills.md) | 2.0.0 | — |
| [python-suite](./python-suite.md) | 1.0.1 | `skills` |
| [latex-tools](./latex-tools.md) | 0.2.1 | — |
| [jira-dev-workflow](./jira-dev-workflow.md) | 0.7.0 | `skills`, `python-suite`, `latex-tools` |
| [obsidian-vault](./obsidian-vault.md) | 0.1.0 | — |
