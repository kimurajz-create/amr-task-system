from datetime import datetime
from html import escape
import inspect
from xml.sax.saxutils import escape as xml_escape
from zipfile import ZipFile, ZIP_DEFLATED

from PySide6.QtCore import QDateTime, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import (
    QCloseEvent,
    QColor,
    QFont,
    QImage,
    QPageSize,
    QPainter,
    QTextDocument,
)
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QCheckBox,
    QDateTimeEdit,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


DASHBOARD_AUTO_REFRESH_MS = 15_000

SUMMARY_CARD_SPECS = [
    ("pending_count", "待執行", "等待派送到 MiR 的任務數量。"),
    ("executing_count", "執行中", "目前由 MiR 執行中的任務數量。"),
    ("completed_count", "已完成", "已正常完成的任務數量。"),
    ("aborted_count", "已中止", "提早結束或被停止的任務數量。"),
    ("total_count", "總任務", "資料庫目前累積的任務總數。"),
]

SECTION_SPECS = [
    {
        "key": "task-volume",
        "title": "任務類型分組",
        "row_label_key": "mission_content",
        "empty_text": "目前還沒有任務類型統計資料。",
    },
    {
        "key": "start-hotspots",
        "title": "起點 Top N",
        "row_label_key": "start_point",
        "empty_text": "目前還沒有起點熱區資料。",
    },
    {
        "key": "target-hotspots",
        "title": "目的地 Top N",
        "row_label_key": "target_point",
        "empty_text": "目前還沒有目的地熱區資料。",
    },
    {
        "key": "route-hotspots",
        "title": "熱門路線 Top N",
        "row_label_key": "route_label",
        "empty_text": "目前還沒有熱門路線資料。",
    },
]


def _normalize_section_label(value):
    if value is None:
        return "(未填寫)"

    text = str(value).strip()
    return text if text else "(未填寫)"


def _normalize_section_rows(items, label_key):
    rows = []
    for item in items or []:
        rows.append(
            {
                "label": _normalize_section_label(item.get(label_key)),
                "value": str(item.get("task_count", 0)),
            }
        )
    return rows


def _format_section_body(rows, empty_text):
    if not rows:
        return empty_text
    return "\n".join(f"{row['label']}: {row['value']}" for row in rows)


def build_performance_dashboard_snapshot(
    task_status_summary=None,
    task_volume_by_mission=None,
    start_hotspots=None,
    target_hotspots=None,
    route_hotspots=None,
    warning_message=None,
):
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

    section_data = {
        "task-volume": task_volume_by_mission,
        "start-hotspots": start_hotspots,
        "target-hotspots": target_hotspots,
        "route-hotspots": route_hotspots,
    }
    sections = []
    for spec in SECTION_SPECS:
        rows = _normalize_section_rows(
            section_data.get(spec["key"]),
            spec["row_label_key"],
        )
        sections.append(
            {
                "key": spec["key"],
                "title": spec["title"],
                "rows": rows,
                "body": _format_section_body(rows, spec["empty_text"]),
            }
        )

    if warning_message:
        status_level = "warning"
        status_text = warning_message
    elif task_status_summary is None:
        status_level = "info"
        status_text = "績效 dashboard 已就緒，開啟或刷新後會載入任務統計與熱門路線資料。"
    else:
        status_level = "ready"
        status_text = "任務量與熱區統計已刷新完成。"

    return {
        "status_level": status_level,
        "status_text": status_text,
        "summary_cards": summary_cards,
        "sections": sections,
    }


def build_performance_dashboard_snapshot_from_db(
    task_db_manager,
    hotspot_limit=10,
):
    if task_db_manager is None:
        return build_performance_dashboard_snapshot(
            warning_message="目前無法取得 TaskDBManager，尚未載入統計資料。"
        )

    summary = task_db_manager.get_task_status_summary()
    task_volume_by_mission = task_db_manager.get_task_volume_by_mission()
    start_hotspots = task_db_manager.get_task_start_hotspots(limit=hotspot_limit)
    target_hotspots = task_db_manager.get_task_target_hotspots(limit=hotspot_limit)
    route_hotspots = task_db_manager.get_task_route_hotspots(limit=hotspot_limit)

    return build_performance_dashboard_snapshot(
        task_status_summary=summary,
        task_volume_by_mission=task_volume_by_mission,
        start_hotspots=start_hotspots,
        target_hotspots=target_hotspots,
        route_hotspots=route_hotspots,
    )


