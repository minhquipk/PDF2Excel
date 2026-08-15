import os
import time
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
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


class PDFTaskSignals(QObject):
    """
    Signal riêng cho 1 PDFTaskRunnable. QRunnable không phải QObject nên
    không tự phát Signal được - tách class con này theo đúng khuyến nghị
    chính thức của Qt cho QRunnable cần giao tiếp bất đồng bộ.
    """
    completed = Signal(object)   # PDFResult
    failed = Signal(str, str)    # (pdf_path_str, error_message)


class PDFTaskRunnable(QRunnable):
    """
    Đóng gói _process_pdf() cho đúng 1 file PDF, chạy trên 1 luồng của
    QThreadPool. Không truy cập UI (đối xứng ADR-001) - chỉ gọi
    Worker._process_pdf() (business logic không đổi, ADR-005) rồi phát
    Signal kết quả.

    Cancellation (MULTI_THREAD_SPECIFICATION.md §4, đã đơn giản hóa có
    chủ đích - Rule 9): chỉ kiểm tra cờ hủy đúng 1 lần TRƯỚC khi gọi
    _process_pdf(). Task đã bắt đầu chạy sẽ chạy tới khi xong tự nhiên -
    không chèn checkpoint giữa _process_pdf() (giữ nguyên khối business
    logic liền mạch, không vi phạm ADR-005). QThreadPool.clear() (gọi từ
    Worker.cancel()) loại các task CHƯA kịp chạy khỏi hàng đợi.
    """

    def __init__(
        self,
        worker: "Worker",
        pdf_file: Path,
        is_cancelled: "callable",
    ) -> None:
        super().__init__()
        self._worker = worker
        self._pdf_file = pdf_file
        self._is_cancelled = is_cancelled
        self.signals = PDFTaskSignals()

    def run(self) -> None:
        if self._is_cancelled():
            return

        try:
            result = self._worker._process_pdf(self._pdf_file)
        except Exception as error:
            self.signals.failed.emit(
                str(self._pdf_file), f"{type(error).__name__}: {error}"
            )
            return

        self.signals.completed.emit(result)


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

        self._excel_writer = ExcelWriter()
        self._report_writer = ReportWriter(REPORTS_DIR)
        self._report_path: Optional[Path] = None

        # Khống chế OpenMP của Tesseract (MULTI_THREAD_SPECIFICATION.md §5.1)
        # - set 1 lần, cấp process, trước khi bất kỳ PDFTaskRunnable nào gọi
        # Tesseract. Tránh N luồng Python x M luồng con OpenMP -> CPU quá tải.
        os.environ["OMP_THREAD_LIMIT"] = "1"
        os.environ["OMP_NUM_THREADS"] = "1"

        self._thread_pool = QThreadPool()
        self._thread_count = 1  # ghi đè qua configure()

        # State tổng hợp cho mô hình event-driven (không blocking waitForDone()
        # trong luồng Worker - xem quyết định kiến trúc Bước 3, mục 1).
        self._total_files = 0
        self._processed_count = 0
        self._batch_start_time = 0.0

    def configure(
            self, input_folder: Path, output_excel: Path, thread_count: int = 1
    ) -> None:
        self._input_folder = Path(input_folder)
        self._output_excel = Path(output_excel)
        self._thread_count = max(1, thread_count)

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
        self._thread_pool.clear()

    @property
    def results(self) -> list[PDFResult]:
        return self._results

    @property
    def report_path(self) -> Optional[Path]:
        """
        Trả về report.txt của phiên xử lý hiện tại (nếu đã Start ít nhất
        1 lần trong lần mở app này); nếu chưa, fallback kiểm tra report.txt
        còn sót lại từ lần chạy trước trên đĩa (ReportWriter.expected_path()) -
        cho phép người dùng xem lại report cũ ngay cả khi vừa mở lại ứng
        dụng mà chưa bấm Start. Nút Report KHÔNG tự sinh report trong cả 2
        trường hợp (ADR-041 vẫn giữ nguyên, chỉ mở rộng phạm vi "đã tồn tại
        sẵn" - xem amend ADR-041).
        """
        if self._report_path is not None:
            return self._report_path

        fallback = ReportWriter.expected_path(REPORTS_DIR)
        return fallback if fallback.exists() else None

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format số giây thành chuỗi HH:MM:SS."""
        if seconds < 0 or seconds > 86400 * 7:
            return "--:--:--"
        total_seconds = int(seconds)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _discover_pdf_files(self) -> list[Path] | None:
        """
        Duyệt đệ quy Input Folder tìm file .pdf (case-insensitive trên
        mọi OS - chấp nhận cả .PDF/.Pdf, khác Path.rglob("*.pdf") cũ vốn
        phụ thuộc case-sensitivity của hệ điều hành).

        Có thể bị huỷ giữa chừng qua self._cancel_requested, kiểm tra sau
        mỗi file/thư mục con - phản hồi gần như tức thời, khác
        Path.rglob() cũ (1 lệnh blocking, generator bị sorted() ép chạy
        hết 1 mạch, không có điểm nào để Stop có tác dụng giữa chừng).

        Returns
        -------
        list[Path]
            Danh sách file PDF tìm được (đã sort), nếu quét xong hoàn
            toàn không bị huỷ.
        None
            Nếu bị huỷ (self._cancel_requested) trong lúc đang quét -
            phân biệt với list rỗng (quét xong, không tìm thấy PDF nào).
        """
        pdf_files: list[Path] = []
        for root, _dirs, files in os.walk(self._input_folder):
            if self._cancel_requested:
                return None
            for name in files:
                if self._cancel_requested:
                    return None
                if name.lower().endswith(".pdf"):
                    pdf_files.append(Path(root) / name)

        return sorted(pdf_files)

    def process(self) -> None:
        pdf_files = self._discover_pdf_files()
        if pdf_files is None:
            self.cancelled.emit()
            return

        self._total_files = len(pdf_files)
        self._processed_count = 0
        self._batch_start_time = time.time()

        if self._total_files == 0:
            self._write_excel()
            self.finished.emit()
            return

        self._thread_pool.setMaxThreadCount(self._thread_count)

        for pdf_file in pdf_files:
            task = PDFTaskRunnable(self, pdf_file, lambda: self._cancel_requested)
            task.signals.completed.connect(self._on_task_completed)
            task.signals.failed.connect(self._on_task_failed)
            self._thread_pool.start(task)

        # process() return ngay - KHÔNG blocking waitForDone(). Toàn bộ tổng
        # hợp kết quả/trigger finished diễn ra qua _on_task_completed()/
        # _on_task_failed() (quyết định kiến trúc Bước 3, mục 1).

    @Slot(object)
    def _on_task_completed(self, result: PDFResult) -> None:
        """Slot chạy trên luồng Worker (Qt tự queue qua thread affinity)."""
        if self._cancel_requested:
            return

        self._results.append(result)
        self.file_processed.emit(result)
        self._advance_progress()

    @Slot(str, str)
    def _on_task_failed(self, pdf_path: str, message: str) -> None:
        """
        Trường hợp hiếm: lỗi ngoài dự kiến thoát khỏi mọi try/except trong
        _process_pdf() (vốn đã tự bắt Exception ở từng stage - xem
        _process_pdf() hiện có). Giữ batch tiếp tục thay vì crash toàn bộ,
        đối xứng triết lý fail-soft per-item đã có (ADR-031/032/033).
        """
        if self._cancel_requested:
            return

        result = PDFResult(
            source_file=Path(pdf_path),
            relative_path=Path(pdf_path),
            file_name=Path(pdf_path).name,
            status=ProcessStatus.FAILED,
            note=message,
        )
        self._results.append(result)
        self.file_processed.emit(result)
        self._advance_progress()

    def _advance_progress(self) -> None:
        self._processed_count += 1

        elapsed_seconds = time.time() - self._batch_start_time
        elapsed_str = self._format_time(elapsed_seconds)

        remaining = self._total_files - self._processed_count
        if remaining > 0 and self._processed_count > 0:
            eta_seconds = (elapsed_seconds / self._processed_count) * remaining
            eta_str = self._format_time(eta_seconds)
        else:
            eta_str = "00:00:00"

        self.progress.emit(self._processed_count, self._total_files, elapsed_str, eta_str)

        if self._processed_count >= self._total_files:
            if self._cancel_requested:
                self.cancelled.emit()
            else:
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
