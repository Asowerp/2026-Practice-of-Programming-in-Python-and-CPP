from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QColor, QDrag
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


def _soft_block_color(color: str, lightness: int = 188) -> str:
    return QColor(color).lighter(lightness).name()


OptionProvider = list[str] | Callable[[], list[str]]


@dataclass
class FieldSpec:
    name: str
    label: str
    field_type: str = "text"
    default: object = ""
    options: OptionProvider | None = None
    minimum: int = 0
    maximum: int = 9999
    editable: bool = True
    placeholder: str = ""
    width: int = 110


@dataclass
class BlockSpec:
    key: str
    title: str
    color: str
    description: str = ""
    fields: list[FieldSpec] = field(default_factory=list)


class BlockPaletteList(QListWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setDragEnabled(True)
        self.setSpacing(8)
        self.setStyleSheet(
            "QListWidget { background: #F8FAFC; padding: 8px; }"
            "QListWidget::item {"
            " background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1;"
            " border-radius: 12px; padding: 12px 14px; margin: 2px 0; font-size: 13px; font-weight: 600; }"
            "QListWidget::item:selected { background: #E0E7FF; border-color: #6366F1; color: #312E81; }"
            "QListWidget::item:hover:!selected { background: #F8FAFC; border-color: #94A3B8; }"
        )

    def startDrag(self, supportedActions) -> None:  # noqa: N802
        item = self.currentItem()
        if item is None:
            return
        block_key = item.data(Qt.ItemDataRole.UserRole)
        if not block_key:
            return

        mime_data = QMimeData()
        mime_data.setText(str(block_key))

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)


class BlockWorkspaceList(QListWidget):
    blockDropped = Signal(str, int)
    orderChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setDropIndicatorShown(True)
        self.setSpacing(10)
        self.setMinimumWidth(520)
        self.setStyleSheet(
            "QListWidget { background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 10px; }"
            "QListWidget::item { background: transparent; border: none; padding: 2px; }"
            "QListWidget::item:selected { background: #EEF2FF; border-radius: 12px; }"
        )

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.source() is self:
            event.acceptProposedAction()
            return
        if event.mimeData().hasText():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        if event.source() is self:
            event.acceptProposedAction()
            return
        if event.mimeData().hasText():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802
        if event.source() is self:
            super().dropEvent(event)
            self.orderChanged.emit()
            return

        if event.mimeData().hasText():
            row = self.indexAt(event.position().toPoint()).row()
            self.blockDropped.emit(event.mimeData().text(), row)
            event.acceptProposedAction()
            return

        super().dropEvent(event)


