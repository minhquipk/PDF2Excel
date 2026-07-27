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
from collections.abc import Mapping as MappingABC
from enum import Enum, auto
from pathlib import Path
from dataclasses import dataclass, field
from datetime import date, datetime, UTC
from decimal import Decimal
from types import MappingProxyType
from typing import Optional, Any, Mapping
from enums import (
    ConfidenceLevel,
    ErrorType,
    PDFType,
    ProcessStage,
    ProcessStatus,
    RuleCategory,
)


def _freeze_value(value: Any) -> Any:
    """Recursively freeze collections stored by immutable domain models."""
    if isinstance(value, MappingABC):
        return MappingProxyType(
            {key: _freeze_value(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(item) for item in value)
    return value


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


class AnalysisMode(Enum):
    """Enum - kết luận phân tích file PDF."""
    UNKNOWN = auto()
    DIGITAL = auto()
    SCANNED = auto()
    HYBRID = auto()


@dataclass(slots=True, frozen=True)
class Evidence:
    """Kết quả quan sát có giải thích do một heuristic rule tạo ra."""
    rule_name: str
    category: RuleCategory
    supports: Mapping[AnalysisMode, float] = field(
        default_factory=lambda: MappingProxyType({})
    )
    reason: str = ""
    warnings: tuple[str, ...] = ()
    metrics: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "supports", _freeze_value(self.supports))
        object.__setattr__(self, "warnings", _freeze_value(self.warnings))
        object.__setattr__(self, "metrics", _freeze_value(self.metrics))


@dataclass(slots=True, frozen=True)
class Confidence:
    """Mức độ chắc chắn có truy vết của một quyết định detector."""
    score: float
    level: ConfidenceLevel
    sources: Mapping[str, float] = field(
        default_factory=lambda: MappingProxyType({})
    )
    explanation: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "sources", _freeze_value(self.sources))
        object.__setattr__(self, "explanation", _freeze_value(self.explanation))


@dataclass(slots=True, frozen=True)
class PageStatistics:
    """
    Thống kê thông tin một page PDF
    Số lượng text, Số lượng image
    kích thước page ...
    """
    text_length: int
    image_count: int

    width: float
    height: float

    rotation: int

    font_count: int = 0
    text_block_count: int = 0
    drawing_count: int = 0
    annotation_count: int = 0

    @property
    def has_text(self) -> bool:
        return self.text_length > 0

    @property
    def has_images(self) -> bool:
        return self.image_count > 0


@dataclass(slots=True, frozen=True)
class PDFPage:
    """Dữ liệu text của một page PDF."""
    page_index: int
    text: str
    statistics: PageStatistics

    @property
    def has_text(self) -> bool:
        return self.statistics.has_text

    @property
    def has_images(self) -> bool:
        return self.statistics.has_images


@dataclass(slots=True, frozen=True)
class PDFDocument:
    """Dữ liệu của một file PDF."""
    path: Path
    pages: tuple[PDFPage, ...]
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        """Freeze collection fields after the reader has populated them."""
        object.__setattr__(self, "pages", tuple(self.pages))
        object.__setattr__(self, "metadata", _freeze_value(self.metadata))

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def text(self) -> str:
        return "\n\n".join(page.text for page in self.pages)

    @property
    def total_text_length(self) -> int:
        return sum(p.statistics.text_length for p in self.pages)

    @property
    def total_image_count(self) -> int:
        return sum(p.statistics.image_count for p in self.pages)

    @property
    def has_any_text(self) -> bool:
        return self.total_text_length > 0

    @property
    def has_any_images(self) -> bool:
        return self.total_image_count > 0

    @property
    def average_text_per_page(self) -> float:
        if not self.pages:
            return 0.0

        return self.total_text_length / len(self.pages)


@dataclass(slots=True, frozen=True)
class DocumentAnalysis:
    """Kết quả suy luận."""
    mode: AnalysisMode
    confidence: Confidence
    fingerprint: str = ""
    parser_name: str = ""
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    knowledge_fingerprint: str | None = None
    properties: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "reasons", _freeze_value(self.reasons))
        object.__setattr__(self, "warnings", _freeze_value(self.warnings))
        object.__setattr__(self, "evidence", _freeze_value(self.evidence))
        object.__setattr__(self, "properties", _freeze_value(self.properties))


@dataclass(slots=True)
class KnowledgeRecord:
    """Các đơn vị/thành phần suy luận."""
    fingerprint: str
    version: int
    preferred_mode: AnalysisMode
    parser_name: str
    confidence: float
    success_count: int = 0
    fail_count: int = 0

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_used_at: datetime | None = None

    properties: dict[str, Any] = field(default_factory=dict)

    @property
    def total_runs(self) -> int:
        return self.success_count + self.fail_count

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0

        return self.success_count / self.total_runs


@dataclass(slots=True, frozen=True)
class AnalysisContext:
    """Snapshot bất biến của các fact dùng trước khi suy luận."""
    total_text_length: int
    average_text_per_page: float
    total_image_count: int
    page_count: int
    empty_pages: int
    pages_with_text: int
    pages_with_images: int
    total_font_count: int = 0
    total_text_block_count: int = 0
    total_drawing_count: int = 0
    pages_with_drawings: int = 0
    rotated_pages: int = 0
    portrait_pages: int = 0
    landscape_pages: int = 0
    text_page_ratio: float = 0.0
    image_page_ratio: float = 0.0
    drawing_page_ratio: float = 0.0
    empty_page_ratio: float = 0.0
    mixed_page_ratio: float = 0.0
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_value(self.metadata))
