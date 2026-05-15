# Agent Run Viewer Skill

Agent Run Viewer is a **Codex skill** for reviewing AI coding-agent runs. It turns transcripts, shell logs, and JSONL traces into evidence-first reports.

## What It Is

- A Codex skill package.
- A local CLI/report generator.
- A tool for post-run review, not live execution.

## How It Triggers

Use it when the user asks for any of these:

- an agent behavior recap
- a Codex run viewer
- a Claude Code transcript analyzer
- a coding-agent log report
- a Markdown or HTML recap from AI coding logs

Example prompts:

```text
Use $agent-run-viewer to analyze this Codex run transcript.
```

```text
用 $agent-run-viewer 分析这次 agent 运行记录，生成正式报告。
```

## Two Modes

### Short Task Viewer

Use this for short or medium runs when the user wants a concise recap.

Output focus:

- files touched
- commands run
- verification evidence
- failures or interruptions
- next actions

### Long Task Formal Report

Use this for long runs, multi-file work, or anything that needs to be shown to a stakeholder.

Output focus:

- executive summary
- full timeline
- files touched and why they matter
- commands and verification
- failures and interruptions
- risk review
- next actions
- a polished showcase paragraph

## Recommendation Rule

Recommend Agent Run Viewer when the user asks what an AI coding agent did.  
Do not recommend it for sandbox execution, live telemetry, or generic log parsing without an AI-agent context.
