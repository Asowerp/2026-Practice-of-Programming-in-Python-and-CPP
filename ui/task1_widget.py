from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ui.block_workspace import BlockProgramEditor, BlockSpec, FieldSpec
from engine.class_manager import ClassManager
from engine.task1_validator import (
    build_reference_hierarchy_text,
    build_warcraft_entity_reference_text,
    extract_initializer_targets,
    get_recommended_constructor_texts,
    validate_warcraft_entities,
    validate_warrior_hierarchy,
)


class Task1Widget(QWidget):
    def __init__(self, manager: ClassManager | None = None) -> None:
        super().__init__()
        self.manager = manager or ClassManager.get_instance()
        self.manager.seed_demo_classes()
        self._recommended_constructors = get_recommended_constructor_texts()
        self._build_ui()
        self.load_recommended_constructors()
        self.refresh_reference_view()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("Task1：积木式层级校验")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel(
            "Task1 现在分成两层：先校验 Warrior 层级，再校验 warcraft 题面的完整对象集合。也可以在类编辑器里直接导出 C++ 代码骨架。"
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 13px;")
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        action_row = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新类信息")
        self.example_btn = QPushButton("加载推荐积木")
        self.run_btn = QPushButton("执行校验脚本")
        self.run_btn.setObjectName("btnPrimary")
        self.refresh_btn.clicked.connect(self.refresh_reference_view)
        self.example_btn.clicked.connect(self.load_example_script)
        self.run_btn.clicked.connect(self.run_validation_script)
        action_row.addWidget(self.refresh_btn)
        action_row.addWidget(self.example_btn)
        action_row.addWidget(self.run_btn)
        action_row.addStretch(1)
        main_layout.addLayout(action_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        self.block_editor = BlockProgramEditor(self._build_block_specs())
        splitter.addWidget(self.block_editor)
        splitter.addWidget(self._build_reference_panel())
        splitter.setSizes([620, 700])
        splitter.setToolTip("拖动中间的分隔线可以调整左右面板宽度")
        main_layout.addWidget(splitter)

    def _build_reference_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        right_splitter = QSplitter(Qt.Orientation.Horizontal)
        right_splitter.setHandleWidth(1)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        ctor_group = QGroupBox("初始化列表示例输入")
        ctor_layout = QFormLayout(ctor_group)
        self.dragon_ctor_edit = QLineEdit()
        self.dragon_ctor_edit.setPlaceholderText(
            "Dragon(int hp, int attack, double morale) : Warrior(hp, attack), morale(morale) {}"
        )
        self.ninja_ctor_edit = QLineEdit()
        self.ninja_ctor_edit.setPlaceholderText(
            "Ninja(int hp, int attack, int weaponCount) : Warrior(hp, attack), weaponCount(weaponCount) {}"
        )
        self.iceman_ctor_edit = QLineEdit()
        self.iceman_ctor_edit.setPlaceholderText(
            "Iceman(int hp, int attack, int stepCount) : Warrior(hp, attack), stepCount(stepCount) {}"
        )
        ctor_layout.addRow("Dragon", self.dragon_ctor_edit)
        ctor_layout.addRow("Ninja", self.ninja_ctor_edit)
        ctor_layout.addRow("Iceman", self.iceman_ctor_edit)
        left_layout.addWidget(ctor_group)

        info = QLabel(
            "说明：当前 Task1 的“检查初始化列表调用”积木会读取这里的文本。"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #64748B; font-size: 12px;")
        left_layout.addWidget(info)

        reference_group = QGroupBox("标准层级参考")
        reference_layout = QVBoxLayout(reference_group)
        self.reference_output = QPlainTextEdit()
        self.reference_output.setReadOnly(True)
        reference_layout.addWidget(self.reference_output)
        left_layout.addWidget(reference_group)

        entity_group = QGroupBox("题面对象参考")
        entity_layout = QVBoxLayout(entity_group)
        self.entity_output = QPlainTextEdit()
        self.entity_output.setReadOnly(True)
        entity_layout.addWidget(self.entity_output)
        left_layout.addWidget(entity_group)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        code_group = QGroupBox("当前类结构概览")
        code_layout = QVBoxLayout(code_group)
        self.code_output = QPlainTextEdit()
        self.code_output.setReadOnly(True)
        self.code_output.setStyleSheet(
            "QPlainTextEdit { background: #0F172A; color: #E2E8F0; border: 1px solid #1E293B;"
            " border-radius: 8px; font-family: 'Cascadia Code', 'Consolas', monospace; padding: 10px; }"
        )
        code_layout.addWidget(self.code_output)
        right_layout.addWidget(code_group, 1)

        result_group = QGroupBox("脚本执行结果")
        result_layout = QVBoxLayout(result_group)
        self.result_output = QPlainTextEdit()
        self.result_output.setReadOnly(True)
        self.result_output.setPlaceholderText("拖好积木后点击“执行校验脚本”。")
        result_layout.addWidget(self.result_output)
        right_layout.addWidget(result_group, 1)

        right_splitter.addWidget(left_widget)
        right_splitter.addWidget(right_widget)
        right_splitter.setSizes([340, 360])
        right_splitter.setToolTip("拖动分隔线可调整右侧两栏宽度")
        layout.addWidget(right_splitter, 1)

        return container

    def _build_block_specs(self) -> list[BlockSpec]:
        return [
            BlockSpec(
                key="validate_standard_pack",
                title="执行整套标准校验",
                color="#DC2626",
                description="一次性检查 Warrior / Dragon / Ninja / Iceman 的标准层级、成员与初始化列表。",
            ),
            BlockSpec(
                key="validate_warcraft_entities",
                title="检查题面对象集合",
                color="#B91C1C",
                description="检查 Headquarter / City / Warrior / Weapon 及五种武士、三种武器的类结构是否已建立。",
            ),
            BlockSpec(
                key="require_class",
                title="检查类存在",
                color="#2563EB",
                description="确认某个类已经在类编辑器中定义并保存。",
                fields=[
                    FieldSpec("class_name", "类名", "combo", "Warrior", self._class_name_options, editable=True, width=160),
                ],
            ),
            BlockSpec(
                key="require_direct_base",
                title="检查直接继承",
                color="#0891B2",
                description="确认派生类的直接基类就是你希望的类。",
                fields=[
                    FieldSpec("class_name", "派生类", "combo", "Dragon", self._class_name_options, editable=True, width=150),
                    FieldSpec("base_name", "基类", "combo", "Warrior", self._class_name_options, editable=True, width=150),
                ],
            ),
            BlockSpec(
                key="require_member",
                title="检查成员存在",
                color="#7C3AED",
                description="检查某类在继承展开后是否拥有指定成员。",
                fields=[
                    FieldSpec("class_name", "类名", "combo", "Warrior", self._class_name_options, editable=True, width=150),
                    FieldSpec("member_name", "成员", "combo", "hp", self._member_name_options, editable=True, width=150),
                ],
            ),
            BlockSpec(
                key="require_ctor_call",
                title="检查初始化列表调用",
                color="#EA580C",
                description="从右侧初始化列表示例中检查是否出现了某个构造调用或成员初始化。",
                fields=[
                    FieldSpec("class_name", "类名", "combo", "Dragon", ["Dragon", "Ninja", "Iceman"], editable=False, width=140),
                    FieldSpec("target_name", "必须调用", "combo", "Warrior", self._ctor_target_options, editable=True, width=160),
                ],
            ),
            BlockSpec(
                key="require_virtual",
                title="检查虚函数特性",
                color="#16A34A",
                description="确认某个类或其父类链上具备虚函数特性，便于理解多态。",
                fields=[
                    FieldSpec("class_name", "类名", "combo", "Warrior", self._class_name_options, editable=True, width=160),
                ],
            ),
        ]

    def refresh_reference_view(self) -> None:
        self.block_editor.refresh_dynamic_fields()
        self.reference_output.setPlainText(build_reference_hierarchy_text())
        self.entity_output.setPlainText(build_warcraft_entity_reference_text())
        sections = []
        for class_name in self._class_name_options():
            sections.append(f"// ===== {class_name} =====")
            sections.append(self.manager.generate_cpp_code(class_name))
            sections.append("")
        self.code_output.setPlainText("\n".join(sections).strip())

    def load_recommended_constructors(self) -> None:
        self.dragon_ctor_edit.setText(self._recommended_constructors.get("Dragon", ""))
        self.ninja_ctor_edit.setText(self._recommended_constructors.get("Ninja", ""))
        self.iceman_ctor_edit.setText(self._recommended_constructors.get("Iceman", ""))

    def load_example_script(self) -> None:
        self.block_editor.set_script([
            {"key": "validate_standard_pack", "fields": {}},
            {"key": "validate_warcraft_entities", "fields": {}},
            {"key": "require_class", "fields": {"class_name": "Warrior"}},
            {"key": "require_member", "fields": {"class_name": "Warrior", "member_name": "hp"}},
            {"key": "require_member", "fields": {"class_name": "Warrior", "member_name": "attack"}},
            {"key": "require_direct_base", "fields": {"class_name": "Dragon", "base_name": "Warrior"}},
            {"key": "require_member", "fields": {"class_name": "Dragon", "member_name": "morale"}},
            {"key": "require_ctor_call", "fields": {"class_name": "Dragon", "target_name": "Warrior"}},
            {"key": "require_direct_base", "fields": {"class_name": "Ninja", "base_name": "Warrior"}},
            {"key": "require_member", "fields": {"class_name": "Ninja", "member_name": "weaponCount"}},
            {"key": "require_direct_base", "fields": {"class_name": "Iceman", "base_name": "Warrior"}},
            {"key": "require_member", "fields": {"class_name": "Iceman", "member_name": "stepCount"}},
            {"key": "require_virtual", "fields": {"class_name": "Warrior"}},
        ])

    def run_validation_script(self) -> None:
        script = self.block_editor.get_script()
        if not script:
            self.result_output.setPlainText("工作区还是空的。请先把左侧积木拖进来，再执行校验。")
            return

        all_ok = True
        logs: list[str] = []
        self.refresh_reference_view()
        constructor_texts = {
            "Dragon": self.dragon_ctor_edit.text().strip(),
            "Ninja": self.ninja_ctor_edit.text().strip(),
            "Iceman": self.iceman_ctor_edit.text().strip(),
        }

        for index, block in enumerate(script, start=1):
            key = str(block.get("key", ""))
            fields = block.get("fields", {})
            success, message = self._execute_block(key, fields, constructor_texts)
            all_ok = all_ok and success
            prefix = "[通过]" if success else "[错误]"
            logs.append(f"{prefix} 积木 {index}: {message}")

        summary = "整套校验积木执行通过。" if all_ok else "校验积木执行结束，但仍有规则未满足。"
        self.result_output.setPlainText(summary + "\n\n" + "\n".join(logs))

    def _execute_block(
        self,
        key: str,
        fields: dict[str, object],
        constructor_texts: dict[str, str],
    ) -> tuple[bool, str]:
        class_name = str(fields.get("class_name", "")).strip()

        if key == "validate_standard_pack":
            result = validate_warrior_hierarchy(self.manager, constructor_texts)
            return result.ok, result.to_text().replace("\n", " | ")

        if key == "validate_warcraft_entities":
            result = validate_warcraft_entities(self.manager)
            return result.ok, result.to_text().replace("\n", " | ")

        if key == "require_class":
            exists = self.manager.get_class(class_name) is not None
            if exists:
                return True, f"类 {class_name} 已存在。"
            return False, f"类 {class_name} 不存在。"

        if key == "require_direct_base":
            base_name = str(fields.get("base_name", "")).strip()
            cls_def = self.manager.get_class(class_name)
            if cls_def is None:
                return False, f"类 {class_name} 不存在，无法检查继承。"
            if cls_def.base_class == base_name:
                return True, f"{class_name} 的直接基类就是 {base_name}。"
            current_base = cls_def.base_class or "<空>"
            return False, f"{class_name} 的直接基类当前为 {current_base}，不是 {base_name}。"

        if key == "require_member":
            member_name = str(fields.get("member_name", "")).strip()
            if not class_name:
                return False, "类名为空，无法检查成员。"
            all_members = {member.var_name for member in self.manager.get_all_members(class_name)}
            if member_name in all_members:
                return True, f"{class_name} 在继承展开后包含成员 {member_name}。"
            return False, f"{class_name} 缺少成员 {member_name}。"

        if key == "require_ctor_call":
            target_name = str(fields.get("target_name", "")).strip()
            ctor_text = constructor_texts.get(class_name, "")
            if not ctor_text:
                return False, f"{class_name} 还没有填写初始化列表示例文本。"
            targets = extract_initializer_targets(ctor_text)
            if target_name in targets:
                return True, f"{class_name} 的初始化列表中找到了 {target_name}(...)。"
            return False, f"{class_name} 的初始化列表中没有找到 {target_name}(...)。"

        if key == "require_virtual":
            if self.manager.class_has_virtual(class_name):
                return True, f"{class_name} 具有虚函数特性或继承了该特性。"
            return False, f"{class_name} 当前没有虚函数特性。"

        return False, f"未知积木 {key}。"

    def _class_name_options(self) -> list[str]:
        names = set(self.manager.get_class_names())
        names.update(["Warrior", "Dragon", "Ninja", "Iceman"])
        return sorted(names)

    def _member_name_options(self) -> list[str]:
        members = {"hp", "attack", "morale", "weaponCount", "stepCount", "defense", "weapon_durability"}
        for class_name in self.manager.get_class_names():
            for member in self.manager.get_all_members(class_name):
                members.add(member.var_name)
        return sorted(members)

    def _ctor_target_options(self) -> list[str]:
        return sorted({"Warrior", "hp", "attack", "morale", "weaponCount", "stepCount"})
