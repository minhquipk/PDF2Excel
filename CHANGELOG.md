# CHANGELOG.md

Ghi lại mọi thay đổi đáng chú ý của dự án, theo thứ tự thời gian, tập
trung vào các mốc kiến trúc chứ không phải từng commit Git.

File này chỉ trả lời **"cái gì đã đổi, ở file nào"**. Lý do kỹ thuật
đầy đủ nằm ở `ARCHITECTURE_DECISIONS.md` (mỗi thay đổi kiến trúc đều
kèm pointer `Xem ADR-xxx`). Bối cảnh thảo luận/phương án bị bác bỏ nằm
ở `SESSION_SUMMARIES.md`. Việc còn tồn đọng cần làm tiếp nằm ở
`PROJECT_CONTEXT.md` §14 (Known Issues) và §15 (Next Tasks) — **không**
lặp lại ở đây.

------------------------------------------------------------------------

## 2026-07 (giai đoạn đầu) — Khởi tạo dự án & Framework

### Added
- Cấu trúc project ban đầu: `constants.py`, `enums.py`, `models.py`.
- UI Framework: `base_widget.py`, `widgets.py`, `main_window.py` — Input
  Folder/Output Excel selector, Start/Stop, Report/Exit, Progress
  widget, Processing Table.
- Worker Framework: `worker.py`, tích hợp QThread, Qt Signal, Mock
  processing mode.
- `ProcessingTableModel` (MVC), hỗ trợ `clear()` trước mỗi lần Start.

### Changed
- Layout UI: Start/Stop chuyển lên trên Progress; Report/Exit chuyển
  xuống dưới Processing Table.

### Quyết định kiến trúc
→ ADR-001 đến ADR-013 (UI/Business Logic tách biệt, Worker dùng
QThread, giao tiếp qua Signal, `process()` orchestrator,
`_process_pdf()` chứa business logic, 1 PDF/lần, lưu `PDFResult` trong
bộ nhớ, ghi Excel 1 lần, `ProcessingTableModel` dùng MVC, Mock First).

### Verified
- UI khởi động đúng, Worker chạy nền không chặn UI, Mock pipeline ổn
  định, Start/Stop hoạt động đúng.

### Việc còn tồn đọng lúc này (đã giải quyết ở các mốc sau)
- Digital PDF reader, OCR reader, Regex extraction, Excel writer,
  Report exporter, ETA/Elapsed time calculation.

------------------------------------------------------------------------

## 2026-07-29 — PDF Reader & PDF Detector hoàn chỉnh

### Added
- `pdf_reader.py`: implement đầy đủ — đọc metadata + mọi trang qua
  PyMuPDF, dựng `PDFPage`/`PageStatistics`, trả `PDFDocument` bất biến.
- `enums.py`: thêm `ConfidenceLevel`, `RuleCategory`.
- `models.py`: thêm `Evidence`, `Confidence`, `AnalysisContext`,
  `KnowledgeRecord`, `DocumentAnalysis`, `AnalysisMode` (frozen
  dataclass).
- `pdf_detector.py`: implement đầy đủ reasoning engine — Build Context
  → Heuristic Evaluation (5/7 rule: Text/Image/Consistency/Quality/
  Layout) → Knowledge Lookup + Confidence Composition → Final
  Decision. Fingerprinting SHA-256.
- `worker.py`: `Worker._process_pdf()` nay gọi `PDFReader.read()` +
  `PDFDetector.analyze()` thật, thay Mock cho giai đoạn detection.
  `PDFResult.pdf_type`/`.status` dẫn xuất từ `DocumentAnalysis`.

### Quyết định kiến trúc
→ ADR-014 đến ADR-023 (Unicode tiếng Việt, Regex thuộc Parser, ranh
giới `PDFReader`, domain model bất biến, Source of Truth = source code,
Knowledge Cache, `PDFDetector` reasoning engine tất định, Confidence
decision-centric, model output bất biến, `KnowledgeRecord` read-only
khi phân tích).

### Issues Encountered (chưa giải quyết ở phiên này)
- **Rule Category coverage:** TDS §7.2 định nghĩa 7 category, mới có
  5/7 (thiếu Document, Graphics) — giải quyết tại Session 2026-08-12
  (xem ADR-057).
- **`processor.py` vs `Worker.process()`:** `core/processor.py` chỉ có
  placeholder call, vai trò orchestrator (ADR-004) thực chất do
  `Worker.process()` đảm nhiệm — giải quyết (xóa file) tại Session
  2026-08-12.
