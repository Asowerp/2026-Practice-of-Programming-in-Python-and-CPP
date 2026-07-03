from __future__ import annotations

from dataclasses import dataclass
import json
import urllib.error
import urllib.request

from engine.task3_log_helper import LogComparison


SUPPORTED_MODELS = {
    "DeepSeek Chat": {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/chat/completions",
    },
    "OpenAI GPT-4o mini": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1/chat/completions",
    },
    "OpenAI GPT-4.1 mini": {
        "provider": "openai",
        "model": "gpt-4.1-mini",
        "base_url": "https://api.openai.com/v1/chat/completions",
    },
    "Codex / Custom OpenAI-Compatible": {
        "provider": "custom",
        "model": "gpt-4.1-mini",
        "base_url": "https://api.openai.com/v1/chat/completions",
    },
}


@dataclass(frozen=True)
class AIModelConfig:
    display_name: str
    api_key: str
    model: str
    base_url: str


@dataclass(frozen=True)
class AIDebugResult:
    ok: bool
    message: str
    suggestion: str = ""


def get_model_names() -> list[str]:
    return list(SUPPORTED_MODELS)


def build_model_config(display_name: str, api_key: str, *, model_override: str = "", base_url_override: str = "") -> AIModelConfig:
    if display_name not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported AI model: {display_name}")
    preset = SUPPORTED_MODELS[display_name]
    return AIModelConfig(
        display_name=display_name,
        api_key=api_key.strip(),
        model=(model_override.strip() or str(preset["model"])),
        base_url=(base_url_override.strip() or str(preset["base_url"])),
    )


def explain_log_mismatch(
    config: AIModelConfig,
    comparison: LogComparison,
    *,
    expected_text: str,
    actual_text: str,
) -> AIDebugResult:
    if not config.api_key:
        return AIDebugResult(False, "请先填写 API Key。")
    if comparison.matched:
        return AIDebugResult(True, "输出已经完全一致，不需要 AI 调错。", "标准输出和你的输出逐行一致。")

    expected_lines = expected_text.splitlines()
    actual_lines = actual_text.splitlines()
    first_window = _build_first_diff_window(expected_lines, actual_lines)
    prompt = _build_prompt(comparison, first_window)
    payload = {
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是 C++ 程序设计课程的助教。请根据魔兽世界作业标准输出与学生输出的差异，"
                    "用中文给出简洁、可操作的调试建议。重点判断是时间点、顺序、生命元、武器、战斗结算、"
                    "司令部报告还是格式问题。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    request = urllib.request.Request(
        config.base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return AIDebugResult(False, f"AI 接口返回错误 {exc.code}: {detail[:500]}")
    except Exception as exc:
        return AIDebugResult(False, f"AI 请求失败: {exc}")

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return AIDebugResult(False, "AI 返回格式无法解析。", json.dumps(data, ensure_ascii=False)[:1000])
    return AIDebugResult(True, "AI 调错建议已生成。", str(content).strip())


def _build_prompt(comparison: LogComparison, first_window: str) -> str:
    mismatch_preview = "\n".join(comparison.mismatches[:12])
    return (
        f"对比摘要：{comparison.summary}\n\n"
        f"前几处差异：\n{mismatch_preview}\n\n"
        f"首个差异附近的标准输出与学生输出：\n{first_window}\n\n"
        "请按以下结构回答：\n"
        "1. 最可能的错误原因\n"
        "2. 应优先检查的 C++ 模块或函数\n"
        "3. 一到三条具体修改建议\n"
        "4. 如果像是纯格式问题，请明确指出格式细节"
    )


def _build_first_diff_window(expected_lines: list[str], actual_lines: list[str], radius: int = 4) -> str:
    first = 0
    for index in range(max(len(expected_lines), len(actual_lines))):
        expected = expected_lines[index] if index < len(expected_lines) else ""
        actual = actual_lines[index] if index < len(actual_lines) else ""
        if expected != actual:
            first = index
            break
    start = max(0, first - radius)
    end = min(max(len(expected_lines), len(actual_lines)), first + radius + 1)
    rows = []
    for index in range(start, end):
        expected = expected_lines[index] if index < len(expected_lines) else "<缺失>"
        actual = actual_lines[index] if index < len(actual_lines) else "<缺失>"
        rows.append(f"{index + 1}: 标准: {expected}\n{index + 1}: 学生: {actual}")
    return "\n".join(rows)
