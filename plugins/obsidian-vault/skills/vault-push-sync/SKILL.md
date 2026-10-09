---
name: vault-push-sync
description: Turn the per-repository "update the vault after git push" hook on or off, or show its status. Use when the user wants vault updates after pushing to be enabled, disabled, or checked for the current repo. User-invoked.
---

# Vault push sync

The plugin's `PostToolUse` hook fires after `git push` run through Claude's Bash tool.
It does nothing unless the repo's folder in the vault has `update_on_push: true` in
`repos/<repo>/brain.config.json`. This skill flips that flag; no settings file is edited.

Run from the repository (the script infers `<repo>` from the git root):

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/vault-push-sync.py" on
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/vault-push-sync.py" off
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/vault-push-sync.py" status
```

- `on` creates `repos/<repo>/brain.config.json` (and the folder) in the vault when
  missing. The user must have `~/Documents/brain` (or `$BRAIN_VAULT`) open as the vault in Obsidian.
- `off` sets the flag to false and keeps the notes.
- When the hook fires and Obsidian is unreachable, the user is told to start it and
  nothing is queued; the next successful run reads commits since `last_pushed_sha`.
- Pushes made outside Claude's Bash tool are not seen. Ask `vault-writer` to update the
  vault manually in that case.

Report the script's output verbatim.

## Review Checklist

- [ ] The script ran from inside the target repository and its output was reported verbatim.
- [ ] After `on`, the user was reminded that the vault must be open in Obsidian.