class PerformanceDashboardWindow(QWidget):
    def __init__(
        self,
        snapshot_provider=None,
        refresh_interval_ms=DASHBOARD_AUTO_REFRESH_MS,
        parent=None,
    ):
        # Keep the dashboard as a true top-level window. Parenting it to the
        # frameless main window can make the native title bar hit area drift
        # outside the visible region on Windows after maximize/restore.
        super().__init__(None)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinMaxButtonsHint
            | Qt.WindowCloseButtonHint
        )
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        self.snapshot_provider = snapshot_provider or build_performance_dashboard_snapshot
        self.refresh_interval_ms = refresh_interval_ms
        self.summary_value_labels = {}
        self.section_body_labels = {}

        self.setObjectName("PerformanceDashboardWindow")
        self.setWindowTitle("MiR 績效儀表板")
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

        title_label = QLabel("MiR 績效儀表板")
        title_label.setObjectName("dashboardTitleLabel")

        subtitle_label = QLabel(
            "P04 / P3 任務統計視圖，集中顯示摘要數量、任務類型分組與熱門路線。"
        )
        subtitle_label.setObjectName("dashboardSubtitleLabel")
        subtitle_label.setWordWrap(True)

        header_actions_layout = QHBoxLayout()
        header_actions_layout.setSpacing(12)

        self.last_refresh_label = QLabel("最後刷新：尚未載入")
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

        summary_title = QLabel("任務摘要")
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

        sections_frame = QFrame()
        sections_frame.setObjectName("dashboardPanel")
        sections_layout = QVBoxLayout(sections_frame)
        sections_layout.setContentsMargins(18, 18, 18, 18)
        sections_layout.setSpacing(14)

        sections_title = QLabel("任務量與熱區統計")
        sections_title.setObjectName("dashboardSectionTitle")
        sections_layout.addWidget(sections_title)

        section_cards_layout = QGridLayout()
        section_cards_layout.setHorizontalSpacing(12)
        section_cards_layout.setVerticalSpacing(12)
        for index, spec in enumerate(SECTION_SPECS):
            section_cards_layout.addWidget(
                self._build_section_card(
                    spec["key"],
                    spec["title"],
                    spec["empty_text"],
                ),
                index // 2,
                index % 2,
            )
        sections_layout.addLayout(section_cards_layout)

        root_layout.addWidget(title_label)
        root_layout.addWidget(subtitle_label)
        root_layout.addLayout(header_actions_layout)
        root_layout.addWidget(self.status_banner)
        root_layout.addWidget(summary_frame)
        root_layout.addWidget(sections_frame)
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
        frame.setObjectName("dashboardSectionCard")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("dashboardSectionCardTitle")

        body_label = QLabel(body)
        body_label.setObjectName("dashboardSectionBody")
        body_label.setWordWrap(True)
        body_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        layout.addWidget(title_label)
        layout.addWidget(body_label)
        layout.addStretch()

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
            QFrame#dashboardSummaryCard, QFrame#dashboardSectionCard {
                background-color: #10171f;
                border: 1px solid #233243;
                border-radius: 12px;
            }
            QLabel#dashboardCardTitle, QLabel#dashboardSectionCardTitle {
                font-size: 14px;
                font-weight: 600;
                color: #d7e2ef;
            }
            QLabel#dashboardCardValue {
                font-size: 28px;
                font-weight: 700;
                color: #f8fbff;
            }
            QLabel#dashboardCardCaption, QLabel#dashboardSectionBody {
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
                warning_message=f"統計資料刷新失敗：{exc}"
            )

        self.apply_snapshot(snapshot)
        refreshed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_refresh_label.setText(
            f"最後刷新：{refreshed_at}  |  自動刷新："
            f"{self.refresh_interval_ms // 1000} 秒"
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

        section_specs_by_key = {spec["key"]: spec for spec in SECTION_SPECS}
        for section in snapshot.get("sections", []):
            body_label = self.section_body_labels.get(section.get("key"))
            if body_label is None:
                continue

            body_text = section.get("body")
            if body_text is None:
                spec = section_specs_by_key.get(section.get("key"), {})
                body_text = _format_section_body(
                    section.get("rows", []),
                    spec.get("empty_text", "目前沒有資料。"),
                )
            body_label.setText(body_text)

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


# Clean override block for the dashboard UI. The original file contains
# legacy strings that are hard to maintain, so we redefine the public API
# below with chart-based section cards while keeping the same module surface.
from PySide6.QtWidgets import QProgressBar, QScrollArea


DASHBOARD_AUTO_REFRESH_MS = 15_000

SUMMARY_CARD_SPECS = [
    ("pending_count", "待執行", "等待派送到 MiR 的任務數量。"),
    ("executing_count", "執行中", "目前由 MiR 執行中的任務數量。"),
    ("completed_count", "已完成", "已正常完成的任務數量。"),
    ("aborted_count", "已中止", "提早結束或被停止的任務數量。"),
    ("total_count", "總任務", "資料庫目前累積的任務總數。"),
]

SECTION_SPECS = [
    {
        "key": "task-volume",
        "title": "任務類型分組",
        "row_label_key": "mission_content",
        "empty_text": "目前沒有任務類型統計資料。",
        "accent": "#4f8cff",
        "summary_prefix": "最高任務類型",
    },
    {
        "key": "start-hotspots",
        "title": "起點 Top N",
        "row_label_key": "start_point",
        "empty_text": "目前沒有起點熱區統計資料。",
        "accent": "#2ec27e",
        "summary_prefix": "最熱門起點",
    },
    {
        "key": "target-hotspots",
        "title": "目的地 Top N",
        "row_label_key": "target_point",
        "empty_text": "目前沒有目的地熱區統計資料。",
        "accent": "#f6c445",
        "summary_prefix": "最熱門目的地",
    },
    {
        "key": "route-hotspots",
        "title": "熱門路線 Top N",
        "row_label_key": "route_label",
        "empty_text": "目前沒有熱門路線統計資料。",
        "accent": "#ff7a59",
        "summary_prefix": "最熱門路線",
    },
]


def _normalize_section_label(value):
    if value is None:
        return "(未命名)"

    text = str(value).strip()
    return text if text else "(未命名)"


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _normalize_section_rows(items, label_key):
    rows = []
    for item in items or []:
        rows.append(
            {
                "label": _normalize_section_label(item.get(label_key)),
                "value": str(item.get("task_count", 0)),
            }
        )
    return rows


def _format_section_body(rows, empty_text):
    if not rows:
        return empty_text
    return "\n".join(f"{row['label']}: {row['value']}" for row in rows)


def _build_section_summary(rows, empty_text, prefix):
    if not rows:
        return empty_text

    top_row = rows[0]
    return f"{prefix}：{top_row['label']} ({top_row['value']})"


def build_performance_dashboard_snapshot(
    task_status_summary=None,
    task_volume_by_mission=None,
    start_hotspots=None,
    target_hotspots=None,
    route_hotspots=None,
    warning_message=None,
    start_point_pie=None,
):
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

    section_data = {
        "task-volume": task_volume_by_mission,
        "start-hotspots": start_hotspots,
        "target-hotspots": target_hotspots,
        "route-hotspots": route_hotspots,
    }
    sections = []
    for spec in SECTION_SPECS:
        rows = _normalize_section_rows(
            section_data.get(spec["key"]),
            spec["row_label_key"],
        )
        sections.append(
            {
                "key": spec["key"],
                "title": spec["title"],
                "rows": rows,
                "body": _format_section_body(rows, spec["empty_text"]),
                "summary": _build_section_summary(
                    rows,
                    spec["empty_text"],
                    spec["summary_prefix"],
                ),
            }
        )

    if warning_message:
        status_level = "warning"
        status_text = warning_message
    elif task_status_summary is None:
        status_level = "info"
        status_text = "績效 dashboard 已開啟，等待載入任務量與熱區統計。"
    else:
        status_level = "ready"
        status_text = "任務量與熱區統計已刷新完成。"

    if start_point_pie is None:
        pie_rows = _normalize_section_rows(start_hotspots, "start_point")
    elif start_point_pie and "label" not in start_point_pie[0]:
        pie_rows = _normalize_section_rows(start_point_pie, "start_point")
    else:
        pie_rows = list(start_point_pie)
    pie_rows = _filter_operating_room_pie_rows(pie_rows)

    return {
        "status_level": status_level,
        "status_text": status_text,
        "summary_cards": summary_cards,
        "sections": sections,
        "start_point_pie": pie_rows,
    }


def _range_kwargs(start_at=None, end_at=None):
    kwargs = {}
    if start_at is not None:
        kwargs["start_at"] = start_at
    if end_at is not None:
        kwargs["end_at"] = end_at
    return kwargs


def build_performance_dashboard_snapshot_from_db(
    task_db_manager,
    hotspot_limit=10,
    start_at=None,
    end_at=None,
):
    if task_db_manager is None:
        return build_performance_dashboard_snapshot(
            warning_message="尚未提供 TaskDBManager，無法讀取任務統計資料。"
        )

    range_kwargs = _range_kwargs(start_at, end_at)
    summary = task_db_manager.get_task_status_summary(**range_kwargs)
    task_volume_by_mission = task_db_manager.get_task_volume_by_mission(**range_kwargs)
    start_hotspots = task_db_manager.get_task_start_hotspots(
        limit=hotspot_limit, **range_kwargs
    )
    start_point_pie = task_db_manager.get_task_start_hotspots(
        limit=100, **range_kwargs
    )
    target_hotspots = task_db_manager.get_task_target_hotspots(
        limit=hotspot_limit, **range_kwargs
    )
    route_hotspots = task_db_manager.get_task_route_hotspots(
        limit=hotspot_limit, **range_kwargs
    )

    return build_performance_dashboard_snapshot(
        task_status_summary=summary,
        task_volume_by_mission=task_volume_by_mission,
        start_hotspots=start_hotspots,
        target_hotspots=target_hotspots,
        route_hotspots=route_hotspots,
        start_point_pie=start_point_pie,
    )


def render_performance_report_html(snapshot, range_label):
    """把目前儀表板快照轉成可列印的 HTML，供 PDF 匯出使用。"""
    snapshot = snapshot or {}
    card_rows = "".join(
        "<tr><td>{title}</td><td>{value}</td></tr>".format(
            title=escape(str(card.get("title", ""))),
            value=escape(str(card.get("value", "0"))),
        )
        for card in snapshot.get("summary_cards", [])
    )
    section_html = []
    for section in snapshot.get("sections", []):
        rows = section.get("rows") or []
        if rows:
            body = "".join(
                "<tr><td>{label}</td><td>{value}</td></tr>".format(
                    label=escape(str(row.get("label", ""))),
                    value=escape(str(row.get("value", ""))),
                )
                for row in rows
            )
        else:
            body = "<tr><td colspan='2'>無資料</td></tr>"
        section_html.append(
            "<div class='section'>{title}</div>"
            "<table>{body}</table>".format(
                title=escape(str(section.get("title", ""))),
                body=body,
            )
        )

    return """
    <html>
      <head>
        <style>
          body {{
            font-family: 'Microsoft JhengHei';
            font-size: 12pt;
            color: #111111;
          }}
          .title {{
            font-size: 16pt;
            font-weight: 700;
            margin: 0 0 8pt 0;
          }}
          .meta {{
            font-size: 12pt;
            margin: 0 0 4pt 0;
          }}
          .section {{
            font-size: 13pt;
            font-weight: 700;
            margin: 14pt 0 6pt 0;
          }}
          table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0 0 8pt 0;
          }}
          td {{
            font-family: 'Microsoft JhengHei';
            font-size: 12pt;
            padding: 6pt 8pt;
            border: 1px solid #666666;
          }}
        </style>
      </head>
      <body>
        <div class="title">MiR 績效儀表板</div>
        <div class="meta">監控區間：{range_label}</div>
        <div class="meta">{status_text}</div>
        <div class="section">任務摘要</div>
        <table>{cards}</table>
        {pie_section}
        {sections}
      </body>
    </html>
    """.format(
        range_label=escape(str(range_label or "全部累積資料")),
        status_text=escape(str(snapshot.get("status_text", ""))),
        cards=card_rows,
        sections="".join(section_html),
        pie_section=_render_start_point_pie_html(snapshot.get("start_point_pie")),
    )


PIE_COLORS = (
    "#4f8cff",
    "#2ec27e",
    "#f6c445",
    "#ff7a59",
    "#b07cff",
    "#3dcdc6",
    "#ff5d8f",
    "#8fd14f",
    "#ffb020",
    "#6c8cff",
    "#d96c6c",
    "#7aa2ff",
)


def _pie_slices(rows):
    slices = []
    for row in rows or []:
        try:
            value = int(row.get("value", 0))
        except (TypeError, ValueError):
            value = 0
        label = str(row.get("label") or "(未命名)")
        if value > 0:
            slices.append((label, value))
    slices.sort(key=lambda item: (-item[1], item[0]))
    return slices


def _most_used_start_text(slices):
    if not slices:
        return "目前沒有起始點資料。"
    total = sum(value for _label, value in slices)
    label, value = slices[0]
    percent = (value / total * 100) if total else 0
    return f"最常使用：{label}（{value} 次，{percent:.1f}%）"


PIE_LEGEND_LINE_HEIGHT = 28
PIE_ON_DARK_TEXT = "#f4f7fb"
PIE_ON_LIGHT_TEXT = "#1b2836"
# 外環起點，不是手術室，不放入起始點圓餅圖。
EXCLUDED_PIE_START_LABELS = ("封閉式架子放置處",)


def _filter_operating_room_pie_rows(rows):
    filtered = []
    for row in rows or []:
        label = str(row.get("label") or "").strip()
        if any(token in label for token in EXCLUDED_PIE_START_LABELS):
            continue
        filtered.append(row)
    return filtered


def paint_start_point_pie(
    painter,
    rect,
    rows,
    text_color=PIE_ON_DARK_TEXT,
    font_size=13,
    line_height=None,
    legend_offset=0,
    legend_count=None,
    draw_pie=True,
):
    """在給定矩形畫起始點圓餅圖與圖例。"""
    painter.setFont(QFont("Microsoft JhengHei", font_size))
    slices = _pie_slices(rows)
    ink = QColor(text_color)
    if not slices:
        painter.setPen(ink)
        painter.drawText(rect, Qt.AlignCenter, "目前沒有起始點資料。")
        return

    total = sum(value for _label, value in slices)
    if draw_pie:
        side = min(max(rect.height() - 24, 80), rect.width() * 0.42, 280)
        pie_rect = QRectF(
            rect.left() + 12,
            rect.top() + max(0, (rect.height() - side) / 2),
            side,
            side,
        )
        start_angle = 90 * 16
        remaining = 360 * 16
        for index, (_label, value) in enumerate(slices):
            if index == len(slices) - 1:
                span = remaining
            else:
                span = int(round(360 * 16 * value / total))
                span = max(1, min(span, remaining - 1))
            color = QColor(PIE_COLORS[index % len(PIE_COLORS)])
            painter.setPen(QColor("#ffffff"))
            painter.setBrush(color)
            painter.drawPie(pie_rect, start_angle, -span)
            start_angle -= span
            remaining -= span
        legend_left = pie_rect.right() + 24
    else:
        legend_left = rect.left() + 12

    legend_top = rect.top() + 8
    line_height = line_height or PIE_LEGEND_LINE_HEIGHT
    visible = slices[legend_offset:]
    if legend_count is not None:
        visible = visible[:legend_count]
    for index, (label, value) in enumerate(visible):
        color_index = legend_offset + index
        y = legend_top + index * line_height
        if y + line_height > rect.bottom():
            break
        painter.setBrush(QColor(PIE_COLORS[color_index % len(PIE_COLORS)]))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(legend_left, y + 6, 14, 14), 2, 2)
        percent = value / total * 100
        painter.setPen(ink)
        painter.drawText(
            QRectF(legend_left + 22, y, rect.right() - legend_left - 28, line_height),
            Qt.AlignLeft | Qt.AlignVCenter,
            f"{label}    {value} 次    {percent:.1f}%",
        )