- **Nghi vấn import path:** `models.py`/`widgets.py` import thiếu
  prefix package (`core.`/`ui.`) — xác nhận không phải bug tại Session
  2026-07-31 (đối chiếu qua chạy thật).

### Validation
- Xác nhận qua source review (chưa có automated test): luồng
  `PDFDetector.analyze()` khớp đúng thứ tự TDS; các model output bất
  biến đúng; `Worker._process_pdf()` delegate đúng.

------------------------------------------------------------------------

## 2026-07-31 — Extractor (module mới)

### Added
- `models.py`: đổi tên `ExtractionResult` cũ (kết quả cấp session)
  thành `SessionResult`, giải phóng tên cho output cấp document mới
  của Extractor. Thêm `WordToken`, `PageImage`. Mở rộng `PDFPage` với
  `words` (thô) và `page_image`. Thêm `ExtractionResult` mới
  (`source_mode`, `words_by_page`, `page_images`, `warnings`).
- `constants.py`: thêm class `Image` (`DPI = 300`,
  `COLORSPACE = "gray"`).
- `pdf_reader.py`: `_read_page()` đọc thêm `page.get_text("words")`
  cho mọi trang; thêm `_render_page_image()` render grayscale mỗi
  trang.
- `extractor.py` (module mới): `Extractor.extract()` dispatch theo
  `AnalysisMode`; `_rotate_bbox()`; `_normalize_bbox()`.
- `ocr_engine.py` (module mới, Mock theo ADR-013): `OCREngine.recognize()`
  luôn trả `()`, chưa có backend thật.
- `worker.py`: `Extractor` được construct trong `__init__`;
  `_process_pdf()` gọi `extract()` (bỏ qua khi mode UNKNOWN);
  `_format_analysis_note()` đổi tên thành `_format_note()`.

### Fixed
- `pdf_reader.py::_read_pages()`: sửa kiểu trả về từ `list[PDFPage]`
  thành `tuple[PDFPage, ...]`, khớp `PDFDocument.pages`.
- `pdf_detector.py::_unique_strings()`: sửa kiểu tham số từ `object`
  thành `Iterable[str]`.

### Quyết định kiến trúc
→ ADR-024 đến ADR-028 (`Extractor` chỉ dispatch, Reader đọc thô/
Extractor chuẩn hóa hình học, render `PageImage` eager, `UNKNOWN` là
vắng mặt quyết định, rotation reconciliation thủ công).

### Known Limitations (deferred to v2.0)
- Trang có cả text layer và ảnh liên quan (con dấu, chữ ký) chỉ được
  trích từ 1 nguồn duy nhất (text-layer thắng) — nội dung ảnh bị bỏ
  qua. 3 phương án đã cân nhắc, quyết định hoãn sang v2.0 (xem
  SESSION_SUMMARIES.md, Session 2026-07-31, cho lý do chi tiết từng
  phương án).

### Issues Encountered
- Đặt tên trùng `ExtractionResult` — giải quyết bằng đổi tên class cũ
  sang `SessionResult`.
- Xác minh hành vi rotation của PyMuPDF (tài liệu chính thức +
  maintainer statement) trước khi thiết kế `_rotate_bbox()`/
  `_normalize_bbox()`.

------------------------------------------------------------------------

## 2026-08-01 / 2026-08-02 — Parser (Template Matching Engine)

### Added
- `enums.py`: thêm `ValueType`, `SpatialDirection`.
- `models.py`: `InvoiceInfo` phần lớn field chuyển `Optional`. Thêm
  `SpatialRelation`, `FieldDefinition`, `TemplateDefinition`,
  `TemplateSelection`.
- `constants.py`: thêm `Logging`, `TemplateMatching` (5 hằng số
  ngưỡng, placeholder).
- `utils/logger.py` (module mới): logger dùng chung, console handler.
- `value_converter.py` (module mới): convert TEXT/DECIMAL/DATE,
  stateless, không raise.
- `template_loader.py` (module mới): đọc/validate JSON template,
  fail-soft per file.
- `template_matcher.py` (module mới): Key Matching + Template Scoring/
  Decision + Windowing + Value Matching.
- `parser.py` (module mới): orchestrator mỏng, `parse()` trả
  `InvoiceInfo | None`.
- `config.py`: thêm `TEMPLATES_DIR`.
- `resources/templates/sample_invoice_v1.json`: template mẫu để test.

