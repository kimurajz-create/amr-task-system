from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


DASHBOARD_AUTO_REFRESH_MS = 15_000

SUMMARY_CARD_SPECS = [
    ("pending_count", "待執行", "目前排隊等待派送"),
    ("executing_count", "執行中", "MiR 正在執行中的任務"),
    ("completed_count", "已完成", "累積完成的任務筆數"),
    ("aborted_count", "已中止", "累積中止的任務筆數"),
    ("total_count", "總任務", "目前資料表內的總任務數"),
]

SECTION_SPECS = [
    (
        "task-volume",
        "任務量概況",
        "P3 會把 mission volume 與任務量統計接到這裡。",
    ),
    (
        "start-hotspots",
        "起點熱區",
        "P3 會把 start_point Top N 統計接到這裡。",
    ),
    (
        "target-hotspots",
        "目的地熱區",
        "P3 會把 target_point Top N 統計接到這裡。",
    ),
    (
        "route-hotspots",
        "熱門路線",
        "P3 會把 route hotspots 與 Top N 接到這裡。",
    ),
]


def build_performance_dashboard_snapshot(task_status_summary=None, warning_message=None):
    summary = task_status_summary or {}

    summary_cards = [
        {
            "key": key,
            "title": title,
            "value": str(summary.get(key, 0)),
            "caption": caption,
        }
        for key, title, caption in SUMMARY_CARD_SPECS
    ]
    sections = [
        {
            "key": key,
            "title": title,
            "body": body,
        }
        for key, title, body in SECTION_SPECS
    ]

    if warning_message:
        status_level = "warning"
        status_text = warning_message
    elif task_status_summary is None:
        status_level = "info"
        status_text = "P04 / P2 視窗骨架已就緒，等待主程式接入摘要資料來源。"
    else:
        status_level = "ready"
        status_text = "目前已接入任務狀態摘要；任務量與熱區明細將在 P3 續接。"

    return {
        "status_level": status_level,
        "status_text": status_text,
        "summary_cards": summary_cards,
        "sections": sections,
    }