def start_point_pie_image_size(rows):
    count = max(1, len(_pie_slices(rows)))
    height = max(240, 24 + count * PIE_LEGEND_LINE_HEIGHT)
    return 980, height


PDF_PAGE_BG = "#ffffff"
PDF_INK = "#1b2836"
PDF_MUTED = "#3e4d5c"
PDF_CARD_BG = "#f7f9fc"
PDF_CARD_BORDER = "#d5dee8"
PDF_BAR_TRACK = "#e4ebf3"
PDF_BAR_ROW_HEIGHT = 58


def _pdf_font(size, bold=False):
    weight = QFont.Weight.Bold if bold else QFont.Weight.Normal
    return QFont("Microsoft JhengHei", size, weight)


def _section_block_height(section):
    rows = (section or {}).get("rows") or []
    body = 40
    body += 40 if not rows else len(rows) * PDF_BAR_ROW_HEIGHT
    return body + 48


def _paint_pdf_bar_section(painter, rect, section):
    painter.setPen(QColor(PDF_CARD_BORDER))
    painter.setBrush(QColor(PDF_CARD_BG))
    painter.drawRoundedRect(rect, 12, 12)

    inner = rect.adjusted(16, 14, -16, -14)
    painter.setPen(QColor(PDF_INK))
    painter.setFont(_pdf_font(18, bold=True))
    painter.drawText(
        QRectF(inner.left(), inner.top(), inner.width(), 30),
        Qt.AlignLeft | Qt.AlignVCenter,
        str(section.get("title") or ""),
    )

    rows = section.get("rows") or []
    y = inner.top() + 40
    if not rows:
        painter.setFont(_pdf_font(15))
        painter.setPen(QColor(PDF_MUTED))
        painter.drawText(
            QRectF(inner.left(), y, inner.width(), 32),
            Qt.AlignLeft | Qt.AlignVCenter,
            str(section.get("summary") or "目前沒有統計資料。"),
        )
        return

    values = [_safe_int(row.get("value")) for row in rows]
    max_value = max(values) if values else 1
    accent = "#4f8cff"
    for spec in SECTION_SPECS:
        if spec["key"] == section.get("key"):
            accent = spec.get("accent", accent)
            break

    for row, value in zip(rows, values):
        painter.setFont(_pdf_font(15))
        painter.setPen(QColor(PDF_INK))
        painter.drawText(
            QRectF(inner.left(), y, inner.width() - 72, 24),
            Qt.AlignLeft | Qt.AlignVCenter,
            str(row.get("label") or ""),
        )
        painter.drawText(
            QRectF(inner.right() - 68, y, 68, 24),
            Qt.AlignRight | Qt.AlignVCenter,
            str(value),
        )
        track = QRectF(inner.left(), y + 28, inner.width(), 12)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(PDF_BAR_TRACK))
        painter.drawRoundedRect(track, 6, 6)
        chunk_width = track.width() * value / max(max_value, 1)
        if chunk_width > 0:
            painter.setBrush(QColor(accent))
            painter.drawRoundedRect(QRectF(track.left(), track.top(), chunk_width, track.height()), 6, 6)
        y += PDF_BAR_ROW_HEIGHT

    painter.setFont(_pdf_font(14))
    painter.setPen(QColor(PDF_MUTED))
    painter.drawText(
        QRectF(inner.left(), y, inner.width(), 26),
        Qt.AlignLeft | Qt.AlignVCenter,
        str(section.get("summary") or ""),
    )