### Changed
- `extractor.py`: mở rộng sang chuẩn hóa whitespace của text token.
- `worker.py`: `__init__` khởi tạo `TemplateLoader`+`TemplateMatcher`+
  `Parser`; `_process_pdf()` gọi `Parser.parse()`.

### Quyết định kiến trúc
→ ADR-029 đến ADR-036. Xem SESSION_SUMMARIES.md, Session 2026-08-01/02
cho bối cảnh 3 lỗi thiết kế thực chất phát hiện qua thực nghiệm
(diacritics, key_tokens ngắn, value_pattern lỏng).

### Known Limitations (found during testing, deferred)
- **Value Matching chỉ lấy 1 `WordToken`** — field nhiều từ (company
  name, address) bị cắt cụt. Giải quyết tại Session 2026-08-07 (ADR-044).
- **Quy tắc vận hành (không phải bug code):** tránh `key_tokens` 1 từ
  (dễ match nhầm); `value_pattern` nên loại trừ token chỉ có dấu câu.
  Cả 2 được đưa vào `TEMPLATE_AUTHORING_GUIDE.md` (Session 2026-08-12).
- `TemplateMatching.*` (`core/constants.py`) là giá trị placeholder,
  chờ tinh chỉnh với PDF thật.
- `sample_invoice_v1.json` chủ đích giữ 2 lỗi đã biết, chờ dữ liệu
  thật thay vì sửa suy đoán.

------------------------------------------------------------------------

## 2026-08-03 — ExcelWriter / ReportWriter

### Added
- `models.py`: thêm `ExcelMapping`, `InvoiceWarning`, `ExcelWriteResult`.
- `resources/excel_mapping.json` + `config.py::EXCEL_MAPPING_PATH`.
- `excel_mapper.py` (module mới): `Mapper` — fail-fast, raise
  `MappingError`.
- `excel_writer.py` (module mới): `ExcelWriter.write()` (openpyxl); 3
  exception class (`WorkbookNotFoundError`, `ExcelTableNotFoundError`,
  `WorkbookSaveError`).
- `utils/logger.py`: thêm `FileHandler` (`logs/app.log`, UTF-8) cạnh
  console handler sẵn có.
- `report_writer.py` (module mới): `ReportWriter.write()` — 2 kênh
  output tách biệt.
- `requirements.txt` (mới ở root): pin `PySide6==6.11.1`,
  `PyMuPDF==1.28.0`, `rapidfuzz==3.14.5`, `openpyxl==3.1.5`.

### Changed
- `worker.py`: khởi tạo `ExcelWriter()`/`ReportWriter()` thật (trước
  đó placeholder `None`); thêm `report_path` property; implement
  `_write_excel()`.
- `main_window.py`: connect Signal `error`; implement lại `_report()`
  (mở file thay vì hiển thị "pending").
- `constants.py::UIText`: thêm `REPORT_NOT_AVAILABLE`,
  `REPORT_OPEN_FAILED`, `ERROR_TITLE`.

### Quyết định kiến trúc
→ ADR-037 đến ADR-041. Bối cảnh thảo luận (bác bỏ `ReportService` gộp,
làm rõ vai trò nút Report, tách 2 luồng dữ liệu report): xem
SESSION_SUMMARIES.md, Session 2026-08-03.

### Testing (phiên này)
Verify bằng script tự động trên source đã clone từ GitHub (không phải
review tĩnh): `models.py` (frozen/immutable), `excel_mapper.py` (happy
path + 5 case lỗi), `excel_writer.py` (happy path + 3/4 case lỗi —
`WorkbookSaveError` chưa tái hiện được, container chạy root), logger.py
(`FileHandler` đúng, không nhân đôi), `report_writer.py` (report.txt
ghi đè, log tích lũy đúng thiết kế lúc đó), `_write_excel()` (happy +
error path), `_report()` (4 nhánh UI), pipeline regression end-to-end
với 1 PDF thật tự tạo (không crash).

**Chưa verify phiên này:** 1 lượt chạy UI thật thủ công với PDF hóa đơn
thật (Input Folder → Start → Report) — thực hiện tại Session
2026-08-08/09.

------------------------------------------------------------------------

## 2026-08-07 — excel_mapping.json & sample_invoice_v1.json (kiểm thử trên PDF thật)

Người dùng cung cấp PDF hóa đơn thật đầu tiên (`HD2026-0003_digital.pdf`).
Toàn bộ nội dung dưới đây được verify bằng dựng lại module trong
sandbox và chạy thật, không suy đoán tĩnh.

### Added
- `resources/EXCEL_MAPPING_GUIDE.md` — hướng dẫn viết
  `excel_mapping.json` cho người điều hành không biết lập trình.
