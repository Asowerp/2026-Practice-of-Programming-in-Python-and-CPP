from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from engine.class_manager import ClassManager
from constants import APP_STYLE, TYPE_COLORS
from engine.models import MemoryBlock


# 内存画布：将类的内存布局按块绘制为可视化条形切片，并支持悬浮提示与选中高亮。
# 该控件只负责显示布局结果，不直接参与布局计算。
class MemoryCanvas(QFrame):
    # 初始化画布状态，保存待绘制的内存块、选中项以及命中检测矩形集合。
    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[MemoryBlock] = []
        self.total_size = 0
        self.selected_index = -1
        self.block_rects: list[QRect] = []
        self.class_name = ""
        self.setMouseTracking(True)
        self.setMinimumHeight(420)
        self.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; }"
        )

    # 设置最新的内存布局数据，并重置选中状态后触发界面重绘。
    def set_layout_data(self, blocks: list[MemoryBlock], total_size: int, class_name: str = "") -> None:
        self.blocks = blocks
        self.total_size = total_size
        self.selected_index = -1
        self.block_rects = []
        self.class_name = class_name
        self.update()

    # 按比例绘制对象内存切片图，将各内存块映射到画布上的可视矩形。
    # 包含：宽柱状条（居中）、偏移标签、类型名、来源类标签、继承分组虚线框、总量徽章。
    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bar_width = 220
        margin_left = max(80, (self.width() - bar_width) // 2)
        margin_top = 28
        available_height = max(280, self.height() - 60)
        total_size = max(1, self.total_size)
        scale = available_height / total_size

        self.block_rects = []

        title_font = QFont("Segoe UI", 11)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#334155"))
        painter.drawText(20, 20, "对象内存切片")

        label_font = QFont("Segoe UI", 9)
        label_font.setBold(True)
        block_font = QFont("Segoe UI", 9)
        block_font.setBold(True)
        tag_font = QFont("Segoe UI", 7)
        tag_font.setBold(True)

        for index, block in enumerate(self.blocks):
            rect_height = max(28, int(block.size * scale))
            y = margin_top + int(block.offset * scale)
            rect = QRect(margin_left, y, bar_width, rect_height)
            self.block_rects.append(rect)

            color = QColor(TYPE_COLORS.get(block.type_name,
                           TYPE_COLORS.get(block.block_type, "#94A3B8")))
            painter.setBrush(color)
            border_color = QColor("#6366F1") if index == self.selected_index else QColor("#E2E8F0")
            pen = QPen(border_color)
            pen.setWidth(2 if index == self.selected_index else 1)
            painter.setPen(pen)
            painter.drawRoundedRect(rect, 4, 4)

            painter.setFont(block_font)
            painter.setPen(QColor("#1E293B"))
            text_rect = rect.adjusted(10, 0, -10, 0)
            painter.drawText(text_rect,
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             f"{block.name}  ({block.size}B)")

            painter.setFont(label_font)
            painter.setPen(QColor("#64748B"))
            mid_y = y + rect_height // 2 + 4
            painter.drawText(margin_left - 44, mid_y, f"{block.offset}")
            painter.drawText(margin_left + bar_width + 30, mid_y, block.type_name)

            if block.source_class and block.block_type != "padding":
                source_text = block.source_class
                tag_width = len(source_text) * 10 + 12
                tag_x = margin_left + bar_width + 88
                tag_rect = QRect(tag_x, y + 3, tag_width, rect_height - 6)
                tag_bg = QColor("#F1F5F9")
                painter.setBrush(tag_bg)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(tag_rect, 4, 4)
                painter.setFont(tag_font)
                painter.setPen(QColor("#64748B"))
                painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, source_text)

        if not self.blocks:
            placeholder_font = QFont("Segoe UI", 11)
            painter.setFont(placeholder_font)
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "请选择一个类并点击刷新，查看内存布局")
            return

        self._draw_inheritance_brackets(painter, margin_left, bar_width)

        badge_font = QFont("Segoe UI", 10)
        badge_font.setBold(True)
        badge_text = f"总大小 {self.total_size} B"
        badge_width = len(badge_text) * 12 + 24
        badge_x = self.width() - badge_width - 16
        badge_y = self.height() - 38
        badge_rect = QRect(badge_x, badge_y, badge_width, 30)
        painter.setBrush(QColor("#EEF2FF"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(badge_rect, 15, 15)
        painter.setFont(badge_font)
        painter.setPen(QColor("#4F46E5"))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)

    # 为继承自基类的内存块组绘制虚线分组框与来源标注，强化继承关系的视觉区隔。
    def _draw_inheritance_brackets(self, painter: QPainter, margin_left: int, bar_width: int) -> None:
        if not self.class_name:
            return

        groups: list[tuple[str, list[int]]] = []
        current_source = ""
        current_indices: list[int] = []

        for i, block in enumerate(self.blocks):
            source = block.source_class
            if source == current_source:
                current_indices.append(i)
            else:
                if current_indices and current_source and current_source != self.class_name:
                    groups.append((current_source, current_indices[:]))
                current_source = source
                current_indices = [i]

        if current_indices and current_source and current_source != self.class_name:
            groups.append((current_source, current_indices[:]))

        if not groups:
            return

        bracket_font = QFont("Segoe UI", 11)
        bracket_font.setBold(True)

        for source_name, indices in groups:
            if not indices:
                continue

            min_y = min(self.block_rects[i].top() for i in indices)
            max_y = max(self.block_rects[i].bottom() for i in indices)
            pad = 6

            bracket_rect = QRect(
                margin_left - 12, min_y - pad,
                bar_width + 24, max_y - min_y + pad * 2,
            )

            pen = QPen(QColor("#818CF8"))
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setWidthF(1.5)
            painter.setPen(pen)
            fill = QColor("#EEF2FF")
            fill.setAlpha(45)
            painter.setBrush(fill)
            painter.drawRoundedRect(bracket_rect, 8, 8)

            painter.setFont(bracket_font)
            mid_y = int((min_y + max_y) / 2)
            label = f"继承自 {source_name}"
            fm = painter.fontMetrics()
            text_width = fm.horizontalAdvance(label)
            text_right = margin_left - 48
            text_left = text_right - text_width

            painter.setPen(QColor("#818CF8"))
            label_rect = QRect(text_left, mid_y - 13, text_width, 26)
            painter.drawText(
                label_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                label,
            )

            arrow_start_x = text_right + 6
            arrow_end_x = margin_left - 12
            arrow_y = mid_y

            line_pen = QPen(QColor("#818CF8"), 1.2)
            painter.setPen(line_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(arrow_start_x + 5, arrow_y, arrow_end_x, arrow_y)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#818CF8"))
            painter.drawPolygon([
                QPoint(arrow_start_x, arrow_y),
                QPoint(arrow_start_x + 5, arrow_y - 3),
                QPoint(arrow_start_x + 5, arrow_y + 3),
            ])

    # 鼠标移动时检测当前命中的内存块，并以工具提示方式显示其偏移、大小和类型信息。
    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        global_pos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
        for index, rect in enumerate(self.block_rects):
            if rect.contains(event.position().toPoint()):
                block = self.blocks[index]
                QToolTip.showText(
                    global_pos,
                    f"名称: {block.name}\n类型: {block.type_name}\n偏移: {block.offset}\n大小: {block.size} 字节",
                    self,
                )
                return
        QToolTip.hideText()
        super().mouseMoveEvent(event)

    # 鼠标点击时更新选中的内存块索引，并通过重绘显示高亮边框。
    def mousePressEvent(self, event) -> None:  # noqa: N802
        for index, rect in enumerate(self.block_rects):
            if rect.contains(event.pos()):
                self.selected_index = index
                self.update()
                return
        self.selected_index = -1
        self.update()
        super().mousePressEvent(event)


# 内存视图主界面：负责选择类、触发布局刷新，并同时展示图形化切片和表格详情。
# 它通过 ClassManager 获取内存布局计算结果，再同步更新多个显示区域。
class MemoryViewWidget(QWidget):
    # 初始化内存视图，准备共享管理器并构建界面与默认展示内容。
    def __init__(self, manager: ClassManager | None = None) -> None:
        super().__init__()
        self.manager = manager or ClassManager.get_instance()
        self.manager.seed_demo_classes()
        self._build_ui()
        self.refresh_class_names()
        self.refresh_layout()

    # 构建主界面布局，包括顶部控制区、左侧画布和右侧说明/详情区域。
    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("内存切片视图")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("用教学化简方式展示对象的内存布局：vptr、成员变量、padding 与总大小")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 13px;")
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        control_group = QGroupBox("查看设置")
        control_layout = QHBoxLayout(control_group)
        control_layout.addWidget(QLabel("选择类"))
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.refresh_layout)
        control_layout.addWidget(self.class_combo)

        self.reload_classes_btn = QPushButton("刷新类列表")
        self.reload_classes_btn.clicked.connect(self.refresh_class_names)
        control_layout.addWidget(self.reload_classes_btn)

        self.refresh_btn = QPushButton("刷新布局")
        self.refresh_btn.setObjectName("btnPrimary")
        self.refresh_btn.clicked.connect(self.refresh_layout)
        control_layout.addWidget(self.refresh_btn)
        control_layout.addStretch(1)

        self.summary_label = QLabel("总大小：0 字节")
        self.summary_label.setStyleSheet("font-weight: 700; color: #4F46E5; font-size: 14px;")
        control_layout.addWidget(self.summary_label)

        content_layout = QHBoxLayout()
        self.canvas = MemoryCanvas()
        content_layout.addWidget(self.canvas, 3)

        right_panel = QVBoxLayout()
        right_panel.addWidget(self._build_legend_group())
        right_panel.addWidget(self._build_table_group(), 3)
        content_layout.addLayout(right_panel, 2)

        main_layout.addWidget(control_group)
        main_layout.addLayout(content_layout)

    # 构建颜色说明面板，帮助用户理解不同内存块类型的可视化颜色含义。
    def _build_legend_group(self) -> QGroupBox:
        group = QGroupBox("颜色说明")
        layout = QVBoxLayout(group)
        legend_items = [
            ("vptr", "虚函数表指针"),
            ("int", "整型成员"),
            ("double", "双精度成员"),
            ("char", "字符成员"),
            ("bool", "布尔成员"),
            ("pointer", "指针/引用型成员"),
            ("padding", "对齐补位"),
        ]
        for key, text in legend_items:
            row = QHBoxLayout()
            color_box = QLabel()
            color_box.setFixedSize(18, 18)
            color_box.setStyleSheet(
                f"background: {TYPE_COLORS.get(key, '#94A3B8')}; border: 1px solid #E2E8F0; border-radius: 4px;"
            )
            row.addWidget(color_box)
            row.addWidget(QLabel(text))
            row.addStretch(1)
            layout.addLayout(row)
        return group

    # 构建详细信息表格，用于按行展示每个内存块的偏移、大小、名称和类型。
    def _build_table_group(self) -> QGroupBox:
        group = QGroupBox("详细信息")
        layout = QVBoxLayout(group)
        self.detail_table = QTableWidget(0, 5)
        self.detail_table.setHorizontalHeaderLabels(["offset", "size", "name", "type", "定义来源"])
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.horizontalHeader().setStretchLastSection(True)
        self.detail_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.detail_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.detail_table)
        return group

    # 重新读取当前全部类名并刷新下拉框，同时尽量保留用户原来的选中项。
    def refresh_class_names(self) -> None:
        current_text = self.class_combo.currentText()
        self.class_combo.blockSignals(True)
        self.class_combo.clear()
        class_names = self.manager.get_class_names()
        self.class_combo.addItems(class_names)
        if current_text:
            index = self.class_combo.findText(current_text)
            if index >= 0:
                self.class_combo.setCurrentIndex(index)
            elif class_names:
                self.class_combo.setCurrentIndex(0)
        elif class_names:
            self.class_combo.setCurrentIndex(0)
        self.class_combo.blockSignals(False)
        self.refresh_layout()

    # 根据当前选中的类重新计算并展示内存布局；若没有可选类则清空所有展示结果。
    def refresh_layout(self) -> None:
        class_name = self.class_combo.currentText().strip()
        if not class_name:
            self.canvas.set_layout_data([], 0)
            self.summary_label.setText("总大小：0 字节")
            self.detail_table.setRowCount(0)
            return

        blocks, total_size = self.manager.compute_memory_layout(class_name)
        self.canvas.set_layout_data(blocks, total_size, class_name)
        self.summary_label.setText(f"总大小：{total_size} 字节")
        self._fill_detail_table(blocks)

    # 将计算得到的内存块逐行填入详情表，并用浅色背景与画布中的颜色保持对应关系。
    def _fill_detail_table(self, blocks: list[MemoryBlock]) -> None:
        self.detail_table.setRowCount(0)
        for block in blocks:
            row = self.detail_table.rowCount()
            self.detail_table.insertRow(row)
            self.detail_table.setItem(row, 0, QTableWidgetItem(str(block.offset)))
            self.detail_table.setItem(row, 1, QTableWidgetItem(str(block.size)))
            self.detail_table.setItem(row, 2, QTableWidgetItem(block.name))
            self.detail_table.setItem(row, 3, QTableWidgetItem(block.type_name))
            self.detail_table.setItem(row, 4, QTableWidgetItem(block.source_class))

            color = TYPE_COLORS.get(block.type_name, TYPE_COLORS.get(block.block_type, "#94A3B8"))
            for column in range(5):
                item = self.detail_table.item(row, column)
                if item is not None:
                    item.setBackground(QColor(color).lighter(165))
