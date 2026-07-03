from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QIcon


class TimelineController(QObject):
    eventSelected = Signal(int, object)

    def __init__(self, ui) -> None:
        super().__init__()
        self.ui = ui
        self.timeline_events: list[object] = []
        self.current_index = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_step)

        self.setup_ui()
        self.connect_signals()

    def load_simulation_bundle(self, bundle) -> None:
        self.set_events(list(bundle.events))

    def set_events(self, events: list[object]) -> None:
        self.timeline_events = events
        self.current_index = 0
        if events:
            self.ui.horizontalSlider.setMinimum(0)
            self.ui.horizontalSlider.setMaximum(len(events) - 1)
            self.ui.horizontalSlider.setValue(0)
        else:
            self.ui.horizontalSlider.setMinimum(0)
            self.ui.horizontalSlider.setMaximum(0)
        self.refresh_event_list()

    def setup_ui(self) -> None:
        self.play_icon = QIcon(":/icons/play.svg")
        self.pause_icon = QIcon(":/icons/pause.svg")
        self.replay_icon = QIcon(":/icons/replay.svg")

        if self.timeline_events:
            self.ui.horizontalSlider.setMinimum(0)
            self.ui.horizontalSlider.setMaximum(len(self.timeline_events) - 1)
            self.ui.horizontalSlider.setValue(0)
            self.refresh_event_list()
        else:
            self.ui.horizontalSlider.setMinimum(0)
            self.ui.horizontalSlider.setMaximum(0)
            self.ui.listWidget.clear()

    def connect_signals(self) -> None:
        self.ui.btn_prev.clicked.connect(self.prev_step)
        self.ui.btn_play.clicked.connect(self.toggle_play)
        self.ui.btn_next.clicked.connect(self.next_step)
        self.ui.horizontalSlider.valueChanged.connect(self.sync_log)
        self.ui.listWidget.currentRowChanged.connect(self._handle_list_selection)

    def refresh_event_list(self) -> None:
        self.ui.listWidget.clear()
        if self.timeline_events:
            for event in self.timeline_events:
                self.ui.listWidget.addItem(self._format_event_item(event))
            self.sync_log(0)
        else:
            self.ui.horizontalSlider.setMaximum(0)
            self.ui.lbl_timeline.setText("尚未从 Task2 接收事件。请先在 Task2 执行模拟并导出事件。")
            self.update_play_button_icon()

    def prev_step(self) -> None:
        if self.current_index > 0:
            self.ui.horizontalSlider.setValue(self.current_index - 1)

    def next_step(self) -> None:
        if self.current_index < len(self.timeline_events) - 1:
            self.ui.horizontalSlider.setValue(self.current_index + 1)

    def toggle_play(self) -> None:
        if self.timer.isActive():
            self.timer.stop()
        else:
            if self.current_index >= len(self.timeline_events) - 1:
                self.ui.horizontalSlider.setValue(0)
            self.timer.start(1000)
        self.update_play_button_icon()

    def auto_step(self) -> None:
        if self.current_index < len(self.timeline_events) - 1:
            self.ui.horizontalSlider.setValue(self.current_index + 1)
        else:
            self.timer.stop()
        self.update_play_button_icon()

    def update_play_button_icon(self) -> None:
        if self.timer.isActive():
            self.ui.btn_play.setIcon(self.pause_icon)
        elif self.current_index >= len(self.timeline_events) - 1:
            self.ui.btn_play.setIcon(self.replay_icon)
        else:
            self.ui.btn_play.setIcon(self.play_icon)

    def sync_log(self, index: int) -> None:
        if not self.timeline_events:
            self.current_index = 0
            self.update_play_button_icon()
            return
        index = max(0, min(index, len(self.timeline_events) - 1))
        self.current_index = index
        if self.ui.listWidget.currentRow() != index:
            self.ui.listWidget.blockSignals(True)
            self.ui.listWidget.setCurrentRow(index)
            self.ui.listWidget.blockSignals(False)
        event = self.timeline_events[index]
        self.ui.lbl_timeline.setText(self._format_event_detail(index, event))
        self.update_play_button_icon()
        self.eventSelected.emit(index, event)

    def _handle_list_selection(self, row: int) -> None:
        if row < 0 or row >= len(self.timeline_events):
            return
        if row != self.current_index:
            self.ui.horizontalSlider.setValue(row)
            return
        self.sync_log(row)

    @staticmethod
    def _format_event_item(event: object) -> str:
        event_time = getattr(event, "display_time", "--:--")
        stage_key = getattr(event, "stage_key", "")
        description = getattr(event, "description", str(event))
        stage_part = f" · {stage_key}" if stage_key else ""
        return f"[{event_time}{stage_part}] {description}"

    @staticmethod
    def _format_event_detail(index: int, event: object) -> str:
        event_time = getattr(event, "display_time", "--:--")
        stage_key = getattr(event, "stage_key", "unknown")
        description = getattr(event, "description", str(event))
        location_order = getattr(event, "location_order", "")
        location_text = f"｜位置序 {location_order}" if location_order != "" else ""
        return f"事件 {index + 1}｜时间 {event_time}｜阶段 {stage_key}{location_text}\n{description}"
