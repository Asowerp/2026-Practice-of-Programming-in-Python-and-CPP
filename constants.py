# 用于教学化简内存布局计算的类型大小表，单位为字节。
TYPE_SIZES = {
    "bool": 1,
    "char": 1,
    "int": 4,
    "float": 4,
    "double": 8,
    "string": 8,
    "pointer": 8,
}

#内存切片视图中不同类型对应的显示颜色。
TYPE_COLORS = {
    "vptr": "#C084FC",
    "bool": "#FDA4AF",
    "char": "#FBBF24",
    "int": "#38BDF8",
    "float": "#38BDF8",
    "double": "#34D399",
    "string": "#F9A8D4",
    "pointer": "#818CF8",
    "padding": "#94A3B8",
}

# 编辑器中允许用户添加的预定义成员类型列表。
AVAILABLE_TYPES = [
    "int",
    "double",
    "char",
    "bool",
    "float",
    "string",
    "pointer",
]

# 新增成员变量时，不同类型默认生成的变量名。
DEFAULT_MEMBER_NAMES = {
    "int": "value",
    "double": "ratio",
    "char": "flag",
    "bool": "enabled",
    "float": "speed",
    "string": "name",
    "pointer": "ptr",
}

# 项目统一界面样式表（扁平化现代仪表盘风格）。
APP_STYLE = """
/* ========== 全局 ========== */
QWidget {
    background-color: #F8FAFC;
    color: #1E293B;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}

/* ========== 标签页 ========== */
QTabWidget::pane {
    background: #F8FAFC;
    border: none;
    border-top: 1px solid #E2E8F0;
    top: -1px;
}
QTabBar::tab {
    background: #F1F5F9;
    color: #64748B;
    border: 1px solid #E2E8F0;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 20px;
    margin-right: 2px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #FFFFFF;
    color: #4F46E5;
    border-bottom: 2px solid #4F46E5;
}
QTabBar::tab:hover:!selected {
    background: #E2E8F0;
    color: #1E293B;
}

/* ========== 卡片容器 ========== */
QGroupBox {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: 700;
    font-size: 13px;
    color: #334155;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #1E293B;
}

QFrame[frameShape="4"], QFrame[frameShape="1"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
}

/* ========== 输入控件 ========== */
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #1E293B;
    selection-background-color: #C7D2FE;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #6366F1;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #E2E8F0;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    selection-background-color: #EEF2FF;
    selection-color: #1E293B;
    outline: none;
}

/* ========== 表格 ========== */
QTableWidget {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    gridline-color: transparent;
    outline: none;
}
QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #F1F5F9;
}
QTableWidget::item:selected {
    background: #EEF2FF;
    color: #1E293B;
}
QHeaderView::section {
    background: #F8FAFC;
    border: none;
    border-bottom: 2px solid #E2E8F0;
    padding: 8px 10px;
    font-weight: 700;
    font-size: 12px;
    color: #64748B;
}

/* ========== 列表 ========== */
QListWidget {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    outline: none;
    padding: 4px;
}
QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
    border: none;
}
QListWidget::item:selected {
    background: #EEF2FF;
    color: #1E293B;
}
QListWidget::item:hover:!selected {
    background: #F1F5F9;
}

/* ========== 滚动条 ========== */
QScrollBar:vertical {
    background: #F8FAFC;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #F8FAFC;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #CBD5E1;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #94A3B8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ========== 分割器 ========== */
QSplitter::handle {
    background: #E2E8F0;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QSplitter::handle:vertical {
    height: 1px;
}

/* ========== 复选框 ========== */
QCheckBox {
    spacing: 8px;
    color: #334155;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #CBD5E1;
    border-radius: 4px;
    background: #FFFFFF;
}
QCheckBox::indicator:checked {
    background: #4F46E5;
    border-color: #4F46E5;
}
QCheckBox::indicator:hover {
    border-color: #6366F1;
}

/* ========== 默认按钮 — 柔和边框样式 ========== */
QPushButton {
    background: #FFFFFF;
    color: #334155;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 13px;
    min-height: 20px;
}
QPushButton:hover {
    background: #F1F5F9;
    border-color: #94A3B8;
}
QPushButton:pressed {
    background: #E2E8F0;
}
QPushButton:disabled {
    background: #F1F5F9;
    color: #94A3B8;
    border-color: #E2E8F0;
}

/* ========== 主要操作按钮 ========== */
QPushButton#btnPrimary {
    background: #4F46E5;
    color: #FFFFFF;
    border: 1px solid #4F46E5;
}
QPushButton#btnPrimary:hover {
    background: #4338CA;
    border-color: #4338CA;
}
QPushButton#btnPrimary:pressed {
    background: #3730A3;
    border-color: #3730A3;
}

/* ========== 危险操作按钮 ========== */
QPushButton#btnDanger {
    background: #EF4444;
    color: #FFFFFF;
    border: 1px solid #EF4444;
}
QPushButton#btnDanger:hover {
    background: #DC2626;
    border-color: #DC2626;
}
QPushButton#btnDanger:pressed {
    background: #B91C1C;
    border-color: #B91C1C;
}

/* ========== 工具提示 ========== */
QToolTip {
    background: #1E293B;
    color: #F1F5F9;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
"""
