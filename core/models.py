"""
Định nghĩa các Data Model dùng trong toàn bộ ứng dụng.
Quy ước:
- Chỉ chứa Dataclass.
- Không chứa Business Logic.
- Không chứa UI.
- Không chứa Regex.
- Không chứa xử lý Excel.
"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional
from .enums import ErrorType, PDFType, ProcessStage, ProcessStatus


# ======================================================================
# Invoice Information
# ======================================================================

@dataclass(slots=True)
class InvoiceInfo:
    """Thông tin trích xuất từ một hóa đơn PDF."""
    source_file: str

    company_name: str
    tax_code: str
    address: str

    buyer_name: str
    buyer_tax_code: str

    payment_method: str

    invoice_number: str
    invoice_date: Optional[date]

    subtotal: Optional[Decimal]
    vat_rate: Optional[Decimal]
    vat_amount: Optional[Decimal]
    total_amount: Optional[Decimal]


# ======================================================================
# PDF Processing Result
# ======================================================================

@dataclass(slots=True)
class PDFResult:
    """
    Trạng thái xử lý của một file PDF.
    Dùng để hiển thị trên QTableView.
    """
    session_id: int = 0

    source_file: Path = Path()

    relative_path: Path = Path()

    file_name: str = ""

    pdf_type: PDFType | None = None

    status: ProcessStatus = ProcessStatus.WAITING

    invoice: InvoiceInfo | None = None

    note: str = ""


# ======================================================================
# Processing Error
# ======================================================================

@dataclass(slots=True)
class ProcessError:
    """Mô tả một lỗi phát sinh trong quá trình xử lý."""
    pdf_name: str

    stage: ProcessStage

    error_type: ErrorType

    message: str


# ======================================================================
# Whole Processing Result
# ======================================================================

@dataclass(slots=True)
class ExtractionResult:
    """Kết quả của toàn bộ phiên xử lý."""
    invoices: list[InvoiceInfo] = field(default_factory=list)

    pdf_results: list[PDFResult] = field(default_factory=list)

    errors: list[ProcessError] = field(default_factory=list)
