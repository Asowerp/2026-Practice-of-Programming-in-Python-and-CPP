from __future__ import annotations

import argparse
import compileall
import importlib.util
import shutil
import subprocess
import tempfile
from pathlib import Path

from engine.class_manager import ClassManager
from engine.ai_log_assistant import (
    build_chat_completion_payload,
    build_model_config,
    explain_log_mismatch,
    get_model_names,
)
from engine.task2_cpp_exporter import export_task2_cpp_project
from engine.task3_log_helper import compare_logs, filter_events
from engine.task1_validator import validate_warcraft_entities, validate_warrior_hierarchy
from engine.warcraft_engine import WarcraftEngine, build_default_config, build_schedule_profile
from engine.warriors4_runner import solve_warriors4_file


ROOT = Path(__file__).resolve().parent


def _assert_equal(name: str, actual: str, expected: str) -> None:
    actual_normalized = actual.replace("\r\n", "\n")
    expected_normalized = expected.replace("\r\n", "\n")
    if actual_normalized == expected_normalized:
        print(f"[PASS] {name}")
        return

    actual_lines = actual_normalized.splitlines()
    expected_lines = expected_normalized.splitlines()
    for index in range(1, max(len(actual_lines), len(expected_lines)) + 1):
        actual_line = actual_lines[index - 1] if index <= len(actual_lines) else "<missing>"
        expected_line = expected_lines[index - 1] if index <= len(expected_lines) else "<missing>"
        if actual_line != expected_line:
            raise AssertionError(
                f"{name} failed at line {index}\n"
                f"actual  : {actual_line}\n"
                f"expected: {expected_line}"
            )
    raise AssertionError(f"{name} failed with an unknown diff.")


def check_compileall() -> None:
    if not compileall.compile_dir(str(ROOT), quiet=1):
        raise AssertionError("Python compileall failed.")
    print("[PASS] Python compileall")


def check_gui_imports_if_available(*, strict: bool = False) -> None:
    if importlib.util.find_spec("PySide6") is None:
        if strict:
            raise AssertionError(
                "GUI imports failed because PySide6 is not installed in this interpreter. "
                "Use a CPython environment and run: python -m pip install -r requirements.txt"
            )
        print("[SKIP] GUI imports: PySide6 not installed in this interpreter")
        return

    import ui.mainwindow  # noqa: F401
    import ui.task1_widget  # noqa: F401
    import ui.task2_widget  # noqa: F401
    import ui.task3_widget  # noqa: F401

    print("[PASS] GUI imports")


