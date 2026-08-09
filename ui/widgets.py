"""
Các Widget tái sử dụng của ứng dụng.
Hiện tại:
    - PathSelectorWidget
"""
from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import Signal
from core.constants import Progress, UIText
from ui.base_widget import BaseWidget
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QProgressBar,
    QTableView,
    QAbstractItemView,
)


# =============================================================================
# Path Selector Widget
# =============================================================================

class PathSelectorWidget(BaseWidget):
    """
    Widget dùng để chọn đường dẫn.
    Cấu trúc:
        +-------------------------------------------+
        Input Folder
        +-------------------------------------------+
        | C:\\Invoice\\2025              | Browse |
        +-------------------------------------------+
    Widget này KHÔNG mở QFileDialog.
    Chỉ phát tín hiệu browse_clicked().
    """

    browse_clicked = Signal()

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------

    def __init__(
        self,
        title: str,
        button_text: str = UIText.BUTTON_INPUT,
        parent=None,
    ) -> None:

        self._title = title
        self._button_text = button_text

        super().__init__(parent)

    # -------------------------------------------------------------------------
    # Protected Life Cycle
    # -------------------------------------------------------------------------

    def _create_widgets(self) -> None:

        self.lbl_title = QLabel(self._title)

        self.edit_path = QLineEdit()
        self.edit_path.setReadOnly(True)

        self.btn_browse = QPushButton(self._button_text)

    def _create_layout(self) -> None:

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.edit_path)
        button_layout.addWidget(self.btn_browse)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.lbl_title)
        main_layout.addLayout(button_layout)

    def _connect_signals(self) -> None:

        self.btn_browse.clicked.connect(self.browse_clicked)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def set_path(self, path: str | Path) -> None:
        """Hiển thị đường dẫn lên LineEdit."""
        self.edit_path.setText(str(path))

    def path(self) -> Path:
        """Trả về đường dẫn hiện tại."""
        text = self.edit_path.text().strip()

        if not text:
            return Path()

        return Path(text)

    def clear(self) -> None:

        self.edit_path.clear()

    def reset(self) -> None:

        self.clear()

# =============================================================================
# Progress Widget
# =============================================================================


class ProgressWidget(BaseWidget):
    """
    Hiển thị tiến trình xử lý.
        Progress
        ████████████████████░░░░░
        120 / 450
        26 %

        Elapsed : 00:01:15
        ETA     : 00:03:20
    Widget này chỉ hiển thị dữ liệu.
    Không tự tính toán thời gian.
    """

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------

    def __init__(self, parent=None):

        super().__init__(parent)

    # -------------------------------------------------------------------------
    # Protected Life Cycle
    # -------------------------------------------------------------------------

    def _create_widgets(self):

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(Progress.PERCENT_MIN)
        self.progress_bar.setMaximum(Progress.PERCENT_MAX)
        self.progress_bar.setValue(Progress.PERCENT_MIN)

        self.lbl_progress = QLabel(
            UIText.PROGRESS_COUNT_FORMAT.format(processed=0, total=0)
        )
        self.lbl_percent = QLabel(UIText.PROGRESS_PERCENT_FORMAT.format(percent=0))

        self.lbl_elapsed = QLabel(Progress.TIME_PLACEHOLDER)
        self.lbl_eta = QLabel(Progress.TIME_PLACEHOLDER)

    def _create_layout(self):

        form = QFormLayout()

        form.addRow(UIText.PROGRESS, self.progress_bar)
        form.addRow(UIText.PROCESSED, self.lbl_progress)
        form.addRow(UIText.PERCENT, self.lbl_percent)
        form.addRow(UIText.ELAPSED, self.lbl_elapsed)
        form.addRow(UIText.ETA, self.lbl_eta)

        group = QGroupBox(UIText.PROGRESS_GROUP)
        group.setLayout(form)

        layout = QVBoxLayout(self)
        layout.addWidget(group)

    def _connect_signals(self):

        pass

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def update_progress(
        self,
        processed: int,
        total: int,
        eta: str = Progress.TIME_PLACEHOLDER,
    ) -> None:
        """Cập nhật processed/total/percent/eta. Elapsed được cập nhật riêng qua update_elapsed()."""
        percent = 0

        if total > 0:
            percent = int(processed * 100 / total)

        self.progress_bar.setValue(percent)

        self.lbl_progress.setText(
            UIText.PROGRESS_COUNT_FORMAT.format(
                processed=processed,
                total=total,
            )
        )

        self.lbl_percent.setText(
            UIText.PROGRESS_PERCENT_FORMAT.format(percent=percent)
        )

        self.lbl_eta.setText(eta)

    def update_elapsed(self, elapsed: str) -> None:
        """Cập nhật chỉ nhãn elapsed — được gọi từ QTimer mỗi giây."""
        self.lbl_elapsed.setText(elapsed)

    def clear(self):

        self.reset()

    def reset(self):

        self.update_progress(0, 0)


# =============================================================================
# Processing Table
# =============================================================================


class ProcessingTable(BaseWidget):
    """
    Widget bao bọc QTableView.
    Chỉ quản lý giao diện.
    Không lưu dữ liệu.
    Không biết QAbstractTableModel.
    """
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------

    def __init__(self, parent=None):

        super().__init__(parent)

    # -------------------------------------------------------------------------
    # Protected Life Cycle
    # -------------------------------------------------------------------------

    def _create_widgets(self):

        self.lbl_title = QLabel(UIText.TABLE_TITLE)

        self.table = QTableView()

        self.table.setAlternatingRowColors(True)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(False)

        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

    def _create_layout(self):

        layout = QVBoxLayout(self)

        layout.addWidget(self.lbl_title)

        layout.addWidget(self.table)

    def _connect_signals(self):

        pass

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def set_model(self, model) -> None:
        """Gán QAbstractTableModel."""
        self.table.setModel(model)

    def model(self):
        """Trả về model hiện tại."""
        return self.table.model()

    def resize_columns(self, widths: list[int]) -> None:
        """Thiết lập chiều rộng các cột."""
        for column, width in enumerate(widths):
            self.table.setColumnWidth(column, width)

    def clear(self):

        self.table.clearSelection()

    def reset(self):

        self.clear()
