#!/usr/bin/env bash
# convert_templates.sh
# Convert between *.py-tpl and *.py within dj_templates (or templates) directory.
# Usage:
#   ./convert_templates.sh --to-py       # convert *.py-tpl -> *.py
#   ./convert_templates.sh --to-tpl      # convert *.py -> *.py-tpl
#   ./convert_templates.sh --toggle      # do both (first to-py, then to-tpl) (default: to-py)
# Options:
#   -n, --dry-run    : show what would be done
#   -f, --force      : overwrite existing target files
#   -h, --help       : show help

set -euo pipefail

show_help() {
  sed -n '1,120p' "$0" | sed -n '1,40p'
}

DRY_RUN=0
FORCE=0
MODE="to-py"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --to-py) MODE="to-py"; shift;;
    --to-tpl) MODE="to-tpl"; shift;;
    --toggle) MODE="toggle"; shift;;
    -n|--dry-run) DRY_RUN=1; shift;;
    -f|--force) FORCE=1; shift;;
    -h|--help) show_help; exit 0;;
    *) echo "Unknown arg: $1"; show_help; exit 2;;
  esac
done

# Locate base directory: prefer dj_templates, fall back to templates
if [[ -d "dj_templates" ]]; then
  BASE_DIR="dj_templates"
elif [[ -d "templates" ]]; then
  BASE_DIR="templates"
else
  echo "Neither 'dj_templates' nor 'templates' directory found in project root." >&2
  exit 1
fi

echo "Operating on template directory: $BASE_DIR"

run_cmd() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "DRY-RUN: $*"
  else
    eval "$*"
  fi
}

convert_to_py() {
  # Find files ending with .py-tpl and rename to remove -tpl suffix
  find "$BASE_DIR" -type f -name "*.py-tpl" -print0 | while IFS= read -r -d '' src; do
    dest="${src%-tpl}"
    if [[ -e "$dest" && $FORCE -ne 1 ]]; then
      echo "Skipping $src -> $dest (target exists). Use --force to overwrite."
      continue
    fi
    echo "Converting: $src -> $dest"
    if [[ $DRY_RUN -eq 1 ]]; then
      continue
    fi
    mv -f "$src" "$dest"
  done
}

convert_to_tpl() {
  # Find files ending with .py but not already -tpl and add -tpl suffix
  find "$BASE_DIR" -type f -name "*.py" ! -name "*-tpl" -print0 | while IFS= read -r -d '' src; do
    dest="${src}-tpl"
    if [[ -e "$dest" && $FORCE -ne 1 ]]; then
      echo "Skipping $src -> $dest (target exists). Use --force to overwrite."
      continue
    fi
    echo "Converting: $src -> $dest"
    if [[ $DRY_RUN -eq 1 ]]; then
      continue
    fi
    mv -f "$src" "$dest"
  done
}

case "$MODE" in
  "to-py")
    convert_to_py
    ;;
  "to-tpl")
    convert_to_tpl
    ;;
  "toggle")
    convert_to_py
    convert_to_tpl
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    exit 2
    ;;
esac

echo "Done."
