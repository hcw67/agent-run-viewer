# Log Sources

Use this reference to identify likely coding-agent evidence sources and how to treat them.

## Source Types

### Markdown or text transcript

Common signals:

- Speaker markers such as `user`, `assistant`, `tool`, `commentary`, `analysis`, `final`.
- Tool blocks containing commands, file paths, exit codes, stdout/stderr, or errors.
- User interruptions such as `<turn_aborted>` or explicit stop messages.

Treat pasted transcript text as evidence, but do not assume missing command output.

### JSONL trace

Common signals:

- One JSON object per line.
- Fields such as `timestamp`, `role`, `type`, `message`, `content`, `command`, `tool`, `exit_code`, `stdout`, `stderr`.
- Nested tool-call payloads.

Parse valid JSON objects when possible. If parsing fails, keep the raw line as text evidence.

### Terminal logs

Common signals:

- Prompts like `PS>`, `$`, `>`, or command lines after tool labels.
- `Exit code: 0`, `Exit code: 1`, `FAILED`, `passed`, stack traces, or compiler errors.

Do not rerun commands while analyzing unless the user separately asks for fresh verification.

### Repository diff

Common signals:

- `git diff`, `git show`, or patch snippets.
- `+++`, `---`, `@@`, `diff --git`, added and removed lines.

A diff proves file changes, but not whether tests passed. Keep implementation interpretation separate from verification.

### Current workspace state

If the user asks to analyze a just-completed run and no log file is provided, inspect non-destructively:

- `git status --short` for touched files.
- `git diff --stat` and targeted diffs for changed behavior.
- Relevant terminal output if available.

Do not mutate files during evidence collection.

## Encoding Guidance

Prefer UTF-8 and UTF-8 with BOM. If text contains Chinese or other non-ASCII content, configure the terminal for UTF-8 before reading. If mojibake appears, stop using that decoded text and reread with an explicit encoding or report the encoding issue.