def check_ui_static_wiring() -> None:
    files = {
        "ui/mainwindow.py": (ROOT / "ui" / "mainwindow.py").read_text(encoding="utf-8"),
        "ui/task2_widget.py": (ROOT / "ui" / "task2_widget.py").read_text(encoding="utf-8"),
        "ui/task3_widget.py": (ROOT / "ui" / "task3_widget.py").read_text(encoding="utf-8"),
    }

    required_snippets = {
        "ui/mainwindow.py": [
            "self.task2_widget.eventsExported.connect(self.task3_widget.load_simulation_bundle)",
            "self.ui.tabWidget.removeTab(timeline_index)",
        ],
        "ui/task2_widget.py": [
            "from ui.timeline_panel import TimelinePanel",
            "self.timeline_controller = TimelineController(self.timeline_panel)",
            "self.export_mode_combo.addItem(\"OJ 单文件题解\", \"standalone\")",
            "self.export_mode_combo.addItem(\"模块化学习工程骨架\", \"skeleton\")",
            "export_task2_cpp_project(directory, config, schedule)",
            "self.manager.export_cpp_skeleton(directory)",
        ],
        "ui/task3_widget.py": [
            "from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot",
            "from ui.timeline_panel import TimelinePanel",
            "self.timeline_controller = TimelineController(self.timeline_panel)",
            "from engine.ai_log_assistant import AIDebugResult, build_model_config, explain_log_mismatch, get_model_names",
            "self.ai_model_combo.addItems(get_model_names())",
            "self.ai_key_edit.setEchoMode(QLineEdit.EchoMode.Password)",
            "class AIAnalysisWorker(QObject):",
            "progress = Signal(str)",
            "self.ai_worker.progress.connect(self._on_ai_progress)",
            "self.ai_thread = QThread(self)",
            "progress=self.progress.emit",
            "self.ai_output.setPlainText(result.suggestion)",
        ],
    }

    missing: list[str] = []
    for path, snippets in required_snippets.items():
        text = files[path]
        for snippet in snippets:
            if snippet not in text:
                missing.append(f"{path}: {snippet}")
    if missing:
        raise AssertionError("UI static wiring check failed:\n" + "\n".join(missing))
    forbidden_mainwindow_snippets = [
        "from ui.timeline_controller import TimelineController",
        "self.timeline_controller = TimelineController(self.ui)",
        "self.ui.tabWidget.setCurrentWidget(self.ui.timeline)",
    ]
    stale = [snippet for snippet in forbidden_mainwindow_snippets if snippet in files["ui/mainwindow.py"]]
    if stale:
        raise AssertionError(f"MainWindow still exposes standalone timeline wiring: {stale}")

    task3_text = files["ui/task3_widget.py"]
    run_ai_start = task3_text.index("    def run_ai_debug(self) -> None:")
    start_ai_start = task3_text.index("    def _start_ai_analysis(")
    run_ai_body = task3_text[run_ai_start:start_ai_start]
    forbidden_sync_ai_snippets = [
        "result = explain_log_mismatch(",
        "urlopen(",
    ]
    stale_ai = [snippet for snippet in forbidden_sync_ai_snippets if snippet in run_ai_body]
    if stale_ai:
        raise AssertionError(f"Task3 AI button callback still runs synchronous AI work: {stale_ai}")
    print("[PASS] UI static wiring")


def check_engine_layer_is_gui_free() -> None:
    offenders: list[str] = []
    for path in (ROOT / "engine").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "PySide6" in text:
            offenders.append(path.relative_to(ROOT).as_posix())
    if offenders:
        raise AssertionError(f"Engine layer should not import PySide6: {offenders}")
    print("[PASS] Engine layer has no GUI dependency")


def check_warriors4_sample(input_name: str, output_name: str) -> None:
    actual = solve_warriors4_file(ROOT / "warriors4_data" / input_name)
    expected = (ROOT / "warriors4_data" / output_name).read_text(encoding="utf-8")
    _assert_equal(f"Warriors4 {input_name}", actual, expected)


def check_task2_export_smoke() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        exported = export_task2_cpp_project(
            tmpdir,
            build_default_config(),
            build_schedule_profile(),
        )
        expected_files = {"task2_solution.cpp", "README.txt", "expected_log.txt", "MODULE_DESIGN.md"}
        missing = expected_files.difference(exported)
        if missing:
            raise AssertionError(f"Task2 export missing files: {sorted(missing)}")

        module_design = Path(tmpdir, "MODULE_DESIGN.md").read_text(encoding="utf-8")
        required_phrases = [
            "Task2 Module Design",
            "WarcraftEngine",
            "EventScheduleProfile",
            "HeadquarterState",
            "WarriorUnit",
            "WeaponSet",
            "WarriorFactory",
            "StageRunner",
            "MovementSystem",
            "WeaponSystem",
            "BattleResolver",
            "EventLog",
        ]
        missing_phrases = [phrase for phrase in required_phrases if phrase not in module_design]
        if missing_phrases:
            raise AssertionError(f"MODULE_DESIGN.md missing phrases: {missing_phrases}")

        compiler = shutil.which("g++")
        if compiler is None:
            print("[SKIP] Task2 standalone compile: g++ not found")
        else:
            compile_result = subprocess.run(
                [
                    compiler,
                    "-std=c++20",
                    "-O2",
                    "task2_solution.cpp",
                    "-o",
                    "task2_solution.exe",
                ],
                cwd=output_dir,
                text=True,
                capture_output=True,
                check=False,
            )
            if compile_result.returncode != 0:
                raise AssertionError(
                    "Task2 standalone C++ failed to compile.\n"
                    f"stdout:\n{compile_result.stdout}\n"
                    f"stderr:\n{compile_result.stderr}"
                )
            run_result = subprocess.run(
                [str(output_dir / "task2_solution.exe")],
                cwd=output_dir,
                text=True,
                capture_output=True,
                check=False,
            )
            if run_result.returncode != 0:
                raise AssertionError(
                    "Task2 standalone C++ failed to run.\n"
                    f"stdout:\n{run_result.stdout}\n"
                    f"stderr:\n{run_result.stderr}"
                )
            expected_log = (output_dir / "expected_log.txt").read_text(encoding="utf-8")
            _assert_equal("Task2 standalone C++ output", run_result.stdout, expected_log)
    print("[PASS] Task2 export smoke")


