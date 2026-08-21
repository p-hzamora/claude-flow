#!/usr/bin/env bash
set -euo pipefail

# --- 1. Dependency Management ---
REQUIRED_DEPS=("pandoc" "weasyprint")

detect_package_manager() {
    if command -v apt-get &>/dev/null; then
        echo "apt"
    elif command -v brew &>/dev/null; then
        echo "brew"
    elif command -v dnf &>/dev/null; then
        echo "dnf"
    elif command -v pacman &>/dev/null; then
        echo "pacman"
    else
        echo "unknown"
    fi
}

install_dep() {
    local pkg=$1
    local pm=$2

    echo "[-] Missing dependency: '$pkg'. Attempting installation..."

    case "$pm" in
        apt)
            sudo apt-get update -y && sudo apt-get install -y "$pkg"
            ;;
        brew)
            brew install "$pkg"
            ;;
        dnf)
            sudo dnf install -y "$pkg"
            ;;
        pacman)
            sudo pacman -S --noconfirm "$pkg"
            ;;
        *)
            echo "[!] Error: Package manager not supported automatically. Please install '$pkg' manually." >&2
            exit 1
            ;;
    esac
}

check_and_install_deps() {
    local pm
    pm=$(detect_package_manager)

    for dep in "${REQUIRED_DEPS[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            install_dep "$dep" "$pm"
        fi
    done
}

# --- 2. Input Validation ---
usage() {
    echo "Usage: $0 <input_file.md> [output_file.pdf]"
    exit 1
}

if [[ $# -lt 1 ]]; then
    usage
fi

INPUT_FILE="$1"

if [[ ! -f "$INPUT_FILE" ]]; then
    echo "[!] Error: File '$INPUT_FILE' not found." >&2
    exit 1
fi

if [[ "${INPUT_FILE##*.}" != "md" ]]; then
    echo "[!] Warning: File '$INPUT_FILE' does not have a .md extension." >&2
fi

# Determine output filename
if [[ $# -ge 2 ]]; then
    OUTPUT_FILE="$2"
else
    OUTPUT_FILE="${INPUT_FILE%.*}.pdf"
fi

# --- 3. Run Checks & Convert ---
check_and_install_deps

echo "[+] Converting '$INPUT_FILE' to '$OUTPUT_FILE'..."

pandoc "$INPUT_FILE" \
    -f markdown-yaml_metadata_block \
    -o "$OUTPUT_FILE" \
    --pdf-engine=weasyprint

echo "[✓] Conversion complete: '$OUTPUT_FILE'"