class BlockItemWidget(QFrame):
    removeRequested = Signal()

    def __init__(
        self,
        spec: BlockSpec,
        field_values: dict[str, object] | None = None,
        *,
        step_no: int = 0,
    ) -> None:
        super().__init__()
        self.spec = spec
        self.step_no = step_no
        self.field_specs = {field_spec.name: field_spec for field_spec in spec.fields}
        self.controls: dict[str, QWidget] = {}
        self.setObjectName("BlockItemWidget")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "QFrame#BlockItemWidget {"
            " background: #FFFFFF; border-radius: 16px; border: 1px solid #CBD5E1; }"
            "QLabel#BlockStepBadge {"
            " background: #0F172A; color: #FFFFFF; border-radius: 10px; padding: 3px 10px;"
            " font-size: 12px; font-weight: 700; }"
            f"QLabel#BlockTag {{ background: {_soft_block_color(spec.color)}; color: {spec.color};"
            " border-radius: 10px; padding: 3px 10px; font-size: 12px; font-weight: 700; }"
            "QLabel#BlockTitle { color: #0F172A; font-size: 16px; font-weight: 800; }"
            "QLabel#BlockDesc { color: #475569; font-size: 13px; line-height: 1.4; }"
            "QLabel#FieldLabel { color: #334155; font-size: 12px; font-weight: 700; }"
            "QPushButton#BlockRemoveBtn { background: #F8FAFC; color: #334155; border: 1px solid #CBD5E1; border-radius: 10px; padding: 5px 12px; font-weight: 700; }"
            "QPushButton#BlockRemoveBtn:hover { background: #EEF2FF; border-color: #94A3B8; }"
            "QLineEdit, QComboBox, QSpinBox {"
            " background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 10px; padding: 6px 10px; min-height: 18px; }"
            "QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #6366F1; }"
        )
        self._build_ui()
        if field_values:
            self.set_field_values(field_values)
        self.refresh_dynamic_fields()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        accent = QFrame()
        accent.setFixedHeight(6)
        accent.setStyleSheet(
            f"background: {self.spec.color}; border-radius: 3px;"
        )
        layout.addWidget(accent)

        header_row = QHBoxLayout()
        badge = QLabel(self._step_text())
        badge.setObjectName("BlockStepBadge")
        header_row.addWidget(badge)

        tag = QLabel(self.spec.key)
        tag.setObjectName("BlockTag")
        header_row.addWidget(tag)
        header_row.addStretch(1)

        remove_button = QPushButton("删除")
        remove_button.setObjectName("BlockRemoveBtn")
        remove_button.clicked.connect(self.removeRequested.emit)
        header_row.addWidget(remove_button)
        layout.addLayout(header_row)

        title_label = QLabel(self.spec.title)
        title_label.setObjectName("BlockTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        if self.spec.description:
            desc_label = QLabel(self.spec.description)
            desc_label.setObjectName("BlockDesc")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        if not self.spec.fields:
            return

        field_grid = QGridLayout()
        field_grid.setContentsMargins(0, 2, 0, 0)
        field_grid.setHorizontalSpacing(12)
        field_grid.setVerticalSpacing(10)
        for index, field_spec in enumerate(self.spec.fields):
            row = index // 2
            column = index % 2
            label = QLabel(field_spec.label)
            label.setObjectName("FieldLabel")
            control = self._create_control(field_spec)
            self.controls[field_spec.name] = control
            cell = QWidget()
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(5)
            cell_layout.addWidget(label)
            cell_layout.addWidget(control)
            field_grid.addWidget(cell, row, column)
        layout.addLayout(field_grid)

    def _create_control(self, field_spec: FieldSpec) -> QWidget:
        if field_spec.field_type == "int":
            control = QSpinBox()
            control.setRange(field_spec.minimum, field_spec.maximum)
            control.setValue(int(field_spec.default))
            control.setMinimumWidth(max(120, field_spec.width))
            return control

        if field_spec.field_type == "combo":
            control = QComboBox()
            control.setEditable(field_spec.editable)
            control.setMinimumWidth(max(130, field_spec.width))
            options = self._resolve_options(field_spec.options)
            if options:
                control.addItems(options)
            if field_spec.default:
                self._set_combo_value(control, str(field_spec.default), field_spec.editable)
            return control

        control = QLineEdit()
        control.setText(str(field_spec.default))
        if field_spec.placeholder:
            control.setPlaceholderText(field_spec.placeholder)
        control.setMinimumWidth(max(130, field_spec.width))
        return control

    def set_step_no(self, step_no: int) -> None:
        self.step_no = step_no
        for label in self.findChildren(QLabel, "BlockStepBadge"):
            label.setText(self._step_text())

    def _step_text(self) -> str:
        return f"步骤 {self.step_no}" if self.step_no > 0 else "步骤"

    def refresh_dynamic_fields(self) -> None:
        for field_name, control in self.controls.items():
            field_spec = self.field_specs[field_name]
            if field_spec.field_type != "combo" or field_spec.options is None:
                continue
            if not callable(field_spec.options):
                continue

            combo = control
            if not isinstance(combo, QComboBox):
                continue
            current_text = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(self._resolve_options(field_spec.options))
            self._set_combo_value(combo, current_text or str(field_spec.default), field_spec.editable)
            combo.blockSignals(False)

    def read_fields(self) -> dict[str, object]:
        values: dict[str, object] = {}
        for field_name, control in self.controls.items():
            if isinstance(control, QSpinBox):
                values[field_name] = control.value()
            elif isinstance(control, QComboBox):
                values[field_name] = control.currentText().strip()
            elif isinstance(control, QLineEdit):
                values[field_name] = control.text().strip()
        return values

    def set_field_values(self, values: dict[str, object]) -> None:
        for field_name, value in values.items():
            control = self.controls.get(field_name)
            field_spec = self.field_specs.get(field_name)
            if control is None or field_spec is None:
                continue

            if isinstance(control, QSpinBox):
                control.setValue(int(value))
            elif isinstance(control, QComboBox):
                self._set_combo_value(control, str(value), field_spec.editable)
            elif isinstance(control, QLineEdit):
                control.setText(str(value))

    def serialize(self) -> dict[str, object]:
        return {
            "key": self.spec.key,
            "fields": self.read_fields(),
        }

    @staticmethod
    def _resolve_options(options: OptionProvider | None) -> list[str]:
        if options is None:
            return []
        if callable(options):
            return list(options())
        return list(options)

    @staticmethod
    def _set_combo_value(combo: QComboBox, value: str, editable: bool) -> None:
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)
            return
        if editable:
            combo.setEditText(value)


