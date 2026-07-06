from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from urllib.parse import urlparse
import urllib.error
import urllib.request

from engine.task3_log_helper import LogComparison


CHAT_COMPLETIONS_PATH = "/chat/completions"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 30
ProgressCallback = Callable[[str], None]

SUPPORTED_MODELS = {
    "DeepSeek V4 Flash": {
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com",
        "thinking": "disabled",
        "reasoning_effort": "",
    },
    "DeepSeek V4 Pro (Thinking)": {
        "provider": "deepseek",
        "model": "deepseek-v4-pro",
        "base_url": "https://api.deepseek.com",
        "thinking": "enabled",
        "reasoning_effort": "high",
    },
    "OpenAI GPT-4o mini": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
        "thinking": "",
        "reasoning_effort": "",
    },
    "OpenAI GPT-4.1 mini": {
        "provider": "openai",
        "model": "gpt-4.1-mini",
        "base_url": "https://api.openai.com/v1",
        "thinking": "",
        "reasoning_effort": "",
    },
    "Codex / Custom OpenAI-Compatible": {
        "provider": "custom",
        "model": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com",
        "thinking": "",
        "reasoning_effort": "",
    },
}

MODEL_ALIASES = {
    "DeepSeek Chat": "DeepSeek V4 Flash",
}


@dataclass(frozen=True)
class AIModelConfig:
    display_name: str
    api_key: str
    model: str
    base_url: str
    provider: str = "custom"
    thinking: str = ""
    reasoning_effort: str = ""

    @property
    def chat_completions_url(self) -> str:
        return build_chat_completions_url(self.base_url)


@dataclass(frozen=True)
class AIDebugResult:
    ok: bool
    message: str
    suggestion: str = ""


def get_model_names() -> list[str]:
    return list(SUPPORTED_MODELS)


def build_model_config(
    display_name: str,
    api_key: str,
    *,
    model_override: str = "",
    base_url_override: str = "",
) -> AIModelConfig:
    preset_name = MODEL_ALIASES.get(display_name, display_name)
    if preset_name not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported AI model: {display_name}")
    preset = SUPPORTED_MODELS[preset_name]
    model = model_override.strip() or str(preset["model"])
    base_url = normalize_base_url(base_url_override.strip() or str(preset["base_url"]))
    thinking = str(preset.get("thinking", ""))
    reasoning_effort = str(preset.get("reasoning_effort", ""))
    if model_override.strip() and preset["provider"] == "deepseek":
        thinking, reasoning_effort = infer_deepseek_thinking(model)
    return AIModelConfig(
        display_name=preset_name,
        api_key=api_key.strip(),
        model=model,
        base_url=base_url,
        provider=str(preset["provider"]),
        thinking=thinking,
        reasoning_effort=reasoning_effort,
    )


def explain_log_mismatch(
    config: AIModelConfig,
    comparison: LogComparison,
    *,
    expected_text: str,
    actual_text: str,
    progress: ProgressCallback | None = None,
    timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
) -> AIDebugResult:
    _emit_progress(progress, "AI 正在检查输入...")
    if not config.api_key:
        return AIDebugResult(False, "请先填写 API Key。")
    if comparison.matched:
        return AIDebugResult(True, "输出已经完全一致，不需要 AI 调错。", "标准输出和你的输出逐行一致。")

    _emit_progress(progress, "AI 正在整理首个差异窗口...")
    expected_lines = expected_text.splitlines()
    actual_lines = actual_text.splitlines()
    first_window = _build_first_diff_window(expected_lines, actual_lines)
    _emit_progress(progress, "AI 正在构造调试提示词...")
    prompt = _build_prompt(comparison, first_window)
    payload = build_chat_completion_payload(config, prompt)
    _emit_progress(progress, f"AI 正在连接 {config.model}...")
    request = urllib.request.Request(
        config.chat_completions_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            _emit_progress(progress, "AI 正在思考中，正在接收返回内容...")
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return AIDebugResult(False, f"AI 接口返回错误 {exc.code}: {detail[:800]}")
    except urllib.error.URLError as exc:
        return AIDebugResult(False, f"AI 请求失败: {exc.reason}")
    except Exception as exc:
        return AIDebugResult(False, f"AI 请求失败: {exc}")

    _emit_progress(progress, "AI 正在解析调试建议...")
    return parse_chat_completion_response(data)


def _emit_progress(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)


def build_chat_completion_payload(config: AIModelConfig, prompt: str) -> dict[str, object]:
    payload: dict[str, object] = {
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是 C++ 程序设计课程的助教。请根据《魔兽世界》作业的标准输出和学生输出差异，"
                    "用中文给出简洁、可操作的调试建议。重点判断时间点、事件顺序、生命元、武器、"
                    "战斗结算、司令部报告或纯格式问题。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }
    if config.provider == "deepseek" or "api.deepseek.com" in config.base_url:
        if config.thinking in {"enabled", "disabled"}:
            payload["thinking"] = {"type": config.thinking}
        if config.reasoning_effort:
            payload["reasoning_effort"] = config.reasoning_effort
    if config.thinking != "enabled":
        payload["temperature"] = 0.2
    return payload


def parse_chat_completion_response(data: object) -> AIDebugResult:
    if not isinstance(data, dict):
        return AIDebugResult(False, "AI 返回格式无法解析。", str(data)[:1000])
    try:
        choice = data["choices"][0]
        message = choice["message"]
        content = message.get("content")
    except (KeyError, IndexError, TypeError, AttributeError):
        return AIDebugResult(False, "AI 返回格式无法解析。", json.dumps(data, ensure_ascii=False)[:1000])
    if not content:
        fallback = message.get("reasoning_content") if isinstance(message, dict) else ""
        return AIDebugResult(False, "AI 没有返回最终调试建议。", str(fallback or data)[:1000])
    finish_reason = str(choice.get("finish_reason", "")) if isinstance(choice, dict) else ""
    suffix = ""
    if finish_reason and finish_reason != "stop":
        suffix = f"\n\n[提示] finish_reason={finish_reason}，建议必要时减少日志窗口或提高 max_tokens。"
    return AIDebugResult(True, "AI 调试建议已生成。", str(content).strip() + suffix)


def normalize_base_url(base_url: str) -> str:
    base_url = base_url.strip().rstrip("/")
    if not base_url:
        raise ValueError("AI 接口地址不能为空。")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"AI 接口地址无效: {base_url}")
    return base_url


def build_chat_completions_url(base_url: str) -> str:
    base_url = normalize_base_url(base_url)
    if base_url.endswith(CHAT_COMPLETIONS_PATH):
        return base_url
    return base_url + CHAT_COMPLETIONS_PATH


def infer_deepseek_thinking(model: str) -> tuple[str, str]:
    if model == "deepseek-v4-pro":
        return "enabled", "high"
    if model == "deepseek-v4-flash":
        return "disabled", ""
    if model == "deepseek-reasoner":
        return "enabled", "high"
    if model == "deepseek-chat":
        return "disabled", ""
    return "", ""


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
