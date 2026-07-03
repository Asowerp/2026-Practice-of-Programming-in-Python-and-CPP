from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QVBoxLayout
from PySide6.QtGui import QIcon
from engine.class_manager import ClassManager
from ui.ui_form import Ui_MainWindow
from ui.class_editor_widget import ClassEditorWidget
from ui.memory_view_widget import MemoryViewWidget
from ui.task1_widget import Task1Widget
from ui.task2_widget import Task2Widget
from ui.task3_widget import Task3Widget
from ui.ui_dialog import QDialog, Ui_Dialog


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        screen = QApplication.primaryScreen().availableGeometry()
        target_width = min(1440, max(1180, int(screen.width() * 0.88)))
        target_height = min(920, max(760, int(screen.height() * 0.86)))
        self.setMinimumSize(QSize(1100, 700))
        self.resize(target_width, target_height)
        self.move(
            screen.x() + max(0, (screen.width() - target_width) // 2),
            screen.y() + max(0, (screen.height() - target_height) // 2),
        )
        self.setWindowTitle("魔兽世界大作业辅助工具  World of Warcraft Helper")

        self.manager = ClassManager.get_instance()
        self.manager.seed_demo_classes()

        self.task2_widget = Task2Widget(self.manager)
        self.task3_widget = Task3Widget(self.manager)

        QVBoxLayout(self.ui.class_editor).addWidget(ClassEditorWidget(self.manager))
        QVBoxLayout(self.ui.memory_view).addWidget(MemoryViewWidget(self.manager))
        QVBoxLayout(self.ui.task1).addWidget(Task1Widget(self.manager))
        QVBoxLayout(self.ui.task2).addWidget(self.task2_widget)
        QVBoxLayout(self.ui.task3).addWidget(self.task3_widget)

        self.task2_widget.eventsExported.connect(self.task3_widget.load_simulation_bundle)

        self.ui.tabWidget.setCurrentIndex(0)
        self._polish_navigation()

        self.setup_menu()

    def setup_menu(self):
        self.setWindowIcon(QIcon(":/icons/app_icon.svg"))
        self.ui.statusbar.showMessage("从“类设计”开始，完成层级设计后进入 Task2 模拟和 Task3 对拍。", 8000)
        self.ui.act_quit.triggered.connect(self.close)
        self.ui.act_about.triggered.connect(self.show_about)
        self.ui.act_introduction.triggered.connect(self.show_introduction)
        self.ui.act_export_cpp_code.triggered.connect(self.export_cpp)

    def _polish_navigation(self):
        timeline_index = self.ui.tabWidget.indexOf(self.ui.timeline)
        if timeline_index >= 0:
            self.ui.tabWidget.removeTab(timeline_index)

        tab_labels = [
            ("1 类设计", "设计 Warrior / Weapon / Headquarter 等 C++ 类结构"),
            ("2 内存", "查看对象大小、成员偏移、vptr 和 padding"),
            ("3 Task1 校验", "检查武士层级、成员和构造初始化思路"),
            ("4 Task2 模拟", "按 Warriors4 题面阶段推进整局模拟，并在页内复盘时间轴"),
            ("5 Task3 对拍", "生成标准日志、按内置时间轴定位输出差异，并用 AI 辅助调错"),
        ]
        for index, (label, tip) in enumerate(tab_labels):
            self.ui.tabWidget.setTabText(index, label)
            self.ui.tabWidget.setTabToolTip(index, tip)

        self.ui.tabWidget.currentChanged.connect(self._handle_tab_changed)

    def _handle_tab_changed(self, index: int) -> None:
        hints = [
            "类设计页：先检查默认模块化结构，再按题面补充自己的类。",
            "内存页：选择类后查看成员偏移、继承来源和 padding。",
            "Task1 页：加载推荐积木后执行校验，快速定位层级设计问题。",
            "Task2 页：加载推荐积木，初始化 Case，运行后可在右侧内置时间轴复盘。",
            "Task3 页：接收 Task2 事件，粘贴输出，对拍后可用内置时间轴定位差异。",
        ]
        if 0 <= index < len(hints):
            self.ui.statusbar.showMessage(hints[index], 6000)

    def export_cpp(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "导出C++类定义", "", "C++ Header Files (*.h)")
        if file_path:
            self.manager.export_all_cpp(file_path)
            QMessageBox.information(self, "导出成功", f"已导出到: {file_path}")

    def show_about(self):
        QMessageBox.about(self, "关于本程序", "魔兽世界大作业辅助工具\nv 1.0")
    
    def show_introduction(self):

        # 实例化弹窗
        dlg = QDialog(self)
        ui_dlg = Ui_Dialog()
        ui_dlg.setupUi(dlg)
        # 如需提前给弹窗控件赋值：ui_dlg.xxx控件.setText("xxx")
        dlg.exec()
