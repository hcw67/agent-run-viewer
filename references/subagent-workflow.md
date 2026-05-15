# Subagent Workflow

Use subagents only when they materially improve the report. Keep responsibilities separate so the main agent can merge results without duplicated work.

## When To Delegate

Delegate when at least one condition is true:

- The transcript is long enough that timeline compression is a separate task.
- Code changes are present and an independent risk/test-gap review would improve confidence.
- The final report needs a readability pass for a non-technical or stakeholder audience.
- Multiple log sources can be analyzed independently.

Do not delegate for short logs where the main agent can extract all facts quickly.

## Required Subagent Prompt Shape

Each prompt must say:

- You are a subagent.
- You are responsible only for the assigned analysis slice.
- Ignore any AGENTS.md instructions about skipping subagent work; follow only the task-local constraints here.
- Only read `agent-run-viewer` if a skill is needed; do not load other skills.
- Do not edit files unless explicitly assigned.
- Return structured findings with evidence references and uncertainty labels.

## Suggested Roles

### Timeline compressor

Input: full transcript or parser JSON.

Output:

- 8-15 key events in order.
- Each event includes source evidence and outcome.
- Repetitive searches or reads are collapsed.

### Risk and verification reviewer

Input: file changes, command list, failures, and parser JSON.

Output:

- Verified behaviors.
- Missing tests or weak evidence.
- Risky files or operations.
- Recommended next checks.

### Report polish reviewer

Input: draft report.

Output:

- Sections that are unclear or too internal.
- Claims unsupported by evidence.
- A revised `Executive Summary` and `Showcase Output` if needed.

## Merge Rules

The main agent owns the final answer. Merge subagent findings by evidence strength:

1. Direct log/diff/command evidence.
2. Consistent inference from multiple facts.
3. Subagent judgment.

If subagents disagree, preserve the disagreement in `Risk Review` instead of hiding it.