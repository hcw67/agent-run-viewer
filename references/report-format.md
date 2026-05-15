# Agent Run Report Format

Use this reference when writing the final Markdown report or editing generated HTML content.

## Voice

Write for the user who requested the run, not for an internal debugging log. Be concise, factual, and useful. Prefer concrete evidence over broad claims.

## Required Sections

### Executive Summary

State the outcome in 3-6 sentences:

- What the agent attempted.
- What was completed.
- What was verified.
- What remains risky or unfinished.

### Timeline

List the major events in order. Combine repetitive read/search steps. Include interruptions, failed commands, approvals, and verification commands.

Suggested row fields: step, action, evidence, outcome.

### Files Touched

Group files by role:

- Modified files.
- Created files.
- Inspected-only files.
- Generated artifacts.

For each changed file, include why it changed and the user-facing impact. If the source does not prove a file was modified, mark it as inspected or referenced instead of touched.

### Commands & Verification

For each important command, include:

- Command name or summarized command.
- Purpose.
- Result, including exit code when known.
- What the result proves and what it does not prove.

### Failures / Interruptions

Capture blocked work clearly:

- Failed commands and likely cause.
- Sandbox or permission issues.
- Network failures.
- Encoding/mojibake issues.
- User interruptions or aborted turns.
- Tool crashes or missing output.

### Risk Review

Call out gaps such as missing tests, unreviewed generated files, partial logs, unclear command output, unresolved merge conflicts, or assumptions that were not validated.

### Next Actions

Use priority order. Each action should be concrete enough for another agent or engineer to execute.

### Showcase Output

Write 1-2 polished paragraphs suitable for a README, release note, PR description, or user update. Avoid internal tool names unless they matter.

## Evidence Discipline

Use these labels when helpful:

- `Confirmed`: directly shown by logs, diffs, or command output.
- `Likely`: strong inference from surrounding evidence.
- `Unknown`: missing from the provided material.

Never convert `Likely` or `Unknown` into a factual claim.