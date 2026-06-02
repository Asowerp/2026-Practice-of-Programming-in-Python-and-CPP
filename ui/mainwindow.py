from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QVBoxLayout
from PySide6.QtGui import QIcon
from engine.timeline import TimelineController
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
        self.resize(screen.width(), screen.height())
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

        self.timeline_controller = TimelineController(self.ui)

        self.task2_widget.eventsExported.connect(self.task3_widget.load_simulation_bundle)
        self.task2_widget.eventsExported.connect(self.timeline_controller.load_simulation_bundle)

        self.ui.tabWidget.setCurrentIndex(0)

        self.setup_menu()

    def setup_menu(self):
        self.setWindowIcon(QIcon(":/icons/app_icon.svg"))
        self.ui.act_quit.triggered.connect(self.close)
        self.ui.act_about.triggered.connect(self.show_about)
        self.ui.act_introduction.triggered.connect(self.show_introduction)
        self.ui.act_export_cpp_code.triggered.connect(self.export_cpp)

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
