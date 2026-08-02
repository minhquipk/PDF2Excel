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
