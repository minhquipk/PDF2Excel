from __future__ import annotations
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot
from core.models import PDFResult


class Worker(QObject):
    """Workflow engine coordinating the processing pipeline."""

    started = Signal()
    progress = Signal(int, int, str, str)
    file_processed = Signal(object)
    error = Signal(str)
    finished = Signal()
    cancelled = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._input_folder: Optional[Path] = None
        self._output_excel: Optional[Path] = None
        self._results: list[PDFResult] = []
        self._cancel_requested = False

        self._pdf_reader = None
        self._ocr_reader = None
        self._parser = None
        self._excel_writer = None
        self._report_writer = None

    def configure(self, input_folder: Path, output_excel: Path) -> None:
        self._input_folder = Path(input_folder)
        self._output_excel = Path(output_excel)

    @Slot()
    def run(self) -> None:
        if self._input_folder is None:
            self.error.emit("Input folder is not configured.")
            return
        if self._output_excel is None:
            self.error.emit("Output excel is not configured.")
            return

        self._cancel_requested = False
        self._results.clear()
        self.started.emit()
        self.process()

    def cancel(self) -> None:
        self._cancel_requested = True

    @property
    def results(self) -> list[PDFResult]:
        return self._results

    def process(self) -> None:
        pdf_files = sorted(self._input_folder.rglob("*.pdf"))
        total = len(pdf_files)

        for index, pdf_file in enumerate(pdf_files, start=1):
            if self._cancel_requested:
                self.cancelled.emit()
                return

            result = self._process_pdf(pdf_file)
            self._results.append(result)
            self.file_processed.emit(result)
            self.progress.emit(index, total, "--:--:--", "--:--:--")

        self._write_excel()
        self.finished.emit()

    @staticmethod
    def _process_pdf(pdf_file: Path) -> PDFResult:
        result = PDFResult()
        result.source_file = pdf_file
        result.file_name = pdf_file.name
        return result

    def _write_excel(self) -> None:
        pass
