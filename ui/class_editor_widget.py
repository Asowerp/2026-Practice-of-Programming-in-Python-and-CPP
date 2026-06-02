from __future__ import annotations

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QDrag, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from engine.class_manager import ClassManager
from constants import APP_STYLE, AVAILABLE_TYPES, DEFAULT_MEMBER_NAMES
from engine.models import ClassDef, MemberDef

# 类型拖拽列表：展示可选的预定义成员类型，并支持拖拽到成员表中创建新成员。
# 该控件只负责类型项的展示与拖拽数据封装，不处理具体的成员落地逻辑。
class TypePaletteList(QListWidget):
    # 初始化类型列表控件，并将预定义类型逐项填充到可拖拽列表中。
    def __init__(self) -> None:
        super().__init__()
        self.setDragEnabled(True)
        self.setSpacing(8)
        self.setViewMode(QListWidget.ViewMode.ListMode)
        self.setAlternatingRowColors(False)
        for type_name in AVAILABLE_TYPES:
            item = QListWidgetItem(type_name)
            item.setText(f"  {type_name}")
            self.addItem(item)

    # 开始拖拽当前选中的类型，将类型名写入 MIME 文本数据供目标控件接收。
    def startDrag(self, supportedActions) -> None:  # noqa: N802
        item = self.currentItem()
        if item is None:
            return
        type_name = item.text().strip()
        mime_data = QMimeData()
        mime_data.setText(type_name)

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)


