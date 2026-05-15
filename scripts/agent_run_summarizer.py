#!/usr/bin/env python3
"""Summarize coding-agent logs into structured JSON, Markdown, and HTML reports.

This script performs text extraction only. It never executes commands found in logs.
It uses only the Python standard library.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

TEXT_EXTENSIONS = {".jsonl", ".log", ".txt", ".md", ".markdown", ".out", ".err"}
CHINESE_ERROR_TERMS = "|".join(["\u4e71\u7801", "\u4e2d\u65ad", "\u5931\u8d25", "\u9519\u8bef"])
CHINESE_VERIFY_TERMS = "|".join(["\u9a8c\u8bc1", "\u6d4b\u8bd5", "\u901a\u8fc7"])
ERROR_RE = re.compile(r"\b(error|failed|failure|exception|traceback|permission denied|access denied|timeout|aborted|interrupted|nonzero|denied)\b|" + CHINESE_ERROR_TERMS, re.I)
VERIFY_RE = re.compile(r"\b(test|pytest|unittest|vitest|jest|npm test|pnpm test|yarn test|cargo test|go test|dotnet test|build|lint|typecheck|quick_validate|passed|success|exit code:\s*0)\b|" + CHINESE_VERIFY_TERMS, re.I)
EXIT_RE = re.compile(r"exit code:\s*(-?\d+)", re.I)
TIMESTAMP_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b")
PATH_RE = re.compile(r"(?<![A-Za-z0-9_])(?:[A-Za-z]:\\[^\s:'\"<>|]+|(?:\.?\.?/)?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.@()\[\]-]+)+)(?![A-Za-z0-9_])")
COMMAND_PREFIX_RE = re.compile(r"^\s*(?:PS [^>]*>|PS>|\$|>)\s+(.+?)\s*$")
COMMAND_FIELD_RE = re.compile(r"\bcommand:\s*(.+?)\s*$", re.I)
COMMAND_WORD_RE = re.compile(r"\b(python|node|npm|pnpm|yarn|bun|cargo|go|dotnet|git|gh|pytest|ruff|mypy|tsc|vitest|jest|powershell|pwsh|docker|kubectl)\b", re.I)


@dataclass
class SourceText:
    path: str
    text: str
    encoding: str
    issue: str | None = None


def default_output_dir() -> str:
    env_value = os.environ.get("AGENT_RUN_VIEWER_OUT")
    if env_value:
        return env_value
    return str(Path(tempfile.gettempdir()) / "agent-run-viewer")


def read_text(path: Path) -> SourceText:
    encodings = ["utf-8-sig", "utf-8", "gb18030", "cp1252"]
    raw = path.read_bytes()
    for enc in encodings:
        try:
            return SourceText(str(path), raw.decode(enc), enc)
        except UnicodeDecodeError:
            continue
    return SourceText(str(path), raw.decode("utf-8", errors="replace"), "utf-8-replace", "decoded with replacement characters")


def iter_input_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    files: list[Path] = []
    for child in input_path.rglob("*"):
        if child.is_file() and child.suffix.lower() in TEXT_EXTENSIONS:
            files.append(child)
    return sorted(files)


def flatten_json(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from flatten_json(item)
    elif isinstance(value, list):
        for item in value:
            yield from flatten_json(item)


def text_from_json(value: Any) -> str:
    parts: list[str] = []
    for _, item in flatten_json(value):
        if isinstance(item, (str, int, float)):
            parts.append(str(item))
    return "\n".join(parts)


def first_timestamp(line: str) -> str | None:
    match = TIMESTAMP_RE.search(line)
    return match.group(0) if match else None


def compact(text: str, limit: int = 220) -> str:
    one_line = re.sub(r"\s+", " ", text).strip()
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 1].rstrip() + "..."


def classify_event(line: str) -> str | None:
    lowered = line.lower()
    if ERROR_RE.search(line):
        return "error"
    if VERIFY_RE.search(line):
        return "verification"
    if "tool" in lowered or "shell_command" in lowered or "function" in lowered:
        return "tool"
    if COMMAND_PREFIX_RE.match(line) or (COMMAND_WORD_RE.search(line) and len(line) < 300):
        return "command"
    if PATH_RE.search(line):
        return "file"
    if any(marker in lowered for marker in ["assistant", "user", "final", "commentary", "analysis"]):
        return "message"
    return None


def add_unique(items: list[dict[str, Any]], seen: set[str], key: str, item: dict[str, Any]) -> None:
    value = str(item.get(key, ""))
    if not value or value in seen:
        return
    seen.add(value)
    items.append(item)


def extract_command_from_json(obj: Any) -> list[str]:
    commands: list[str] = []
    for key, item in flatten_json(obj):
        normalized = key.lower()
        if normalized in {"command", "cmd", "script", "shell", "args"}:
            if isinstance(item, list):
                commands.append(" ".join(str(part) for part in item))
            elif isinstance(item, (str, int, float)):
                commands.append(str(item))
    return commands


def extract_exit_code_from_json(obj: Any) -> int | None:
    for key, item in flatten_json(obj):
        if key.lower() in {"exit_code", "exitcode", "status_code"}:
            try:
                return int(item)
            except (TypeError, ValueError):
                return None
    return None


def command_status(exit_code: int | None, evidence: str) -> str:
    if exit_code == 0:
        return "success"
    if exit_code is not None:
        return "failed"
    if ERROR_RE.search(evidence):
        return "failed_or_error"
    if VERIFY_RE.search(evidence):
        return "verification_signal"
    return "unknown"


def summarize_sources(sources: list[SourceText], max_events: int, max_items: int) -> dict[str, Any]:
    timeline: list[dict[str, Any]] = []
    commands: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    verification: list[dict[str, Any]] = []
    seen_files: set[str] = set()
    seen_errors: set[str] = set()
    seen_verification: set[str] = set()
    event_counts: Counter[str] = Counter()

    for source in sources:
        lines = source.text.splitlines()
        last_command_index: int | None = None
        for line_no, raw_line in enumerate(lines, 1):
            line = raw_line.strip()
            if not line:
                continue

            parsed_json: Any | None = None
            if source.path.lower().endswith(".jsonl") and (line.startswith("{") or line.startswith("[")):
                try:
                    parsed_json = json.loads(line)
                except json.JSONDecodeError:
                    parsed_json = None

            scan_text = text_from_json(parsed_json) if parsed_json is not None else line
            exit_match = EXIT_RE.search(scan_text)
            parsed_exit_code = extract_exit_code_from_json(parsed_json) if parsed_json is not None else None
            current_exit_code = parsed_exit_code
            if current_exit_code is None and exit_match:
                current_exit_code = int(exit_match.group(1))

            if current_exit_code is not None and last_command_index is not None:
                previous = commands[last_command_index]
                if previous.get("source") == source.path and previous.get("exit_code") is None:
                    previous["exit_code"] = current_exit_code
                    previous["evidence"] = compact(f"{previous.get('evidence', '')} | {scan_text}")
                    previous["status"] = command_status(current_exit_code, previous["evidence"])

            event_type = classify_event(scan_text)
            if event_type and len(timeline) < max_events:
                event_counts[event_type] += 1
                timeline.append({
                    "source": source.path,
                    "line": line_no,
                    "timestamp": first_timestamp(scan_text),
                    "type": event_type,
                    "summary": compact(scan_text),
                })

            candidate_commands: list[str] = []
            if parsed_json is not None:
                candidate_commands.extend(extract_command_from_json(parsed_json))
            else:
                field_match = COMMAND_FIELD_RE.search(line)
                prefix_match = COMMAND_PREFIX_RE.match(line)
                if field_match:
                    candidate_commands.append(field_match.group(1))
                elif prefix_match:
                    candidate_commands.append(prefix_match.group(1))
                elif COMMAND_WORD_RE.search(line) and len(line) < 300 and not EXIT_RE.search(line):
                    candidate_commands.append(line)

            line_seen_commands: set[str] = set()
            for command in candidate_commands:
                normalized_command = compact(command, 260)
                if not normalized_command or normalized_command in line_seen_commands:
                    continue
                line_seen_commands.add(normalized_command)
                if len(commands) >= max_items:
                    break
                commands.append({
                    "command": normalized_command,
                    "source": source.path,
                    "line": line_no,
                    "exit_code": current_exit_code,
                    "status": command_status(current_exit_code, scan_text),
                    "evidence": compact(scan_text),
                })
                last_command_index = len(commands) - 1

            for path_match in PATH_RE.finditer(scan_text):
                path_value = path_match.group(0).rstrip(".,);]")
                add_unique(files, seen_files, "path", {
                    "path": path_value,
                    "source": source.path,
                    "line": line_no,
                    "evidence": compact(scan_text),
                })
                if len(files) >= max_items:
                    break

            if ERROR_RE.search(scan_text):
                add_unique(errors, seen_errors, "evidence", {
                    "source": source.path,
                    "line": line_no,
                    "evidence": compact(scan_text),
                })

            if VERIFY_RE.search(scan_text):
                add_unique(verification, seen_verification, "evidence", {
                    "source": source.path,
                    "line": line_no,
                    "evidence": compact(scan_text),
                    "status": "success" if current_exit_code == 0 or re.search(r"\b(passed|success|exit code:\s*0)\b", scan_text, re.I) else "signal_only",
                })

    encoding_issues = [
        {"source": source.path, "encoding": source.encoding, "issue": source.issue}
        for source in sources
        if source.issue
    ]
    command_status_counts = Counter(str(command.get("status", "unknown")) for command in commands)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": [{"path": s.path, "encoding": s.encoding, "characters": len(s.text)} for s in sources],
        "stats": {
            "source_count": len(sources),
            "timeline_events": len(timeline),
            "commands": len(commands),
            "files": len(files),
            "errors": len(errors),
            "verification_signals": len(verification),
            "command_statuses": dict(command_status_counts),
            "event_types": dict(event_counts),
        },
        "timeline": timeline,
        "commands": commands[:max_items],
        "files": files[:max_items],
        "errors": errors[:max_items],
        "verification": verification[:max_items],
        "encoding_issues": encoding_issues,
        "notes": [
            "Commands were extracted as text only and were not executed.",
            "Use this JSON as evidence for a polished Agent Run Viewer report.",
        ],
    }


def render_stat(label: str, value: Any) -> str:
    return f'<div class="stat"><strong>{html.escape(str(value))}</strong><span>{html.escape(label)}</span></div>'


def render_list(items: list[dict[str, Any]], key: str, css_class: str = "item") -> str:
    if not items:
        return '<p class="muted">No evidence found in the provided sources.</p>'
    rows = []
    for item in items:
        main = html.escape(str(item.get(key, "")))
        status = html.escape(str(item.get("status", "")))
        source = html.escape(f"{item.get('source', '')}:{item.get('line', '')}")
        evidence = html.escape(str(item.get("evidence", item.get("summary", ""))))
        status_html = f' <span class="muted">[{status}]</span>' if status else ""
        rows.append(f'<div class="{css_class}"><strong>{main}</strong>{status_html}<br><span class="muted">{source}</span><br>{evidence}</div>')
    return '<div class="list">' + "\n".join(rows) + "</div>"


def render_timeline(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">No timeline events found.</p>'
    rows = ["<table><thead><tr><th>Line</th><th>Type</th><th>Summary</th><th>Source</th></tr></thead><tbody>"]
    for item in items:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('line', '')))}</td>"
            f"<td>{html.escape(str(item.get('type', '')))}</td>"
            f"<td>{html.escape(str(item.get('summary', '')))}</td>"
            f"<td>{html.escape(Path(str(item.get('source', ''))).name)}</td>"
            "</tr>"
        )
    rows.append("</tbody></table>")
    return "\n".join(rows)


def render_markdown(summary: dict[str, Any]) -> str:
    def bullet_items(items: list[dict[str, Any]], label_key: str, limit: int = 12) -> str:
        if not items:
            return "- No evidence found."
        lines = []
        for item in items[:limit]:
            label = str(item.get(label_key, item.get("summary", "")))
            status = f" [{item.get('status')}]" if item.get("status") else ""
            source = f"{Path(str(item.get('source', ''))).name}:{item.get('line', '')}"
            evidence = str(item.get("evidence", item.get("summary", "")))
            lines.append(f"- `{label}`{status} ({source}) - {evidence}")
        return "\n".join(lines)

    stats = summary.get("stats", {})
    sources = summary.get("sources", [])
    source_lines = "\n".join(f"- `{Path(str(src.get('path', ''))).name}` ({src.get('encoding')}, {src.get('characters')} chars)" for src in sources) or "- No sources found."
    timeline_lines = "\n".join(
        f"- {item.get('type', 'event')}: {item.get('summary', '')} ({Path(str(item.get('source', ''))).name}:{item.get('line', '')})"
        for item in summary.get("timeline", [])[:20]
    ) or "- No timeline events found."

    return "\n".join([
        "# Agent Run Report",
        "",
        "## Executive Summary",
        f"- Sources analyzed: {stats.get('source_count', 0)}.",
        f"- Timeline events found: {stats.get('timeline_events', 0)}.",
        f"- Commands found: {stats.get('commands', 0)}; command statuses: {stats.get('command_statuses', {})}.",
        f"- Errors/interruption signals found: {stats.get('errors', 0)}.",
        "- This generated report is evidence-first; review the sections below before making final claims to a user.",
        "",
        "## Sources",
        source_lines,
        "",
        "## Timeline",
        timeline_lines,
        "",
        "## Files Touched",
        bullet_items(summary.get("files", []), "path"),
        "",
        "## Commands & Verification",
        bullet_items(summary.get("commands", []), "command"),
        "",
        "## Failures / Interruptions",
        bullet_items(summary.get("errors", []), "evidence"),
        "",
        "## Risk Review",
        "- Confirm whether the extracted command outputs are complete before claiming full verification.",
        "- Treat `signal_only` verification entries as weak evidence until paired with a successful command result.",
        "- Review file paths manually if the transcript includes generated text that resembles paths.",
        "",
        "## Next Actions",
        "- Use this Markdown as a draft, then replace generic bullets with run-specific conclusions.",
        "- If logs are long or code changes are risky, use the subagent workflow for timeline compression and risk review.",
        "",
        "## Showcase Output",
        "This run was converted into a structured, evidence-first report with timeline events, commands, files, failures, and verification signals. The report is suitable as a starting point for a user-facing recap, PR update, or debugging handoff.",
        "",
    ])


def render_html(summary: dict[str, Any], template_path: Path) -> str:
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        template = "<html><body><pre>{{REPORT_JSON}}</pre></body></html>"
    stats = summary.get("stats", {})
    stats_html = "\n".join([
        render_stat("Sources", stats.get("source_count", 0)),
        render_stat("Timeline", stats.get("timeline_events", 0)),
        render_stat("Commands", stats.get("commands", 0)),
        render_stat("Files", stats.get("files", 0)),
        render_stat("Errors", stats.get("errors", 0)),
        render_stat("Verification", stats.get("verification_signals", 0)),
    ])
    return (template
        .replace("{{GENERATED_AT}}", html.escape(str(summary.get("generated_at", ""))))
        .replace("{{STATS}}", stats_html)
        .replace("{{TIMELINE}}", render_timeline(summary.get("timeline", [])))
        .replace("{{FILES}}", render_list(summary.get("files", []), "path"))
        .replace("{{COMMANDS}}", render_list(summary.get("commands", []), "command"))
        .replace("{{VERIFICATION}}", render_list(summary.get("verification", []), "evidence", "item verify"))
        .replace("{{ERRORS}}", render_list(summary.get("errors", []), "evidence", "item error"))
        .replace("{{REPORT_JSON}}", html.escape(json.dumps(summary, ensure_ascii=False, indent=2))))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize coding-agent logs into JSON, Markdown, and HTML.")
    parser.add_argument("--input", required=True, help="Log/transcript file or directory containing text logs.")
    parser.add_argument("--out", default=default_output_dir(), help="Output directory for run-summary.json, report.md, and report.html.")
    parser.add_argument("--max-events", type=int, default=120, help="Maximum timeline events to include.")
    parser.add_argument("--max-items", type=int, default=80, help="Maximum files/commands/errors/verification items to include.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input path does not exist: {input_path}")

    files = iter_input_files(input_path)
    if not files:
        raise SystemExit(f"No supported text log files found under: {input_path}")

    sources = [read_text(path) for path in files]
    summary = summarize_sources(sources, max_events=args.max_events, max_items=args.max_items)

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "run-summary.json"
    md_path = out_dir / "report.md"
    html_path = out_dir / "report.html"
    template_path = Path(__file__).resolve().parent.parent / "assets" / "report-template.html"

    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    html_path.write_text(render_html(summary, template_path), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {html_path}")
    print(json.dumps(summary["stats"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