def _new_export_image(width, height):
    image = QImage(int(width), int(max(height, 1)), QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor(PDF_PAGE_BG))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    return image, painter


def _rows_that_fit(row_count, max_height):
    if row_count <= 0:
        return 0
    fitted = 1
    for count in range(1, row_count + 1):
        if _section_block_height({"rows": [{}] * count}) <= max_height:
            fitted = count
        else:
            break
    return fitted


def _chunk_section_pairs(sections, max_block_height):
    chunks = []
    for index in range(0, len(sections), 2):
        pair = sections[index:index + 2]
        offsets = [0 for _ in pair]
        totals = [len(section.get("rows") or []) for section in pair]
        if max_block_height is None:
            chunks.append(pair)
            continue
        if all(total == 0 for total in totals):
            chunks.append(pair)
            continue
        while any(offsets[item] < totals[item] for item in range(len(pair))):
            remaining = [totals[item] - offsets[item] for item in range(len(pair))]
            room = max(remaining) if remaining else 1
            take = _rows_that_fit(room, max_block_height)
            chunk = []
            for item, section in enumerate(pair):
                rows = section.get("rows") or []
                if offsets[item] >= len(rows):
                    continue
                chunk.append(
                    {
                        **section,
                        "rows": rows[offsets[item]:offsets[item] + take],
                    }
                )
                offsets[item] += take
            if chunk:
                chunks.append(chunk)
            else:
                break
    return chunks


def _pie_legend_chunks(pie_count, max_block_height):
    pie_line = 36
    header = 68
    if max_block_height is None:
        return [(0, pie_count, True)]
    chunks = []
    offset = 0
    first = True
    while offset < pie_count:
        if first:
            room = max(1, int((max_block_height - header - 8) / pie_line))
            chunks.append((offset, min(room, pie_count - offset), True))
            offset += min(room, pie_count - offset)
            first = False
        else:
            room = max(1, int((max_block_height - 16) / pie_line))
            chunks.append((offset, min(room, pie_count - offset), False))
            offset += min(room, pie_count - offset)
    return chunks or [(0, 0, True)]


