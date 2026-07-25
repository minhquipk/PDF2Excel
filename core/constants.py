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
