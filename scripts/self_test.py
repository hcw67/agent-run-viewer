#!/usr/bin/env python3
"""Self-test for agent-run-viewer using bundled sample logs."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    skill_dir = Path(__file__).resolve().parent.parent
    samples = skill_dir / "assets" / "sample-logs"
    script = skill_dir / "scripts" / "agent_run_summarizer.py"
    out_dir = Path(tempfile.mkdtemp(prefix="agent-run-viewer-self-test-"))
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--input", str(samples), "--out", str(out_dir)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            return result.returncode
        summary_path = out_dir / "run-summary.json"
        report_md = out_dir / "report.md"
        report_html = out_dir / "report.html"
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        assert data["stats"]["source_count"] == 2
        assert any(command["command"] == "npm test" and command["exit_code"] == 1 for command in data["commands"])
        assert any(command["command"] == "npm test" and command["exit_code"] == 0 for command in data["commands"])
        assert any(command["command"] == "pnpm test" and command["exit_code"] == 1 for command in data["commands"])
        assert report_md.exists() and report_md.stat().st_size > 0
        assert report_html.exists() and report_html.stat().st_size > 0
        print("agent-run-viewer self-test: OK")
        print(f"output: {out_dir}")
        return 0
    finally:
        if "--keep-output" not in sys.argv:
            shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())