# 成员变量表格：既支持表格行内部拖拽排序，也支持从类型面板拖入新成员类型。
# 通过自定义信号向外部通知“新增成员”和“顺序变化”两类编辑事件。
class MemberTableWidget(QTableWidget):
    memberDropped = Signal(str)
    orderChanged = Signal()

    # 初始化两列表格结构，并开启行选择、拖放、行重排等交互能力。
    def __init__(self) -> None:
        super().__init__(0, 2)
        self.setHorizontalHeaderLabels(["类型", "变量名"])
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setDropIndicatorShown(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setMinimumHeight(260)

    # 当拖拽进入表格时，根据来源决定是内部排序还是外部类型拖入，并接受可处理的动作。
    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.source() is self:
            event.acceptProposedAction()
            return
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    # 在拖拽移动过程中持续维持可放置状态，保证内部重排和外部拖入都能正确显示落点。
    def dragMoveEvent(self, event) -> None:  # noqa: N802
        if event.source() is self:
            event.acceptProposedAction()
            return
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    # 放下时若来源是自身则触发行顺序更新；若来源是类型列表则发出新增成员类型信号。
    def dropEvent(self, event) -> None:  # noqa: N802
        if event.source() is self:
            super().dropEvent(event)
            self.orderChanged.emit()
            return
        if event.mimeData().hasText():
            self.memberDropped.emit(event.mimeData().text())
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


# 类编辑器主界面：负责类列表管理、类信息编辑、成员维护以及 C++ 代码实时预览。
# 它通过 ClassManager 读写类定义，并将所有界面操作同步到统一的数据源中。
class ClassEditorWidget(QWidget):
    # 初始化编辑器，准备共享的类管理器、基础状态以及整套界面内容。
    def __init__(self, manager: ClassManager | None = None) -> None:
        super().__init__()
        self.manager = manager or ClassManager.get_instance()
        self.manager.seed_demo_classes()
        self.current_class_name = ""
        self._building_ui = False

        self._build_ui()
        self.refresh_class_list()
        names = self.manager.get_class_names()
        if names:
            self.load_class_into_editor(names[0])

    # 构建主布局，将类列表、编辑区和代码预览区组合到同一个分割窗口中。
    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        title = QLabel("类结构编辑器")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        subtitle = QLabel("创建类、设置继承关系、拖拽添加成员，并实时预览 C++ 代码")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 13px;")

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        splitter = QSplitter()
        splitter.addWidget(self._build_class_list_panel())
        splitter.addWidget(self._build_editor_panel())
        splitter.addWidget(self._build_preview_panel())
        splitter.setSizes([220, 520, 420])
        main_layout.addWidget(splitter)

    # 创建左侧类列表面板，提供类选择、新建和删除入口。
    def _build_class_list_panel(self) -> QWidget:
        panel = QGroupBox("类列表")
        layout = QVBoxLayout(panel)

        self.class_list = QListWidget()
        self.class_list.currentTextChanged.connect(self.load_class_into_editor)
        layout.addWidget(self.class_list)

        button_row = QHBoxLayout()
        self.add_class_btn = QPushButton("新建类")
        self.add_class_btn.setObjectName("btnPrimary")
        self.delete_class_btn = QPushButton("删除类")
        self.delete_class_btn.setObjectName("btnDanger")
        self.add_class_btn.clicked.connect(self.add_class)
        self.delete_class_btn.clicked.connect(self.delete_current_class)
        button_row.addWidget(self.add_class_btn)
        button_row.addWidget(self.delete_class_btn)
        layout.addLayout(button_row)
        return panel

    # 创建中间编辑面板，用于修改类名、基类、虚函数选项和成员变量列表。
    def _build_editor_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        info_group = QGroupBox("类信息")
        info_form = QFormLayout(info_group)
        self.class_name_edit = QLineEdit()
        self.base_class_combo = QComboBox()
        self.base_class_combo.currentIndexChanged.connect(self.on_editor_changed)
        self.has_virtual_check = QCheckBox("包含虚函数")
        self.has_virtual_check.stateChanged.connect(self.on_editor_changed)
        self.class_name_edit.textChanged.connect(self.on_editor_changed)
        info_form.addRow("类名", self.class_name_edit)
        info_form.addRow("基类", self.base_class_combo)
        info_form.addRow("特性", self.has_virtual_check)

        member_group = QGroupBox("成员变量")
        member_layout = QVBoxLayout(member_group)
        hint = QLabel("支持两种方式：点击按钮添加，或从右侧类型区拖拽到表格中")
        hint.setStyleSheet("color: #94A3B8; font-size: 12px;")
        member_layout.addWidget(hint)

        self.member_table = MemberTableWidget()
        self.member_table.memberDropped.connect(self.add_member_from_type)
        self.member_table.itemChanged.connect(self.on_editor_changed)
        self.member_table.orderChanged.connect(self.on_editor_changed)
        member_layout.addWidget(self.member_table)

        member_buttons = QHBoxLayout()
        self.quick_type_combo = QComboBox()
        self.quick_type_combo.addItems(AVAILABLE_TYPES)
        self.add_member_btn = QPushButton("添加成员")
        self.remove_member_btn = QPushButton("删除成员")
        self.remove_member_btn.setObjectName("btnDanger")
        self.add_member_btn.clicked.connect(self.add_member_from_combo)
        self.remove_member_btn.clicked.connect(self.remove_selected_member)
        member_buttons.addWidget(self.quick_type_combo)
        member_buttons.addWidget(self.add_member_btn)
        member_buttons.addWidget(self.remove_member_btn)
        member_layout.addLayout(member_buttons)

        action_row = QHBoxLayout()
        self.save_btn = QPushButton("保存类定义")
        self.save_btn.setObjectName("btnPrimary")
        self.export_btn = QPushButton("导出全部 C++")
        self.export_skeleton_btn = QPushButton("导出工程骨架")
        self.save_btn.clicked.connect(self.save_current_class)
        self.export_btn.clicked.connect(self.export_all_cpp)
        self.export_skeleton_btn.clicked.connect(self.export_cpp_skeleton)
        action_row.addWidget(self.save_btn)
        action_row.addWidget(self.export_btn)
        action_row.addWidget(self.export_skeleton_btn)

        layout.addWidget(info_group)
        layout.addWidget(member_group)
        layout.addLayout(action_row)
        return container

    # 创建右侧预览面板，展示可拖拽的类型列表以及实时生成的 C++ 代码。
    def _build_preview_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        type_group = QGroupBox("预定义类型（可拖拽）")
        type_layout = QVBoxLayout(type_group)
        type_label = QLabel("将类型拖到成员变量表格中，即可快速创建成员")
        type_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
        type_layout.addWidget(type_label)
        self.type_palette = TypePaletteList()
        type_layout.addWidget(self.type_palette)

        preview_group = QGroupBox("C++ 代码预览")
        preview_layout = QVBoxLayout(preview_group)
        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setStyleSheet(
            "QTextEdit { background: #0F172A; color: #E2E8F0; border: 1px solid #1E293B;"
            " border-radius: 8px; font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;"
            " font-size: 13px; padding: 12px; selection-background-color: #334155; }"
        )
        preview_layout.addWidget(self.code_preview)

        layout.addWidget(type_group, 2)
        layout.addWidget(preview_group, 3)
        return container

    # 从管理器重新读取全部类名并刷新列表，同时尽量保持当前选中项不变。
    def refresh_class_list(self) -> None:
        current = self.current_class_name
        self.class_list.blockSignals(True)
        self.class_list.clear()
        for cls_def in self.manager.get_all_classes():
            self.class_list.addItem(cls_def.name)
        self.class_list.blockSignals(False)

        names = self.manager.get_class_names()
        if current in names:
            self.class_list.setCurrentRow(names.index(current))
        elif names:
            self.class_list.setCurrentRow(0)
        self.refresh_base_class_combo()

    # 刷新基类下拉框内容，并排除当前类自身，避免直接形成“自己继承自己”的非法选择。
    def refresh_base_class_combo(self) -> None:
        current_text = self.base_class_combo.currentText()
        self.base_class_combo.blockSignals(True)
        self.base_class_combo.clear()
        self.base_class_combo.addItem("")
        for class_name in self.manager.get_class_names():
            if class_name != self.class_name_edit.text().strip():
                self.base_class_combo.addItem(class_name)
        index = self.base_class_combo.findText(current_text)
        if index >= 0:
            self.base_class_combo.setCurrentIndex(index)
        self.base_class_combo.blockSignals(False)

    # 新建一个带唯一默认名称的类，并立即加载到编辑区供用户继续编辑。
    def add_class(self) -> None:
        base_name = self._generate_unique_class_name("NewClass")
        cls_def = ClassDef(name=base_name)
        try:
            self.manager.add_class(cls_def)
        except ValueError as exc:
            QMessageBox.warning(self, "创建失败", str(exc))
            return
        self.current_class_name = cls_def.name
        self.refresh_class_list()
        self.load_class_into_editor(cls_def.name)

    # 删除当前选中的类；删除后自动切换到其他可用类，若已无类则清空编辑器。
    def delete_current_class(self) -> None:
        if not self.current_class_name:
            return
        reply = QMessageBox.question(self, "确认删除", f"确定删除类 {self.current_class_name} 吗？")
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.manager.remove_class(self.current_class_name)
        self.current_class_name = ""
        self.refresh_class_list()
        names = self.manager.get_class_names()
        if names:
            self.load_class_into_editor(names[0])
        else:
            self.clear_editor()

    # 将指定类定义加载到界面控件中，并在加载完成后同步更新代码预览。
    def load_class_into_editor(self, class_name: str) -> None:
        cls_def = self.manager.get_class(class_name)
        if cls_def is None:
            return
        self._building_ui = True
        self.current_class_name = class_name
        self.class_name_edit.setText(cls_def.name)
        self.refresh_base_class_combo()
        index = self.base_class_combo.findText(cls_def.base_class)
        self.base_class_combo.setCurrentIndex(index if index >= 0 else 0)
        self.has_virtual_check.setChecked(cls_def.has_virtual)

        self.member_table.blockSignals(True)
        self.member_table.setRowCount(0)
        for member in cls_def.members:
            self._append_member_row(member.type_name, member.var_name)
        self.member_table.blockSignals(False)
        self._building_ui = False
        self.update_code_preview()

    # 清空编辑区的所有输入与预览内容，通常在类列表为空时调用。
    def clear_editor(self) -> None:
        self._building_ui = True
        self.class_name_edit.clear()
        self.base_class_combo.setCurrentIndex(0)
        self.has_virtual_check.setChecked(False)
        self.member_table.setRowCount(0)
        self.code_preview.clear()
        self._building_ui = False

    # 按快速添加下拉框当前选中的类型，向成员表中追加一个新成员。
    def add_member_from_combo(self) -> None:
        self.add_member_from_type(self.quick_type_combo.currentText())

    # 根据给定类型名创建成员，并自动生成当前类内唯一的默认变量名。
    def add_member_from_type(self, type_name: str) -> None:
        base_name = DEFAULT_MEMBER_NAMES.get(type_name, "member")
        var_name = self._generate_unique_member_name(base_name)
        self._append_member_row(type_name, var_name)
        self.on_editor_changed()

    # 在成员表格末尾插入一行，将类型名与变量名写入对应单元格。
    def _append_member_row(self, type_name: str, var_name: str) -> None:
        row = self.member_table.rowCount()
        self.member_table.insertRow(row)

        type_item = QTableWidgetItem(type_name)
        name_item = QTableWidgetItem(var_name)
        self.member_table.setItem(row, 0, type_item)
        self.member_table.setItem(row, 1, name_item)

    # 删除当前选中的成员行，并触发后续预览更新。
    def remove_selected_member(self) -> None:
        row = self.member_table.currentRow()
        if row >= 0:
            self.member_table.removeRow(row)
            self.on_editor_changed()

    # 统一处理编辑区变化事件；在非界面构建阶段刷新基类选项并更新代码预览。
    def on_editor_changed(self) -> None:
        if self._building_ui:
            return
        self.refresh_base_class_combo()
        self.update_code_preview()

    # 收集界面中的类定义信息并保存到管理器；支持新增、更新和类名重命名。
    def save_current_class(self) -> None:
        class_name = self.class_name_edit.text().strip()
        if not class_name:
            QMessageBox.warning(self, "保存失败", "请先输入类名")
            return

        members = []
        for row in range(self.member_table.rowCount()):
            type_item = self.member_table.item(row, 0)
            name_item = self.member_table.item(row, 1)
            if type_item is None or name_item is None:
                continue
            members.append(MemberDef(type_item.text().strip(), name_item.text().strip()))

        cls_def = ClassDef(
            name=self.class_name_edit.text().strip(),
            base_class=self.base_class_combo.currentText().strip(),
            members=members,
            has_virtual=self.has_virtual_check.isChecked(),
        )

        try:
            old_name = self.current_class_name or cls_def.name
            if self.current_class_name and self.manager.get_class(self.current_class_name):
                self.manager.update_class(old_name, cls_def)
            else:
                self.manager.add_class(cls_def)
            self.current_class_name = cls_def.name
            self.refresh_class_list()
            self.load_class_into_editor(cls_def.name)
            QMessageBox.information(self, "保存成功", f"类 {cls_def.name} 已保存")
        except ValueError as exc:
            QMessageBox.warning(self, "保存失败", str(exc))

    # 将当前管理器中的全部类定义导出为一个 C++ 头文件。
    def export_all_cpp(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "导出 C++ 头文件", "warcraft_classes.h", "Header Files (*.h)")
        if not path:
            return
        try:
            self.manager.export_all_cpp(path)
            QMessageBox.information(self, "导出成功", f"已导出到：\n{path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "导出失败", str(exc))

    def export_cpp_skeleton(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not directory:
            return
        try:
            self.manager.export_cpp_skeleton(directory)
            QMessageBox.information(self, "导出成功", f"已导出工程骨架到：\n{directory}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "导出失败", str(exc))

    # 根据当前编辑器状态构造临时类定义，并实时刷新右侧代码预览文本。
    def update_code_preview(self) -> None:
        cls_name = self.class_name_edit.text().strip()
        if not cls_name:
            self.code_preview.setPlainText("// 请先创建或选择一个类")
            return

        self.refresh_base_class_combo()
        members = []
        for row in range(self.member_table.rowCount()):
            type_item = self.member_table.item(row, 0)
            name_item = self.member_table.item(row, 1)
            if type_item and name_item:
                members.append(MemberDef(type_item.text().strip(), name_item.text().strip()))

        temp_def = ClassDef(
            name=cls_name,
            base_class=self.base_class_combo.currentText().strip(),
            members=members,
            has_virtual=self.has_virtual_check.isChecked(),
        )

        preview_text = self._generate_preview_for_temp_class(temp_def)
        self.code_preview.setPlainText(preview_text)

    # 按当前类定义生成预览用的 C++ 类声明文本，不直接写回数据管理器。
    # 这里会依次拼接继承声明、构造函数、虚函数接口以及成员变量区块，便于用户即时查看结构变化。
    def _generate_preview_for_temp_class(self, cls_def: ClassDef) -> str:
        inherit_part = f" : public {cls_def.base_class}" if cls_def.base_class else ""
        lines = [f"class {cls_def.name}{inherit_part}", "{", "public:"]
        lines.append(f"    {cls_def.name}();")
        if cls_def.has_virtual:
            lines.append(f"    virtual ~{cls_def.name}() = default;")
            lines.append("    virtual void act();")
        lines.append("")
        lines.append("private:")
        if cls_def.members:
            for member in cls_def.members:
                cpp_type = "std::string" if member.type_name == "string" else ("void*" if member.type_name == "pointer" else member.type_name)
                lines.append(f"    {cpp_type} {member.var_name};")
        else:
            lines.append("    // 暂无成员变量")
        lines.append("};")
        return "\n".join(lines)

    # 依据给定前缀生成未被占用的类名，避免新建类时与已有名称冲突。
    def _generate_unique_class_name(self, prefix: str) -> str:
        names = set(self.manager.get_class_names())
        if prefix not in names:
            return prefix
        index = 1
        while f"{prefix}{index}" in names:
            index += 1
        return f"{prefix}{index}"

    # 依据基础变量名生成当前成员表内唯一的新变量名，用于快速添加成员。
    def _generate_unique_member_name(self, base_name: str) -> str:
        existing = set()
        for row in range(self.member_table.rowCount()):
            item = self.member_table.item(row, 1)
            if item:
                existing.add(item.text().strip())
        if base_name not in existing:
            return base_name
        index = 1
        while f"{base_name}{index}" in existing:
            index += 1
        return f"{base_name}{index}"
