import time
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot
from config import EXCEL_MAPPING_PATH, REPORTS_DIR, TEMPLATES_DIR
from core.domain.enums import PDFType, ProcessStatus
from core.export.excel_mapper import Mapper, MappingError
from core.export.excel_writer import (
    ExcelTableNotFoundError,
    ExcelWriter,
    WorkbookNotFoundError,
    WorkbookSaveError,
)
from core.domain.models import (
    AnalysisMode,
    DocumentAnalysis,
    ExcelWriteResult,
    ExtractionResult,
    InvoiceInfo,
    PDFResult,
)
from core.detection.pdf_detector import PDFDetector
from core.reading.pdf_reader import PDFReader
from core.extraction.extractor import Extractor
from core.parsing.parser import Parser
from core.parsing.template.template_loader import TemplateLoader
from core.parsing.template.template_matcher import TemplateMatcher
from core.export.report_writer import ReportWriter


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

        templates = TemplateLoader(TEMPLATES_DIR).load_all()
        self._parser = Parser(TemplateMatcher(templates))

        self._ocr_reader = None
        self._excel_writer = ExcelWriter()
        self._report_writer = ReportWriter(REPORTS_DIR)
        self._report_path: Optional[Path] = None

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

    @property
    def report_path(self) -> Optional[Path]:
        return self._report_path

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format số giây thành chuỗi HH:MM:SS."""
        if seconds < 0 or seconds > 86400 * 7:
            return "--:--:--"
        total_seconds = int(seconds)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def process(self) -> None:
        pdf_files = sorted(self._input_folder.rglob("*.pdf"))
        total = len(pdf_files)

        start_time = time.time()
        avg_digital_time = 0.15
        avg_ocr_time = 2.0
        digital_count = 0
        ocr_count = 0

        for index, pdf_file in enumerate(pdf_files, start=1):
            if self._cancel_requested:
                self.cancelled.emit()
                return

            file_start = time.time()
            result = self._process_pdf(pdf_file)
            file_duration = time.time() - file_start

            if result.pdf_type == PDFType.DIGITAL:
                digital_count += 1
                avg_digital_time = 0.7 * avg_digital_time + 0.3 * file_duration
            else:
                ocr_count += 1
                avg_ocr_time = 0.7 * avg_ocr_time + 0.3 * file_duration

            elapsed_seconds = time.time() - start_time
            elapsed_str = self._format_time(elapsed_seconds)

            remaining_files = total - index
            if remaining_files > 0:
                processed_so_far = digital_count + ocr_count
                ocr_ratio = ocr_count / processed_so_far if processed_so_far > 0 else 0.5

                est_remaining_ocr = remaining_files * ocr_ratio
                est_remaining_digital = remaining_files * (1.0 - ocr_ratio)

                eta_seconds = (est_remaining_digital * avg_digital_time) + (
                    est_remaining_ocr * avg_ocr_time
                )
                eta_str = self._format_time(eta_seconds)
            else:
                eta_str = "00:00:00"

            self._results.append(result)
            self.file_processed.emit(result)
            self.progress.emit(index, total, elapsed_str, eta_str)

        self._write_excel()
        self.finished.emit()

    def _process_pdf(self, pdf_file: Path) -> PDFResult:
        """Read, classify, extract, and parse one PDF without accessing the UI."""
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

        invoice: InvoiceInfo | None = None
        if extraction is not None:
            try:
                invoice = self._parser.parse(extraction, str(pdf_file))
            except Exception as error:
                result.status = ProcessStatus.FAILED
                result.note = f"{type(error).__name__}: {error}"
                return result
            # invoice is None ở đây nghĩa là "không xác định được template" -
            # KHÔNG coi là lỗi (nguyên nhân có thể là thiếu template, template
            # sai, PDF chất lượng kém, hoặc nhầm file - không thể khẳng định).
            # Theo quyết định đã chốt (Phương án B): không đổi result.status,
            # không ghi note. Người dùng tự nhận biết qua Report (cột invoice
            # trống); nếu lặp lại nhiều lần trên cùng 1 mẫu -> báo admin cập
            # nhật template.

        result.pdf_type = self._result_pdf_type(analysis.mode)
        result.status = (
            ProcessStatus.WARNING
            if analysis.mode is AnalysisMode.UNKNOWN
            else ProcessStatus.SUCCESS
        )
        result.note = self._format_note(analysis)
        result.invoice = invoice
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
    def _format_note(analysis: DocumentAnalysis) -> str:
        note = (
            f"Detected {analysis.mode.name} "
            f"({analysis.confidence.level.value}: "
            f"{analysis.confidence.score:.2f})."
        )

        if analysis.warnings:
            return f"{note} {analysis.warnings[0]}"

        return note

    def _write_excel(self) -> None:
        """Ghi Excel (1 lần, cuối batch - ADR-008), sau đó luôn sinh report."""
        invoices = [
            result.invoice for result in self._results if result.invoice is not None
        ]

        try:
            mapping = Mapper(EXCEL_MAPPING_PATH).load()
            excel_result = self._excel_writer.write(
                self._output_excel,
                invoices,
                mapping,
            )
        except (
            MappingError,
            WorkbookNotFoundError,
            ExcelTableNotFoundError,
            WorkbookSaveError,
        ) as error:
            self.error.emit(f"{type(error).__name__}: {error}")
            excel_result = ExcelWriteResult(
                total=len(invoices),
                written=0,
                errors=(f"{type(error).__name__}: {error}",),
            )

        self._report_path = self._report_writer.write(self._results, excel_result)
