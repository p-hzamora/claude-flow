---
status: accepted
---

# One shared Obsidian vault, one folder per area

The Obsidian MCP serves only the vault currently open in Obsidian, so one vault per repo meant switching vaults before every agent call. We use a single vault at `~/Documents/brain/` instead: each repo owns `repos/<repo>/`, other know-how lives in its own top-level folders, and notes link across them with full-path wikilinks.

## Considered options

- **One vault per repo.** Strong isolation on disk, but unreachable unless that vault is open, and cross-area links are hard. Rejected because the MCP limit makes it unusable day to day.

## Consequences

- No filesystem isolation between repos; `vault-writer` is confined to `repos/<repo>/` by convention and its instructions, not by Obsidian.
- Splitting an area into its own vault later means moving its folder. Links from it to notes left behind, and from them back, stop resolving and must be rewritten. The `repos/` prefix is also baked into the agents' write scope.