def build_dashboard_export_blocks(snapshot, range_label, width=860, max_block_height=None):
    """每個區塊都是完整的標題、卡片或一整列圖表，方便換頁時不被從中切開。"""
    snapshot = snapshot or {}
    width = int(width)
    margin = 28
    content_width = width - margin * 2
    blocks = []

    header, painter = _new_export_image(width, 86)
    painter.setPen(QColor(PDF_INK))
    painter.setFont(_pdf_font(26, bold=True))
    painter.drawText(QRectF(margin, 16, content_width, 36), Qt.AlignLeft | Qt.AlignVCenter, "MiR 績效儀表板")
    painter.setFont(_pdf_font(16))
    painter.setPen(QColor(PDF_MUTED))
    painter.drawText(
        QRectF(margin, 52, content_width, 26),
        Qt.AlignLeft | Qt.AlignVCenter,
        f"監控區間：{range_label}",
    )
    painter.end()
    blocks.append(header)

    cards = list(snapshot.get("summary_cards") or [])
    if cards:
        card_height = 118
        card_rows = (len(cards) + 2) // 3
        cards_height = card_rows * card_height + max(0, card_rows - 1) * 12
        card_image, painter = _new_export_image(width, cards_height)
        card_width = (content_width - 24) / 3
        for index, card in enumerate(cards):
            column = index % 3
            row = index // 3
            card_rect = QRectF(
                margin + column * (card_width + 12),
                row * (card_height + 12),
                card_width,
                card_height,
            )
            painter.setPen(QColor(PDF_CARD_BORDER))
            painter.setBrush(QColor(PDF_CARD_BG))
            painter.drawRoundedRect(card_rect, 12, 12)
            painter.setPen(QColor(PDF_MUTED))
            painter.setFont(_pdf_font(15))
            painter.drawText(
                card_rect.adjusted(14, 12, -14, 0),
                Qt.AlignLeft | Qt.AlignTop,
                str(card.get("title") or ""),
            )
            painter.setPen(QColor(PDF_INK))
            painter.setFont(_pdf_font(28, bold=True))
            painter.drawText(
                card_rect.adjusted(14, 40, -14, -28),
                Qt.AlignLeft | Qt.AlignVCenter,
                str(card.get("value") or "0"),
            )
        painter.end()
        blocks.append(card_image)

    pie_rows = snapshot.get("start_point_pie") or []
    pie_slices = _pie_slices(pie_rows)
    pie_count = max(1, len(pie_slices))
    pie_line = 36
    for offset, count, draw_pie in _pie_legend_chunks(pie_count, max_block_height):
        if draw_pie:
            body_height = max(280, 8 + count * pie_line) if max_block_height is None else 8 + count * pie_line
            block_height = 68 + body_height
        else:
            block_height = 16 + count * pie_line
        pie_image, painter = _new_export_image(width, block_height)
        legend_top = 0
        if draw_pie:
            painter.setPen(QColor(PDF_INK))
            painter.setFont(_pdf_font(20, bold=True))
            painter.drawText(QRectF(margin, 0, content_width, 32), Qt.AlignLeft | Qt.AlignVCenter, "起始點使用比例")
            painter.setFont(_pdf_font(16))
            painter.setPen(QColor(PDF_MUTED))
            painter.drawText(
                QRectF(margin, 36, content_width, 28),
                Qt.AlignLeft | Qt.AlignVCenter,
                _most_used_start_text(pie_slices),
            )
            legend_top = 68
        paint_start_point_pie(
            painter,
            QRectF(margin, legend_top, content_width, block_height - legend_top),
            pie_rows,
            text_color=PIE_ON_LIGHT_TEXT,
            font_size=16,
            line_height=pie_line,
            legend_offset=offset,
            legend_count=count,
            draw_pie=draw_pie,
        )
        painter.end()
        blocks.append(pie_image)

    sections = list(snapshot.get("sections") or [])
    column_width = (content_width - 16) / 2
    for chunk in _chunk_section_pairs(sections, max_block_height):
        row_height = max(_section_block_height(section) for section in chunk)
        row_image, painter = _new_export_image(width, row_height)
        for column, section in enumerate(chunk):
            _paint_pdf_bar_section(
                painter,
                QRectF(margin + column * (column_width + 16), 0, column_width, row_height),
                section,
            )
        painter.end()
        blocks.append(row_image)

    return blocks


def render_dashboard_export_image(snapshot, range_label, width=860):
    """淺色、較大字級的儀表板匯出圖，四張長條圖都會完整畫出。"""
    blocks = build_dashboard_export_blocks(snapshot, range_label, width=width)
    gap = 18
    width = int(width)
    height = sum(block.height() for block in blocks) + gap * max(0, len(blocks) - 1)
    image, painter = _new_export_image(width, height)
    y = 0
    for block in blocks:
        painter.drawImage(0, y, block)
        y += block.height() + gap
    painter.end()
    return image