def check_task2_module_split() -> None:
    module_files = {
        "engine/warcraft_models.py": ["class WarcraftConfig", "class EventRecord"],
        "engine/warcraft_factory.py": ["def create_next_warrior", "def build_initial_weapons"],
        "engine/warcraft_queries.py": ["def alive_warriors", "def first_alive_enemy_at"],
        "engine/warcraft_battle_rules.py": ["def resolve_attacker", "def update_city_flag"],
        "engine/warcraft_reporting.py": ["def format_march", "def format_headquarter_reached"],
        "engine/warcraft_engine.py": ["create_next_warrior", "resolve_attacker", "alive_warriors"],
    }
    for relative_path, required_markers in module_files.items():
        path = ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"Task2 split module missing: {relative_path}")
        text = path.read_text(encoding="utf-8")
        missing = [marker for marker in required_markers if marker not in text]
        if missing:
            raise AssertionError(f"{relative_path} missing split markers: {missing}")

    for module_name in [
        "engine.warcraft_models",
        "engine.warcraft_factory",
        "engine.warcraft_queries",
        "engine.warcraft_battle_rules",
        "engine.warcraft_reporting",
        "engine.warcraft_engine",
    ]:
        if importlib.util.find_spec(module_name) is None:
            raise AssertionError(f"Task2 module cannot be imported: {module_name}")
    print("[PASS] Task2 module split is explicit and importable")


