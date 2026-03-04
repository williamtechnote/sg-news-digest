#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

PYTHON_BIN="python3"
if [[ -x "$SKILL_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$SKILL_ROOT/.venv/bin/python"
elif [[ -x "$WORKSPACE_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$WORKSPACE_ROOT/.venv/bin/python"
fi

PYTHONPATH="$SCRIPT_DIR" "$PYTHON_BIN" -m pipeline.runner "$@"