- `value_converter.py`: `_to_decimal()` strip `%` cuối chuỗi (xem
  ADR-043).
- `template_matcher.py`: `_select_best_value()` + `_merge_same_line()`
  — ghép nhiều `WordToken` cùng dòng cho field Text (xem ADR-044).
- `models.py`: `SectionDefinition` mới; `FieldDefinition` thêm field
  bắt buộc `section`; `TemplateDefinition` thêm `sections` + validate
  (xem ADR-045).
- `template_matcher.py`: `_find_key_match()` refactor dùng chung
  Field/Section; thêm `_resolve_sections()`, `_filter_phrases_by_range()`.
- `template_loader.py`: parse `sections`/`field.section` từ JSON.
- `constants.py`: thêm `TemplateMatching.SECTION_TIE_MARGIN = 10`.

### Fixed (lỗi rõ ràng, đối chiếu trực tiếp PDF thật)
- `company_name`/`invoice_number`/`invoice_date`/`total_amount`/
  `vat_rate` trong `sample_invoice_v1.json`: 5 lỗi `key_tokens`/
  `value_pattern`/`direction` sai — sửa theo nội dung PDF thật.

### Fixed (phát hiện mới qua chạy thật, không thấy được qua review tĩnh)
- `axis_tolerance` mặc định quá lớn so với khoảng cách dòng thật → hạ
  xuống `0.006`.
- `max_distance` của field tiền tệ quá nhỏ so với khoảng cách nhãn-giá
  trị thật → tăng lên `0.85`.
- Định dạng số của PDF test dùng dấu phẩy ngăn nghìn (ngược mặc định
  VN) → override `decimal_format` riêng cho template này, không đổi
  mặc định toàn cục.

### sample_invoice_v1.json — v2 → v3
- Thêm 4 field mới: `address`, `buyer_name`, `buyer_tax_code`,
  `payment_method`.
- Thêm 4 `sections`: `header`, `seller`, `buyer`, `detail`.

### Quyết định kiến trúc
→ ADR-042 đến ADR-045. Bối cảnh 3 vòng thực nghiệm (đối chiếu tĩnh →
chạy thật → phát hiện vấn đề cần sửa code) và 4 phương án Section được
cân nhắc: xem SESSION_SUMMARIES.md, Session 2026-08-07.

### Testing
Kết quả cuối: **12/12 field ra đúng giá trị** so với PDF gốc.

### Known Limitations còn lại
- Gap-based merge (ADR-044) có thể tràn field nếu nhãn liền kề không
  kết thúc bằng `:` — chưa gặp thật, giới hạn cố hữu.
- Section header (ADR-045) vẫn có thể va chạm lý thuyết.
- `SECTION_TIE_MARGIN = 10` là placeholder.
- `FieldDefinition.section` nay bắt buộc — mọi template khác thiếu
  `section` sẽ bị `TemplateLoader` skip.

------------------------------------------------------------------------

## 2026-08-07 (b) — Khắc phục crash OCREngine lúc khởi động UI

### Changed
- `ocr_engine.py` (bản PaddleOCR): chuyển sang Lazy Loading
  (`self._ocr = None`, khởi tạo qua `_get_ocr()` lần đầu `recognize()`
  được gọi).
- `constants.py`: thêm `USE_DOC_ORIENTATION_CLASSIFY = False`,
  `USE_DOC_UNWARPING = False`.

### Quyết định kiến trúc
→ ADR-046 (bối cảnh lịch sử — không còn áp dụng sau khi đổi sang
Tesseract, xem ADR-047).

### Verified
- Chạy offscreen `MainWindow()` thành công, không freeze, không crash.

------------------------------------------------------------------------

## 2026-08-08 / 2026-08-09 — OCR Engine thật (thay Mock) & lần chạy UI thật đầu tiên

### Added
- `ocr_engine.py`: implement thật bằng Tesseract 5.x + tessdata_best
  (qua `pytesseract`). Fail-fast kiểm tra `vie.traineddata`. Tự triển
  khai deskew (cv2, giữ nguyên canvas).
- `config.py`: thêm `TESSDATA_DIR`.
- `constants.py::OCR`: viết lại cho Tesseract (`LANG`, `PSM`, `OEM`,
  `DESKEW_MIN_ANGLE`, `DESKEW_MAX_ANGLE`).
- `requirements.txt`: `pytesseract==0.3.13`.
- `models.py::PageImage`: thêm field `channels: int = 3`.

