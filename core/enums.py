"""
Định nghĩa các kiểu Enum dùng chung cho toàn bộ ứng dụng.
Quy ước:
- Enum chỉ mô tả trạng thái hoặc kiểu dữ liệu.
- Không chứa Business Logic.
- Không chứa Dataclass.
"""

from enum import Enum


class PDFType(str, Enum):
    """Kiểu của file PDF."""
    DIGITAL = "Digital"
    OCR = "OCR"
    HYBRID = "Hybrid"


class ProcessStatus(str, Enum):
    """Trạng thái xử lý của một file PDF."""
    WAITING = "Waiting"

    PROCESSING = "Processing"

    SUCCESS = "Success"

    WARNING = "Warning"

    FAILED = "Failed"

    CANCELLED = "Cancelled"


class ProcessStage(str, Enum):
    """
    Giai đoạn đang xử lý.
    Dùng cho:
    - Log
    - Report
    - Debug
    """

    DETECT = "Detect PDF"

    READ = "Read PDF"

    OCR = "OCR"

    PARSE = "Parse"

    VALIDATE = "Validate"

    EXPORT = "Export Excel"

    COMPLETE = "Complete"


class ErrorType(str, Enum):
    """Phân loại lỗi để xuất Report."""
    PDF_READ = "PDF Read Error"

    OCR = "OCR Error"

    PARSE = "Parse Error"

    VALIDATION = "Validation Error"

    EXCEL = "Excel Error"

    UNKNOWN = "Unknown Error"


class ConfidenceLevel(str, Enum):
    """Biểu diễn ngữ nghĩa của final confidence."""
    VERY_LOW = "Very Low"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"


class RuleCategory(str, Enum):
    """Nhóm đặc trưng mà một heuristic rule đánh giá."""
    DOCUMENT = "Document"
    TEXT = "Text"
    IMAGE = "Image"
    GRAPHICS = "Graphics"
    LAYOUT = "Layout"
    CONSISTENCY = "Consistency"
    QUALITY = "Quality"
