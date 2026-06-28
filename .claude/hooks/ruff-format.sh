#!/usr/bin/env bash
# PostToolUse hook: auto-format the file Claude just edited with ruff.
# Best-effort and non-blocking — always exits 0 so it never interrupts the agent.
# Real quality enforcement happens in /check and CI.
set -uo pipefail

file="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("tool_input",{}).get("file_path",""))' 2>/dev/null || true)"

case "$file" in
  *.py)
    if command -v uv >/dev/null 2>&1; then
      uv run ruff format "$file" >/dev/null 2>&1 || true
      uv run ruff check --fix "$file" >/dev/null 2>&1 || true
    fi
    ;;
esac

exit 0
