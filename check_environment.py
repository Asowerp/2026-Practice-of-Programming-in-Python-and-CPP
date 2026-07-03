from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys


def _check_python() -> list[str]:
    lines = [
        "[Python]",
        f"executable: {sys.executable}",
        f"implementation: {sys.implementation.name}",
        f"version: {sys.version.splitlines()[0]}",
    ]
    if sys.implementation.name != "cpython":
        lines.append("note: GUI 建议使用 CPython；当前解释器可能不适合安装或运行 PySide6。")
    return lines


def _check_pyside6() -> list[str]:
    lines = ["", "[PySide6]"]
    if importlib.util.find_spec("PySide6") is None:
        lines.append("status: missing")
        lines.append("fix: 在准备用来启动 GUI 的 CPython 中执行 python -m pip install -r requirements.txt")
    else:
        lines.append("status: installed")
        try:
            import PySide6

            version = getattr(PySide6, "__version__", "unknown")
            lines.append(f"version: {version}")
        except Exception as exc:  # noqa: BLE001
            lines.append(f"warning: PySide6 可定位，但导入失败：{exc}")
    return lines


def _check_gpp() -> list[str]:
    lines = ["", "[g++]"]
    compiler = shutil.which("g++")
    if compiler is None:
        lines.append("status: missing")
        lines.append("note: C++ 骨架和 OJ 单文件仍可导出，但无法在本机自动编译验证。")
        return lines

    lines.append(f"path: {compiler}")
    result = subprocess.run(
        [compiler, "--version"],
        text=True,
        capture_output=True,
        check=False,
    )
    first_line = (result.stdout or result.stderr).splitlines()[0] if (result.stdout or result.stderr) else "unknown"
    lines.append(f"version: {first_line}")
    return lines


def _recommend_next_step() -> list[str]:
    lines = ["", "[Next step]"]
    if importlib.util.find_spec("PySide6") is None:
        if sys.implementation.name == "cpython":
            lines.append("当前 Python 是 CPython，但缺少 PySide6：运行 python -m pip install -r requirements.txt。")
        else:
            lines.append("当前 Python 不是 CPython：请先切换到 CPython，再安装 requirements.txt 并运行 python main.py。")
    else:
        lines.append("环境已具备 GUI 依赖：可以运行 python main.py。")
    lines.append("核心逻辑验证请运行 python run_regressions.py。")
    return lines


def main() -> None:
    sections = [
        *_check_python(),
        *_check_pyside6(),
        *_check_gpp(),
        *_recommend_next_step(),
    ]
    print("\n".join(sections))


if __name__ == "__main__":
    main()
