from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ui.block_workspace import BlockProgramEditor, BlockSpec, FieldSpec
from engine.class_manager import ClassManager
from engine.task2_cpp_exporter import export_task2_cpp_project
from engine.warcraft_engine import (
    BLUE_PRODUCTION_ORDER,
    RED_PRODUCTION_ORDER,
    STANDARD_STAGE_DEFINITIONS,
    WarcraftConfig,
    WarcraftEngine,
    build_default_config,
    build_schedule_profile,
    get_schedule_profile_names,
    get_stage_keys,
)


class Task2Widget(QWidget):
    eventsExported = Signal(object)

    def __init__(self, manager: ClassManager | None = None) -> None:
        super().__init__()
        self.manager = manager or ClassManager.get_instance()
        self.engine: WarcraftEngine | None = None
        self.last_bundle = None
        self.last_context: dict[str, object] | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("Task2：题面驱动模拟器")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel(
            "按魔兽世界最终版题目的整点事件模型来跑整局模拟。左侧不是自由战斗，而是配置 Case 参数、阶段子集、分钟值，再按时间推进。"
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 13px;")
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        action_row = QHBoxLayout()
        self.example_btn = QPushButton("加载推荐积木")
        self.run_btn = QPushButton("执行模拟脚本")
        self.run_btn.setObjectName("btnPrimary")
        self.export_cpp_btn = QPushButton("导出 C++ 单文件")
        self.clear_btn = QPushButton("清空结果")
        self.example_btn.clicked.connect(self.load_example_script)
        self.run_btn.clicked.connect(self.run_script)
        self.export_cpp_btn.clicked.connect(self.export_cpp_project)
        self.clear_btn.clicked.connect(self.clear_outputs)
        action_row.addWidget(self.example_btn)
        action_row.addWidget(self.run_btn)
        action_row.addWidget(self.export_cpp_btn)
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

        self.summary_label = QLabel("先配置 Case 和阶段表，再初始化并推进模拟。")
        self.summary_label.setStyleSheet("font-weight: 700; color: #4F46E5;")
        layout.addWidget(self.summary_label)

        state_group = QGroupBox("当前世界状态")
        state_layout = QVBoxLayout(state_group)
        self.world_output = QPlainTextEdit()
        self.world_output.setReadOnly(True)
        state_layout.addWidget(self.world_output)
        layout.addWidget(state_group)

        schedule_group = QGroupBox("当前事件日程")
        schedule_layout = QVBoxLayout(schedule_group)
        self.schedule_output = QPlainTextEdit()
        self.schedule_output.setReadOnly(True)
        schedule_layout.addWidget(self.schedule_output)
        layout.addWidget(schedule_group)

        event_group = QGroupBox("解释执行日志")
        event_layout = QVBoxLayout(event_group)
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        event_layout.addWidget(self.log_output)
        layout.addWidget(event_group, 1)
        return container

    def _build_block_specs(self) -> list[BlockSpec]:
        stage_keys = get_stage_keys()
        return [
            BlockSpec(
                key="set_case_params",
                title="设置 Case 参数",
                color="#2563EB",
                description="设置 M N R K T。即初始生命元、城市数、arrow 攻击力、lion 忠诚度下降值和总时间。",
                fields=[
                    FieldSpec("M", "M", "int", 20, minimum=1, maximum=10000, width=110),
                    FieldSpec("N", "N", "int", 2, minimum=1, maximum=20, width=110),
                    FieldSpec("R", "R", "int", 10, minimum=1, maximum=10000, width=110),
                    FieldSpec("K", "K", "int", 10, minimum=0, maximum=10000, width=110),
                    FieldSpec("T", "T", "int", 240, minimum=0, maximum=5000, width=110),
                ],
            ),
            BlockSpec(
                key="set_health_table",
                title="设置生命值表",
                color="#0891B2",
                description="依次设置 dragon、ninja、iceman、lion、wolf 的初始生命值。",
                fields=[
                    FieldSpec("dragon", "dragon", "int", 20, minimum=1, maximum=10000, width=120),
                    FieldSpec("ninja", "ninja", "int", 20, minimum=1, maximum=10000, width=120),
                    FieldSpec("iceman", "iceman", "int", 30, minimum=1, maximum=10000, width=120),
                    FieldSpec("lion", "lion", "int", 20, minimum=1, maximum=10000, width=120),
                    FieldSpec("wolf", "wolf", "int", 20, minimum=1, maximum=10000, width=120),
                ],
            ),
            BlockSpec(
                key="set_attack_table",
                title="设置攻击力表",
                color="#0EA5E9",
                description="依次设置 dragon、ninja、iceman、lion、wolf 的攻击力。",
                fields=[
                    FieldSpec("dragon", "dragon", "int", 5, minimum=1, maximum=10000, width=120),
                    FieldSpec("ninja", "ninja", "int", 5, minimum=1, maximum=10000, width=120),
                    FieldSpec("iceman", "iceman", "int", 5, minimum=1, maximum=10000, width=120),
                    FieldSpec("lion", "lion", "int", 5, minimum=1, maximum=10000, width=120),
                    FieldSpec("wolf", "wolf", "int", 5, minimum=1, maximum=10000, width=120),
                ],
            ),
            BlockSpec(
                key="load_schedule_profile",
                title="加载阶段模板",
                color="#7C3AED",
                description="加载标准题面或教学预设模板。自定义只允许在标准 10 阶段内做子集和分钟调整。",
                fields=[
                    FieldSpec("profile_name", "模板", "combo", "标准题面", get_schedule_profile_names(), editable=False, width=170),
                ],
            ),
            BlockSpec(
                key="toggle_stage",
                title="启用或禁用阶段",
                color="#9333EA",
                description="从标准 10 阶段中选择某一项，并决定是否参与当前教学日程。",
                fields=[
                    FieldSpec("stage_key", "阶段", "combo", stage_keys[0], stage_keys, editable=False, width=170),
                    FieldSpec("enabled", "状态", "combo", "启用", ["启用", "禁用"], editable=False, width=120),
                ],
            ),
            BlockSpec(
                key="set_stage_minute",
                title="调整阶段分钟",
                color="#A855F7",
                description="在保留标准阶段类型不变的前提下，调整某个阶段在一小时中的分钟值。",
                fields=[
                    FieldSpec("stage_key", "阶段", "combo", stage_keys[0], stage_keys, editable=False, width=170),
                    FieldSpec("minute", "分钟", "int", 0, minimum=0, maximum=59, width=120),
                ],
            ),
            BlockSpec(
                key="inspect_schedule",
                title="查看当前日程",
                color="#16A34A",
                description="把当前启用的阶段表和分钟值打印到右侧。",
            ),
            BlockSpec(
                key="initialize_case",
                title="初始化 Case",
                color="#EA580C",
                description="根据前面的参数和阶段表创建一局新的模拟。",
            ),
            BlockSpec(
                key="run_next_stage",
                title="运行下一阶段",
                color="#F59E0B",
                description="按当前阶段表推进一个事件槽。",
            ),
            BlockSpec(
                key="run_next_hour",
                title="运行下一小时",
                color="#D97706",
                description="推进直到跨过当前小时。",
                fields=[
                    FieldSpec("max_steps", "安全上限", "int", 20, minimum=1, maximum=50, width=140),
                ],
            ),
            BlockSpec(
                key="run_until_limit",
                title="运行到 T",
                color="#DC2626",
                description="持续推进直到到达时间上限或司令部被占领。",
                fields=[
                    FieldSpec("max_steps", "安全上限", "int", 300, minimum=1, maximum=5000, width=140),
                ],
            ),
            BlockSpec(
                key="inspect_headquarter",
                title="查看司令部",
                color="#059669",
                description="查看红方或蓝方司令部当前状态。",
                fields=[
                    FieldSpec("camp", "阵营", "combo", "red", ["red", "blue"], editable=False, width=120),
                ],
            ),
            BlockSpec(
                key="inspect_city",
                title="查看城市",
                color="#10B981",
                description="查看某座城市的生命元、旗帜和驻扎武士。",
                fields=[
                    FieldSpec("city_id", "城市编号", "int", 1, minimum=1, maximum=20, width=140),
                ],
            ),
            BlockSpec(
                key="export_events",
                title="导出事件到 Task3",
                color="#4F46E5",
                description="把当前模拟的统一事件流导给 Task3 做标准日志生成和对拍。",
            ),
            BlockSpec(
                key="reset_simulation",
                title="重置模拟器",
                color="#475569",
                description="清空当前引擎和输出，重新开始下一组配置。",
            ),
        ]

    def load_example_script(self) -> None:
        self.block_editor.set_script([
            {"key": "set_case_params", "fields": {"M": 20, "N": 1, "R": 10, "K": 10, "T": 180}},
            {"key": "set_health_table", "fields": {"dragon": 20, "ninja": 20, "iceman": 30, "lion": 10, "wolf": 20}},
            {"key": "set_attack_table", "fields": {"dragon": 5, "ninja": 5, "iceman": 5, "lion": 5, "wolf": 5}},
            {"key": "load_schedule_profile", "fields": {"profile_name": "标准题面"}},
            {"key": "inspect_schedule", "fields": {}},
            {"key": "initialize_case", "fields": {}},
            {"key": "run_next_hour", "fields": {"max_steps": 20}},
            {"key": "inspect_headquarter", "fields": {"camp": "blue"}},
            {"key": "run_until_limit", "fields": {"max_steps": 120}},
            {"key": "export_events", "fields": {}},
        ])

    def clear_outputs(self) -> None:
        self.log_output.clear()
        self.world_output.clear()
        self.schedule_output.clear()
        self.summary_label.setText("输出已清空。")
        self.summary_label.setStyleSheet("font-weight: 700; color: #4F46E5;")

    def run_script(self) -> None:
        script = self.block_editor.get_script()
        if not script:
            self.summary_label.setText("工作区还是空的，请先拖拽模拟积木。")
            self.summary_label.setStyleSheet("font-weight: 700; color: #DC2626;")
            return

        context = {
            "config": build_default_config(),
            "schedule": build_schedule_profile(),
            "engine": None,
            "last_note": "",
        }
        logs: list[str] = []

        for index, block in enumerate(script, start=1):
            ok, message = self._execute_block(context, str(block.get("key", "")), block.get("fields", {}))
            prefix = "[通过]" if ok else "[错误]"
            logs.append(f"{prefix} 积木 {index}: {message}")

        self.last_context = context
        self.engine = context.get("engine") if isinstance(context.get("engine"), WarcraftEngine) else None
        self.log_output.setPlainText("\n".join(logs))
        self._render_context(context)
        self.summary_label.setText(context.get("last_note", "模拟脚本执行结束。"))
        self.summary_label.setStyleSheet("font-weight: 700; color: #4F46E5;")

    def export_cpp_project(self) -> None:
        if self.last_context is None:
            QMessageBox.warning(self, "导出失败", "请先执行一次模拟脚本，再导出当前 Task2 的 C++ 工程。")
            return

        config = self.last_context.get("config")
        schedule = self.last_context.get("schedule")
        if not isinstance(config, WarcraftConfig) or not hasattr(schedule, "get_enabled_slots"):
            QMessageBox.warning(self, "导出失败", "当前没有可用的 Task2 Case 配置，请先重新执行模拟脚本。")
            return

        directory = QFileDialog.getExistingDirectory(self, "选择 C++ 工程导出目录")
        if not directory:
            return

        try:
            exported_files = export_task2_cpp_project(directory, config, schedule)
            self.summary_label.setText(f"Task2 C++ 单文件已导出到：{directory}")
            self.summary_label.setStyleSheet("font-weight: 700; color: #059669;")
            QMessageBox.information(
                self,
                "导出成功",
                "已导出 Task2 独立 C++ 题解到：\n"
                f"{directory}\n\n"
                "task2_solution.cpp 是可直接提交 OJ 的单文件。\n\n"
                "包含文件：\n"
                + "\n".join(exported_files),
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "导出失败", str(exc))

    def _execute_block(self, context: dict[str, object], key: str, fields: dict[str, object]) -> tuple[bool, str]:
        config = context.get("config")
        schedule = context.get("schedule")
        engine = context.get("engine")
        if not isinstance(config, WarcraftConfig):
            config = build_default_config()
            context["config"] = config
        if not hasattr(schedule, "get_enabled_slots"):
            schedule = build_schedule_profile()
            context["schedule"] = schedule

        if key == "set_case_params":
            config.initial_elements = int(fields.get("M", config.initial_elements))
            config.city_count = int(fields.get("N", config.city_count))
            config.arrow_attack = int(fields.get("R", config.arrow_attack))
            config.lion_loyalty_decay = int(fields.get("K", config.lion_loyalty_decay))
            config.time_limit = int(fields.get("T", config.time_limit))
            context["last_note"] = "Case 参数已更新。"
            return True, f"已设置 M={config.initial_elements}, N={config.city_count}, R={config.arrow_attack}, K={config.lion_loyalty_decay}, T={config.time_limit}。"

        if key == "set_health_table":
            for warrior_type in config.warrior_health:
                config.warrior_health[warrior_type] = int(fields.get(warrior_type, config.warrior_health[warrior_type]))
            context["last_note"] = "生命值表已更新。"
            return True, f"生命值表已设置为 {config.warrior_health}。"

        if key == "set_attack_table":
            for warrior_type in config.warrior_attack:
                config.warrior_attack[warrior_type] = int(fields.get(warrior_type, config.warrior_attack[warrior_type]))
            context["last_note"] = "攻击力表已更新。"
            return True, f"攻击力表已设置为 {config.warrior_attack}。"

        if key == "load_schedule_profile":
            profile_name = str(fields.get("profile_name", "标准题面"))
            context["schedule"] = build_schedule_profile(profile_name)
            context["last_note"] = f"已加载阶段模板：{profile_name}。"
            return True, f"当前阶段模板为 {profile_name}。"

        if key == "toggle_stage":
            slot = context["schedule"].get_slot(str(fields.get("stage_key", "")))
            if slot is None:
                return False, "目标阶段不存在。"
            slot.enabled = str(fields.get("enabled", "启用")) == "启用"
            context["schedule"].strict_mode = False
            context["schedule"].name = "自定义版"
            return True, f"阶段 {slot.key} 已{'启用' if slot.enabled else '禁用'}。"

        if key == "set_stage_minute":
            slot = context["schedule"].get_slot(str(fields.get("stage_key", "")))
            if slot is None:
                return False, "目标阶段不存在。"
            slot.minute = int(fields.get("minute", slot.minute))
            context["schedule"].strict_mode = False
            context["schedule"].name = "自定义版"
            return True, f"阶段 {slot.key} 已调整到每小时第 {slot.minute:02d} 分。"

        if key == "inspect_schedule":
            note = context["schedule"].name
            context["last_note"] = f"已查看当前阶段表：{note}。"
            return True, "当前阶段表已输出到右侧。"

        if key == "initialize_case":
            context["engine"] = WarcraftEngine(context["config"], context["schedule"])
            init_message = context["engine"].initialize_case()
            context["last_note"] = init_message
            return True, init_message

        if key == "run_next_stage":
            if not isinstance(engine, WarcraftEngine):
                engine = context.get("engine")
            if not isinstance(engine, WarcraftEngine):
                return False, "请先初始化 Case。"
            execution = engine.next_stage()
            context["last_note"] = execution.summary
            return True, self._format_stage_execution(execution)

        if key == "run_next_hour":
            if not isinstance(engine, WarcraftEngine):
                engine = context.get("engine")
            if not isinstance(engine, WarcraftEngine):
                return False, "请先初始化 Case。"
            max_steps = int(fields.get("max_steps", 20))
            executions = engine.run_next_hour(max_steps=max_steps)
            context["last_note"] = executions[-1].summary if executions else "没有执行任何阶段。"
            return True, self._format_stage_list(executions)

        if key == "run_until_limit":
            if not isinstance(engine, WarcraftEngine):
                engine = context.get("engine")
            if not isinstance(engine, WarcraftEngine):
                return False, "请先初始化 Case。"
            max_steps = int(fields.get("max_steps", 300))
            executions = engine.run_until_limit(max_steps=max_steps)
            context["last_note"] = executions[-1].summary if executions else "没有执行任何阶段。"
            return True, self._format_stage_list(executions)

        if key == "inspect_headquarter":
            if not isinstance(engine, WarcraftEngine):
                engine = context.get("engine")
            if not isinstance(engine, WarcraftEngine):
                return False, "请先初始化 Case。"
            camp = str(fields.get("camp", "red"))
            context["last_note"] = f"已查看 {camp} 司令部。"
            return True, engine.build_headquarter_summary(camp)

        if key == "inspect_city":
            if not isinstance(engine, WarcraftEngine):
                engine = context.get("engine")
            if not isinstance(engine, WarcraftEngine):
                return False, "请先初始化 Case。"
            city_id = int(fields.get("city_id", 1))
            context["last_note"] = f"已查看城市 {city_id}。"
            return True, engine.build_city_summary(city_id)

        if key == "export_events":
            if not isinstance(engine, WarcraftEngine):
                engine = context.get("engine")
            if not isinstance(engine, WarcraftEngine):
                return False, "没有可导出的模拟结果。"
            bundle = engine.export_bundle()
            self.last_bundle = bundle
            self.eventsExported.emit(bundle)
            context["last_note"] = f"已导出 {len(bundle.events)} 条事件到 Task3。"
            return True, f"已导出 {len(bundle.events)} 条事件，模式为 {bundle.mode_label}。"

        if key == "reset_simulation":
            self.engine = None
            self.last_bundle = None
            context["engine"] = None
            context["last_note"] = "模拟器已重置。"
            return True, "已清空当前引擎和导出缓存。"

        return False, f"未知积木 {key}。"

    def _render_context(self, context: dict[str, object]) -> None:
        schedule = context.get("schedule")
        engine = context.get("engine")
        if hasattr(schedule, "get_enabled_slots"):
            self.schedule_output.setPlainText(schedule_summary(schedule))
        else:
            self.schedule_output.clear()

        if isinstance(engine, WarcraftEngine):
            self.world_output.setPlainText(engine.build_world_summary())
        else:
            config = context.get("config")
            if isinstance(config, WarcraftConfig):
                self.world_output.setPlainText(
                    "尚未初始化 Case\n"
                    f"M={config.initial_elements}, N={config.city_count}, R={config.arrow_attack}, K={config.lion_loyalty_decay}, T={config.time_limit}\n"
                    f"红方造兵序列: {' -> '.join(RED_PRODUCTION_ORDER)}\n"
                    f"蓝方造兵序列: {' -> '.join(BLUE_PRODUCTION_ORDER)}"
                )
            else:
                self.world_output.clear()

    @staticmethod
    def _format_stage_execution(execution) -> str:
        if not execution.events:
            return execution.summary
        event_lines = [event.to_log_line() for event in execution.events[:6]]
        if len(execution.events) > 6:
            event_lines.append(f"... 本阶段其余还有 {len(execution.events) - 6} 条事件")
        return execution.summary + "\n" + "\n".join(event_lines)

    def _format_stage_list(self, executions: list[object]) -> str:
        if not executions:
            return "没有执行任何阶段。"
        lines: list[str] = []
        for execution in executions:
            lines.append(self._format_stage_execution(execution))
        return "\n\n".join(lines)


def schedule_summary(schedule) -> str:
    lines = [f"模板: {schedule.name}"]
    lines.append(f"模式: {'标准题面模式' if schedule.strict_mode else '自定义教学模式'}")
    lines.append("启用阶段:")
    for slot in schedule.get_enabled_slots():
        lines.append(f"- {slot.key}: 第 {slot.minute:02d} 分")
    disabled = [slot.key for slot in schedule.slots if not slot.enabled]
    if disabled:
        lines.append("")
        lines.append("已禁用阶段:")
        lines.extend(f"- {key}" for key in disabled)
    return "\n".join(lines)
