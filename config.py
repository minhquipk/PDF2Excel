"""
Cấu hình đường dẫn / thiết lập runtime của ứng dụng.
Quy ước:
- Chỉ khai báo cấu hình (đường dẫn, thiết lập).
- Không chứa Business Logic.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Thư mục chứa Template Definition (JSON) cho Parser.
TEMPLATES_DIR = BASE_DIR / "resources" / "templates"
# File mapping cột Excel Table -> field InvoiceInfo, dùng bởi ExcelWriter.
EXCEL_MAPPING_PATH = BASE_DIR / "resources" / "excel_mapping.json"
# Thư mục chứa log file (utils/logger.py).
LOG_DIR = BASE_DIR / "logs"
# Thư mục chứa report.txt (ReportWriter).
REPORTS_DIR = BASE_DIR / "reports"
# Thư mục chứa tessdata_best (vie.traineddata) cho OCREngine (Tesseract).
# Đóng gói cùng project - KHÔNG dùng tessdata mặc định của hệ điều hành
# (chất lượng thấp hơn, xem CHANGELOG.md/SESSION_SUMMARIES.md phiên OCR).
TESSDATA_DIR = BASE_DIR / "resources" / "tessdata_best"
