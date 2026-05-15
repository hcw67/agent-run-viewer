---
name: agent-run-viewer
description: Analyze AI coding-agent runs and generate user-facing replay reports. Use when Codex needs to review Codex, Claude Code, OpenCode, Gemini CLI, or other coding-agent transcripts/logs; debug agent behavior; summarize file changes, commands, failures, interruptions, verification, and risks; or create Markdown/HTML showcase reports from .jsonl, .log, .txt, Markdown transcripts, terminal output, or repository diffs.
---

# Agent Run Viewer

## Purpose

Turn raw AI coding-agent activity into an evidence-first report a user can understand and share. The report must answer what happened, what changed, what was verified, where the run failed or was interrupted, what risks remain, and what should happen next.

Use the bundled parser for long or file-based logs, then apply judgment. Never invent files, commands, test results, timestamps, or model behavior that are not present in the source material.

## Quick Start

```powershell
python C:\Users\hcw_h\.codex\skills\agent-run-viewer\scripts\agent_run_summarizer.py --input <log-or-directory> --out <output-dir>
```

From a cloned skill directory:

```powershell
python scripts\self_test.py
powershell -ExecutionPolicy Bypass -File scripts\run.ps1 -InputPath .\assets\sample-logs -OutPath .\out
```

The parser writes `run-summary.json`, `report.md`, and `report.html`. It only reads logs and writes derived reports; it does not execute extracted commands and does not modify source logs or repositories.

## Workflow

1. Identify the input source: local log/transcript files, pasted transcript, terminal output, repository diff, or agent JSONL. Read `references/log-sources.md` when source shape is unclear.
2. Extract facts before interpretation: timeline events, files read or modified, commands, command outcomes, verification signals, errors, permission/network/encoding issues, user interruptions, and missing evidence.
3. For file or directory input, run `scripts/agent_run_summarizer.py`. If `--out` is omitted, output defaults to `D:\CODEX\TEMP\agent-run-viewer` on this Windows setup, or the system temp directory elsewhere.
4. Read `references/report-format.md` before writing the final Markdown report or polishing generated HTML content.
5. Use `references/subagent-workflow.md` only when the log is long, code-risk review is needed, or a report-quality pass would materially help.
6. Produce the final user-facing report. Keep internal speculation out of the report; put uncertain items in `Risk Review` or `Missing Evidence`.

## Required Report Sections

Always include these sections unless the user explicitly requests a shorter format:

- `Executive Summary`: 3-6 sentences in plain language.
- `Timeline`: key actions in order.
- `Files Touched`: files changed or inspected, with reason and risk when known.
- `Commands & Verification`: commands run and what their outputs prove.
- `Failures / Interruptions`: failed commands, aborted work, permission/network/encoding issues.
- `Risk Review`: gaps, unverified assumptions, likely regressions, or missing tests.
- `Next Actions`: prioritized follow-up actions.
- `Showcase Output`: a concise shareable summary suitable for a README, changelog, or user update.

## Resources

- `scripts/agent_run_summarizer.py`: zero-dependency parser and report generator.
- `scripts/self_test.py`: clone-and-run smoke test using bundled sample logs.
- `scripts/run.ps1` and `scripts/run.sh`: platform wrappers.
- `assets/report-template.html`: static HTML template.
- `assets/sample-logs/`: portable parser fixtures.
- `references/portable-usage.md`: clone-and-run instructions.
- `references/log-sources.md`: source identification guidance.
- `references/report-format.md`: final report format and evidence rules.
- `references/subagent-workflow.md`: optional subagent delegation pattern.

## Quality Rules

- Separate evidence from judgment. Attribute every claim to the transcript, log, diff, or command output.
- If command output is unavailable, say `output not present` instead of implying success or failure.
- Treat `exit code 0`, `passed`, `success`, and equivalent tool output as verification signals only for the command that produced them.
- Treat `signal_only` verification entries as weak evidence until paired with a successful command result.
- Treat `interrupted`, `aborted`, permission denial, network denial, sandbox failure, and encoding warnings as first-class timeline events.
- For Chinese or mixed-language transcripts, preserve meaningful original labels and translate only when it improves user comprehension.