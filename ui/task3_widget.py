from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from engine.ai_log_assistant import AIDebugResult, build_model_config, explain_log_mismatch, get_model_names
from engine.class_manager import ClassManager
from engine.task3_log_helper import LogComparison, build_log_text, compare_logs, filter_events, summarize_bundle
from engine.warcraft_engine import STANDARD_STAGE_DEFINITIONS, SimulationBundle
from ui.block_workspace import BlockProgramEditor, BlockSpec, FieldSpec
from ui.timeline_controller import TimelineController
from ui.timeline_panel import TimelinePanel


class AIAnalysisWorker(QObject):
    progress = Signal(str)
    finished = Signal(object)

    def __init__(self, config, comparison: LogComparison, expected_text: str, actual_text: str) -> None:
        super().__init__()
        self.config = config
        self.comparison = comparison
        self.expected_text = expected_text
        self.actual_text = actual_text

    @Slot()
    def run(self) -> None:
        try:
            result = explain_log_mismatch(
                self.config,
                self.comparison,
                expected_text=self.expected_text,
                actual_text=self.actual_text,
                progress=self.progress.emit,
            )
        except Exception as exc:
            result = AIDebugResult(False, f"AI 分析线程异常: {exc}")
        self.finished.emit(result)


class Task3Widget(QWidget):
    def __init__(self, manager: ClassManager | None = None) -> None:
        super().__init__()
        self.manager = manager or ClassManager.get_instance()
        self.imported_bundle: SimulationBundle | None = None
        self.last_comparison: LogComparison | None = None
        self.timeline_controller: TimelineController | None = None
        self.ai_thread: QThread | None = None
        self.ai_worker: AIAnalysisWorker | None = None
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
            "Task3 消费 Task2 导出的整局事件流。可以生成标准日志、筛选局部事件、对比学生输出，"
            "并在提供 API Key 后让 AI 辅助定位格式或逻辑错误。"
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
        self.ai_btn = QPushButton("AI 分析差异")
        self.example_btn.setToolTip("自动填入导入、生成日志、对拍输出的推荐流程。")
        self.run_btn.setToolTip("按左侧积木顺序生成标准日志并对拍你的输出。")
        self.clear_btn.setToolTip("清空右侧日志、差异和 AI 建议，不删除左侧积木脚本。")
        self.ai_btn.setToolTip("在存在差异时，用所选模型辅助定位原因。")
        self.example_btn.clicked.connect(self.load_example_script)
        self.run_btn.clicked.connect(self.run_script)
        self.clear_btn.clicked.connect(self.clear_outputs)
        self.ai_btn.clicked.connect(self.run_ai_debug)
        action_row.addWidget(self.example_btn)
        action_row.addWidget(self.run_btn)
        action_row.addWidget(self.clear_btn)
        action_row.addWidget(self.ai_btn)
        action_row.addStretch(1)
        main_layout.addLayout(action_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        self.block_editor = BlockProgramEditor(self._build_block_specs())
        splitter.addWidget(self.block_editor)
        splitter.addWidget(self._build_result_panel())
        splitter.setSizes([600, 780])
        splitter.setToolTip("拖动中间的分隔线可以调整左右面板宽度")
        main_layout.addWidget(splitter)
        self._refresh_ai_button_state()

    def _build_result_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        self.import_status_label = QLabel("尚未接收 Task2 导出的整局事件流。")
        self.import_status_label.setStyleSheet("font-weight: 700; color: #4F46E5;")
        layout.addWidget(self.import_status_label)

        self.summary_label = QLabel("导入 Task2 结果后，再用左侧积木生成标准日志并对拍。")
        self.summary_label.setStyleSheet("font-weight: 700; color: #4F46E5;")
        layout.addWidget(self.summary_label)

        right_splitter = QSplitter(Qt.Orientation.Horizontal)
        right_splitter.setHandleWidth(1)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        timeline_group = QGroupBox("导入事件时间轴")
        timeline_layout = QVBoxLayout(timeline_group)
        self.timeline_panel = TimelinePanel(
            "Task3 对拍时间轴",
            "从 Task2 导入事件后，这里会显示同一条事件流，便于按时间定位日志差异。",
        )
        self.timeline_controller = TimelineController(self.timeline_panel)
        self.timeline_controller.eventSelected.connect(self.focus_timeline_event)
        timeline_layout.addWidget(self.timeline_panel)
        left_layout.addWidget(timeline_group, 1)

        ai_group = QGroupBox("AI 调错助手")
        ai_layout = QFormLayout(ai_group)
        self.ai_model_combo = QComboBox()
        self.ai_model_combo.addItems(get_model_names())
        self.ai_key_edit = QLineEdit()
        self.ai_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.ai_key_edit.setPlaceholderText("填写 API Key，仅用于本次请求，不会保存")
        self.ai_model_override_edit = QLineEdit()
        self.ai_model_override_edit.setPlaceholderText("可选：覆盖模型名，例如 deepseek-v4-flash 或 deepseek-v4-pro")
        self.ai_base_url_edit = QLineEdit()
        self.ai_base_url_edit.setPlaceholderText("可选：OpenAI 兼容 base URL，例如 https://api.deepseek.com")
        ai_layout.addRow("模型", self.ai_model_combo)
        ai_layout.addRow("API Key", self.ai_key_edit)
        ai_layout.addRow("模型名", self.ai_model_override_edit)
        ai_layout.addRow("接口地址", self.ai_base_url_edit)
        left_layout.addWidget(ai_group)

        process_group = QGroupBox("脚本执行日志")
        process_layout = QVBoxLayout(process_group)
        self.process_output = QPlainTextEdit()
        self.process_output.setReadOnly(True)
        self.process_output.setPlaceholderText("执行日志脚本后，这里会显示每个积木的处理结果。")
        process_layout.addWidget(self.process_output)
        left_layout.addWidget(process_group)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        text_row = QHBoxLayout()

        expected_group = QGroupBox("当前标准日志")
        expected_layout = QVBoxLayout(expected_group)
        self.expected_output = QPlainTextEdit()
        self.expected_output.setReadOnly(True)
        self.expected_output.setPlaceholderText("生成标准日志后会显示在这里。")
        expected_layout.addWidget(self.expected_output)

        actual_group = QGroupBox("你的输出")
        actual_layout = QVBoxLayout(actual_group)
        self.actual_output = QPlainTextEdit()
        self.actual_output.setPlaceholderText("把你程序的输出粘贴到这里，再执行“对比我的输出”。")
        actual_layout.addWidget(self.actual_output)

        text_row.addWidget(expected_group)
        text_row.addWidget(actual_group)
        right_layout.addLayout(text_row, 1)

        diff_group = QGroupBox("差异高亮")
        diff_layout = QVBoxLayout(diff_group)
        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setPlaceholderText("执行“对比我的输出”后，这里会显示逐行差异。")
        diff_layout.addWidget(self.diff_view)
        right_layout.addWidget(diff_group, 1)

        ai_result_group = QGroupBox("AI 调错建议")
        ai_result_layout = QVBoxLayout(ai_result_group)
        self.ai_output = QPlainTextEdit()
        self.ai_output.setReadOnly(True)
        self.ai_output.setPlaceholderText("先执行日志脚本并产生差异，再点击“AI 分析差异”。")
        ai_result_layout.addWidget(self.ai_output)
        right_layout.addWidget(ai_result_group, 1)

        right_splitter.addWidget(left_widget)
        right_splitter.addWidget(right_widget)
        right_splitter.setSizes([320, 460])
        right_splitter.setToolTip("拖动分隔线可调整右侧两栏宽度")
        layout.addWidget(right_splitter, 1)

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
                description="只保留某个小时内的事件，用来单独查看局部输出。",
                fields=[
                    FieldSpec("hour", "小时", "int", 0, minimum=0, maximum=100, width=140),
                ],
            ),
            BlockSpec(
                key="filter_stage",
                title="按阶段筛选",
                color="#22C55E",
                description="只保留某类阶段，例如 spawn / march / battle。",
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
        self.summary_label.setText("已加载推荐积木。下一步先从 Task2 导入事件，再点击“执行日志脚本”。")
        self.summary_label.setStyleSheet("font-weight: 700; color: #4F46E5;")

    def clear_outputs(self) -> None:
        self.process_output.clear()
        self.expected_output.clear()
        self.diff_view.clear()
        self.ai_output.clear()
        self.last_comparison = None
        if self.timeline_controller is not None and self.imported_bundle is None:
            self.timeline_controller.set_events([])
        self.summary_label.setText("输出已清空。导入结果和左侧脚本仍保留，可继续对拍。")
        self.summary_label.setStyleSheet("font-weight: 700; color: #4F46E5;")
        self._refresh_ai_button_state()

    def load_simulation_bundle(self, bundle: object) -> None:
        if not isinstance(bundle, SimulationBundle):
            self.imported_bundle = None
            self.import_status_label.setText("收到的数据不是合法的 Task2 模拟结果。")
            self.import_status_label.setStyleSheet("font-weight: 700; color: #DC2626;")
            if self.timeline_controller is not None:
                self.timeline_controller.set_events([])
            return
        self.imported_bundle = bundle
        self.import_status_label.setText(
            f"已接收 Task2 导出的 {len(bundle.events)} 条事件，当前模式：{bundle.mode_label}。"
        )
        self.import_status_label.setStyleSheet("font-weight: 700; color: #4F46E5;")
        self.process_output.setPlainText(summarize_bundle(bundle))
        if self.timeline_controller is not None:
            self.timeline_controller.load_simulation_bundle(bundle)
        self.summary_label.setText("Task2 事件已导入。下一步加载推荐积木或执行已有日志脚本。")
        self.summary_label.setStyleSheet("font-weight: 700; color: #4F46E5;")
        self._refresh_ai_button_state()

    def focus_timeline_event(self, index: int, event: object) -> None:
        event_time = getattr(event, "display_time", "--:--")
        stage_key = getattr(event, "stage_key", "unknown")
        description = getattr(event, "description", str(event))
        self.summary_label.setText(f"时间轴已定位到事件 #{index + 1}：{event_time} / {stage_key}。")
        self.summary_label.setStyleSheet("font-weight: 700; color: #4F46E5;")
        if self.expected_output.toPlainText().strip():
            matching_line = event.to_log_line() if hasattr(event, "to_log_line") else description
            self.diff_view.setHtml(
                "<div style='font-family:Consolas,monospace; padding:10px;'>"
                f"<b>当前时间轴事件 #{index + 1}</b><br>"
                f"时间：{event_time}<br>阶段：{stage_key}<br>"
                f"<pre style='white-space:pre-wrap;'>{matching_line}</pre>"
                "</div>"
            )

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
        self.last_comparison = None

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
        self._refresh_ai_button_state()

    def run_ai_debug(self) -> None:
        expected_text = self.expected_output.toPlainText()
        actual_text = self.actual_output.toPlainText()
        if not expected_text.strip():
            self.ai_output.setPlainText("请先执行日志脚本，生成当前标准日志。")
            self._refresh_ai_button_state()
            return
        comparison = self.last_comparison or compare_logs(expected_text, actual_text)
        if comparison.matched:
            self.ai_output.setPlainText("输出已经完全一致，不需要 AI 调错。")
            self._refresh_ai_button_state()
            return
        try:
            config = build_model_config(
                self.ai_model_combo.currentText(),
                self.ai_key_edit.text(),
                model_override=self.ai_model_override_edit.text(),
                base_url_override=self.ai_base_url_edit.text(),
            )
        except ValueError as exc:
            self.ai_output.setPlainText(str(exc))
            return

        self._start_ai_analysis(config, comparison, expected_text, actual_text)

    def _start_ai_analysis(self, config, comparison: LogComparison, expected_text: str, actual_text: str) -> None:
        if self.ai_thread is not None and self.ai_thread.isRunning():
            self.ai_output.setPlainText("AI 正在思考中，请等待当前分析完成。")
            return

        self.ai_output.setPlainText("AI 正在思考中：准备发送差异摘要...")
        self.ai_btn.setEnabled(False)
        self.ai_btn.setText("AI 分析中...")

        self.ai_thread = QThread(self)
        self.ai_worker = AIAnalysisWorker(config, comparison, expected_text, actual_text)
        self.ai_worker.moveToThread(self.ai_thread)
        self.ai_thread.started.connect(self.ai_worker.run)
        self.ai_worker.progress.connect(self._on_ai_progress)
        self.ai_worker.finished.connect(self._on_ai_finished)
        self.ai_worker.finished.connect(self.ai_thread.quit)
        self.ai_worker.finished.connect(self.ai_worker.deleteLater)
        self.ai_thread.finished.connect(self._cleanup_ai_thread)
        self.ai_thread.start()

    @Slot(str)
    def _on_ai_progress(self, message: str) -> None:
        self.ai_output.setPlainText(message)

    @Slot(object)
    def _on_ai_finished(self, result) -> None:
        if result.ok:
            self.ai_output.setPlainText(result.suggestion)
        else:
            self.ai_output.setPlainText(result.message + ("\n\n" + result.suggestion if result.suggestion else ""))

    @Slot()
    def _cleanup_ai_thread(self) -> None:
        if self.ai_thread is not None:
            self.ai_thread.deleteLater()
        self.ai_thread = None
        self.ai_worker = None
        self.ai_btn.setText("AI 分析差异")
        self._refresh_ai_button_state()

    def _refresh_ai_button_state(self) -> None:
        if self.ai_thread is not None and self.ai_thread.isRunning():
            self.ai_btn.setEnabled(False)
            self.ai_btn.setToolTip("AI 正在后台分析当前差异，请稍等。")
            return
        has_expected = bool(self.expected_output.toPlainText().strip())
        has_mismatch = self.last_comparison is not None and not self.last_comparison.matched
        self.ai_btn.setEnabled(has_expected and has_mismatch)
        if not has_expected:
            self.ai_btn.setToolTip("先执行日志脚本生成标准日志。")
        elif not has_mismatch:
            self.ai_btn.setToolTip("只有存在对拍差异时才需要 AI 分析。")
        else:
            self.ai_btn.setToolTip("使用所选模型分析当前日志差异。")

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
            self.last_comparison = comparison
            return comparison.matched, comparison.summary, comparison.summary, comparison.html

        if key == "reset_filters":
            if not isinstance(bundle, SimulationBundle):
                return False, "当前没有导入结果可恢复。", "", ""
            context["events"] = list(bundle.events)
            context["log_text"] = ""
            return True, "已恢复为导入时的完整事件流。", "筛选链已清空。", ""

        return False, f"未知积木 {key}。", "", ""