### Changed
- `pdf_reader.py::_render_page_image()`: `fitz.csGRAY` → `fitz.csRGB`.
- `constants.py::Image.COLORSPACE`: `"gray"` → `"rgb"`.
- `utils/logger.py`: `app.log` đổi từ tích lũy (append) sang ghi đè
  mỗi lần chạy.
- `processing_table_model.py`: hiển thị kết quả đổi từ append sang
  **prepend** (kết quả mới nhất ở đầu bảng).
- Elapsed/ETA: hoàn thiện (trước đó "not implemented").

> Các thay đổi `logger.py`/`processing_table_model.py`/Elapsed-ETA ở
> trên được ghi nhận theo mô tả của người dùng, **chưa đối chiếu qua
> source thật** trong phiên này (đối chiếu sau, tại Session 2026-08-13
> phần review memory/dead code không phát hiện sai lệch).

### Removed (đã thử qua nhưng không còn trong source cuối)
- `ocr_engine.py` bản PaddleOCR — loại bỏ do xung đột `paddlepaddle`
  PIR (GitHub Issue #18162).
- `ocr_engine.py` bản RapidOCR — loại bỏ do chất lượng nhận dạng tiếng
  Việt kém.

### Fixed (bug phát sinh trong lúc triển khai)
- RapidOCR: `model_type` phải là `Enum` không phải string.
- RapidOCR: `onnxruntime` không phải dependency chính thức — thêm dòng
  riêng vào `requirements.txt`; hạ `1.24.4`→`1.23.2` (không có wheel
  macOS Intel).
- RapidOCR: lỗi lazy loading tự triển khai (`recognize()` gọi thẳng
  `self._ocr(...)`).
- Tesseract: `_estimate_skew_angle()` nhầm trang A4 dọc thành góc
  nghiêng ~90° → `_deskew` xoay hỏng vị trí mọi `WordToken`, khiến
  `select_template()` thất bại toàn bộ. Sửa bằng `DESKEW_MAX_ANGLE=10.0`.

### Quyết định kiến trúc
→ ADR-047 (lịch sử lựa chọn PaddleOCR → RapidOCR → Tesseract),
ADR-048 (RGB render), ADR-049 (deskew), ADR-050 (app.log). Bối cảnh 3
vòng thực nghiệm thư viện: xem SESSION_SUMMARIES.md, Session
2026-08-08/09.

### Known Issue mới (chưa sửa ở phiên này)
- `Worker._format_note()` luôn chọn warning của `text_coverage` đầu
  tiên bất kể mức liên quan — giải quyết tại Session 2026-08-12 (xem
  ADR-055).

------------------------------------------------------------------------

## 2026-08-09 / 2026-08-11 — Xử lý field tiền tệ thiếu & lỗi OCR nhầm dấu `,`/`.`

Debug tiếp nối trực tiếp từ Session 2026-08-08/09: Report.txt cho thấy
~15% data PDF Scanned thiếu 3 field tiền tệ.

### Fixed
- `value_converter.py::_to_decimal()`: xử lý hậu tố đơn vị tiền tệ VND
  dính liền chuỗi số (7 biến thể: vnd/VND/vnđ/VNĐ/₫/đ/Đ). Nới
  `value_pattern` tương ứng trong `sample_invoice_v1.json` (v3→v4).
  Xem ADR-051.
- `value_converter.py`: thêm cơ chế tự phục hồi khi OCR đọc nhầm dấu
  `,`/`.` trong chuỗi số (silent corruption). Heuristic 6 dấu hiệu cấu
  trúc chuỗi. Xem ADR-052.
- `ocr_engine.py`: thêm `_preprocess()` (CLAHE + Unsharp Mask) chạy
  sau `_deskew()`, kết hợp tăng `Image.DPI` 300→450. Xem ADR-053.

### Changed
- `constants.py`: thêm class `NumberRepair`
  (`DECIMAL_TAIL_MAX_LENGTH`); `OCR` bổ sung 4 hằng số Preprocess;
  `Image.DPI` 300 → 450.
- Đánh giá lại lý do giữ `PageImage` RGB cho phù hợp bối cảnh Tesseract
  (đổi lý do, không đổi quyết định). Xem ADR-054.

### Quyết định kiến trúc
→ ADR-051 đến ADR-054. Bối cảnh: silent corruption khó phát hiện hơn
field ra `None`; rủi ro tự tạo vấn đề mới khi sharpen (ringing
artifact) — xem SESSION_SUMMARIES.md, Session 2026-08-09/11.

### Verified
- ADR-051: PASS toàn bộ test case đang có.
- ADR-052+053 (kết hợp): tỷ lệ nhầm dấu `,`/`.` giảm xuống dưới 0.5%
  (chưa về 0%).

------------------------------------------------------------------------

## 2026-08-12 — Đóng v1, Part 1/3: Known Issues từ nhật ký

### Removed
- `core/processor.py` — xóa hoàn toàn (dead code, chưa từng được
  reference; vai trò orchestrator đã do `Worker.process()` đảm nhiệm).
- Dead code trong `constants.py`: `UIText.REPORT_PENDING`,
  `FileDialog.PDF_FILTER`, `FileDialog.ALL_FILES`,
  `UIText.READY/PROCESSING/COMPLETED/CANCELLED`, `Report.FOLDER`.
- `models.py::ExtractionResult.warnings` — hết tác dụng sau ADR-056.

### Fixed
- `extractor.py::Extractor.extract()`: nay thật sự `raise ValueError`
  khi UNKNOWN, khớp lại ADR-027 (source cũ trả về gracefully — sai
  lệch tồn tại từ Session 2026-07-31, phát hiện qua rà soát trực tiếp
  tại phiên này). Xem ADR-056.
- `Worker._format_note()`: warning hiển thị nay ưu tiên theo
  `RuleCategory` thay vì luôn lấy warning chạy đầu tiên. Xem ADR-055.

### Added
- `resources/TEMPLATE_AUTHORING_GUIDE.md`.
- `tests/core/test_extractor.py` — unit test đầu tiên của dự án (9
  case cho `_rotate_bbox()`), `requirements-dev.txt` (`pytest==8.3.4`).
- `pdf_detector.py`: 2 rule mới — `_evaluate_document_rule()`,
  `_evaluate_graphics_rule()` — đủ 7/7 Rule Category theo TDS §7.2. Xem
  ADR-057.

### Changed
- `main.py`: nay chứa `if __name__ == "__main__":` (entry point thật
  duy nhất). `ui/main_window.py`: xóa khối `__main__` tương ứng.

### Verified
- `excel_writer.py::WorkbookSaveError`: tái hiện thành công lỗi
  permission thật bằng kỹ thuật `chattr +i` (chặn được cả root, khác
  `chmod` không hiệu quả ở các lần thử trước). Verify thêm trên
  Windows thật.

### Quyết định kiến trúc
→ ADR-055, ADR-056, ADR-057. Bối cảnh: TDS không đủ chi tiết đặc tả
Document/Graphics Rule; kỹ thuật `chattr +i` vượt giới hạn container
root — xem SESSION_SUMMARIES.md, Session 2026-08-12.

------------------------------------------------------------------------

## 2026-08-13 — Đóng v1, Part 2/3: Vấn đề người dùng tự ghi nhận

### Fixed
- `ui/models/processing_table_model.py::ProcessingTableModel.data()`
  cột PDF: hiển thị `relative_path` thay vì `file_name`, tránh trùng
  tên khi Input Folder có thư mục con lồng nhau. Xem ADR-058.
- `core/export/report_writer.py::ReportWriter._log_results()`: log
  `relative_path` thay vì `file_name`. `_format_report()` mục
  Warnings: giữ nguyên full absolute path. Xem ADR-058.

### Changed
- **Tái cấu trúc toàn bộ `core/` theo pipeline stage** (`domain/`,
  `reading/`, `detection/`, `extraction/`, `parsing/` +
  `parsing/template/`, `export/`), đổi `models/` top-level thành
  `ui/models/`. Triển khai 7 bước tuần tự, verify độc lập từng bước.
  Không đổi hành vi hệ thống. Xem ADR-060.
- `tests/core/test_extractor.py` di chuyển thành
  `tests/core/extraction/test_extractor.py`.

### Verified (rà soát, không sửa code)
- Memory lifecycle: xác nhận không leak, khớp ADR-006/007. Đính chính
  số liệu chi phí `PageImage`/trang trong ADR-048 (đã lỗi thời sau
  ADR-053) — xem amend trong ARCHITECTURE_DECISIONS.md ADR-048.
- `excel_mapping.json` khai ít cột hơn `InvoiceInfo`: xác nhận hoạt
  động đúng theo thiết kế sẵn có, không cần sửa code.
- `_merge_same_line()` lookup bằng value-equality: xác nhận
  `StopIteration` không thể xảy ra; rủi ro lý thuyết còn lại vô hại.
- Confidence score tăng sau ADR-057: xác nhận là hệ quả cơ học đúng
  thiết kế, không ảnh hưởng quyết định `mode`.

### Cancelled (đã thảo luận, quyết định không triển khai)
- Đề xuất tiền xử lý ảnh OCR nâng cao (Binarization, Denoising, Border
  Removal) — hoãn sang v2.0.
- 2 hướng vá multi-line value/`max_distance` tĩnh (window động, khóa
  `direction=BELOW`) — bác bỏ, xác nhận là giới hạn kiến trúc. Xem
  ADR-059.

------------------------------------------------------------------------

## 2026-08-14 — Đóng v1, Part 3/3: Quét trực tiếp mã nguồn

### Fixed
- `core/extraction/ocr_engine.py`: kiểm tra `vie.traineddata` chuyển
  từ `__init__()` sang lazy-check lần đầu `recognize()` — trước patch,
  app crash lúc mở nếu thiếu tessdata_best, kể cả người dùng chỉ xử lý
  PDF Digital. Xem ADR-061.
- `ui/widgets.py`/`ui/main_window.py`: sửa lỗi validate input rỗng ở
  `MainWindow._start()` — `pathlib.Path` không override `__bool__`.
  Thêm `PathSelectorWidget.is_empty()`. Xem ADR-065.
- `ui/worker.py`: PDF discovery chuyển từ `Path.rglob()` (blocking,
  không hủy được giữa chừng) sang `Worker._discover_pdf_files()` bằng
  `os.walk()`, kiểm tra cờ hủy sau mỗi file. Case-insensitive khi so
  khớp `.pdf`. Xem ADR-066.

### Added
- `core/domain/models.py::TemplateDefinition.__post_init__()`:
  validate tổng `identification_weight` > 0. Xem ADR-062.
- `resources/TEMPLATE_AUTHORING_GUIDE.md`: bổ sung Mục 5.2/9 cho
  ràng buộc trên.
- `core/export/report_writer.py::ReportWriter.expected_path()` +
  `ui/worker.py::Worker.report_path` fallback kiểm tra file trên đĩa
  nếu chưa có phiên nào chạy trong lần mở app hiện tại. Xem ADR-064.
- `core/domain/constants.py`: thêm class `PDFDetection` (9 hằng số của
  `PDFDetector`) và `Currency` (4 hằng số của `ValueConverter`). Xem
  ADR-063.
- `tests/core/parsing/template/test_value_converter.py` (+ 2
  `__init__.py` rỗng): unit test thứ 2 của dự án cho `ValueConverter`.

### Removed
- `ui/worker.py::Worker.__init__`: xóa `self._ocr_reader = None` (tàn
  dư từ trước khi `Extractor`/`OCREngine` thật được wire vào).
- `core/domain/models.py::PDFResult.session_id`: field không được
  gán/đọc ở bất kỳ đâu.
- `core/domain/constants.py::Image.COLORSPACE`: constant chưa dùng tới
  (giá trị thật hard-code `fitz.csRGB` trực tiếp trong `pdf_reader.py`).
- `ui/main_window.py::_stop()`: xóa comment TODO lỗi thời.

### Quyết định kiến trúc
→ ADR-061 đến ADR-066. Phương pháp phát hiện: rà soát tĩnh trực tiếp
source (khác đa số phiên trước vốn phát hiện qua debug thực nghiệm) —
xem SESSION_SUMMARIES.md, Session 2026-08-14.

### Known Issues (ghi nhận, không sửa — xem PROJECT_CONTEXT.md §14)
- `ExcelWriter._is_total_row_present()` dùng API nội bộ `openpyxl`,
  cần re-verify nếu nâng cấp version.

------------------------------------------------------------------------

## 2026-08-15 — Mở v2.0: Multi-Threading (Bước 1-3/5)

### Added
- `core/system/hardware.py` (module mới): `get_cpu_info()` — pure
  function, tính `(total_cores, recommended_threads)` theo công thức
  MULTI_THREAD_SPECIFICATION.md §2.2.
- `tests/core/system/test_hardware.py` — 9 test case (parametrize),
  phủ ngưỡng 1/2/3/4/5/8/16/32/64/256 core + case `None`.
- `ui/widgets.py`: `ThreadSelectorWidget` (mới) — `QComboBox` chọn số
  luồng, giới hạn `[1, recommended_threads]`.
- `ui/worker.py`: `PDFTaskSignals` (QObject con, `completed`/`failed`),
  `PDFTaskRunnable` (QRunnable, đóng gói `_process_pdf()` cho 1 file).

### Changed
- `core/domain/constants.py::UIText`: thêm `THREAD_COUNT`.
- `ui/main_window.py`: tích hợp `ThreadSelectorWidget` vào layout +
  `_set_running()`; `_start()` truyền `thread_count()` vào
  `Worker.configure()`.
- `ui/worker.py::Worker`: `configure()` thêm tham số `thread_count`;
  `__init__` khởi tạo `QThreadPool` + set `OMP_THREAD_LIMIT`/
  `OMP_NUM_THREADS`; `cancel()` thêm `QThreadPool.clear()`;
  `process()` viết lại hoàn toàn — non-blocking dispatch (không còn
  vòng lặp tuần tự cũ); thêm `_on_task_completed()`,
  `_on_task_failed()`, `_advance_progress()`.

### Quyết định kiến trúc
→ ADR-067. Bối cảnh thảo luận (đổi QSpinBox→QComboBox, xung đột
ADR-008 vs đặc tả, bool vs threading.Event): xem SESSION_SUMMARIES.md,
Session 2026-08-15.

### Testing
Bước 1: `pytest -v tests/core/system/test_hardware.py` — PASS toàn bộ
(người dùng tự verify). Bước 2: chạy UI thật, verify ComboBox giới hạn
đúng, enable/disable đúng theo `_set_running()` (người dùng tự verify,
qua 2 vòng — vòng 1 QSpinBox, vòng 2 điều chỉnh QComboBox). Bước 3:
chạy thực nghiệm thật (người dùng tự verify) — chưa có báo cáo bằng số
liệu cụ thể (số luồng/tốc độ) trong phiên này.

### Còn lại theo lộ trình MULTI_THREAD_SPECIFICATION.md
Bước 4 (hoàn thiện cơ chế Stop — đã có `QThreadPool.clear()` cơ bản
trong Bước 3, chưa test riêng kịch bản Stop giữa chừng với 100 file);
Bước 5 (kiểm tra tương thích đa nền tảng + đo hiệu năng v1 vs v2).

------------------------------------------------------------------------

## 2026-08-16 — Đóng Lộ Trình Multi-Threading v2.0: Bước 4/5 & Bước 5/5

### Fixed
- `ui/worker.py`: sửa lỗi treo ứng dụng khi Stop giữa batch PDF lớn
  (rõ nhất khi Stop rơi vào chuỗi tác vụ Digital dồn dập) — `Elapsed`
  không dừng, toàn bộ UI khoá vĩnh viễn trừ Exit. Thêm signal `skipped`
  (`PDFTaskSignals`), slot `_on_task_skipped()`, set `_active_tasks`
  giữ tham chiếu Python tới `PDFTaskRunnable` đang active. → ADR-068.

### Added
- `main.py`: cấu hình `QGuiApplication.setHighDpiScaleFactorRoundingPolicy(PassThrough)`
  trước khi khởi tạo `QApplication`, cho Windows scale 125%/150%.
  → ADR-069.

### Verified
- Bước 4: chạy thật batch 600 PDF, Stop nhiều lần ở các thời điểm khác
  nhau (đặc biệt giữa chuỗi Digital) — hết treo.
- Bước 5: đối chiếu 5 nguyên tắc tương thích đa nền tảng
  (`MULTI_THREAD_SPECIFICATION.md` §5) với source — 4/5 đã tuân thủ sẵn
  (OpenMP, File Handle Windows, Path handling, UTF-8 encoding), 1/5
  (High-DPI) đã patch, **chưa verify hình ảnh thật trên Windows**.
- Đo hiệu năng `thread_count=1` vs `thread_count=2` trên batch 600 PDF
  (digital + OCR trộn), 3 lần đo mỗi cấu hình: trung bình 18 phút 37
  giây (1 luồng) → 11 phút 26 giây (2 luồng), speedup ≈ 1.63x. **Lưu ý
  thuật ngữ:** đây là so sánh `thread_count=1` (vẫn qua `QThreadPool`)
  với `thread_count=2`, KHÔNG phải so với code tuần tự v1 gốc (đã không
  còn tồn tại trong source từ ADR-067).

### Quyết định kiến trúc
→ ADR-068, ADR-069.

### Còn tồn đọng
Verify trực quan High-DPI trên Windows thật ở scale 125%/150%
(ADR-069) — chưa có xác nhận từ người dùng.

Lộ trình `MULTI_THREAD_SPECIFICATION.md` (5 bước) — **HOÀN TẤT**.