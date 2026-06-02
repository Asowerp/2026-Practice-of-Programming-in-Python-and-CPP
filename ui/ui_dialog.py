# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QSizePolicy, QTextBrowser, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(533, 634)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(180, 600, 161, 32))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setCenterButtons(True)
        self.textBrowser = QTextBrowser(Dialog)
        self.textBrowser.setObjectName(u"textBrowser")
        self.textBrowser.setGeometry(QRect(10, 10, 511, 581))

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"introduction", None))
        self.textBrowser.setHtml(QCoreApplication.translate("Dialog", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Microsoft YaHei UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<h1 style=\" margin-top:10px; margin-bottom:10px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"p1\"></a><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:22pt; font-weight:700;\">\u9b54</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:22pt; font-weight:700;\">\u517d\u4e16\u754c\u5927\u4f5c\u4e1a\u8f85\u52a9\u5de5\u5177\u4f7f\u7528\u6307\u5357</span></h1>\n"
"<p style=\" margin-top:3px; "
                        "margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u672c\u5de5\u5177\u8986\u76d6C++\u9b54\u517d\u4f5c\u4e1a\u5168\u6d41\u7a0b\uff1a\u7c7b\u8bbe\u8ba1\u3001\u5185\u5b58\u67e5\u770b\u3001\u6e38\u620f\u6a21\u62df\u3001\u6821\u9a8c\u3001\u65e5\u5fd7\u5bf9\u6bd4\u3002</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif';\"> </span></p>\n"
"<h2 style=\" margin-top:16px; margin-bottom:5px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"p2\"></a><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">1</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">. \u7c7b\u7f16\u8f91\u5668</span></h2>\n"
"<p style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-rig"
                        "ht:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u53ef\u89c6\u5316\u8bbe\u8ba1C++\u7c7b\u7ed3\u6784\uff0c\u5b9e\u65f6\u751f\u6210\u4ee3\u7801\u3002</span></p>\n"
"<ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\">\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u70b9\u51fb\u300c\u6dfb\u52a0\u7c7b\u300d\u65b0\u5efa\u7c7b </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u586b\u5199\u7c7b\u540d\u3001\u9009\u62e9\u57fa\u7c7b\u3001\u6dfb\u52a0\u6210\u5458\u53d8\u91cf </"
                        "li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u53f3\u4fa7\u5b9e\u65f6\u9884\u89c8\u751f\u6210\u7684C++\u4ee3\u7801 </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u5b8c\u6210\u540e\u70b9\u51fb\u300c\u5bfc\u51fa\u4ee3\u7801\u300d</li></ul>\n"
"<p style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u652f\u6301\u62d6\u62fd\u6392\u5e8f\u6210\u5458\u3001\u53f3\u952e\u5220\u7c7b\u3001\u81ea\u52a8\u8bc6\u522b\u5df2\u6709\u57fa\u7c7b\u3002</span><span styl"
                        "e=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif';\"> </span></p>\n"
"<h2 style=\" margin-top:16px; margin-bottom:5px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"p3\"></a><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">2</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">. \u5185\u5b58\u89c6\u56fe</span></h2>\n"
"<p style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u53ef\u89c6\u5316\u67e5\u770b\u7c7b\u5bf9\u8c61\u5185\u5b58\u5e03\u5c40\u3002</span></p>\n"
"<ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\">\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans"
                        "-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u4e0b\u62c9\u9009\u62e9\u5bf9\u5e94\u7c7b\uff0c\u67e5\u770b\u5185\u5b58\u6761\u5f62\u56fe </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u60ac\u505c\u67e5\u770b\u6210\u5458\u8be6\u7ec6\u4fe1\u606f </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u7ea2\u8272\uff1a\u865a\u8868\u6307\u9488\uff5c\u84dd\u8272\uff1a\u666e\u901a\u6210\u5458</li></ul>\n"
"<p style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; li"
                        "ne-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u53ef\u67e5\u770b\u5185\u5b58\u5927\u5c0f\u3001\u7406\u89e3\u5185\u5b58\u5bf9\u9f50\u3001\u9a8c\u8bc1\u7ee7\u627f\u5185\u5b58\u5e03\u5c40\u3002</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif';\"> </span></p>\n"
"<h2 style=\" margin-top:16px; margin-bottom:5px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"p4\"></a><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">3</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">. \u65f6\u95f4\u8f74</span></h2>\n"
"<p style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u56de"
                        "\u653e\u6574\u5c40\u6e38\u620f\u6240\u6709\u4e8b\u4ef6\u3002</span></p>\n"
"<ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\">\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u5148\u5728Task2\u8fd0\u884c\u6a21\u62df\u5bf9\u5c40 </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u8fdb\u5165\u65f6\u95f4\u8f74\u67e5\u770b\u5b8c\u6574\u4e8b\u4ef6\u5217\u8868 </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-he"
                        "ight:145%;\">\u64ad\u653e/\u6682\u505c\u3001\u6b65\u8fdb\u3001\u6ed1\u5757\u8df3\u8f6c\u65f6\u95f4</li></ul>\n"
"<p style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u67e5\u770b\u5175\u529b\u51fa\u751f\u3001\u4ea4\u6218\u3001\u57ce\u6c60\u653b\u5360\u8282\u70b9\u3002</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif';\"> </span></p>\n"
"<h2 style=\" margin-top:16px; margin-bottom:5px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"p5\"></a><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">4</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">. Task1\uff1a\u6b66\u58eb\u5c42\u7ea7\u6821\u9a8c</span></h2>\n"
"<p style=\" margin-to"
                        "p:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u81ea\u52a8\u6821\u9a8c\u7c7b\u7ee7\u627f\u7ed3\u6784\u5408\u89c4\u6027\u3002</span></p>\n"
"<ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\">\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u7f16\u8f91\u5668\u8bbe\u8ba1Warrior\u53ca\u5176\u5b50\u7c7b(Dragon/Ninja/Iceman) </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u8865\u9f50hp\u3001attack\u7b49\u5fc5\u9700\u6210"
                        "\u5458 </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u70b9\u51fb\u5f00\u59cb\u6821\u9a8c\uff0c\u6839\u636e\u62a5\u9519\u4fee\u6539\u4ee3\u7801</li></ul>\n"
"<p style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u6821\u9a8c\uff1a\u7ee7\u627f\u5173\u7cfb\u3001\u6210\u5458\u5b8c\u6574\u6027\u3001\u6784\u9020\u521d\u59cb\u5316\u5217\u8868\u3002</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif';\"> </span></p>\n"
"<h2 style=\" margin-top:16px; margin-bottom:5px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"p6\"></a><span style=\" font-family:'Microsoft YaHei UI','Micro"
                        "soft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">5</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">. Task2\uff1a\u6574\u5c40\u6a21\u62df\u5668</span></h2>\n"
"<p style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u5b8c\u6574\u6a21\u62df\u6807\u51c6\u5bf9\u5c40\uff0c\u5339\u914dOJ\u6d4b\u8bd5\u7528\u4f8b\u3002</span></p>\n"
"<ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\">\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u9009\u7528\u9898\u76ee\u6807\u51c6\u6a21\u5f0f </li>\n"
"<li style=\" font-family:'"
                        "Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u81ea\u5b9a\u4e49\u8840\u91cf\u3001\u51fa\u5175\u89c4\u5219\u7b49\u53c2\u6570 </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u542f\u52a8\u6a21\u62df\u67e5\u770b\u5bf9\u5c40\u7ed3\u679c</li></ul>\n"
"<p style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u67e5\u770b\u5bf9\u5c40\u80dc\u8d1f\u3001\u65f6\u5e8f\u53d8\u5316\u3001\u5175\u529b\u57ce\u6c60\u53d8\u52a8\u3002</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei'"
                        ",'sans-serif';\"> </span></p>\n"
"<h2 style=\" margin-top:16px; margin-bottom:5px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"p7\"></a><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">6</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">. Task3\uff1a\u65e5\u5fd7\u52a9\u624b</span></h2>\n"
"<p style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u6bd4\u5bf9\u8f93\u51fa\u4e0e\u6807\u51c6\u7b54\u6848\uff0c\u5feb\u901f\u6392\u67e5\u683c\u5f0fBUG\u3002</span></p>\n"
"<ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\">\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-siz"
                        "e:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u5bfc\u5165Task2\u6807\u51c6\u65e5\u5fd7 </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u7c98\u8d34\u81ea\u5df1\u7a0b\u5e8f\u8f93\u51fa\u8fdb\u884c\u6bd4\u5bf9</li></ul>\n"
"<p style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\"><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\">\u989c\u8272\u6807\u8bb0\uff1a\u7eff=\u6b63\u786e\uff5c\u7ea2=\u9519\u8bef\uff5c\u9ec4=\u65f6\u95f4\u504f\u5dee\uff0c\u7528\u4e8eOJ\u63d0\u4ea4\u9884\u68c0\u3002</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif';\"> </span></p>\n"
"<h2 "
                        "style=\" margin-top:16px; margin-bottom:5px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"p8\"></a><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">\u5feb</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">\u901f\u4e0a\u624b\u6d41\u7a0b</span></h2>\n"
"<ol style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\">\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u7c7b\u7f16\u8f91\u5668\u5b8c\u6210\u7c7b\u7ed3\u6784 </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-in"
                        "dent:0; text-indent:0px; line-height:145%;\">Task1\u6821\u9a8c\u7c7b\u8bbe\u8ba1 </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">Task2\u8fd0\u884c\u6574\u5c40\u6a21\u62df </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u65f6\u95f4\u8f74\u590d\u76d8\u5bf9\u5c40\u7ec6\u8282 </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">Task3\u65e5\u5fd7\u6bd4\u5bf9\u540e\u63d0\u4ea4 </li></ol>\n"
"<h2 style=\" margin-top:16px; margin-bottom:5px; margin-le"
                        "ft:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"p9\"></a><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">\u6838</span><span style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:16pt; font-weight:700;\">\u5fc3\u529f\u80fd</span></h2>\n"
"<ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\">\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u89e3\u6790\u9898\u76ee\u8bbe\u8ba1\u9700\u6c42 </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u6821\u9a8c\u7c7b\u7ed3\u6784"
                        "\u8bbe\u8ba1\u6b63\u8bef </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u9a8c\u8bc1\u7a0b\u5e8f\u8f93\u51fa\u7ed3\u679c </li>\n"
"<li style=\" font-family:'Microsoft YaHei UI','Microsoft YaHei','sans-serif'; font-size:13pt;\" style=\" margin-top:3px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:145%;\">\u5feb\u901f\u5b9a\u4f4d\u4ee3\u7801\u6f0f\u6d1e </li></ul></body></html>", None))
    # retranslateUi

