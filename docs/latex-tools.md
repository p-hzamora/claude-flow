# latex-tools

Document-agnostic LaTeX authoring, including structured Markdown-to-LaTeX source
generation and verified PDF export.

**Version:** 0.2.1
**Dependencies:** none

Every shared skill has a task-specific `Review Checklist` that agents complete before
reporting applicable work done.

**Codex:** the portable `latex-expertise` skill is packaged through
`../plugins/latex-tools/.codex-plugin/plugin.json`. The matching project-scoped Codex
role adapters remain in [`../.codex/agents/`](../.codex/agents/). Matching
Claude/Codex agent definitions carry the same unique routing phrases.

## Agent

| Agent | Responsibility | Codex routing phrases |
|---|---|---|
| `markdown-to-latex-author` | Preserves approved structured Markdown while producing an organized root LaTeX document and generated content source for a later export. | `convert Markdown to LaTeX`; `author LaTeX source` |
| `latex-2-pdf-exporter` | Compiles an approved root LaTeX document into a verified PDF without editing its content or design. | `compile a LaTeX PDF`; `verify PDF output` |

## Skill

| Skill | Path |
|---|---|
| `latex-expertise` | `skills/latex-expertise/SKILL.md` — document-agnostic LaTeX editing, review, Markdown-source generation, and compilation guidance; preserves the existing source's design system and build setup. |

## Script

| Script | Path |
|---|---|
| `compile-latex.sh` | `scripts/compile-latex.sh` — selects the appropriate engine and compiles the requested root document with `latexmk`. |

## Asset

| Asset | Path |
|---|---|
| `markdown-report.tex` | `assets/markdown-report.tex` — bundled minimal report template, used only when a caller explicitly approves it because no existing template is available. |

## Install

```
/plugin install latex-tools
```
