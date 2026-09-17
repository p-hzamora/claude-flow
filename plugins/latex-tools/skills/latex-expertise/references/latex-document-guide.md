# LaTeX guide for documents

## Read the template before changing it

A LaTeX document normally has four layers:

- `\documentclass[...]` selects the base layout or a custom document class.
- The preamble (before `\begin{document}`) loads packages, defines colours/fonts, and declares reusable commands.
- The document body calls those commands to render content.
- `\input{...}` and `\include{...}` split the document across files; the root file is the one containing `\documentclass`.

Custom commands are part of the document's API. A definition such as
`\newcommand{\notice}[1]{...}` means content should be supplied through
`\notice{...}`, rather than recreating its underlying markup. Check the number of
`#1`, `#2`, and other parameters before calling a command.

## Safe content editing

- Prefer changing text arguments and existing data blocks over the preamble or low-level spacing.
- Keep braces, `\begin{environment}` / `\end{environment}`, and `\if...` / `\fi` pairs balanced.
- Put a percent sign in ordinary text as `\%`. Escape literal `#`, `$`, `&`, `_`, `{`, `}`, and `~` as `\#`, `\$`, `\&`, `\_`, `\{`, `\}`, and `\textasciitilde{}`. A backslash is normally written `\textbackslash{}`.
- Use `--` for an en dash and `---` for an em dash. Use LaTeX quotation marks: ``opening''.
- Use `\\` only for intentional line breaks. For a new paragraph, leave a blank source line where the surrounding template permits it.
- For links, follow the existing `hyperref` pattern, usually `\href{URL}{visible text}`. URLs containing underscores or query strings should stay in the URL argument.
- If the document uses UTF-8 text successfully, retain that approach. Do not add `inputenc` to modern XeLaTeX/LuaLaTeX templates without a concrete need.

## Layout and typography

Avoid manual `\vspace`, `\hspace`, negative spacing, or raw font-size commands for
ordinary content edits. Use the document's macros first. If a layout correction is
needed, make it at the shared macro or style level only after checking all its callers.

Package ordering matters. Add a package only when an existing package or macro cannot provide the required feature. Font packages such as `fontspec` require XeLaTeX or LuaLaTeX; they cannot compile under pdfLaTeX.

## Compilation

`latexmk` is the preferred builder because it detects and repeats the necessary LaTeX, bibliography, and index runs. The engine must match the template:

- pdfLaTeX: traditional templates with Type 1 fonts and common packages.
- XeLaTeX: templates using system fonts, `fontspec`, or `\setmainfont`.
- LuaLaTeX: templates using LuaTeX-specific features or configured for it.

The project helper chooses XeLaTeX when it sees common `fontspec` / system-font markers; otherwise it chooses pdfLaTeX. Override the choice only when the template's documentation or source establishes a different engine.

Compile from the root document, not an individual file that is merely included with `\input`. On failure, correct the first real error, then compile again. Warnings about unresolved references can require another successful run; `latexmk` handles that automatically.

## Common errors

- `Undefined control sequence`: a misspelled command, a missing package, or a macro called before its definition.
- `File ... not found`: a wrong relative path, missing asset, or unavailable package/class.
- `Runaway argument` / `Paragraph ended before ... was complete`: a missing closing brace or an unintended blank line inside a command argument.
- `Extra }` / `Missing } inserted`: unbalanced braces, often in a link, macro, or accented text.
- `fontspec` error under pdfLaTeX: compile with XeLaTeX or LuaLaTeX.
- Overfull `\hbox`: text or a URL is wider than its available line. Prefer concise wording or the template's URL/text-wrapping mechanism instead of forcing negative spacing.
