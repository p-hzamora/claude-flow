# Codex agent profiles

Codex discovers project profiles from `.codex/agents/*.toml`. These profiles mirror
the names and responsibilities of the Claude Code agents, but contain only
Codex-specific configuration. Their operating knowledge remains in the shared plugin
skills, so it is not copied between hosts.

Open this repository in Codex to load these profiles automatically. To use the same
profiles from another project without creating a second copy, install the required
plugins from this marketplace and symlink this directory into that project:

```sh
mkdir -p /path/to/project/.codex
ln -s /absolute/path/to/claude-flow/.codex/agents /path/to/project/.codex/agents
```

Then ask Codex to delegate to a profile by name, for example: "use the
`ddd-reviewer` agent to review the orders module." The profile inherits the parent
model and permissions unless it explicitly sets a read-only sandbox.

Codex plugins currently distribute skills and integrations; custom agent profiles are
project/user configuration rather than a plugin-manifest component. Keeping these
profiles in the repository and linking them gives the team one versioned source while
respecting that boundary.