def render_start_point_pie_image(rows, width=None, height=None):
    default_width, default_height = start_point_pie_image_size(rows)
    width = width or default_width
    height = height or default_height
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor("#ffffff"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    paint_start_point_pie(
        painter,
        QRectF(0, 0, width, height),
        rows,
        text_color=PIE_ON_LIGHT_TEXT,
    )
    painter.end()
    return image


def _render_start_point_pie_html(rows):
    slices = _pie_slices(rows)
    if not slices:
        return (
            "<div class='section'>起始點使用比例</div>"
            "<div class='meta'>目前沒有起始點資料。</div>"
        )
    total = sum(value for _label, value in slices)
    body = "".join(
        "<tr><td>{label}</td><td>{value}</td><td>{percent}</td></tr>".format(
            label=escape(label),
            value=escape(str(value)),
            percent=escape(f"{value / total * 100:.1f}%"),
        )
        for label, value in slices
    )
    _width, height = start_point_pie_image_size(rows)
    display_width = 520
    display_height = max(140, int(height * display_width / _width))
    return (
        "<div class='section'>起始點使用比例</div>"
        f"<div class='meta'>{escape(_most_used_start_text(slices))}</div>"
        f"<img src='start-point-pie.png' width='{display_width}' height='{display_height}'/>"
        "<table><tr><td>起始點</td><td>次數</td><td>比例</td></tr>"
        f"{body}</table>"
    )


def performance_export_table(snapshot, range_label):
    """匯出用的純文字列。每一列是 (樣式, 儲存格文字)。"""
    snapshot = snapshot or {}
    rows = [
        ("title", ["MiR 績效儀表板", "", ""]),
        ("meta", [f"監控區間：{range_label or '全部累積資料'}", "", ""]),
        ("meta", [str(snapshot.get("status_text") or ""), "", ""]),
        ("blank", ["", "", ""]),
        ("section", ["任務摘要", "", ""]),
        ("header", ["項目", "數量", "說明"]),
    ]
    for card in snapshot.get("summary_cards") or []:
        rows.append(
            (
                "body",
                [
                    str(card.get("title") or ""),
                    str(card.get("value") or "0"),
                    str(card.get("caption") or ""),
                ],
            )
        )

    pie_rows = snapshot.get("start_point_pie") or []
    slices = _pie_slices(pie_rows)
    rows.append(("blank", ["", "", ""]))
    rows.append(("section", ["起始點使用比例", "", ""]))
    rows.append(("meta", [_most_used_start_text(slices), "", ""]))
    rows.append(("header", ["起始點", "次數", "比例"]))
    if slices:
        total = sum(value for _label, value in slices)
        for label, value in slices:
            percent = value / total * 100 if total else 0
            rows.append(("body", [label, str(value), f"{percent:.1f}%"]))
    else:
        rows.append(("body", ["目前沒有起始點資料。", "", ""]))

    for section in snapshot.get("sections") or []:
        rows.append(("blank", ["", "", ""]))
        rows.append(("section", [str(section.get("title") or ""), "", ""]))
        rows.append(("header", ["項目", "次數", ""]))
        section_rows = section.get("rows") or []
        if section_rows:
            for row in section_rows:
                rows.append(
                    (
                        "body",
                        [
                            str(row.get("label") or ""),
                            str(row.get("value") or ""),
                            "",
                        ],
                    )
                )
        else:
            rows.append(("body", ["無資料", "", ""]))
        summary = section.get("summary")
        if summary:
            rows.append(("meta", [str(summary), "", ""]))
    return rows


def write_performance_xlsx(path, snapshot, range_label):
    """把績效統計寫成只有文字的 Excel，不含圖。"""
    style_ids = {"title": 1, "section": 2, "header": 3, "meta": 4, "body": 0, "blank": 0}
    sheet_rows = []
    for index, (style, cells) in enumerate(performance_export_table(snapshot, range_label), start=1):
        style_id = style_ids.get(style, 0)
        height = {"title": 28, "section": 22}.get(style, 20)
        cell_xml = "".join(
            '<c r="{col}{row}" t="inlineStr" s="{style}"><is><t xml:space="preserve">{text}</t></is></c>'.format(
                col=column,
                row=index,
                style=style_id,
                text=xml_escape(value),
            )
            for column, value in zip("ABC", cells)
        )
        sheet_rows.append(f'<row r="{index}" ht="{height}" customHeight="1">{cell_xml}</row>')

    sheet = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <cols>
    <col min="1" max="1" width="42" customWidth="1"/>
    <col min="2" max="2" width="16" customWidth="1"/>
    <col min="3" max="3" width="42" customWidth="1"/>
  </cols>
  <sheetData>{rows}</sheetData>
</worksheet>
""".format(rows="".join(sheet_rows))

    styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="5">
    <font><sz val="12"/><name val="Microsoft JhengHei"/></font>
    <font><b/><sz val="18"/><name val="Microsoft JhengHei"/></font>
    <font><b/><sz val="14"/><name val="Microsoft JhengHei"/></font>
    <font><b/><sz val="12"/><name val="Microsoft JhengHei"/></font>
    <font><sz val="12"/><name val="Microsoft JhengHei"/></font>
  </fonts>
  <fills count="2">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
  </fills>
  <borders count="1"><border/></borders>
  <cellStyleXfs count="1"><xf/></cellStyleXfs>
  <cellXfs count="5">
    <xf fontId="0" applyFont="1"/>
    <xf fontId="1" applyFont="1"/>
    <xf fontId="2" applyFont="1"/>
    <xf fontId="3" applyFont="1"/>
    <xf fontId="4" applyFont="1"/>
  </cellXfs>
</styleSheet>
"""
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="績效統計" sheetId="1" r:id="rId1"/></sheets>
</workbook>
"""
    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>
""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
""",
        "xl/workbook.xml": workbook,
        "xl/_rels/workbook.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
""",
        "xl/styles.xml": styles,
        "xl/worksheets/sheet1.xml": sheet,
    }
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as workbook_file:
        for name, content in files.items():
            workbook_file.writestr(name, content.encode("utf-8"))


class StartPointPieWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self.setMinimumHeight(280)
        self.setAutoFillBackground(False)

    def set_rows(self, rows):
        self.rows = list(rows or [])
        _width, height = start_point_pie_image_size(self.rows)
        self.setMinimumHeight(height)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        paint_start_point_pie(painter, QRectF(self.rect()), self.rows)
        painter.end()


class SectionBarChartWidget(QWidget):
    def __init__(self, accent_color, empty_text, parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self.empty_text = empty_text
        self.row_frames = []

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(10)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background: transparent;")

        self.rows_host = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_host)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(10)

        self.scroll_area.setWidget(self.rows_host)

        self.summary_label = QLabel(empty_text)
        self.summary_label.setObjectName("dashboardSectionMeta")
        self.summary_label.setWordWrap(True)

        root_layout.addWidget(self.scroll_area, 1)
        root_layout.addWidget(self.summary_label)

    def _delete_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self._delete_layout(child_layout)

    def _clear_rows(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self._delete_layout(child_layout)

        self.row_frames = []

    def _build_bar_row(self, label_text, value, max_value):
        frame = QFrame()
        frame.setObjectName("dashboardBarRow")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        label = QLabel(label_text)
        label.setObjectName("dashboardBarLabel")
        label.setWordWrap(True)

        value_label = QLabel(str(value))
        value_label.setObjectName("dashboardBarValue")
        value_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        progress_bar = QProgressBar()
        progress_bar.setObjectName("dashboardBarProgress")
        progress_bar.setTextVisible(False)
        progress_bar.setRange(0, max(max_value, 1))
        progress_bar.setValue(value)
        progress_bar.setFixedHeight(10)
        progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: #1a2531;
            }
            QProgressBar::chunk {
                border-radius: 5px;
                background-color: %s;
            }
            """
            % self.accent_color
        )

        header_layout.addWidget(label, 1)
        header_layout.addWidget(value_label, 0)

        layout.addLayout(header_layout)
        layout.addWidget(progress_bar)
        return frame

    def set_rows(self, rows, body_text=None, summary_text=None):
        self._clear_rows()

        if not rows:
            empty_label = QLabel(self.empty_text)
            empty_label.setObjectName("dashboardSectionEmpty")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setWordWrap(True)
            self.rows_layout.addWidget(empty_label)
            self.rows_layout.addStretch()
            self.summary_label.setText(summary_text or body_text or self.empty_text)
            return

        numeric_values = [_safe_int(row.get("value")) for row in rows]
        max_value = max(numeric_values) if numeric_values else 1

        for row in rows:
            row_value = _safe_int(row.get("value"))
            row_frame = self._build_bar_row(
                str(row.get("label", "")),
                row_value,
                max_value,
            )
            self.rows_layout.addWidget(row_frame)
            self.row_frames.append(row_frame)

        self.rows_layout.addStretch()
        self.summary_label.setText(summary_text or body_text or self.empty_text)

    def row_count(self):
        return len(self.row_frames)


