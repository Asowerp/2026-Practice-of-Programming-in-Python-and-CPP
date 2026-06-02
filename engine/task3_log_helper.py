from __future__ import annotations

from dataclasses import dataclass, field
from difflib import HtmlDiff

from engine.warcraft_engine import EventRecord, SimulationBundle


@dataclass
class LogComparison:
    matched: bool
    summary: str
    mismatches: list[str] = field(default_factory=list)
    html: str = ""


def build_log_text(events: list[EventRecord]) -> str:
    sorted_events = sorted(events, key=lambda event: (event.total_minutes, event.location_order))
    return "\n".join(event.to_log_line() for event in sorted_events)


def summarize_bundle(bundle: SimulationBundle) -> str:
    lines = [
        f"模式: {bundle.mode_label}",
        f"模板: {bundle.schedule.name}",
        f"事件数: {len(bundle.events)}",
    ]
    preview = sorted(bundle.events, key=lambda event: (event.total_minutes, event.location_order))[:5]
    for index, event in enumerate(preview, start=1):
        lines.append(f"{index}. {event.to_log_line()}")
    if len(bundle.events) > len(preview):
        lines.append(f"... 其余还有 {len(bundle.events) - len(preview)} 条事件")
    return "\n".join(lines)


def filter_events(
    events: list[EventRecord],
    *,
    hour: int | None = None,
    stage_key: str | None = None,
    city_keyword: str = "",
) -> list[EventRecord]:
    result = list(events)
    if hour is not None:
        result = [event for event in result if event.total_minutes // 60 == hour]
    if stage_key:
        result = [event for event in result if event.stage_key == stage_key]
    if city_keyword.strip():
        keyword = city_keyword.strip().lower()
        result = [event for event in result if keyword in event.description.lower()]
    return result


def compare_logs(expected_text: str, actual_text: str) -> LogComparison:
    expected_lines = expected_text.splitlines()
    actual_lines = actual_text.splitlines()
    mismatches: list[str] = []
    first_diff_line = -1

    for index in range(max(len(expected_lines), len(actual_lines))):
        expected_line = expected_lines[index] if index < len(expected_lines) else "<缺失>"
        actual_line = actual_lines[index] if index < len(actual_lines) else "<缺失>"
        if expected_line != actual_line:
            if first_diff_line < 0:
                first_diff_line = index + 1
            mismatches.append(
                f"第 {index + 1} 行不同：标准输出为 `{expected_line}`，你的输出为 `{actual_line}`。"
            )

    matched = not mismatches
    summary = "输出完全一致。" if matched else f"共发现 {len(mismatches)} 处行差异，首个差异在第 {first_diff_line} 行。"

    html_diff = HtmlDiff(wrapcolumn=88).make_table(
        expected_lines,
        actual_lines,
        fromdesc="标准输出",
        todesc="你的输出",
        context=False,
        numlines=0,
    )

    html = (
        "<html><head><style>"
        "body { font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; color: #1E293B; }"
        "table.diff { width: 100%; border-collapse: collapse; font-family: 'Cascadia Code', 'Consolas', monospace; }"
        "table.diff th, table.diff td { border: 1px solid #CBD5E1; padding: 4px 6px; vertical-align: top; }"
        ".diff_header { background: #E2E8F0; }"
        ".diff_add { background: #DCFCE7; }"
        ".diff_sub { background: #FEE2E2; }"
        ".diff_chg { background: #FEF3C7; }"
        "</style></head><body>"
        f"{html_diff}"
        "</body></html>"
    )

    return LogComparison(
        matched=matched,
        summary=summary,
        mismatches=mismatches,
        html=html,
    )
