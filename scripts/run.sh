#!/usr/bin/env sh
set -eu

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/run.sh <input-log-or-directory> [output-directory]" >&2
  exit 2
fi

INPUT_PATH="$1"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$#" -ge 2 ]; then
  PYTHONUTF8=1 python3 "$SCRIPT_DIR/agent_run_summarizer.py" --input "$INPUT_PATH" --out "$2"
else
  PYTHONUTF8=1 python3 "$SCRIPT_DIR/agent_run_summarizer.py" --input "$INPUT_PATH"
fi