class PerformanceDashboardWindow(QWidget):
    def __init__(
        self,
        snapshot_provider=None,
        refresh_interval_ms=DASHBOARD_AUTO_REFRESH_MS,
        parent=None,
    ):
        super().__init__(None)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinMaxButtonsHint
            | Qt.WindowCloseButtonHint
        )
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        self.snapshot_provider = snapshot_provider or build_performance_dashboard_snapshot
        self.refresh_interval_ms = refresh_interval_ms
        self.summary_value_labels = {}
        self.section_body_labels = {}
        self.section_chart_widgets = {}
        self.latest_snapshot = None

        self.setObjectName("PerformanceDashboardWindow")
        self.setWindowTitle("MiR 績效儀表板")
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

        title_label = QLabel("MiR 績效儀表板")
        title_label.setObjectName("dashboardTitleLabel")

        subtitle_label = QLabel(
            "P04 / P3 任務統計視圖，集中顯示摘要數量、任務類型分組與熱門路線。"
        )
        subtitle_label.setObjectName("dashboardSubtitleLabel")
        subtitle_label.setWordWrap(True)

        header_actions_layout = QHBoxLayout()
        header_actions_layout.setSpacing(12)

        self.last_refresh_label = QLabel("最後刷新：等待載入中")
        self.last_refresh_label.setObjectName("dashboardMetaLabel")

        self.refresh_button = QPushButton("立即刷新")
        self.refresh_button.setObjectName("dashboardRefreshButton")
        self.refresh_button.clicked.connect(self.refresh_dashboard)

        header_actions_layout.addWidget(self.last_refresh_label)
        header_actions_layout.addStretch()
        header_actions_layout.addWidget(self.refresh_button)

        range_layout = QHBoxLayout()
        range_layout.setSpacing(12)

        self.range_checkbox = QCheckBox("指定監控區間")
        self.range_checkbox.setObjectName("dashboardRangeCheckbox")
        self.range_checkbox.toggled.connect(self._on_range_toggled)

        self.start_edit = QDateTimeEdit()
        self.start_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDateTime(QDateTime.currentDateTime().date().startOfDay())
        self.start_edit.setEnabled(False)

        self.end_edit = QDateTimeEdit()
        self.end_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.end_edit.setCalendarPopup(True)
        self.end_edit.setDateTime(QDateTime.currentDateTime())
        self.end_edit.setEnabled(False)

        self.apply_range_button = QPushButton("套用區間")
        self.apply_range_button.setObjectName("dashboardRefreshButton")
        self.apply_range_button.clicked.connect(self.refresh_dashboard)

        self.export_pdf_button = QPushButton("匯出")
        self.export_pdf_button.setObjectName("dashboardExportButton")
        self.export_pdf_button.clicked.connect(self.export_pdf)

        self.range_status_label = QLabel("監控區間：全部累積資料")
        self.range_status_label.setObjectName("dashboardMetaLabel")

        range_layout.addWidget(self.range_checkbox)
        range_layout.addWidget(QLabel("開始"))
        range_layout.addWidget(self.start_edit)
        range_layout.addWidget(QLabel("結束"))
        range_layout.addWidget(self.end_edit)
        range_layout.addWidget(self.apply_range_button)
        range_layout.addWidget(self.export_pdf_button)
        range_layout.addStretch()

        self.status_banner = QLabel("")
        self.status_banner.setObjectName("dashboardStatusBanner")
        self.status_banner.setWordWrap(True)

        summary_frame = QFrame()
        summary_frame.setObjectName("dashboardPanel")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(18, 18, 18, 18)
        summary_layout.setSpacing(14)

        summary_title = QLabel("任務摘要")
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

        pie_frame = QFrame()
        pie_frame.setObjectName("dashboardPanel")
        pie_layout = QVBoxLayout(pie_frame)
        pie_layout.setContentsMargins(18, 18, 18, 18)
        pie_layout.setSpacing(8)

        pie_title = QLabel("起始點使用比例")
        pie_title.setObjectName("dashboardSectionTitle")
        self.start_point_caption = QLabel("目前沒有起始點資料。")
        self.start_point_caption.setObjectName("dashboardPieCaption")
        self.start_point_caption.setWordWrap(True)
        self.start_point_caption.setStyleSheet(
            "color: #f4f7fb; font-size: 15px; font-weight: 600;"
        )
        self.start_point_pie = StartPointPieWidget()
        pie_layout.addWidget(pie_title)
        pie_layout.addWidget(self.start_point_caption)
        pie_layout.addWidget(self.start_point_pie)

        sections_frame = QFrame()
        sections_frame.setObjectName("dashboardPanel")
        sections_layout = QVBoxLayout(sections_frame)
        sections_layout.setContentsMargins(18, 18, 18, 18)
        sections_layout.setSpacing(14)

        sections_title = QLabel("任務量與熱區統計")
        sections_title.setObjectName("dashboardSectionTitle")
        sections_layout.addWidget(sections_title)

        section_cards_layout = QGridLayout()
        section_cards_layout.setHorizontalSpacing(12)
        section_cards_layout.setVerticalSpacing(12)
        for index, spec in enumerate(SECTION_SPECS):
            section_cards_layout.addWidget(
                self._build_section_card(
                    spec["key"],
                    spec["title"],
                    spec["empty_text"],
                    spec["accent"],
                ),
                index // 2,
                index % 2,
            )
        sections_layout.addLayout(section_cards_layout)

        root_layout.addWidget(title_label)
        root_layout.addWidget(subtitle_label)
        root_layout.addLayout(header_actions_layout)
        root_layout.addLayout(range_layout)
        root_layout.addWidget(self.range_status_label)
        root_layout.addWidget(self.status_banner)

        content = QWidget()
        content.setObjectName("dashboardReportBody")
        self.report_content = content
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)
        content_layout.addWidget(summary_frame)
        content_layout.addWidget(pie_frame)
        content_layout.addWidget(sections_frame)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)

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

    def _build_section_card(self, key, title, empty_text, accent_color):
        frame = QFrame()
        frame.setObjectName("dashboardSectionCard")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("dashboardSectionCardTitle")

        chart_widget = SectionBarChartWidget(
            accent_color=accent_color,
            empty_text=empty_text,
        )

        layout.addWidget(title_label)
        layout.addWidget(chart_widget, 1)

        self.section_chart_widgets[key] = chart_widget
        self.section_body_labels[key] = chart_widget.summary_label
        return frame

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QWidget#PerformanceDashboardWindow, QWidget#dashboardReportBody {
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
            QFrame#dashboardSummaryCard, QFrame#dashboardSectionCard {
                background-color: #10171f;
                border: 1px solid #233243;
                border-radius: 12px;
            }
            QLabel#dashboardCardTitle, QLabel#dashboardSectionCardTitle {
                font-size: 14px;
                font-weight: 600;
                color: #d7e2ef;
            }
            QLabel#dashboardCardValue {
                font-size: 28px;
                font-weight: 700;
                color: #f8fbff;
            }
            QLabel#dashboardCardCaption,
            QLabel#dashboardSectionMeta,
            QLabel#dashboardSectionEmpty,
            QLabel#dashboardBarLabel,
            QLabel#dashboardBarValue {
                font-size: 12px;
                color: #92a6bc;
            }
            QLabel#dashboardSectionMeta {
                color: #c3d3e4;
            }
            QLabel#dashboardBarLabel {
                color: #dce8f4;
            }
            QLabel#dashboardBarValue {
                color: #f8fbff;
                font-weight: 600;
                min-width: 36px;
            }
            QScrollArea {
                background: transparent;
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
            QPushButton#dashboardExportButton {
                background-color: #243140;
                color: #f4f7fb;
                border: 1px solid #3d5168;
                border-radius: 8px;
                padding: 9px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QCheckBox#dashboardRangeCheckbox, QDateTimeEdit {
                color: #f4f7fb;
                font-size: 13px;
            }
            """
        )

    def _on_range_toggled(self, checked):
        self.start_edit.setEnabled(checked)
        self.end_edit.setEnabled(checked)
        if checked and self.end_edit.dateTime() < self.start_edit.dateTime():
            self.end_edit.setDateTime(QDateTime.currentDateTime())
        self.refresh_dashboard()

    def monitoring_range(self):
        """回傳 (start_at, end_at, label)。未指定區間時時間為 None。"""
        if not self.range_checkbox.isChecked():
            return None, None, "全部累積資料"

        start_at = self.start_edit.dateTime().toPython()
        end_at = self.end_edit.dateTime().toPython()
        label = (
            f"{self.start_edit.dateTime().toString('yyyy-MM-dd HH:mm')}"
            f" ~ {self.end_edit.dateTime().toString('yyyy-MM-dd HH:mm')}"
        )
        return start_at, end_at, label

    def _call_snapshot_provider(self):
        start_at, end_at, _label = self.monitoring_range()
        provider = self.snapshot_provider
        try:
            parameters = inspect.signature(provider).parameters
        except (TypeError, ValueError):
            parameters = {}

        accepts_range = any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            or parameter.name in {"start_at", "end_at"}
            for parameter in parameters.values()
        )
        if accepts_range:
            return provider(start_at=start_at, end_at=end_at)
        return provider()

    def render_export_image(self, width=860):
        """淺色匯出圖：摘要、圓餅圖，以及四張長條圖。"""
        _start_at, _end_at, range_label = self.monitoring_range()
        return render_dashboard_export_image(self.latest_snapshot, range_label, width=width)

    def export_pdf(self):
        if not self.latest_snapshot:
            QMessageBox.information(self, "匯出", "目前沒有可匯出的統計資料。")
            return

        default_name = "mir_performance_{}.pdf".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "匯出績效",
            default_name,
            "PDF 與 Excel (*.pdf)",
        )
        if not path:
            return
        stem = path
        for extension in (".pdf", ".xlsx", ".xls"):
            if stem.lower().endswith(extension):
                stem = stem[: -len(extension)]
                break
        pdf_path = stem + ".pdf"
        xlsx_path = stem + ".xlsx"

        _start_at, _end_at, range_label = self.monitoring_range()
        write_performance_xlsx(xlsx_path, self.latest_snapshot, range_label)

        printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(pdf_path)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

        painter = QPainter(printer)
        page = printer.pageRect(QPrinter.Unit.DevicePixel)
        margin = 24
        gap = 16
        target_width = max(page.width() - margin * 2, 1)
        page_bottom = page.height() - margin
        blocks = build_dashboard_export_blocks(
            self.latest_snapshot,
            self.monitoring_range()[2],
            width=target_width,
            max_block_height=max(page_bottom - margin, 1),
        )
        y = margin
        page_open = False
        for block in blocks:
            if page_open and y + block.height() > page_bottom:
                printer.newPage()
                y = margin
                page_open = False
            if not page_open:
                painter.fillRect(page, QColor(PDF_PAGE_BG))
                page_open = True
            painter.drawImage(QRectF(margin, y, target_width, block.height()), block)
            y += block.height() + gap
        painter.end()
        QMessageBox.information(self, "匯出", f"已匯出：\n{pdf_path}\n{xlsx_path}")

    def set_snapshot_provider(self, snapshot_provider):
        self.snapshot_provider = snapshot_provider or build_performance_dashboard_snapshot

    def refresh_dashboard(self):
        start_at, end_at, range_label = self.monitoring_range()
        if start_at is not None and end_at is not None and end_at < start_at:
            QMessageBox.warning(self, "監控區間", "結束時間必須晚於開始時間。")
            return

        try:
            snapshot = self._call_snapshot_provider() or build_performance_dashboard_snapshot()
        except Exception as exc:
            snapshot = build_performance_dashboard_snapshot(
                warning_message=f"統計資料刷新失敗：{exc}"
            )

        self.latest_snapshot = snapshot
        self.range_status_label.setText(f"監控區間：{range_label}")
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

        section_specs_by_key = {spec["key"]: spec for spec in SECTION_SPECS}
        for section in snapshot.get("sections", []):
            chart_widget = self.section_chart_widgets.get(section.get("key"))
            if chart_widget is None:
                continue

            body_text = section.get("body")
            if body_text is None:
                spec = section_specs_by_key.get(section.get("key"), {})
                body_text = _format_section_body(
                    section.get("rows", []),
                    spec.get("empty_text", "目前沒有統計資料。"),
                )

            chart_widget.set_rows(
                section.get("rows", []),
                body_text=body_text,
                summary_text=section.get("summary"),
            )

        pie_rows = snapshot.get("start_point_pie") or []
        if hasattr(self, "start_point_pie"):
            self.start_point_pie.set_rows(pie_rows)
            self.start_point_caption.setText(_most_used_start_text(_pie_slices(pie_rows)))

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
