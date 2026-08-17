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
        "PDF": 320,
        "TYPE": 100,
        "STATUS": 110,
        "NOTE": 470,
    }


class Logging:
    """Cấu hình logging dùng chung cho toàn bộ ứng dụng."""
    LEVEL = "INFO"
    FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    FILE_NAME = "app.log"


class FileDialog:
    """Bộ lọc File Dialog."""
    EXCEL_FILTER = "Excel Files (*.xlsx)"


class Report:
    """Cấu hình xuất báo cáo."""
    FILE_PREFIX = "Report"
    FILE_EXTENSION = ".txt"


class Image:
    """Cấu hình render ảnh trang PDF."""
    DPI = 450


class OCR:
    """
    Cấu hình cho OCREngine (Tesseract 5.x + tessdata_best).
    Toàn bộ giá trị dưới đây là mặc định ban đầu, CẦN TINH CHỈNH khi có
    dữ liệu PDF Scanned/Hybrid thật đa dạng hơn (đối xứng cách
    TemplateMatching đã ghi chú - xem SESSION_SUMMARIES.md, phiên OCR).
    """
    # Ngôn ngữ nhận dạng (mã ISO 639-2 theo quy ước tessdata, "vie" không
    # phải "vi"). Hard-code v1; UI cho chọn ngôn ngữ dự kiến v2 (xem
    # CHANGELOG.md, Future Improvements).
    LANG = "vie"

    # Page Segmentation Mode: 3 = Fully automatic page segmentation, không
    # giả định layout (mặc định của Tesseract) - phù hợp hoá đơn vì bố cục
    # có nhiều khối (header/bảng/chữ ký) không đồng nhất.
    PSM = 3

    # OCR Engine Mode: 3 = mặc định của Tesseract 5.x, chỉ dùng LSTM
    # (kiến trúc mà tessdata_best được huấn luyện cho) - không dùng engine
    # Legacy cũ (kém chính xác hơn nhiều, chủ yếu giữ để tương thích ngược).
    OEM = 3

    # --- Deskew (làm thẳng trang trước khi đưa vào Tesseract) ---
    # Góc nghiêng tối thiểu (độ) để coi là "nghiêng thật", tránh xoay theo
    # nhiễu đo góc khi trang gần như đã thẳng.
    DESKEW_MIN_ANGLE = 0.5
    # góc vượt ngưỡng này -> coi là artifact của thuật toán
    # (minAreaRect nhầm khung trang A4), không phải nghiêng thật -> bỏ qua
    DESKEW_MAX_ANGLE = 10.0

    # Màu nền lấp vào phần biên trống sau khi xoay (giữ nguyên kích thước
    # canvas gốc). Trắng (255) vì nền hoá đơn/tài liệu văn phòng luôn trắng.
    DESKEW_FILL_VALUE = 255

    # --- Preprocess (tăng contrast + sharpen trước khi đưa vào Tesseract,
    # chạy SAU _deskew() - xem core/ocr_engine.py::_preprocess()) ---

    # CLAHE (Contrast Limited Adaptive Histogram Equalization) - tăng
    # contrast cục bộ, tránh khuếch đại nhiễu ở vùng chi tiết nhỏ (VD
    # đuôi dấu phẩy) so với equalizeHist toàn cục.
    PREPROCESS_CLAHE_CLIP_LIMIT = 2.0
    PREPROCESS_CLAHE_TILE_GRID_SIZE = (8, 8)

    # Unsharp masking - làm sắc nét cạnh ký tự trước OCR.
    # sigmaX nhỏ (bán kính hẹp) để tránh lan halo sang vùng nét mảnh.
    PREPROCESS_SHARPEN_SIGMA = 1.0
    # amount = mức tăng cường (0.0-1.0). Bắt đầu thận trọng (0.3) vì
    # amount cao có nguy cơ tạo ringing artifact quanh nét mảnh (đuôi
    # dấu phẩy), có thể LÀM XẤU THÊM đúng vấn đề đang giải quyết thay
    # vì cải thiện - cần tăng dần qua thực nghiệm, không bắt đầu cao.
    PREPROCESS_SHARPEN_AMOUNT = 0.3

    # --- Median Denoising (Tầng 1, Global Pass) ---
    PREPROCESS_MEDIAN_KERNEL = 3

    # --- Two-Pass ROI OCR (Tầng 2, chỉ áp dụng ValueType.DECIMAL) ---
    ROI_UPSCALE_FACTOR = 2.0
    ROI_PADDING_RATIO = 0.07  # % theo chiều cao bbox - giá trị khởi điểm, xem suy diễn dưới

    # Whitelist ký tự cho Pass 2 (ROI số), theo TỪNG ngôn ngữ - khóa khớp
    # OCR.LANG (mã tessdata, "vie"/"eng"...). "vie" cần thêm đ/Đ (hậu tố
    # VNĐ, xem ValueConverter._strip_currency_suffix - ADR-051); "eng"
    # không cần vì không có hậu tố tiền tệ dạng chữ dính liền số tương tự.
    # Chuẩn bị sẵn cấu trúc cho việc chọn ngôn ngữ ở UI (v2, xem OCR.LANG).
    ROI_CHAR_WHITELIST = {
        "vie": "0123456789.,%+-đĐVND₫vnd",
        "eng": "0123456789.,%+-",
    }


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

    # Report
    REPORT_NOT_AVAILABLE = "No report has been generated yet. Please run Start first."
    REPORT_OPEN_FAILED = "Could not open the report file."
    ERROR_TITLE = "Error"

    # Thread Selector
    THREAD_COUNT = "Threads"
    THREAD_HINT_FORMAT = "Detected {cores} CPU core(s). Recommended: {recommended}."


