# Agent Run Viewer

Agent Run Viewer is a zero-dependency Codex skill and local report generator for AI coding-agent runs. It turns Codex, Claude Code, OpenCode, Gemini CLI, or other agent transcripts into evidence-first summaries, Markdown reports, and static HTML reports.

It is built for one practical question:

> What did the coding agent actually do, what was verified, where did it fail, and what should happen next?

## What It Generates

Given `.jsonl`, `.log`, `.txt`, or Markdown transcripts, the bundled parser writes:

```text
run-summary.json   # structured evidence for tools or follow-up analysis
report.md          # Markdown report draft
report.html        # static, shareable HTML report
```

The report covers:

- Executive summary
- Timeline
- Files touched or referenced
- Commands and verification results
- Failures and interruptions
- Risk review
- Next actions
- Showcase output for a user update, README, changelog, or PR note

## Two Usage Modes

### 1. Short Task Viewer

Use this mode after a small or medium task when you want a quick, evidence-based recap without a heavy formal report.

Best for:

- A single bug fix
- A small document update
- A short coding-agent run
- Checking what commands/tests were actually run
- Producing a concise handoff summary

Prompt examples:

```text
用 $agent-run-viewer 快速复盘刚才这段 Codex 运行记录，重点列出文件、命令、失败点和验证结果。
```

```text
Use $agent-run-viewer in short viewer mode for this agent transcript. Keep the output concise.
```

Expected output style:

- Short summary
- Compact timeline
- Commands and exit codes
- Any failed or missing verification
- 1-3 next actions

### 2. Long Task Formal Report

Use this mode when the run is long, involves multiple files, has failed attempts, includes user interruptions, or needs to be shown to a stakeholder.

Best for:

- Long Codex/Claude Code/OpenCode sessions
- Multi-file implementation work
- Debugging a failed agent run
- Preparing a PR or delivery recap
- Creating a polished report for a user, teammate, or client

Prompt examples:

```text
用 $agent-run-viewer 分析 D:\logs\codex-run.log，生成一份用户可展示的正式复盘报告，包含风险和下一步建议。
```

```text
Use $agent-run-viewer to analyze this coding-agent run and generate a formal Markdown report plus an HTML report.
```

Expected output style:

- Evidence-first executive summary
- Full timeline
- Files touched with impact and risk
- Commands and verification evidence
- Failures/interruption analysis
- Risk review
- Prioritized next actions
- Showcase paragraph suitable for README/PR/user delivery

## How The Skill Triggers

### Explicit Trigger

The most reliable way is to name the skill directly:

```text
用 $agent-run-viewer 分析这个 agent 运行日志。
```

```text
Use $agent-run-viewer to analyze this Codex run transcript.
```

### Intent-Based Trigger

Codex can also load the skill when the user intent matches the skill description, for example:

```text
分析这次 Codex 做了什么，改了哪些文件，跑了哪些命令，哪里失败了。
```

```text
把这段 Claude Code transcript 生成一份可展示复盘报告。
```

Important: a skill is not a post-task hook. It does not automatically run after every long task. It triggers when the user asks for an agent-run recap, viewer, transcript analysis, debugging summary, or formal report.

## Install / Deploy As A Codex Skill

Clone this repository into your Codex skills directory:

```powershell
git clone <your-repo-url> $env:USERPROFILE\.codex\skills\agent-run-viewer
```

Or on macOS/Linux:

```bash
git clone <your-repo-url> ~/.codex/skills/agent-run-viewer
```

Then start a new Codex session so the skill index can discover it.

No third-party Python dependencies are required. The runtime is Python 3.10+ standard library only.

## Quick Start

From the repository root:

```powershell
python scripts\self_test.py
```

Run the bundled sample logs:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run.ps1 -InputPath .\assets\sample-logs -OutPath .\out
```

macOS/Linux:

```bash
sh scripts/run.sh ./assets/sample-logs ./out
```

Direct Python:

```bash
python scripts/agent_run_summarizer.py --input ./assets/sample-logs --out ./out
```

After running, open:

```text
out/report.md
out/report.html
out/run-summary.json
```

## CLI Usage

```bash
python scripts/agent_run_summarizer.py --input <log-file-or-directory> --out <output-directory>
```

Options:

```text
--input       Required. Log/transcript file or directory.
--out         Optional. Output directory.
--max-events  Optional. Maximum timeline events. Default: 120.
--max-items   Optional. Maximum files/commands/errors/verification items. Default: 80.
```

If `--out` is omitted, the script writes to:

- `D:\CODEX\TEMP\agent-run-viewer` on this Windows setup when available
- otherwise the system temp directory, such as `/tmp/agent-run-viewer`

## Example

Input transcript:

```text
tool shell_command command: npm test
Exit code: 1
Error: expected 2 received 1
assistant: Fixed the assertion and reran tests.
tool shell_command command: npm test
Exit code: 0
passed 12 tests
```

Extracted command evidence:

```json
[
  { "command": "npm test", "exit_code": 1, "status": "failed" },
  { "command": "npm test", "exit_code": 0, "status": "success" }
]
```

The formal report will say that the first verification failed, the second passed, and the remaining risk depends on whether broader lint/build/integration checks were run.

## Project Structure

```text
agent-run-viewer/
  SKILL.md
  agents/openai.yaml
  assets/report-template.html
  assets/sample-logs/
  references/log-sources.md
  references/portable-usage.md
  references/report-format.md
  references/subagent-workflow.md
  scripts/agent_run_summarizer.py
  scripts/run.ps1
  scripts/run.sh
  scripts/self_test.py
  requirements.txt
```

## Design Principles

- Evidence before conclusions.
- No invented command results, file changes, or timestamps.
- Zero dependency runtime.
- Reports must be useful to users, not just internal debugging notes.
- Subagents are optional and reserved for long logs, risk review, or report polish.

## Limitations

- The parser is heuristic; Codex should still review `run-summary.json` before making final claims.
- It does not execute commands found in logs.
- It does not inspect live git history unless a user separately asks Codex to do so.
- It is not a real-time agent monitor; it analyzes provided transcripts/log files.

## License

No license has been selected yet. Add one before publishing if you want others to reuse or modify the project under clear terms.