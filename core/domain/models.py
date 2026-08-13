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
from dataclasses import dataclass, field, fields
from datetime import date, datetime, UTC
from decimal import Decimal
from types import MappingProxyType
from typing import Optional, Any, Mapping
from core.domain.enums import (
    ConfidenceLevel,
    ErrorType,
    PDFType,
    ProcessStage,
    ProcessStatus,
    RuleCategory,
    SpatialDirection,
    ValueType,
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


@dataclass(slots=True)
class InvoiceInfo:
    """Thông tin trích xuất từ một hóa đơn PDF."""
    source_file: str

    company_name: Optional[str] = None
    tax_code: Optional[str] = None
    address: Optional[str] = None

    buyer_name: Optional[str] = None
    buyer_tax_code: Optional[str] = None

    payment_method: Optional[str] = None

    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None

    subtotal: Optional[Decimal] = None
    vat_rate: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None


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


@dataclass(slots=True)
class ProcessError:
    """Mô tả một lỗi phát sinh trong quá trình xử lý."""
    pdf_name: str
    stage: ProcessStage
    error_type: ErrorType
    message: str


@dataclass(slots=True)
class SessionResult:
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
class WordToken:
    """Một từ đã được chuẩn hoá bởi Extractor, kèm vị trí hình học."""
    text: str
    normalized_bbox: tuple[float, float, float, float]  # x_min, y_min, x_max, y_max — miền [0.0, 1.0]
    confidence: float | None = None   # None cho nguồn Digital; có giá trị khi nguồn là OCR
    source: str = "digital"           # "digital" | "ocr"


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
class PageImage:
    """Raw grayscale pixmap của một trang PDF đã được render, tự mô tả."""
    samples: bytes   # raw grayscale bytes, 1 byte/pixel, row-major
    width: int        # pixel width
    height: int        # pixel height
    dpi: int            # DPI dùng khi render — có thể truy vết
    channels: int = 3  # số kênh màu mỗi pixel: 1 = grayscale, 3 = RGB


@dataclass(slots=True, frozen=True)
class PDFPage:
    """Dữ liệu text của một page PDF."""
    page_index: int
    text: str
    statistics: PageStatistics
    words: tuple[tuple[float, float, float, float, str, int, int, int], ...] = ()
    page_image: PageImage | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "words", tuple(self.words))

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


@dataclass(slots=True, frozen=True)
class ExtractionResult:
    """Kết quả trích xuất của Extractor cho một PDFDocument, sẵn sàng cho Parser."""
    source_mode: AnalysisMode
    words_by_page: Mapping[int, tuple[WordToken, ...]]
    page_images: Mapping[int, PageImage] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "words_by_page", _freeze_value(self.words_by_page))
        object.__setattr__(self, "page_images", _freeze_value(self.page_images))


@dataclass(slots=True, frozen=True)
class SpatialRelation:
    """Quan hệ không gian giữa Key Token và Value cần tìm."""
    direction: SpatialDirection
    max_distance: float    # Khoảng cách tối đa theo trục chính, tỉ lệ [0.0, 1.0]
    axis_tolerance: float  # Dung sai theo trục vuông góc, tỉ lệ [0.0, 1.0]


@dataclass(slots=True, frozen=True)
class SectionDefinition:
    """
    Định nghĩa 1 khối (section) trong tài liệu - dùng để giới hạn phạm vi
    Key Matching của field, giải quyết va chạm key_tokens giữa các khối
    khác nhau (VD: 'Mã số thuế' của bên bán vs bên mua - Known Limitation
    3.1/3.2, xem ARCHITECTURE_DECISIONS.md ADR mới).
    key_tokens=None đại diện 1 khối "ảo" bắt đầu từ đỉnh trang đầu tiên
    (không cần marker thật) - dùng cho phần đầu tài liệu chưa có section
    header rõ ràng (VD: số/ngày hóa đơn trước khối "ĐƠN VỊ BÁN HÀNG").
    """
    section_id: str
    key_tokens: tuple[str, ...] | None = None
    fuzzy_threshold: int = 85

    def __post_init__(self) -> None:
        if self.key_tokens is not None:
            object.__setattr__(self, "key_tokens", _freeze_value(self.key_tokens))


@dataclass(slots=True, frozen=True)
class FieldDefinition:
    """Định nghĩa cách trích một field của InvoiceInfo từ WordToken."""
    field_name: str
    section: str
    value_type: ValueType
    identification_weight: float
    key_tokens: tuple[str, ...]
    fuzzy_threshold: int
    spatial_relation: SpatialRelation
    value_pattern: str
    date_format: str | None = None
    decimal_format: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        valid_field_names = {f.name for f in fields(InvoiceInfo)}
        if self.field_name not in valid_field_names:
            raise ValueError(
                f"field_name '{self.field_name}' không khớp với bất kỳ field nào "
                f"của InvoiceInfo. Các field hợp lệ: {sorted(valid_field_names)}."
            )

        object.__setattr__(self, "key_tokens", _freeze_value(self.key_tokens))
        if self.decimal_format is not None:
            object.__setattr__(self, "decimal_format", _freeze_value(self.decimal_format))


@dataclass(slots=True, frozen=True)
class TemplateDefinition:
    template_id: str
    version: int
    description: str
    fields: tuple[FieldDefinition, ...]
    sections: tuple[SectionDefinition, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "fields", _freeze_value(self.fields))
        object.__setattr__(self, "sections", _freeze_value(self.sections))

        valid_section_ids = {s.section_id for s in self.sections}
        for field_def in self.fields:
            if field_def.section not in valid_section_ids:
                raise ValueError(
                    f"Field '{field_def.field_name}' khai section='{field_def.section}' "
                    f"không tồn tại trong 'sections' của template '{self.template_id}'. "
                    f"Section hợp lệ: {sorted(valid_section_ids)}."
                )


@dataclass(slots=True, frozen=True)
class TemplateSelection:
    """
    Kết quả select_template(): template thắng kèm vị trí Key Token đã match.
    matched_keys: field_name -> (page_index, WordToken). Giữ cả page_index vì
    normalized_bbox chỉ có ý nghĩa trong phạm vi một trang; extract_fields()
    cần page_index để biết quét words_by_page[page_index] nào khi Windowing,
    tránh phải quét lại toàn bộ WordToken lần thứ hai.
    """
    template: TemplateDefinition
    score: float
    matched_keys: Mapping[str, tuple[int, WordToken]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "matched_keys", _freeze_value(self.matched_keys))


@dataclass(slots=True, frozen=True)
class ExcelMapping:
    """Ánh xạ cột Excel Table -> field của InvoiceInfo, đọc từ mapping.json."""
    table: str
    columns: Mapping[str, str]  # tên cột Excel -> field_name của InvoiceInfo

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", _freeze_value(self.columns))


@dataclass(slots=True, frozen=True)
class InvoiceWarning:
    """Một field InvoiceInfo bị None tại thời điểm ExcelWriter ghi dữ liệu."""
    source_file: str
    field_name: str


@dataclass(slots=True, frozen=True)
class ExcelWriteResult:
    """
    Kết quả có cấu trúc của một lượt ExcelWriter.write().
    Dữ liệu thuần (ADR-006) - ExcelWriter không tự ghi report.txt hay log,
    chỉ trả về đối tượng này để ReportWriter tiêu thụ.
    """
    total: int
    written: int
    warnings: tuple[InvoiceWarning, ...] = ()
    errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "warnings", _freeze_value(self.warnings))
        object.__setattr__(self, "errors", _freeze_value(self.errors))
