# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QSlider, QStatusBar,
    QTabWidget, QVBoxLayout, QWidget)
import ui.resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(648, 368)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(0, 0))
        MainWindow.setMaximumSize(QSize(16777215, 16777215))
        icon = QIcon()
        icon.addFile(u":/icons/app_icon.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setTabShape(QTabWidget.TabShape.Rounded)
        self.act_export_cpp_code = QAction(MainWindow)
        self.act_export_cpp_code.setObjectName(u"act_export_cpp_code")
        self.act_export_cpp_code.setCheckable(True)
        icon1 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentSave))
        self.act_export_cpp_code.setIcon(icon1)
        self.act_export_cpp_code.setMenuRole(QAction.MenuRole.NoRole)
        self.act_quit = QAction(MainWindow)
        self.act_quit.setObjectName(u"act_quit")
        self.act_quit.setCheckable(True)
        icon2 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ApplicationExit))
        self.act_quit.setIcon(icon2)
        self.act_quit.setMenuRole(QAction.MenuRole.NoRole)
        self.act_about = QAction(MainWindow)
        self.act_about.setObjectName(u"act_about")
        self.act_about.setCheckable(True)
        icon3 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.HelpAbout))
        self.act_about.setIcon(icon3)
        self.act_about.setMenuRole(QAction.MenuRole.NoRole)
        self.act_introduction = QAction(MainWindow)
        self.act_introduction.setObjectName(u"act_introduction")
        icon4 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.HelpFaq))
        self.act_introduction.setIcon(icon4)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_2 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setTabsClosable(False)
        self.class_editor = QWidget()
        self.class_editor.setObjectName(u"class_editor")
        self.tabWidget.addTab(self.class_editor, "")
        self.memory_view = QWidget()
        self.memory_view.setObjectName(u"memory_view")
        self.tabWidget.addTab(self.memory_view, "")
        self.timeline = QWidget()
        self.timeline.setObjectName(u"timeline")
        self.verticalLayout_2 = QVBoxLayout(self.timeline)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.btn_prev = QPushButton(self.timeline)
        self.btn_prev.setObjectName(u"btn_prev")
        icon5 = QIcon()
        icon5.addFile(u":/icons/prev.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_prev.setIcon(icon5)

        self.horizontalLayout.addWidget(self.btn_prev)

        self.btn_play = QPushButton(self.timeline)
        self.btn_play.setObjectName(u"btn_play")
        icon6 = QIcon()
        icon6.addFile(u":/icons/play.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_play.setIcon(icon6)

        self.horizontalLayout.addWidget(self.btn_play)

        self.btn_next = QPushButton(self.timeline)
        self.btn_next.setObjectName(u"btn_next")
        icon7 = QIcon()
        icon7.addFile(u":/icons/next.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_next.setIcon(icon7)

        self.horizontalLayout.addWidget(self.btn_next)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.lbl_timeline = QLabel(self.timeline)
        self.lbl_timeline.setObjectName(u"lbl_timeline")
        self.lbl_timeline.setMinimumSize(QSize(0, 1))

        self.verticalLayout.addWidget(self.lbl_timeline)

        self.horizontalSlider = QSlider(self.timeline)
        self.horizontalSlider.setObjectName(u"horizontalSlider")
        self.horizontalSlider.setOrientation(Qt.Orientation.Horizontal)

        self.verticalLayout.addWidget(self.horizontalSlider)

        self.listWidget = QListWidget(self.timeline)
        self.listWidget.setObjectName(u"listWidget")

        self.verticalLayout.addWidget(self.listWidget)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.tabWidget.addTab(self.timeline, "")
        self.task1 = QWidget()
        self.task1.setObjectName(u"task1")
        self.tabWidget.addTab(self.task1, "")
        self.task2 = QWidget()
        self.task2.setObjectName(u"task2")
        self.tabWidget.addTab(self.task2, "")
        self.task3 = QWidget()
        self.task3.setObjectName(u"task3")
        self.tabWidget.addTab(self.task3, "")

        self.horizontalLayout_2.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 648, 17))
        self.menu_file = QMenu(self.menubar)
        self.menu_file.setObjectName(u"menu_file")
        self.menu_help = QMenu(self.menubar)
        self.menu_help.setObjectName(u"menu_help")
        self.menu_help.setSeparatorsCollapsible(False)
        self.menu_help.setToolTipsVisible(False)
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menu_file.menuAction())
        self.menubar.addAction(self.menu_help.menuAction())
        self.menu_file.addAction(self.act_export_cpp_code)
        self.menu_file.addAction(self.act_quit)
        self.menu_help.addAction(self.act_about)
        self.menu_help.addAction(self.act_introduction)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(5)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.act_export_cpp_code.setText(QCoreApplication.translate("MainWindow", u"\u5bfc\u51faC++\u4ee3\u7801", None))
#if QT_CONFIG(shortcut)
        self.act_export_cpp_code.setShortcut(QCoreApplication.translate("MainWindow", u"Alt+E", None))
#endif // QT_CONFIG(shortcut)
        self.act_quit.setText(QCoreApplication.translate("MainWindow", u"\u9000\u51fa", None))
#if QT_CONFIG(shortcut)
        self.act_quit.setShortcut(QCoreApplication.translate("MainWindow", u"Alt+Q", None))
#endif // QT_CONFIG(shortcut)
        self.act_about.setText(QCoreApplication.translate("MainWindow", u"\u5173\u4e8e", None))
#if QT_CONFIG(shortcut)
        self.act_about.setShortcut(QCoreApplication.translate("MainWindow", u"Alt+H", None))
#endif // QT_CONFIG(shortcut)
        self.act_introduction.setText(QCoreApplication.translate("MainWindow", u"\u6307\u5357", None))
#if QT_CONFIG(shortcut)
        self.act_introduction.setShortcut(QCoreApplication.translate("MainWindow", u"Alt+I", None))
#endif // QT_CONFIG(shortcut)
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.class_editor), QCoreApplication.translate("MainWindow", u"\u7c7b\u7f16\u8f91\u5668", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.memory_view), QCoreApplication.translate("MainWindow", u"\u5185\u5b58\u89c6\u56fe", None))
        self.btn_prev.setText("")
        self.btn_play.setText("")
        self.btn_next.setText("")
        self.lbl_timeline.setText(QCoreApplication.translate("MainWindow", u"\u65f6\u95f4\u8f74\u8fdb\u5ea6", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.timeline), QCoreApplication.translate("MainWindow", u"\u65f6\u95f4\u8f74", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.task1), QCoreApplication.translate("MainWindow", u"Task1\uff1a\u6b66\u58eb\u5c42\u7ea7", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.task2), QCoreApplication.translate("MainWindow", u"Task2\uff1a\u6218\u6597\u5b9e\u9a8c\u5ba4", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.task3), QCoreApplication.translate("MainWindow", u"Task3\uff1a\u65e5\u5fd7\u52a9\u624b", None))
        self.menu_file.setTitle(QCoreApplication.translate("MainWindow", u"\u6587\u4ef6", None))
        self.menu_help.setTitle(QCoreApplication.translate("MainWindow", u"\u5e2e\u52a9", None))
    # retranslateUi

