#!/usr/bin/env bash
# Compile a root LaTeX document into a PDF with the document-appropriate engine.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: compile-latex.sh <root.tex> [--output-dir DIR] [--engine auto|pdflatex|xelatex|lualatex]

Compiles a root LaTeX file with latexmk. The default engine is auto: XeLaTeX for
templates using fontspec or system-font commands, otherwise pdfLaTeX. Without
--output-dir, artifacts go in this repository's build/<source-path-without-.tex>/.
EOF
}

if [[ $# -eq 0 ]]; then
  usage >&2
  exit 64
fi

source_file=""
output_dir=""
engine="auto"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir|-o)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 64; }
      output_dir="$2"
      shift 2
      ;;
    --engine)
      [[ $# -ge 2 ]] || { echo "Missing value for --engine" >&2; exit 64; }
      engine="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 64
      ;;
    *)
      [[ -z "$source_file" ]] || { echo "Only one .tex file may be supplied." >&2; exit 64; }
      source_file="$1"
      shift
      ;;
  esac
done

[[ -n "$source_file" && -f "$source_file" ]] || { echo "LaTeX source not found: $source_file" >&2; exit 66; }
[[ "$source_file" == *.tex ]] || { echo "Expected a .tex file: $source_file" >&2; exit 64; }

case "$engine" in auto|pdflatex|xelatex|lualatex) ;; *)
  echo "Unsupported engine: $engine" >&2
  exit 64
  ;;
esac

source_dir="$(cd "$(dirname "$source_file")" && pwd)"
source_name="$(basename "$source_file")"
source_stem="${source_name%.tex}"
source_path="$source_dir/$source_name"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "$script_dir/../.." && pwd)"

if [[ -z "$output_dir" ]]; then
  case "$source_path" in
    "$project_root"/*)
      source_relative="${source_path#"$project_root"/}"
      output_dir="$project_root/build/${source_relative%.tex}"
      ;;
    *)
      output_dir="$project_root/build/$source_stem"
      ;;
  esac
fi
mkdir -p "$output_dir"
output_dir="$(cd "$output_dir" && pwd)"

if [[ "$engine" == "auto" ]]; then
  if rg -q '\\usepackage(?:\[[^]]*\])?\{fontspec\}|\\(?:setmainfont|setsansfont|setmonofont)\b' "$source_file"; then
    engine="xelatex"
  else
    engine="pdflatex"
  fi
fi

command -v latexmk >/dev/null || { echo "latexmk is required to compile reliably." >&2; exit 69; }
command -v "$engine" >/dev/null || { echo "Requested LaTeX engine is not installed: $engine" >&2; exit 69; }

if [[ "$engine" == "xelatex" ]]; then
  kpsewhich lmroman10-regular.otf >/dev/null || {
    echo "XeLaTeX needs the Latin Modern font, but it is not installed." >&2
    echo "On Arch, install it with: sudo pacman -S texlive-fontsrecommended" >&2
    exit 69
  }
fi

case "$engine" in
  pdflatex) latexmk_engine=(-pdf) ;;
  xelatex) latexmk_engine=(-xelatex) ;;
  lualatex) latexmk_engine=(-lualatex) ;;
esac

echo "Compiling $source_name with $engine..."
# Always rebuild: latexmk otherwise retains a prior failed invocation in its
# dependency database and can incorrectly report "Nothing to do" on a retry.
if ! latexmk "${latexmk_engine[@]}" -g -interaction=nonstopmode -halt-on-error -file-line-error -outdir="$output_dir" "$source_file"; then
  echo "Compilation failed. Review: $output_dir/$source_stem.log" >&2
  exit 1
fi

pdf_file="$output_dir/$source_stem.pdf"
[[ -s "$pdf_file" ]] || { echo "Compilation completed without producing: $pdf_file" >&2; exit 1; }
echo "PDF ready: $pdf_file"