class PerformanceDashboardWindow(QWidget):
    def __init__(
        self,
        snapshot_provider=None,
        refresh_interval_ms=DASHBOARD_AUTO_REFRESH_MS,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowFlag(Qt.Window, True)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        self.snapshot_provider = snapshot_provider or build_performance_dashboard_snapshot
        self.refresh_interval_ms = refresh_interval_ms
        self.summary_value_labels = {}
        self.section_body_labels = {}

        self.setObjectName("PerformanceDashboardWindow")
        self.setWindowTitle("MiR 績效看板")
        self.resize(980, 720)
        self.setMinimumSize(860, 620)

        self._build_ui()
        self._apply_styles()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_dashboard)
        self.refresh_timer.start(self.refresh_interval_ms)

        self.refresh_dashboard()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(18)

        title_label = QLabel("MiR 績效看板")
        title_label.setObjectName("dashboardTitleLabel")

        subtitle_label = QLabel(
            "P04 / P2 先完成入口、單例視窗與刷新骨架，詳細統計在後續 phase 續接。"
        )
        subtitle_label.setObjectName("dashboardSubtitleLabel")
        subtitle_label.setWordWrap(True)

        header_actions_layout = QHBoxLayout()
        header_actions_layout.setSpacing(12)

        self.last_refresh_label = QLabel("最後刷新：尚未更新")
        self.last_refresh_label.setObjectName("dashboardMetaLabel")

        self.refresh_button = QPushButton("立即刷新")
        self.refresh_button.setObjectName("dashboardRefreshButton")
        self.refresh_button.clicked.connect(self.refresh_dashboard)

        header_actions_layout.addWidget(self.last_refresh_label)
        header_actions_layout.addStretch()
        header_actions_layout.addWidget(self.refresh_button)

        self.status_banner = QLabel("")
        self.status_banner.setObjectName("dashboardStatusBanner")
        self.status_banner.setWordWrap(True)

        summary_frame = QFrame()
        summary_frame.setObjectName("dashboardPanel")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(18, 18, 18, 18)
        summary_layout.setSpacing(14)

        summary_title = QLabel("任務狀態摘要")
        summary_title.setObjectName("dashboardSectionTitle")
        summary_layout.addWidget(summary_title)

        summary_cards_layout = QGridLayout()
        summary_cards_layout.setHorizontalSpacing(12)
        summary_cards_layout.setVerticalSpacing(12)
        for index, (key, title, caption) in enumerate(SUMMARY_CARD_SPECS):
            summary_cards_layout.addWidget(
                self._build_summary_card(key, title, caption),
                index // 3,
                index % 3,
            )
        summary_layout.addLayout(summary_cards_layout)

        placeholder_frame = QFrame()
        placeholder_frame.setObjectName("dashboardPanel")
        placeholder_layout = QVBoxLayout(placeholder_frame)
        placeholder_layout.setContentsMargins(18, 18, 18, 18)
        placeholder_layout.setSpacing(14)

        placeholder_title = QLabel("後續統計區塊")
        placeholder_title.setObjectName("dashboardSectionTitle")
        placeholder_layout.addWidget(placeholder_title)

        for key, title, body in SECTION_SPECS:
            placeholder_layout.addWidget(self._build_section_card(key, title, body))

        root_layout.addWidget(title_label)
        root_layout.addWidget(subtitle_label)
        root_layout.addLayout(header_actions_layout)
        root_layout.addWidget(self.status_banner)
        root_layout.addWidget(summary_frame)
        root_layout.addWidget(placeholder_frame)
        root_layout.addStretch()

    def _build_summary_card(self, key, title, caption):
        frame = QFrame()
        frame.setObjectName("dashboardSummaryCard")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("dashboardCardTitle")

        value_label = QLabel("0")
        value_label.setObjectName("dashboardCardValue")

        caption_label = QLabel(caption)
        caption_label.setObjectName("dashboardCardCaption")
        caption_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(caption_label)

        self.summary_value_labels[key] = value_label
        return frame

    def _build_section_card(self, key, title, body):
        frame = QFrame()
        frame.setObjectName("dashboardPlaceholderCard")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("dashboardPlaceholderTitle")

        body_label = QLabel(body)
        body_label.setObjectName("dashboardPlaceholderBody")
        body_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(body_label)

        self.section_body_labels[key] = body_label
        return frame

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QWidget#PerformanceDashboardWindow {
                background-color: #131a22;
                color: #f4f7fb;
            }
            QLabel#dashboardTitleLabel {
                font-size: 26px;
                font-weight: 700;
                color: #f8fbff;
            }
            QLabel#dashboardSubtitleLabel, QLabel#dashboardMetaLabel {
                color: #9fb0c3;
                font-size: 13px;
            }
            QLabel#dashboardStatusBanner {
                border-radius: 10px;
                padding: 12px 14px;
                font-size: 13px;
                background-color: #1f3146;
                color: #dbe8f8;
            }
            QFrame#dashboardPanel {
                background-color: #19222d;
                border: 1px solid #243445;
                border-radius: 16px;
            }
            QLabel#dashboardSectionTitle {
                font-size: 17px;
                font-weight: 700;
                color: #f4f7fb;
            }
            QFrame#dashboardSummaryCard, QFrame#dashboardPlaceholderCard {
                background-color: #10171f;
                border: 1px solid #233243;
                border-radius: 12px;
            }
            QLabel#dashboardCardTitle, QLabel#dashboardPlaceholderTitle {
                font-size: 14px;
                font-weight: 600;
                color: #d7e2ef;
            }
            QLabel#dashboardCardValue {
                font-size: 28px;
                font-weight: 700;
                color: #f8fbff;
            }
            QLabel#dashboardCardCaption, QLabel#dashboardPlaceholderBody {
                font-size: 12px;
                color: #92a6bc;
            }
            QPushButton#dashboardRefreshButton {
                background-color: #2f81f7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#dashboardRefreshButton:hover {
                background-color: #4691fa;
            }
            """
        )

    def set_snapshot_provider(self, snapshot_provider):
        self.snapshot_provider = snapshot_provider or build_performance_dashboard_snapshot

    def refresh_dashboard(self):
        try:
            snapshot = self.snapshot_provider() or build_performance_dashboard_snapshot()
        except Exception as exc:
            snapshot = build_performance_dashboard_snapshot(
                warning_message=f"統計資料暫時無法更新：{exc}"
            )

        self.apply_snapshot(snapshot)
        refreshed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_refresh_label.setText(
            f"最後刷新：{refreshed_at}  |  自動刷新：{self.refresh_interval_ms // 1000} 秒"
        )

    def apply_snapshot(self, snapshot):
        status_level = snapshot.get("status_level", "info")
        status_text = snapshot.get("status_text", "")
        self.status_banner.setText(status_text)

        palette = {
            "ready": ("#173326", "#b6f0cd"),
            "warning": ("#3a2a14", "#ffd89a"),
            "error": ("#431d1d", "#ffb0b0"),
            "info": ("#1f3146", "#dbe8f8"),
        }
        background, foreground = palette.get(status_level, palette["info"])
        self.status_banner.setStyleSheet(
            "border-radius: 10px; padding: 12px 14px; "
            f"background-color: {background}; color: {foreground};"
        )

        for card in snapshot.get("summary_cards", []):
            value_label = self.summary_value_labels.get(card.get("key"))
            if value_label is not None:
                value_label.setText(str(card.get("value", "0")))

        for section in snapshot.get("sections", []):
            body_label = self.section_body_labels.get(section.get("key"))
            if body_label is not None:
                body_label.setText(section.get("body", ""))

    def closeEvent(self, event: QCloseEvent):
        self.hide()
        event.ignore()


class PerformanceDashboardController:
    def __init__(self, window_factory=None):
        self.window_factory = window_factory or PerformanceDashboardWindow
        self.window = None

    def open(self, snapshot_provider=None, parent=None):
        if self.window is None:
            self.window = self.window_factory(
                snapshot_provider=snapshot_provider,
                parent=parent,
            )
        else:
            self.window.set_snapshot_provider(snapshot_provider)

        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        self.window.refresh_dashboard()
        return self.window
