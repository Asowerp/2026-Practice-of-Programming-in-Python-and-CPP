from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.block_workspace import BlockProgramEditor, BlockSpec, FieldSpec
from engine.class_manager import ClassManager
from engine.task3_log_helper import build_log_text, compare_logs, filter_events, summarize_bundle
from engine.warcraft_engine import STANDARD_STAGE_DEFINITIONS, SimulationBundle


class Task3Widget(QWidget):
    def __init__(self, manager: ClassManager | None = None) -> None:
        super().__init__()
        self.manager = manager or ClassManager.get_instance()
        self.imported_bundle: SimulationBundle | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("Task3：完整日志生成与对拍")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel(
            "Task3 只负责消费 Task2 导出的整局事件流。可以生成标准日志，也可以基于自定义教学模式筛选小时、阶段和关键词。"
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 13px;")
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        action_row = QHBoxLayout()
        self.example_btn = QPushButton("加载推荐积木")
        self.run_btn = QPushButton("执行日志脚本")
        self.run_btn.setObjectName("btnPrimary")
        self.clear_btn = QPushButton("清空差异视图")
        self.example_btn.clicked.connect(self.load_example_script)
        self.run_btn.clicked.connect(self.run_script)
        self.clear_btn.clicked.connect(self.clear_outputs)
        action_row.addWidget(self.example_btn)
        action_row.addWidget(self.run_btn)
        action_row.addWidget(self.clear_btn)
        action_row.addStretch(1)
        main_layout.addLayout(action_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.block_editor = BlockProgramEditor(self._build_block_specs())
        splitter.addWidget(self.block_editor)
        splitter.addWidget(self._build_result_panel())
        splitter.setSizes([860, 520])
        main_layout.addWidget(splitter)

    def _build_result_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        self.import_status_label = QLabel("尚未接收 Task2 导出的整局事件流。")
        self.import_status_label.setStyleSheet("font-weight: 700; color: #4F46E5;")
        layout.addWidget(self.import_status_label)

        self.summary_label = QLabel("导入 Task2 结果后，再用左侧积木生成标准日志并对拍。")
        self.summary_label.setStyleSheet("font-weight: 700; color: #4F46E5;")
        layout.addWidget(self.summary_label)

        process_group = QGroupBox("解释执行日志")
        process_layout = QVBoxLayout(process_group)
        self.process_output = QPlainTextEdit()
        self.process_output.setReadOnly(True)
        process_layout.addWidget(self.process_output)
        layout.addWidget(process_group)

        text_row = QHBoxLayout()

        expected_group = QGroupBox("当前标准日志")
        expected_layout = QVBoxLayout(expected_group)
        self.expected_output = QPlainTextEdit()
        self.expected_output.setReadOnly(True)
        expected_layout.addWidget(self.expected_output)

        actual_group = QGroupBox("你的输出")
        actual_layout = QVBoxLayout(actual_group)
        self.actual_output = QPlainTextEdit()
        self.actual_output.setPlaceholderText("把你程序的输出粘贴到这里，再执行“对比我的输出”。")
        actual_layout.addWidget(self.actual_output)

        text_row.addWidget(expected_group)
        text_row.addWidget(actual_group)
        layout.addLayout(text_row, 1)

        diff_group = QGroupBox("差异高亮")
        diff_layout = QVBoxLayout(diff_group)
        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        diff_layout.addWidget(self.diff_view)
        layout.addWidget(diff_group, 1)
        return container

    def _build_block_specs(self) -> list[BlockSpec]:
        stage_keys = [definition.key for definition in STANDARD_STAGE_DEFINITIONS]
        return [
            BlockSpec(
                key="use_imported_bundle",
                title="使用 Task2 导入结果",
                color="#2563EB",
                description="读取 Task2 导出的整局事件流、Case 参数和阶段日程。",
            ),
            BlockSpec(
                key="inspect_bundle",
                title="查看当前导入摘要",
                color="#0891B2",
                description="查看当前是标准题面模式还是自定义教学模式，并预览前几条事件。",
            ),
            BlockSpec(
                key="filter_hour",
                title="按小时筛选",
                color="#16A34A",
                description="只保留某个小时内的事件，用来单独查看 0 点、1 点等局部输出。",
                fields=[
                    FieldSpec("hour", "小时", "int", 0, minimum=0, maximum=100, width=140),
                ],
            ),
            BlockSpec(
                key="filter_stage",
                title="按阶段筛选",
                color="#22C55E",
                description="只保留某类阶段，如 spawn / march / battle。",
                fields=[
                    FieldSpec("stage_key", "阶段", "combo", stage_keys[0], stage_keys, editable=False, width=170),
                ],
            ),
            BlockSpec(
                key="filter_keyword",
                title="按关键词筛选",
                color="#65A30D",
                description="按关键词过滤事件描述，例如 city 1、dragon、headquarter。",
                fields=[
                    FieldSpec("keyword", "关键词", "text", "city 1", width=170, placeholder="例如 city 1"),
                ],
            ),
            BlockSpec(
                key="generate_log",
                title="生成当前日志",
                color="#EA580C",
                description="把当前筛选后的事件序列转换成标准文本。",
            ),
            BlockSpec(
                key="compare_output",
                title="对比我的输出",
                color="#DC2626",
                description="将当前生成的日志与右侧“你的输出”逐行比较。",
            ),
            BlockSpec(
                key="reset_filters",
                title="清空筛选链",
                color="#475569",
                description="恢复为导入时的完整事件流。",
            ),
        ]

    def load_example_script(self) -> None:
        self.block_editor.set_script([
            {"key": "use_imported_bundle", "fields": {}},
            {"key": "inspect_bundle", "fields": {}},
            {"key": "generate_log", "fields": {}},
            {"key": "compare_output", "fields": {}},
        ])

    def clear_outputs(self) -> None:
        self.process_output.clear()
        self.expected_output.clear()
        self.diff_view.clear()
        self.summary_label.setText("输出已清空。")
        self.summary_label.setStyleSheet("font-weight: 700; color: #4F46E5;")

    def load_simulation_bundle(self, bundle: object) -> None:
        if not isinstance(bundle, SimulationBundle):
            self.imported_bundle = None
            self.import_status_label.setText("收到的数据不是合法的 Task2 模拟结果。")
            self.import_status_label.setStyleSheet("font-weight: 700; color: #DC2626;")
            return
        self.imported_bundle = bundle
        self.import_status_label.setText(
            f"已接收 Task2 导出的 {len(bundle.events)} 条事件，当前模式：{bundle.mode_label}。"
        )
        self.import_status_label.setStyleSheet("font-weight: 700; color: #4F46E5;")
        self.process_output.setPlainText(summarize_bundle(bundle))

    def run_script(self) -> None:
        script = self.block_editor.get_script()
        if not script:
            self.summary_label.setText("工作区还是空的，请先拖拽日志积木。")
            self.summary_label.setStyleSheet("font-weight: 700; color: #DC2626;")
            return

        context: dict[str, object] = {
            "bundle": None,
            "events": [],
            "log_text": "",
        }
        messages: list[str] = []
        last_summary = "日志脚本执行结束。"
        last_html = ""

        for index, block in enumerate(script, start=1):
            ok, message, summary, html = self._execute_block(context, str(block.get("key", "")), block.get("fields", {}))
            prefix = "[通过]" if ok else "[错误]"
            messages.append(f"{prefix} 积木 {index}: {message}")
            if summary:
                last_summary = summary
            if html:
                last_html = html

        self.process_output.setPlainText("\n".join(messages))
        self.expected_output.setPlainText(str(context.get("log_text", "")))
        self.diff_view.setHtml(last_html)
        self.summary_label.setText(last_summary)
        color = "#16A34A" if "完全一致" in last_summary else "#4F46E5"
        if "差异" in last_summary:
            color = "#DC2626"
        self.summary_label.setStyleSheet(f"font-weight: 700; color: {color};")

    def _execute_block(self, context: dict[str, object], key: str, fields: dict[str, object]) -> tuple[bool, str, str, str]:
        bundle = context.get("bundle")
        events = context.get("events")
        if key == "use_imported_bundle":
            if self.imported_bundle is None:
                return False, "当前还没有从 Task2 导入整局事件流。", "", ""
            context["bundle"] = self.imported_bundle
            context["events"] = list(self.imported_bundle.events)
            return True, f"已载入 {len(self.imported_bundle.events)} 条事件。", f"当前模式：{self.imported_bundle.mode_label}", ""

        if key == "inspect_bundle":
            if not isinstance(bundle, SimulationBundle):
                return False, "请先使用 Task2 导入结果。", "", ""
            return True, summarize_bundle(bundle), f"当前模式：{bundle.mode_label}", ""

        if key == "filter_hour":
            if not isinstance(events, list):
                return False, "当前没有事件流，请先导入 Task2 结果。", "", ""
            hour = int(fields.get("hour", 0))
            context["events"] = filter_events(events, hour=hour)
            return True, f"已筛选到第 {hour} 小时，共剩余 {len(context['events'])} 条事件。", "", ""

        if key == "filter_stage":
            if not isinstance(events, list):
                return False, "当前没有事件流，请先导入 Task2 结果。", "", ""
            stage_key = str(fields.get("stage_key", "")).strip()
            context["events"] = filter_events(events, stage_key=stage_key)
            return True, f"已筛选阶段 {stage_key}，共剩余 {len(context['events'])} 条事件。", "", ""

        if key == "filter_keyword":
            if not isinstance(events, list):
                return False, "当前没有事件流，请先导入 Task2 结果。", "", ""
            keyword = str(fields.get("keyword", "")).strip()
            context["events"] = filter_events(events, city_keyword=keyword)
            return True, f"已按关键词 `{keyword}` 筛选，共剩余 {len(context['events'])} 条事件。", "", ""

        if key == "generate_log":
            if not isinstance(events, list):
                return False, "当前没有事件流，请先导入 Task2 结果。", "", ""
            context["log_text"] = build_log_text(events)
            if not str(context["log_text"]).strip():
                return True, "当前筛选链下没有可输出的事件。", "日志已生成，但为空。", ""
            return True, f"已生成 {len(str(context['log_text']).splitlines())} 行日志。", "标准日志已生成。", ""

        if key == "compare_output":
            log_text = str(context.get("log_text", ""))
            if not log_text.strip():
                return False, "请先生成当前日志。", "", ""
            comparison = compare_logs(log_text, self.actual_output.toPlainText())
            return comparison.matched, comparison.summary, comparison.summary, comparison.html

        if key == "reset_filters":
            if not isinstance(bundle, SimulationBundle):
                return False, "当前没有导入结果可恢复。", "", ""
            context["events"] = list(bundle.events)
            context["log_text"] = ""
            return True, "已恢复为导入时的完整事件流。", "筛选链已清空。", ""

        return False, f"未知积木 {key}。", "", ""
