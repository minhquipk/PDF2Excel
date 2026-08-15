"""
Ghi nhận kết quả một phiên xử lý theo 2 luồng tách biệt hoàn toàn:

- list[PDFResult] (log kỹ thuật, cấp file) -> logger (utils/logger.py),
  phục vụ dev/admin, không xuất hiện trong report.txt.
- ExcelWriteResult (kết quả ghi Excel, cấp field) -> report.txt, phục vụ
  end-user, mở qua nút Report trên UI.

Hai luồng không được trộn nội dung (quyết định đã chốt trong phiên thảo
luận excel_writer). report.txt là 1 file cố định, ghi đè mỗi lần chạy -
không có timestamp trong tên file.
"""

from __future__ import annotations
import logging
from pathlib import Path
from core.domain.constants import Report
from core.domain.enums import ProcessStatus
from core.domain.models import ExcelWriteResult, PDFResult
from utils.logger import get_logger

logger = get_logger(__name__)

_WARNING_STATUSES = (ProcessStatus.WARNING, ProcessStatus.FAILED)


class ReportWriter:
    """Ghi log kỹ thuật (PDFResult) và report.txt (ExcelWriteResult)."""

    def __init__(self, reports_dir: Path) -> None:
        self._reports_dir = Path(reports_dir)

    def write(
        self,
        results: list[PDFResult],
        excel_result: ExcelWriteResult,
    ) -> Path:
        """
        Ghi log kỹ thuật cho results, ghi report.txt cho excel_result.
        Trả về đường dẫn report.txt đã ghi (dùng bởi Worker/MainWindow).
        """
        self._log_results(results)
        return self._write_report_file(excel_result)

    @staticmethod
    def expected_path(reports_dir: Path) -> Path:
        """
        Đường dẫn report.txt cố định, không đổi giữa các lần chạy (tên
        không có timestamp - ADR-040). Dùng để kiểm tra sự TỒN TẠI của
        report từ lần chạy trước đó, KHÔNG cần đã gọi write() trong phiên
        Worker hiện tại - phục vụ Worker.report_path fallback về report
        cũ khi người dùng mở lại app mà chưa Start (xem amend ADR-041).
        """
        return Path(reports_dir) / f"{Report.FILE_PREFIX}{Report.FILE_EXTENSION}"

    # ------------------------------------------------------------------
    # Loại 1: list[PDFResult] -> logger (dev/admin)
    # ------------------------------------------------------------------

    @staticmethod
    def _log_results(results: list[PDFResult]) -> None:
        for result in results:
            level = (
                logging.WARNING
                if result.status in _WARNING_STATUSES
                else logging.INFO
            )
            logger.log(
                level,
                "%s | %s | %s",
                result.relative_path,
                result.status.value,
                result.note,
            )

    # ------------------------------------------------------------------
    # Loại 2: ExcelWriteResult -> report.txt (end-user)
    # ------------------------------------------------------------------

    def _write_report_file(self, excel_result: ExcelWriteResult) -> Path:
        self._reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.expected_path(self._reports_dir)

        content = self._format_report(excel_result)
        report_path.write_text(content, encoding="utf-8")

        return report_path

    @staticmethod
    def _format_report(excel_result: ExcelWriteResult) -> str:
        lines: list[str] = [
            "Summary:",
            f"Total: {excel_result.total}",
            f"Written: {excel_result.written}",
            "",
            "Warnings:",
        ]

        if excel_result.warnings:
            for warning in excel_result.warnings:
                lines.append(f"Invoice {warning.source_file}: {warning.field_name}=None")
        else:
            lines.append("(none)")

        lines.append("")
        lines.append("Errors:")

        if excel_result.errors:
            lines.extend(excel_result.errors)
        else:
            lines.append("(none)")

        return "\n".join(lines) + "\n"
