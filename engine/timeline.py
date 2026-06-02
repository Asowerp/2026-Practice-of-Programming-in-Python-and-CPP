from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon


class TimelineController:
    def __init__(self, ui):
        self.ui = ui
        self.timeline_events = []
        self.current_index = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_step)

        self.setup_ui()
        self.connect_signals()

    def load_simulation_bundle(self, bundle):
        events = []
        for event in bundle.events:
            events.append((event.display_time, event.description))
        self.set_events(events)

    def set_events(self, events):
        self.timeline_events = events
        if len(events) > 0:
            self.ui.horizontalSlider.setMinimum(0)
            self.ui.horizontalSlider.setMaximum(len(events) - 1)
            self.ui.horizontalSlider.setValue(0)
        else:
            self.ui.horizontalSlider.setMinimum(0)
            self.ui.horizontalSlider.setMaximum(0)
        self.refresh_event_list()

    def setup_ui(self):
        self.play_icon = QIcon(":/icons/play.svg")
        self.pause_icon = QIcon(":/icons/pause.svg")
        self.replay_icon = QIcon(":/icons/replay.svg")

        if len(self.timeline_events) > 0:
            self.ui.horizontalSlider.setMinimum(0)
            self.ui.horizontalSlider.setMaximum(len(self.timeline_events) - 1)
            self.ui.horizontalSlider.setValue(0)
            self.refresh_event_list()
        else:
            self.ui.horizontalSlider.setMinimum(0)
            self.ui.horizontalSlider.setMaximum(0)
            self.ui.listWidget.clear()

    def connect_signals(self):
        self.ui.btn_prev.clicked.connect(self.prev_step)
        self.ui.btn_play.clicked.connect(self.toggle_play)
        self.ui.btn_next.clicked.connect(self.next_step)
        self.ui.horizontalSlider.valueChanged.connect(self.sync_log)

    def refresh_event_list(self):
        self.ui.listWidget.clear()
        if len(self.timeline_events) > 0:
            for event in self.timeline_events:
                self.ui.listWidget.addItem(f"[{event[0]}] {event[1]}")
            self.sync_log(0)
        else:
            self.ui.horizontalSlider.setMaximum(0)

    def prev_step(self):
        if self.current_index > 0:
            self.ui.horizontalSlider.setValue(self.current_index - 1)

    def next_step(self):
        if self.current_index < len(self.timeline_events) - 1:
            self.ui.horizontalSlider.setValue(self.current_index + 1)

    def toggle_play(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            if self.current_index >= len(self.timeline_events) - 1:
                self.ui.horizontalSlider.setValue(0)
            self.timer.start(1000)
        self.update_play_button_icon()

    def auto_step(self):
        if self.current_index < len(self.timeline_events) - 1:
            self.ui.horizontalSlider.setValue(self.current_index + 1)
        else:
            self.timer.stop()
        self.update_play_button_icon()

    def update_play_button_icon(self):
        if self.timer.isActive():
            self.ui.btn_play.setIcon(self.pause_icon)
        elif self.current_index >= len(self.timeline_events) - 1:
            self.ui.btn_play.setIcon(self.replay_icon)
        else:
            self.ui.btn_play.setIcon(self.play_icon)

    def sync_log(self, index):
        self.current_index = index
        self.ui.listWidget.setCurrentRow(index)
        self.update_play_button_icon()
