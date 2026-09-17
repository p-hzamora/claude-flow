# Markdown as a LaTeX source

Use Markdown as the canonical editorial source when a deliverable begins as prose but
must become a LaTeX PDF. Keep the source `.md` beside the generated `.tex` files so a
reviewer can trace the PDF back to the approved content.

## Artifact contract

```text
source.md  ->  content.tex + root.tex  ->  verified.pdf
```

The Markdown-to-LaTeX author owns the first transformation. The PDF exporter owns only
the second. Do not bypass the Markdown source with an ad-hoc PDF conversion.

## Markdown requirements

- Use semantic headings, paragraphs, ordered or unordered lists, Markdown tables,
  links, block quotes, and fenced code blocks.
- Keep one clear H1 title and use a consistent H2/H3 hierarchy. The author maps these
  to the template's title, `\section`, and `\subsection` conventions.
- Keep prose in the intended final language. File paths, commit hashes, URLs, and code
  blocks remain literal.
- Use plain text inside table cells where possible. Complex nested lists, images, raw
  HTML, Mermaid, and raw LaTeX require an explicit template or caller decision; do not
  guess a rendering.

## Source-generation rules

1. Inspect the Markdown and a caller-supplied template before writing LaTeX. Reuse the
   template's macros and include structure.
2. If no template exists, use `assets/markdown-report.tex` only when the caller has
   explicitly approved the bundled minimal report layout. Copy it to the requested root
   path and generate a sibling `content.tex` file.
3. Convert semantic Markdown rather than copying it verbatim. Escape literal `#`, `$`,
   `%`, `&`, `_`, `{`, `}`, `~`, and backslashes. Keep code blocks in the template's
   code environment; do not escape their contents as ordinary prose.
4. Preserve links with the template's `hyperref` convention. Render tables with the
   table facilities already provided by the template; use a long table only when it can
   span pages safely.
5. Report an unsupported construct, a missing referenced asset, or an ambiguous mapping
   before compiling. Do not silently discard source content.
