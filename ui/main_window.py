from __future__ import annotations
from core.constants import FileDialog, Table, UIText, Window
from models.processing_table_model import ProcessingTableModel
from ui.widgets import PathSelectorWidget, ProgressWidget, ProcessingTable
from PySide6.QtCore import QThread, QUrl
from PySide6.QtGui import QDesktopServices
from ui.worker import Worker
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    """
    Main window of the PDF to Excel Extractor application.
    Responsibilities:
    - Build the UI.
    - Open file dialogs.
    - Update UI state.
    """
    def __init__(self) -> None:
        super().__init__()

        self._thread = QThread(self)
        self._worker = Worker()
        self._worker.moveToThread(self._thread)
        self._table_model = ProcessingTableModel()
        self._has_error = False

        self.setWindowTitle(UIText.TITLE)
        self.resize(Window.WIDTH, Window.HEIGHT)
        self.setMinimumSize(Window.MIN_WIDTH, Window.MIN_HEIGHT)

        self._create_widgets()
        self._create_layout()
        self._connect_signals()
        self._set_running(False)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        self.input_widget = PathSelectorWidget(UIText.INPUT_FOLDER)
        self.output_widget = PathSelectorWidget(UIText.OUTPUT_EXCEL)

        self.btn_start = QPushButton(UIText.BUTTON_START)
        self.btn_stop = QPushButton(UIText.BUTTON_STOP)
        self.btn_report = QPushButton(UIText.BUTTON_REPORT)
        self.btn_exit = QPushButton(UIText.BUTTON_EXIT)

        self.progress_widget = ProgressWidget()
        self.processing_table = ProcessingTable()
        self.processing_table.set_model(self._table_model)
        self.processing_table.resize_columns(
            [Table.COLUMN_WIDTH[header] for header in Table.HEADERS]
        )

    def _create_layout(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        layout.addWidget(self.input_widget)
        layout.addWidget(self.output_widget)

        start_layout = QHBoxLayout()
        start_layout.addStretch()
        start_layout.addWidget(self.btn_start)
        start_layout.addWidget(self.btn_stop)
        start_layout.addStretch()
        layout.addLayout(start_layout)

        layout.addWidget(self.progress_widget)
        layout.addWidget(self.processing_table)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(self.btn_report)
        bottom.addWidget(self.btn_exit)
        layout.addLayout(bottom)

    def _connect_signals(self) -> None:
        self.input_widget.browse_clicked.connect(self._browse_input)
        self.output_widget.browse_clicked.connect(self._browse_output)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.on_worker_progress)
        self._worker.finished.connect(self.on_worker_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.cancelled.connect(self.on_worker_cancelled)
        self._worker.cancelled.connect(self._thread.quit)
        self._worker.file_processed.connect(self._table_model.append)
        self._worker.error.connect(self.on_worker_error)

        self.btn_start.clicked.connect(self._start)
        self.btn_stop.clicked.connect(self._stop)
        self.btn_report.clicked.connect(self._report)
        self.btn_exit.clicked.connect(self.close)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def _set_running(self, running: bool) -> None:
        self.input_widget.setEnabled(not running)
        self.output_widget.setEnabled(not running)

        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)

        self.btn_report.setEnabled(not running)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _browse_input(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            UIText.SELECT_INPUT_FOLDER,
        )
        if folder:
            self.input_widget.set_path(folder)

    def _browse_output(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            UIText.SELECT_EXCEL_TEMPLATE,
            "",
            FileDialog.EXCEL_FILTER,
        )
        if file_name:
            self.output_widget.set_path(file_name)

    def _start(self) -> None:
        if not self.input_widget.path():
            QMessageBox.warning(
                self,
                UIText.WARNING_TITLE,
                UIText.INPUT_FOLDER_REQUIRED,
            )
            return
        if not self.output_widget.path():
            QMessageBox.warning(
                self,
                UIText.WARNING_TITLE,
                UIText.OUTPUT_EXCEL_REQUIRED,
            )
            return

        self._has_error = False
        self._table_model.clear()
        self._set_running(True)
        self._worker.configure(
            self.input_widget.path(),
            self.output_widget.path(),
        )
        self._thread.start()

    def _stop(self) -> None:
        # TODO: worker.stop()
        self._worker.cancel()

    def _report(self) -> None:
        report_path = self._worker.report_path

        if report_path is None:
            QMessageBox.information(
                self,
                UIText.REPORT_TITLE,
                UIText.REPORT_NOT_AVAILABLE,
            )
            return

        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(report_path)))
        if not opened:
            QMessageBox.warning(
                self,
                UIText.WARNING_TITLE,
                UIText.REPORT_OPEN_FAILED,
            )

    # ------------------------------------------------------------------
    # Worker callbacks (reserved)
    # ------------------------------------------------------------------

    def on_worker_finished(self) -> None:
        self._set_running(False)
        if not self._has_error:
            self._report()

    def on_worker_cancelled(self) -> None:
        self._set_running(False)

    def on_worker_progress(
        self,
        processed: int,
        total: int,
        elapsed: str,
        eta: str,
    ) -> None:
        self.progress_widget.update_progress(
            processed,
            total,
            elapsed,
            eta,
        )

    def on_worker_error(self, message: str) -> None:
        self._has_error = True
        QMessageBox.warning(
            self,
            UIText.ERROR_TITLE,
            message,
        )


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