class BlockProgramEditor(QWidget):
    scriptChanged = Signal()

    def __init__(self, block_specs: list[BlockSpec]) -> None:
        super().__init__()
        self.block_specs = {block_spec.key: block_spec for block_spec in block_specs}
        self._ordered_specs = block_specs
        self._build_ui()
        self._fill_palette()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_palette_group())
        splitter.addWidget(self._build_workspace_group())
        splitter.setSizes([260, 620])
        layout.addWidget(splitter)

    def _build_palette_group(self) -> QGroupBox:
        group = QGroupBox("积木库")
        layout = QVBoxLayout(group)
        hint = QLabel("把左边积木拖到右侧工作区，再上下拖动调整顺序。双击也能快速加入。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #64748B; font-size: 12px;")
        layout.addWidget(hint)

        self.palette = BlockPaletteList()
        self.palette.itemDoubleClicked.connect(self._handle_palette_double_click)
        layout.addWidget(self.palette)
        return group

    def _build_workspace_group(self) -> QGroupBox:
        group = QGroupBox("脚本工作区")
        layout = QVBoxLayout(group)

        summary = QLabel("建议按从上到下的顺序组织流程。每个积木都会显示“步骤编号、标题、说明和输入字段”。")
        summary.setWordWrap(True)
        summary.setStyleSheet("color: #64748B; font-size: 12px;")
        layout.addWidget(summary)

        self.workspace = BlockWorkspaceList()
        self.workspace.blockDropped.connect(self.add_block_by_key)
        self.workspace.orderChanged.connect(self._handle_workspace_order_changed)
        layout.addWidget(self.workspace)

        button_row = QHBoxLayout()
        self.delete_btn = QPushButton("删除选中积木")
        self.clear_btn = QPushButton("清空工作区")
        self.delete_btn.clicked.connect(self.delete_selected_block)
        self.clear_btn.clicked.connect(self.clear_blocks)
        button_row.addWidget(self.delete_btn)
        button_row.addWidget(self.clear_btn)
        button_row.addStretch(1)
        layout.addLayout(button_row)
        return group

    def _fill_palette(self) -> None:
        self.palette.clear()
        for block_spec in self._ordered_specs:
            item = QListWidgetItem(block_spec.title)
            item.setData(Qt.ItemDataRole.UserRole, block_spec.key)
            item.setToolTip(block_spec.description)
            item.setBackground(QColor(block_spec.color).lighter(165))
            self.palette.addItem(item)

    def _handle_palette_double_click(self, item: QListWidgetItem) -> None:
        block_key = item.data(Qt.ItemDataRole.UserRole)
        if block_key:
            self.add_block_by_key(str(block_key), -1)

    def add_block_by_key(
        self,
        block_key: str,
        index: int = -1,
        field_values: dict[str, object] | None = None,
    ) -> None:
        block_spec = self.block_specs.get(block_key)
        if block_spec is None:
            return

        item = QListWidgetItem()
        widget = BlockItemWidget(block_spec, field_values, step_no=self._resolve_step_no(index))
        widget.removeRequested.connect(lambda: self._remove_item(item))
        item.setSizeHint(widget.sizeHint())

        if 0 <= index < self.workspace.count():
            self.workspace.insertItem(index, item)
        else:
            self.workspace.addItem(item)
        self.workspace.setItemWidget(item, widget)
        self._refresh_step_numbers()
        self.scriptChanged.emit()

    def get_script(self) -> list[dict[str, object]]:
        script: list[dict[str, object]] = []
        for row in range(self.workspace.count()):
            item = self.workspace.item(row)
            widget = self.workspace.itemWidget(item)
            if isinstance(widget, BlockItemWidget):
                script.append(widget.serialize())
        return script

    def set_script(self, script: list[dict[str, object]]) -> None:
        self.clear_blocks()
        for block in script:
            self.add_block_by_key(
                str(block.get("key", "")),
                -1,
                block.get("fields", {}),
            )

    def clear_blocks(self) -> None:
        while self.workspace.count() > 0:
            item = self.workspace.takeItem(0)
            widget = self.workspace.itemWidget(item)
            if widget is not None:
                widget.deleteLater()
            del item
        self._refresh_step_numbers()
        self.scriptChanged.emit()

    def delete_selected_block(self) -> None:
        row = self.workspace.currentRow()
        if row >= 0:
            self._remove_item(self.workspace.item(row))

    def refresh_dynamic_fields(self) -> None:
        for row in range(self.workspace.count()):
            item = self.workspace.item(row)
            widget = self.workspace.itemWidget(item)
            if isinstance(widget, BlockItemWidget):
                widget.refresh_dynamic_fields()

    def _remove_item(self, item: QListWidgetItem) -> None:
        row = self.workspace.row(item)
        taken_item = self.workspace.takeItem(row)
        widget = self.workspace.itemWidget(taken_item)
        if widget is not None:
            widget.deleteLater()
        del taken_item
        self._refresh_step_numbers()
        self.scriptChanged.emit()

    def _handle_workspace_order_changed(self) -> None:
        self._refresh_step_numbers()
        self.scriptChanged.emit()

    def _refresh_step_numbers(self) -> None:
        for row in range(self.workspace.count()):
            item = self.workspace.item(row)
            widget = self.workspace.itemWidget(item)
            if isinstance(widget, BlockItemWidget):
                widget.set_step_no(row + 1)
                item.setSizeHint(widget.sizeHint())

    def _resolve_step_no(self, index: int) -> int:
        if 0 <= index < self.workspace.count():
            return index + 1
        return self.workspace.count() + 1