class PDFDetection:
    """
    Cấu hình ngưỡng/trọng số cho PDFDetector (Reasoning Engine).
    Toàn bộ giá trị dưới đây là ước lượng ban đầu dựa trên
    PDF_Detector_Technical_Design.docx và thực nghiệm ban đầu (Session
    2026-07-29), CẦN TINH CHỈNH khi có thêm dữ liệu PDF thật đa dạng hơn
    - cùng nhóm "placeholder cần tinh chỉnh" với TemplateMatching.*/OCR.*.
    """
    # --- Ngưỡng quyết định DIGITAL (rule text_coverage) ---
    DIGITAL_TEXT_PAGE_RATIO = 0.80
    DIGITAL_AVERAGE_TEXT_LENGTH = 20

    # --- Ngưỡng quyết định HYBRID (rule mixed_content) ---
    HYBRID_CONTENT_PAGE_RATIO = 0.25

    # --- Ngưỡng cảnh báo chất lượng tài liệu (rule content_coverage) ---
    HIGH_EMPTY_PAGE_RATIO = 0.25

    # --- Quyết định cuối (_decide_mode) ---
    DECISION_TIE_MARGIN = 0.10

    # --- Confidence Composition (_compose_confidence) ---
    EVIDENCE_SCORE_SCALE = 1.40

    # --- Document Rule / Graphics Rule (ADR-057, RC-001/RC-004) ---
    # CHƯA qua thực nghiệm với dữ liệu thật (khác các ngưỡng phía trên đã
    # verify trên PDF thật) - weight cố ý đặt thấp để không làm lệch các
    # quyết định biên đã ổn định.
    DOCUMENT_RULE_WEIGHT = 0.20
    GRAPHICS_RULE_WEIGHT = 0.20
    GRAPHICS_DRAWING_PAGE_RATIO = 0.50


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


class Currency:
    """
    Cấu hình cho ValueConverter._to_decimal()/_strip_currency_suffix()
    (ADR-051). Định dạng số mặc định theo quy ước Việt Nam; danh sách
    hậu tố VND chia 2 nhóm theo mức rủi ro strip nhầm - xem ADR-051.
    """
    # Định dạng số mặc định khi FieldDefinition.decimal_format không khai
    # báo. Khớp quy ước phân cách số của hóa đơn Việt Nam (ADR-014).
    DEFAULT_THOUSAND_SEPARATOR = "."
    DEFAULT_DECIMAL_SEPARATOR = ","

    # Hậu tố đơn vị tiền tệ VND — strip vô điều kiện trước khi parse
    # Decimal (ADR-051). Biến thể ≥2 ký tự hoặc ký tự Unicode riêng biệt
    # (₫) không thể là 1 phần hợp lệ khác của số Decimal -> an toàn để
    # strip không điều kiện.
    SUFFIXES = ("vnd", "vnđ", "₫")

    # Biến thể 1 ký tự ('đ'/'Đ') CẦN ràng buộc vị trí riêng (chỉ strip
    # khi liền sau chữ số) - khác SUFFIXES vì 1 ký tự chữ đơn lẻ có rủi
    # ro trùng nội dung khác cao hơn nhiều so với chuỗi 2+ ký tự.
    SINGLE_CHAR_SUFFIXES = ("đ", "Đ")


class NumberRepair:
    """
    Cấu hình cho ValueConverter._normalize_number_separators() (fallback
    heuristic khi OCR nhầm lẫn dấu ',' và '.' trong chuỗi số). Giá trị
    ban đầu là ước lượng, dự kiến cho phép người dùng tuỳ chỉnh theo loại
    hóa đơn ở version sau.
    """
    DECIMAL_TAIL_MAX_LENGTH = 3
