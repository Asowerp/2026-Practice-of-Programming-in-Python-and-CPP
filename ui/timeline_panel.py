from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class TimelinePanel(QWidget):
    def __init__(self, title: str = "事件时间轴", empty_hint: str = "尚未接收事件。") -> None:
        super().__init__()
        self.empty_hint = empty_hint
        self._build_ui(title)

    def _build_ui(self, title: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 800; color: #0F172A;")
        header.addWidget(title_label)
        header.addStretch(1)

        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(QIcon(":/icons/prev.svg"))
        self.btn_prev.setToolTip("上一条事件")
        self.btn_play = QPushButton()
        self.btn_play.setIcon(QIcon(":/icons/play.svg"))
        self.btn_play.setToolTip("播放 / 暂停")
        self.btn_next = QPushButton()
        self.btn_next.setIcon(QIcon(":/icons/next.svg"))
        self.btn_next.setToolTip("下一条事件")
        for button in [self.btn_prev, self.btn_play, self.btn_next]:
            button.setFixedWidth(36)
            header.addWidget(button)
        layout.addLayout(header)

        self.lbl_timeline = QLabel(self.empty_hint)
        self.lbl_timeline.setWordWrap(True)
        self.lbl_timeline.setStyleSheet(
            "background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; "
            "padding: 8px 10px; color: #334155; font-weight: 700;"
        )
        layout.addWidget(self.lbl_timeline)

        self.horizontalSlider = QSlider(Qt.Orientation.Horizontal)
        self.horizontalSlider.setToolTip("拖动跳转到指定事件")
        layout.addWidget(self.horizontalSlider)

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        self.listWidget = QListWidget()
        self.listWidget.setAlternatingRowColors(True)
        self.listWidget.setToolTip("点击事件可同步定位页面上下文。")
        frame_layout.addWidget(self.listWidget)
        layout.addWidget(frame, 1)
