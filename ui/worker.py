from __future__ import annotations
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot
from core.enums import PDFType, ProcessStatus
from core.models import AnalysisMode, DocumentAnalysis, PDFResult, ExtractionResult
from core.pdf_detector import PDFDetector
from core.pdf_reader import PDFReader
from core.extractor import Extractor


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

        self._pdf_reader = PDFReader()
        self._pdf_detector = PDFDetector()
        self._extractor = Extractor()
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

    def _process_pdf(self, pdf_file: Path) -> PDFResult:
        """Read, classify, and extract one PDF without accessing the UI."""
        relative_path = pdf_file
        if self._input_folder is not None:
            relative_path = pdf_file.relative_to(self._input_folder)

        result = PDFResult(
            source_file=pdf_file,
            relative_path=relative_path,
            file_name=pdf_file.name,
        )

        try:
            document = self._pdf_reader.read(pdf_file)
            analysis = self._pdf_detector.analyze(document)
        except Exception as error:
            result.status = ProcessStatus.FAILED
            result.note = f"{type(error).__name__}: {error}"
            return result

        extraction: ExtractionResult | None = None
        if analysis.mode is not AnalysisMode.UNKNOWN:
            try:
                extraction = self._extractor.extract(document, analysis)
            except Exception as error:
                result.status = ProcessStatus.FAILED
                result.note = f"{type(error).__name__}: {error}"
                return result

        result.pdf_type = self._result_pdf_type(analysis.mode)
        result.status = (
            ProcessStatus.WARNING
            if analysis.mode is AnalysisMode.UNKNOWN
            else ProcessStatus.SUCCESS
        )
        result.note = self._format_note(analysis, extraction)
        return result

    @staticmethod
    def _result_pdf_type(mode: AnalysisMode) -> PDFType | None:
        if mode is AnalysisMode.DIGITAL:
            return PDFType.DIGITAL
        if mode is AnalysisMode.SCANNED:
            return PDFType.OCR
        if mode is AnalysisMode.HYBRID:
            return PDFType.HYBRID
        return None

    @staticmethod
    def _format_note(
            analysis: DocumentAnalysis,
            extraction: ExtractionResult | None,
    ) -> str:
        note = (
            f"Detected {analysis.mode.name} "
            f"({analysis.confidence.level.value}: "
            f"{analysis.confidence.score:.2f})."
        )

        if extraction is not None and extraction.warnings:
            return f"{note} {extraction.warnings[0]}"

        if analysis.warnings:
            return f"{note} {analysis.warnings[0]}"

        return note

    def _write_excel(self) -> None:
        pass
