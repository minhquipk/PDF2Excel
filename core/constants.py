"""
Khai báo các hằng số dùng chung cho toàn bộ ứng dụng.
Lưu ý:
- Chỉ chứa các hằng số cấu hình.
- Không chứa Business Logic.
- Không chứa Enum.
- Không chứa Dataclass.
- Không chứa Regex.
"""


class App:
    """Thông tin ứng dụng."""
    NAME = "PDF to Excel Extractor"
    VERSION = "1.0.0"
    AUTHOR = "Nguyen Le Minh Qui"


class Window:
    """Cấu hình cửa sổ chính."""
    WIDTH = 1200
    HEIGHT = 800

    MIN_WIDTH = 1000
    MIN_HEIGHT = 700


class Table:
    """Cấu hình bảng trạng thái."""
    HEADERS = (
        "PDF",
        "TYPE",
        "STATUS",
        "NOTE",
    )

    COLUMN_WIDTH = {
        "PDF": 280,
        "TYPE": 100,
        "STATUS": 120,
        "NOTE": 500,
    }


class Logging:
    """Cấu hình logging dùng chung cho toàn bộ ứng dụng."""
    LEVEL = "INFO"
    FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    FILE_NAME = "app.log"


class FileDialog:
    """Bộ lọc File Dialog."""
    PDF_FILTER = "PDF Files (*.pdf)"
    EXCEL_FILTER = "Excel Files (*.xlsx)"
    ALL_FILES = "All Files (*.*)"


class Report:
    """Cấu hình xuất báo cáo."""
    FOLDER = "reports"
    FILE_PREFIX = "Report"
    FILE_EXTENSION = ".txt"


class Image:
    """Cấu hình render ảnh trang PDF."""
    DPI = 300
    COLORSPACE = "gray"


class Progress:
    """Cấu hình hiển thị tiến trình."""
    PERCENT_MIN = 0
    PERCENT_MAX = 100
    TIME_PLACEHOLDER = "--:--:--"


class UIText:
    """Chuỗi hiển thị trên giao diện."""
    # Window
    TITLE = App.NAME

    # Label
    INPUT_FOLDER = "Input Folder"
    OUTPUT_EXCEL = "Output Excel"
    PROGRESS = "Progress"

    # Button
    BUTTON_INPUT = "Browse..."
    BUTTON_OUTPUT = "Browse..."
    BUTTON_START = "Start"
    BUTTON_STOP = "Stop"
    BUTTON_REPORT = "Report"
    BUTTON_EXIT = "Exit"

    # Table
    TABLE_TITLE = "Processing Status"

    # Message
    READY = "Ready."
    PROCESSING = "Processing..."
    COMPLETED = "Completed."
    CANCELLED = "Cancelled."

    # Progress
    PROGRESS_GROUP = "Processing Progress"
    PROCESSED = "Processed"
    PERCENT = "Percent"
    ELAPSED = "Elapsed"
    ETA = "ETA"
    PROGRESS_COUNT_FORMAT = "{processed} / {total}"
    PROGRESS_PERCENT_FORMAT = "{percent} %"

    # Dialogs and messages
    SELECT_INPUT_FOLDER = "Select PDF Folder"
    SELECT_EXCEL_TEMPLATE = "Select Excel Template"
    WARNING_TITLE = "Warning"
    REPORT_TITLE = "Report"
    INPUT_FOLDER_REQUIRED = "Please select an input folder."
    OUTPUT_EXCEL_REQUIRED = "Please select an output Excel file."
    REPORT_PENDING = "Report feature will be implemented later."

    # Report
    REPORT_NOT_AVAILABLE = "No report has been generated yet. Please run Start first."
    REPORT_OPEN_FAILED = "Could not open the report file."
    ERROR_TITLE = "Error"


class TemplateMatching:
    """
    Cấu hình cho TemplateMatcher (Parser).
    Toàn bộ giá trị dưới đây là ước lượng ban đầu (placeholder), CẦN TINH
    CHỈNH LẠI sau khi có dữ liệu PDF hóa đơn thật. Xem SESSION_SUMMARIES.md
    - ghi chú "cần thảo luận thêm sau khi Parser chạy thử nghiệm".
    """
    # Dung sai gom WordToken vào cùng 1 "dòng" theo trục y_center (tỉ lệ
    # normalized_bbox [0.0, 1.0]). 2 token có |y_center_a - y_center_b|
    # <= LINE_Y_TOLERANCE được coi là cùng dòng.
    LINE_Y_TOLERANCE = 0.01

    # Khoảng cách ngang tối đa (tỉ lệ [0.0, 1.0]) giữa 2 token liên tiếp
    # trong cùng dòng để được gộp vào cùng 1 cụm từ (candidate phrase) khi
    # Key Matching. Gap lớn hơn ngưỡng này coi như 2 "trường" khác nhau.
    WORD_GAP_TOLERANCE = 0.02

    # Số từ tối đa trong 1 cụm Key Token sinh ra bằng sliding window.
    # VD: "tổng cộng tiền thanh toán" = 4 từ -> cần MAX_KEY_WORDS >= 4.
    MAX_KEY_WORDS = 4

    # Độ chênh lệch điểm tối thiểu giữa template hạng 1 và hạng 2 để coi là
    # "chọn được rõ ràng". Nếu chênh lệch nhỏ hơn ngưỡng này -> không xác
    # định được template (đối xứng PDFDetector._DECISION_TIE_MARGIN).
    TEMPLATE_TIE_MARGIN = 0.10

    # Điểm match_score tối thiểu để 1 template được coi là ứng viên hợp lệ,
    # kể cả khi nó dẫn đầu và không bị tie với template thứ 2.
    TEMPLATE_MIN_SCORE = 0.5
    # Độ chênh lệch ratio (thang 0-100 của rapidfuzz) tối thiểu giữa section
    # header khớp tốt nhất và tốt nhì để coi là "xác định được rõ ràng".
    # Áp dụng RIÊNG cho Section (field thường không có cơ chế này) - quyết
    # định trong phiên thảo luận Nhóm 3.1/3.2 (Section).
    SECTION_TIE_MARGIN = 10