def check_task3_log_and_ai_helpers() -> None:
    config = build_default_config()
    schedule = build_schedule_profile()
    engine = WarcraftEngine(config, schedule)
    engine.initialize_case()
    engine.run_next_hour(max_steps=20)
    events = engine.export_bundle().events
    if not events:
        raise AssertionError("Task3 helper check expected at least one exported event.")

    spawn_events = filter_events(events, stage_key="spawn")
    if not spawn_events or any(event.stage_key != "spawn" for event in spawn_events):
        raise AssertionError("Task3 stage filtering failed for spawn events.")

    hour_zero_events = filter_events(events, hour=0)
    if not hour_zero_events or any(event.total_minutes // 60 != 0 for event in hour_zero_events):
        raise AssertionError("Task3 hour filtering failed for hour 0 events.")

    expected = "\n".join(event.to_log_line() for event in events[:3])
    comparison = compare_logs(expected, expected)
    if not comparison.matched or comparison.mismatches:
        raise AssertionError("Task3 exact log comparison should match.")

    mismatched = compare_logs(expected, expected + "\nextra line")
    if mismatched.matched or not mismatched.mismatches or "第 4 行不同" not in mismatched.mismatches[0]:
        raise AssertionError("Task3 mismatch comparison did not report the first differing line.")

    model_names = get_model_names()
    if "DeepSeek V4 Flash" not in model_names or "DeepSeek V4 Pro (Thinking)" not in model_names:
        raise AssertionError(f"AI model presets are incomplete: {model_names}")

    ai_config = build_model_config(
        "Codex / Custom OpenAI-Compatible",
        "  test-key  ",
        model_override="custom-debug-model",
        base_url_override="https://example.invalid/v1",
    )
    if ai_config.api_key != "test-key" or ai_config.model != "custom-debug-model":
        raise AssertionError("AI model config did not trim key or apply model override.")
    if ai_config.chat_completions_url != "https://example.invalid/v1/chat/completions":
        raise AssertionError("AI helper did not build the OpenAI-compatible chat completions URL.")

    no_key = build_model_config("DeepSeek V4 Flash", "")
    no_key_result = explain_log_mismatch(no_key, mismatched, expected_text=expected, actual_text=expected + "\nextra line")
    if no_key_result.ok or "API Key" not in no_key_result.message:
        raise AssertionError("AI helper should reject empty API keys before making a request.")

    deepseek_config = build_model_config("DeepSeek V4 Pro (Thinking)", "test-key")
    deepseek_payload = build_chat_completion_payload(deepseek_config, "debug prompt")
    if deepseek_config.chat_completions_url != "https://api.deepseek.com/chat/completions":
        raise AssertionError("DeepSeek base URL should follow the official OpenAI-compatible endpoint.")
    if deepseek_payload.get("model") != "deepseek-v4-pro":
        raise AssertionError("DeepSeek V4 Pro preset did not use the documented model id.")
    if deepseek_payload.get("thinking") != {"type": "enabled"} or deepseek_payload.get("reasoning_effort") != "high":
        raise AssertionError("DeepSeek thinking payload does not match the official API shape.")

    matched_result = explain_log_mismatch(ai_config, comparison, expected_text=expected, actual_text=expected)
    if not matched_result.ok or "完全一致" not in matched_result.message:
        raise AssertionError("AI helper should short-circuit matching logs without making a request.")

    print("[PASS] Task3 log and AI helpers")


def check_default_class_design() -> None:
    manager = ClassManager()
    manager.seed_demo_classes()

    warrior_result = validate_warrior_hierarchy(manager)
    if not warrior_result.ok:
        raise AssertionError("Default Warrior hierarchy failed validation:\n" + warrior_result.to_text())

    entity_result = validate_warcraft_entities(manager)
    if not entity_result.ok:
        raise AssertionError("Default Warcraft entity design failed validation:\n" + entity_result.to_text())

    warrior_cpp = manager.generate_cpp_code("Warrior")
    if "inline Warrior::Warrior()\n    :" in warrior_cpp:
        raise AssertionError("Generated C++ contains an empty constructor initializer list.")

    required_classes = {
        "Headquarter",
        "City",
        "Weapon",
        "Sword",
        "Bomb",
        "Arrow",
        "Warrior",
        "Dragon",
        "Ninja",
        "Iceman",
        "Lion",
        "Wolf",
    }
    missing = required_classes.difference(manager.get_class_names())
    if missing:
        raise AssertionError(f"Default class design missing classes: {sorted(missing)}")
    print("[PASS] Default modular class design")


def check_class_export_and_memory_layout() -> None:
    manager = ClassManager()
    manager.seed_demo_classes()

    blocks, total_size = manager.compute_memory_layout("Dragon")
    if total_size <= 0:
        raise AssertionError("Dragon memory layout should have a positive object size.")
    if not any(block.block_type == "vptr" for block in blocks):
        raise AssertionError("Dragon memory layout should include inherited vptr information.")
    if not any(block.name == "morale" and block.source_class == "Dragon" for block in blocks):
        raise AssertionError("Dragon memory layout should include Dragon::morale with source class.")
    if not any(block.name == "hp" and block.source_class == "Warrior" for block in blocks):
        raise AssertionError("Dragon memory layout should include inherited Warrior::hp with source class.")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        header_path = output_dir / "warcraft_classes.h"
        manager.export_all_cpp(str(header_path))
        header = header_path.read_text(encoding="utf-8")
        for class_name in ["Headquarter", "City", "Weapon", "Warrior", "Dragon", "Lion", "Wolf"]:
            if f"class {class_name}" not in header:
                raise AssertionError(f"Exported class header missing {class_name}.")

        smoke_cpp = output_dir / "class_export_smoke.cpp"
        smoke_cpp.write_text(
            '#include "warcraft_classes.h"\n'
            "int main() {\n"
            "    Warrior warrior;\n"
            "    Dragon dragon;\n"
            "    Lion lion;\n"
            "    Wolf wolf;\n"
            "    (void)warrior; (void)dragon; (void)lion; (void)wolf;\n"
            "    return 0;\n"
            "}\n",
            encoding="utf-8",
        )
        compiler = shutil.which("g++")
        if compiler is None:
            print("[SKIP] Class header compile: g++ not found")
        else:
            result = subprocess.run(
                [compiler, "-std=c++20", "-Wall", "-Wextra", "-pedantic", "class_export_smoke.cpp", "-o", "class_export_smoke.exe"],
                cwd=output_dir,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                raise AssertionError(
                    "Exported class header failed to compile.\n"
                    f"stdout:\n{result.stdout}\n"
                    f"stderr:\n{result.stderr}"
                )

    print("[PASS] Class export and memory layout")


def check_cpp_skeleton_compile() -> None:
    compiler = shutil.which("g++")
    if compiler is None:
        print("[SKIP] C++ skeleton compile: g++ not found")
        return

    manager = ClassManager()
    manager.seed_demo_classes()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        manager.export_cpp_skeleton(str(output_dir))
        generated_text = "\n".join(
            (output_dir / name).read_text(encoding="utf-8")
            for name in [
                "README.txt",
                "main.cpp",
                "game.h",
                "game.cpp",
                "headquarter.h",
                "headquarter.cpp",
                "city.h",
                "city.cpp",
                "warrior.h",
                "warrior.cpp",
                "weapon.h",
                "weapon.cpp",
            ]
        )
        forbidden_markers = [
            "Warcraft skeleton project",
            "TODO:",
            "not a complete",
            "不是可直接提交",
        ]
        found_markers = [marker for marker in forbidden_markers if marker in generated_text]
        if found_markers:
            raise AssertionError(f"C++ skeleton still contains placeholder markers: {found_markers}")
        sources = [
            "main.cpp",
            "game.cpp",
            "headquarter.cpp",
            "city.cpp",
            "warrior.cpp",
            "weapon.cpp",
        ]
        command = [
            compiler,
            "-std=c++20",
            "-Wall",
            "-Wextra",
            "-pedantic",
            *sources,
            "-o",
            "warcraft_skeleton.exe",
        ]
        result = subprocess.run(
            command,
            cwd=output_dir,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(
                "C++ skeleton failed to compile.\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        run_result = subprocess.run(
            [str(output_dir / "warcraft_skeleton.exe")],
            cwd=output_dir,
            text=True,
            capture_output=True,
            check=False,
        )
        if run_result.returncode != 0:
            raise AssertionError(
                "C++ skeleton failed to run.\n"
                f"stdout:\n{run_result.stdout}\n"
                f"stderr:\n{run_result.stderr}"
            )
        expected_snippets = [
            "Case 1:",
            "red iceman 1 born",
            "city 1 produced 10 elements",
            "elements in red headquarter",
        ]
        missing_snippets = [snippet for snippet in expected_snippets if snippet not in run_result.stdout]
        if missing_snippets:
            raise AssertionError(f"C++ skeleton run output missing snippets: {missing_snippets}")
    print("[PASS] C++ skeleton compile")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run project regression checks.")
    parser.add_argument(
        "--strict-gui",
        action="store_true",
        help="Fail if PySide6 is unavailable instead of marking GUI imports as skipped.",
    )
    args = parser.parse_args()

    check_compileall()
    check_gui_imports_if_available(strict=args.strict_gui)
    check_ui_static_wiring()
    check_engine_layer_is_gui_free()
    check_task2_module_split()
    check_default_class_design()
    check_class_export_and_memory_layout()
    check_cpp_skeleton_compile()
    check_task3_log_and_ai_helpers()
    check_warriors4_sample("extra.in", "extra.out")
    check_warriors4_sample("Warcraft.in", "Warcraft.out")
    check_task2_export_smoke()
    print("All regressions passed.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(f"[FAIL] {exc}")
        raise SystemExit(1) from exc
