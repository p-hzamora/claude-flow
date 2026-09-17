---
name: latex-expertise
description: Edit, review, and troubleshoot LaTeX documents while preserving their existing design system, macros, and build setup. Use when changing .tex content, converting approved structured Markdown into LaTeX source, layout, commands, packages, or compilation-related errors; not for PDF-only edits.
---

# LaTeX expertise

Make the smallest change that meets the requested document update. Treat the existing
`.tex` source as the authority for its visual system and command interface. This skill
does not assume a document type, audience, or domain.

## Workflow

1. For an existing document, inspect its root, document class, preamble, included files, custom commands, and build configuration before editing. For approved Markdown that starts a new document, inspect the selected LaTeX template before generating source.
2. Reuse the template's section, entry, spacing, and hyperlink macros. Do not replace the design system or change the document engine unless the request requires it.
3. Keep editable content separate from presentation commands whenever the document
   already supports that separation. Escape LaTeX-special characters in literal text
   and preserve balanced braces and environments.
4. Compile after meaningful changes. When this plugin is installed, use its compiler
   helper rather than rebuilding its engine-selection logic. In Claude Code, invoke:

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/compile-latex.sh path/to/document.tex
   ```

5. If compilation fails, read the first actionable error (usually marked `!` or given as `file:line`) and fix its cause before pursuing downstream messages. Keep the `.log` file available for diagnosis.

When an approved Markdown file is the editorial source, preserve it and create an
organized root `.tex` document plus generated content source before PDF export. Prefer
a supplied template; use the bundled minimal report template only with explicit caller
approval. Read [the Markdown-source guide](references/markdown-source.md) for this
workflow.

Read [the LaTeX document guide](references/latex-document-guide.md) when editing or
diagnosing a document. It contains practical source, typography, and build guidance.

## Review Checklist

- [ ] The root document, class, preamble, included files, and existing build setup were inspected before editing.
- [ ] Existing commands, environments, and typography conventions were reused where applicable.
- [ ] When Markdown is the source, it remains available and its semantic structure was mapped without silently omitting content.
- [ ] Literal content has valid LaTeX escaping and balanced delimiters/environments.
- [ ] The correct root document was compiled after meaningful changes, or compilation is not applicable to the requested review.
- [ ] Any compilation failure identifies the first actionable error and preserves the log path.
