# Portable Usage

`agent-run-viewer` is intentionally zero-dependency. Users do not need a checked-in `.venv`; the parser uses only the Python 3.10+ standard library.

## Quick Self-Test

From the skill directory:

```bash
python scripts/self_test.py
```

The self-test runs the parser against bundled sample logs and verifies `run-summary.json`, `report.md`, and `report.html`.

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run.ps1 -InputPath .\assets\sample-logs -OutPath .\out
```

## macOS / Linux

```bash
sh scripts/run.sh ./assets/sample-logs ./out
```

## Direct Python

```bash
python scripts/agent_run_summarizer.py --input ./assets/sample-logs --out ./out
```

If a repository template later adds third-party dependencies, create `.venv` locally from `requirements.txt`; do not commit `.venv` because virtual environments contain machine-specific paths and executables.