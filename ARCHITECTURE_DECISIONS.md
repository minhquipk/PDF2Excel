# ARCHITECTURE_DECISIONS.md

# Architecture Decision Records (ADR)

File này ghi lại các quyết định kiến trúc đã được chốt (Accepted). Mọi
thay đổi đối với các quyết định này cần được thảo luận trước khi triển
khai (xem DEVELOPMENT_WORKFLOW.md, Rule 1/11).

Bối cảnh thảo luận dẫn tới từng quyết định (phương án bị bác bỏ, lý do
tranh luận, diễn biến) nằm ở `SESSION_SUMMARIES.md` — file này chỉ ghi
quyết định cuối cùng và lý do kỹ thuật của nó.

------------------------------------------------------------------------

## Bảng Tra Cứu ADR

| ADR | Chủ đề | Trạng thái |
|-----|--------|------------|
| ADR-001 | Tách biệt UI và Business Logic | Accepted |
| ADR-002 | Worker chạy trong QThread riêng | Accepted |
| ADR-003 | Giao tiếp qua Qt Signals | Accepted |
| ADR-004 | `process()` là orchestrator | Accepted |
| ADR-005 | Business logic nằm trong `_process_pdf()` | Accepted |
| ADR-006 | Xử lý 1 PDF tại 1 thời điểm | Accepted |
| ADR-007 | Chỉ giữ lại structured data (`PDFResult`) trong bộ nhớ | Accepted |
| ADR-008 | Ghi Excel đúng 1 lần | Accepted |
| ADR-009 | Trách nhiệm của `InvoiceInfo` | Accepted |
| ADR-010 | Trách nhiệm của `PDFResult` | Accepted |
| ADR-011 | `ProcessingTableModel` dùng `QAbstractTableModel` | Accepted |
| ADR-012 | Phát triển tăng dần (incremental) | Accepted |
| ADR-013 | Mock First — mock trước, code thật sau | Accepted |
| ADR-014 | Bảo toàn dữ liệu tiếng Việt (Unicode) | Accepted |
| ADR-015 | Regex thuộc về Parser, không thuộc Worker | Accepted |
| ADR-016 | Ranh giới trách nhiệm của `PDFReader` | Accepted |
| ADR-017 | Domain model bất biến (frozen) | Accepted |
| ADR-018 | Source code là tham chiếu implementation duy nhất | Accepted |
| ADR-019 | Chiến lược Knowledge Cache | Accepted |
| ADR-020 | `PDFDetector` là reasoning engine tất định (deterministic) | Accepted |
| ADR-021 | Confidence lấy quyết định làm trung tâm, dẫn xuất từ Evidence | Accepted |
| ADR-022 | Các model output của Analysis là bất biến (frozen) | Accepted |
| ADR-023 | `KnowledgeRecord` mutable ở tầng lưu trữ, read-only khi phân tích | Accepted |
| ADR-024 | `Extractor` chỉ dispatch theo mode, không tự quyết định | Accepted |
| ADR-025 | Reader đọc thô, Extractor chuẩn hóa (mở rộng sang hình học) | Accepted |
| ADR-026 | Render `PageImage` grayscale, eager, cho mọi trang | Accepted (amended by ADR-048) |
| ADR-027 | `UNKNOWN` là sự vắng mặt quyết định, không phải 1 case cần xử lý | Accepted |
| ADR-028 | Rotation reconciliation tính thủ công, không qua `fitz.Page` | Accepted |
| ADR-029 | Parser = orchestrator mỏng + TemplateMatcher engine tách biệt | Accepted |
| ADR-030 | Chọn Template bằng Evidence-Weighted Scoring | Accepted |
| ADR-031 | Template Definition lưu dạng JSON ngoài, fail-soft per file | Accepted |
| ADR-032 | Field của `InvoiceInfo` là Optional; convert lỗi → `None` | Accepted |
| ADR-033 | Gap ở cấp invoice là vấn đề của Report, không phải của Worker status | Accepted |
| ADR-034 | `TemplateSelection` giữ kèm `page_index` cùng matched key | Accepted |
| ADR-035 | Bắt buộc chuẩn hóa dấu tiếng Việt trước fuzzy Key Matching | Accepted |
| ADR-036 | Extractor cũng chuẩn hóa whitespace của text (không chỉ hình học) | Accepted |
| ADR-037 | `ExcelWriter`/`ReportWriter` là 2 module tách biệt, không gộp `ReportService` | Accepted |
| ADR-038 | Excel Mapping load fail-fast (khác Template fail-soft) | Accepted |
| ADR-039 | Cột Excel không khớp là lỗi soft-fail theo từng cột | Accepted |
| ADR-040 | `ReportWriter` có 2 kênh output tách biệt hoàn toàn | Accepted (amended by ADR-050) |
| ADR-041 | Nút Report chỉ mở file đã sinh sẵn, không tự trigger sinh report | Accepted (amended by ADR-064) |
| ADR-042 | Excel Mapping giữ nguyên `table` + `columns`, không thêm `sheet` | Accepted |
| ADR-043 | `ValueConverter` bỏ ký hiệu `%` cuối chuỗi trước khi convert Decimal | Accepted |
| ADR-044 | Value Matching ghép nhiều từ bằng gap-based line clustering | Accepted |
| ADR-045 | Section-Scoped Key Matching — giải quyết va chạm `key_tokens` giữa các khối | Accepted |
| ADR-046 | Lazy Loading OCREngine (PaddleOCR) & tắt tiền xử lý phụ của PaddleX | Accepted (bối cảnh lịch sử — không còn áp dụng sau ADR-047) |
| ADR-047 | Chốt OCR Engine: Tesseract 5.x + tessdata_best | Accepted (amended by ADR-061) |
| ADR-048 | `PageImage` render RGB thay vì Grayscale | Accepted (amends ADR-026; amended by ADR-054) |
| ADR-049 | Deskew: giữ nguyên canvas + ngưỡng chặn góc giả `DESKEW_MAX_ANGLE` | Accepted |
| ADR-050 | `app.log` ghi đè mỗi lần chạy (thay vì tích lũy) | Accepted (amends ADR-040) |
| ADR-051 | `ValueConverter` strip hậu tố đơn vị tiền tệ VND | Accepted |
| ADR-052 | `ValueConverter` tự phục hồi số bị OCR nhầm lẫn dấu `,`/`.` | Accepted |
| ADR-053 | OCR: tăng DPI 300→450 & thêm bước Preprocess (CLAHE + Sharpen) | Accepted |
| ADR-054 | Amend ADR-048: lý do giữ RGB đổi sang tính bất khả nghịch của chuyển đổi | Accepted (amends ADR-048) |
| ADR-055 | Thứ tự ưu tiên hiển thị warning theo `RuleCategory` | Accepted |
| ADR-056 | `Extractor.extract()` raise `ValueError` khi UNKNOWN (sửa code khớp ADR-027) | Accepted |
| ADR-057 | Bổ sung Document Rules & Graphics Rules cho `PDFDetector` (đủ 7/7 category) | Accepted |
| ADR-058 | Hiển thị `relative_path` thay vì `file_name` để tránh trùng tên | Accepted |
| ADR-059 | Giới hạn kiến trúc của TemplateMatcher với giá trị đa dòng — không patch ở v1 | Accepted |
| ADR-060 | Tái cấu trúc `core/` theo pipeline stage; `ui/models/` thay `models/` | Accepted |
| ADR-061 | OCREngine: kiểm tra tessdata_best trì hoãn đến lần đầu `recognize()` | Accepted (amends ADR-047) |
| ADR-062 | `TemplateDefinition` validate tổng `identification_weight` > 0 | Accepted |
| ADR-063 | Tập trung hằng số threshold của `PDFDetector`/`ValueConverter` vào `constants.py` | Accepted |
| ADR-064 | `Worker.report_path` fallback về `report.txt` trên đĩa | Accepted (amends ADR-041) |
| ADR-065 | Sửa lỗi validate input rỗng (`Path()` truthiness bug) | Accepted |
| ADR-066 | PDF Discovery chuyển sang `os.walk()` — cancellable + case-insensitive | Accepted |
| ADR-067 | Worker v2.0: xử lý đa luồng qua QThreadPool, mô hình event-driven | Accepted |
| ADR-068 | Sửa lỗi treo khi Stop batch lớn — đảm bảo mọi `PDFTaskRunnable.run()` luôn emit đúng 1 signal | Accepted |
| ADR-069 | High-DPI Scaling Policy — `PassThrough` cho Windows scale lẻ (125%/150%) | Accepted |
| ADR-070 | Two-Pass ROI OCR cho field DECIMAL nguồn OCR (`TemplateMatcher` tự sở hữu `OCREngine`) | Accepted |
| ADR-071 | Validate `roi_text` theo `value_pattern` trước khi chấp nhận Pass 2 | Accepted |
| ADR-072 | `recognize_numeric_roi()` phải deskew trước khi crop | Accepted |
| ADR-073 | ROI padding tính theo tỉ lệ chiều cao bbox (`ROI_PADDING_RATIO`), không theo kích thước trang | Accepted (đang tinh chỉnh giá trị) |
| ADR-074 | Bác bỏ cấu hình tắt DAWG/`textord_heavy_nr` cho Global Pass (Mục 4.1.C spec) | Accepted |
| ADR-075 | Cô lập 3 giai đoạn cải thiện OCR khi thực nghiệm | Accepted |
| ADR-076 | Pass 1 dùng `vie`/tessdata_best; Pass 2 dùng `eng`/tessdata_fast + PSM=8 | Accepted |
| ADR-077 | ROI Preprocess riêng cho Pass 2 (`_apply_clahe_sharpen` dùng chung + `ROI_PREPROCESS_*`) — chốt tham số qua thực nghiệm 103 PDF/412 field | Accepted (điều kiện: `INTER_CUBIC`, `ROI_UPSCALE_FACTOR=1.5` — xem Known Issues nếu source chưa khớp) |
| ADR-078 | Hoãn xây `ROI_UPSCALE_FACTOR = f(bbox.height)`; giữ hằng số `1.5` cho đến khi có bộ PDF đa dạng font hơn | Accepted (deferred) |

------------------------------------------------------------------------

## ADR-001 --- Tách Biệt UI và Business Logic

**Status:** Accepted

- UI chỉ chịu trách nhiệm tương tác với người dùng.
- Business logic không bao giờ được cài đặt bên trong các class UI.
- `MainWindow` chỉ đóng vai trò điều phối (coordinate).

------------------------------------------------------------------------

## ADR-002 --- Worker Chạy Trong QThread Riêng

**Status:** Accepted

- Mọi tác vụ chạy lâu đều thực thi bên trong `Worker`.
- `Worker` luôn chạy trong 1 `QThread` riêng biệt.
- UI thread phải luôn phản hồi (responsive).

------------------------------------------------------------------------

## ADR-003 --- Giao Tiếp Qua Qt Signals

**Status:** Accepted

`Worker` không bao giờ cập nhật widget trực tiếp.

Các Signal gồm:
- `started`
- `progress`
- `file_processed`
- `finished`
- `cancelled`
- `error`

------------------------------------------------------------------------

## ADR-004 --- `process()` Là Orchestrator

**Status:** Accepted

`process()` chỉ điều khiển luồng chạy (workflow), không được chứa:
- PDF parsing
- OCR
- Regex
- Logic ghi Excel

Trách nhiệm của nó:
1. Duyệt qua các PDF
2. Gọi `_process_pdf()`
3. Lưu `PDFResult`
4. Emit progress
5. Ghi Excel đúng 1 lần

**Ghi chú (2026-07-29):** vai trò orchestrator này hiện do
`Worker.process()` (`ui/worker.py`) đảm nhiệm. Mối quan hệ giữa ADR
này và `core/processor.py` (khi đó còn là placeholder) từng là câu hỏi
mở — đã đóng tại Session 2026-08-12 (`core/processor.py` bị xóa, xem
CHANGELOG.md 2026-08-12).

------------------------------------------------------------------------

## ADR-005 --- Business Logic Nằm Trong `_process_pdf()`

**Status:** Accepted

Toàn bộ xử lý tài liệu thuộc về `_process_pdf()` hoặc các module chuyên
biệt được gọi từ đó.

------------------------------------------------------------------------

## ADR-006 --- Xử Lý 1 PDF Tại 1 Thời Điểm

**Status:** Accepted

Chỉ 1 PDF được xử lý tại bất kỳ thời điểm nào.

Lý do: bộ nhớ thấp, debug đơn giản hơn, workflow ổn định.

------------------------------------------------------------------------

## ADR-007 --- Chỉ Giữ Lại Structured Data

**Status:** Accepted

Giải phóng tài nguyên PDF ngay sau khi parse xong. Chỉ giữ lại object
`PDFResult` trong bộ nhớ.

------------------------------------------------------------------------

## ADR-008 --- Ghi Excel Đúng 1 Lần

**Status:** Accepted

Output Excel chỉ được ghi sau khi MỌI PDF đã được xử lý xong. Không bao
giờ ghi từng dòng trong lúc đang xử lý.

------------------------------------------------------------------------

## ADR-009 --- Trách Nhiệm Của `InvoiceInfo`

**Status:** Accepted

`InvoiceInfo` chỉ chứa các field của hóa đơn. Không chứa processing
state hay thông tin UI.

------------------------------------------------------------------------

## ADR-010 --- Trách Nhiệm Của `PDFResult`

**Status:** Accepted

`PDFResult` gộp chung:
- Metadata của PDF
- Trạng thái xử lý (status)
- Ghi chú (notes)
- `InvoiceInfo`

------------------------------------------------------------------------

## ADR-011 --- `ProcessingTableModel`

**Status:** Accepted

Dùng `QAbstractTableModel`. Không thao tác trực tiếp trên `QTableWidget`.

------------------------------------------------------------------------

## ADR-012 --- Phát Triển Tăng Dần (Incremental)

**Status:** Accepted

Implement 1 tính năng nhỏ → Compile → Run → Verify → tiếp tục.

------------------------------------------------------------------------

## ADR-013 --- Mock First

**Status:** Accepted

Trước khi implement 1 module thật:
- Tạo Mock
- Validate UI
- Validate Worker
- Validate Signals

Sau đó mới thay Mock bằng code sản xuất (production code).

**Ghi chú (2026-07-29):** đã áp dụng đúng trình tự cho PDFReader/
PDFDetector → Extractor → Parser → ExcelWriter/ReportWriter → OCREngine
(mỗi module Mock trước, code thật sau, xem CHANGELOG.md theo từng mốc
tương ứng). Tính đến Session 2026-08-14, toàn bộ pipeline đã là code
thật, không còn module nào ở trạng thái Mock.

------------------------------------------------------------------------

## ADR-014 --- Dữ Liệu Tiếng Việt

**Status:** Accepted

Hệ thống phải bảo toàn văn bản Unicode tiếng Việt xuyên suốt toàn bộ
pipeline.

------------------------------------------------------------------------

## ADR-015 --- Regular Expressions

**Status:** Accepted

Regex parsing thuộc về 1 module parser riêng biệt. `Worker` không được
chứa regex pattern.

------------------------------------------------------------------------

## ADR-016 --- Ranh Giới Trách Nhiệm Của `PDFReader`

**Status:** Accepted

`PDFReader` chỉ chuyển đổi object PyMuPDF thành domain model. Không có
business logic, không có parser, không có OCR.

Xác nhận trong implementation: `core/reading/pdf_reader.py`.

------------------------------------------------------------------------

## ADR-017 --- Domain Model Bất Biến (Frozen)

**Status:** Accepted

Implementation phải tuân theo các domain model bất biến (frozen).
Implementation không bao giờ thay đổi model trong lúc phát triển.

------------------------------------------------------------------------

## ADR-018 --- Source Code Là Tham Chiếu Implementation

**Status:** Accepted

Quyết định implementation dựa trên source code hiện tại. Lịch sử chat
không phải nguồn tham chiếu chính thức.

------------------------------------------------------------------------

## ADR-019 --- Chiến Lược Knowledge Cache

**Status:** Accepted

Phân tích tài liệu trong tương lai sẽ xây dựng 1 knowledge cache tái sử
dụng được. Machine learning bị loại trừ có chủ đích. Knowledge tăng
trưởng tất định (deterministic) từ các tài liệu đã xử lý.

**Ghi chú (2026-07-29):** domain model `KnowledgeRecord` đã tồn tại
(`core/domain/models.py`) và `PDFDetector` tham vấn nó theo dạng
read-only trong lúc phân tích (xem ADR-023). Việc lưu trữ/lifecycle/
governance của knowledge cache (TDS Chapter 9) chưa được implement
tính đến cuối v1 (xem PROJECT_CONTEXT.md §14).

------------------------------------------------------------------------

## ADR-020 --- `PDFDetector` Là Reasoning Engine Tất Định

**Status:** Accepted

`PDFDetector` được implement như 1 reasoning engine theo từng giai
đoạn, tất định (deterministic), theo `PDF_Detector_Technical_Design.docx`:

1. Build Context — chuyển `PDFDocument` thành `AnalysisContext` bất
   biến (chỉ số liệu thô + dẫn xuất, không đánh giá).
2. Heuristic Evaluation — các rule độc lập, stateless, chỉ đọc
   `AnalysisContext` và sinh ra `Evidence`. Rule không bao giờ tự
   quyết định mode cuối.
3. Knowledge Lookup — `KnowledgeRecord` (tùy chọn) được tham vấn sau
   khi Evidence đã hình thành; không bao giờ mutate hay ghi đè Evidence.
4. Confidence Composition — kết hợp các nguồn confidence độc lập
   (evidence strength, consistency, coverage, và tùy chọn knowledge)
   thành 1 `Confidence` duy nhất.
5. Final Decision — tạo ra 1 `DocumentAnalysis` bất biến duy nhất.

Không dùng machine learning hay bất kỳ suy luận non-explainable nào
trong detector (nhất quán với ADR-019).

Xác nhận trong implementation: `core/detection/pdf_detector.py`.

------------------------------------------------------------------------

## ADR-021 --- Confidence Lấy Quyết Định Làm Trung Tâm

**Status:** Accepted

Confidence do `PDFDetector` sinh ra:
- Là thuộc tính của quyết định (`DocumentAnalysis`), không phải của
  bản thân PDF.
- Luôn được dẫn xuất từ `Evidence` đã thu thập và, tùy chọn,
  `KnowledgeRecord` — không bao giờ gán giá trị cố định/tùy tiện.
- Được phân rã thành các nguồn độc lập, giải thích được (evidence
  strength, consistency, coverage, knowledge) trước khi tổng hợp
  thành 1 điểm số và map sang `ConfidenceLevel`.

Xác nhận trong implementation: `PDFDetector._compose_confidence()`,
`core/domain/enums.py::ConfidenceLevel`.

------------------------------------------------------------------------

## ADR-022 --- Bất Biến Của Các Model Output Phân Tích

**Status:** Accepted

`Evidence`, `Confidence`, `AnalysisContext`, và `DocumentAnalysis` được
implement như frozen dataclass. Collection lồng nhau (dict, list, set)
được đóng băng đệ quy (`MappingProxyType`, `tuple`, `frozenset`) khi
construct.

Lý do: đảm bảo không giai đoạn nào của reasoning pipeline — hay bất kỳ
subsystem downstream nào tiêu thụ `DocumentAnalysis` — có thể mutate dữ
liệu quan sát hoặc 1 quyết định đã hoàn tất, thỏa mục tiêu Determinism
và Explainability (TDS §1.3 G1/G2, §2 DP-004/DP-005).

`KnowledgeRecord` chủ đích **không** frozen (xem ADR-023).

Xác nhận trong implementation: `core/domain/models.py`.

------------------------------------------------------------------------

## ADR-023 --- `KnowledgeRecord` Mutable Ở Tầng Lưu Trữ, Read-Only Khi Phân Tích

**Status:** Accepted

`KnowledgeRecord` là mutable dataclass ở tầng lưu trữ/lifecycle (nội
dung được kỳ vọng tiến hóa theo thời gian, theo ADR-019), nhưng
`PDFDetector` coi nó là input read-only nghiêm ngặt trong 1 lần gọi
`analyze()`: không bao giờ tạo/cập nhật/xóa bởi detector, và fingerprint
không khớp sẽ tạo warning thay vì bị bỏ qua âm thầm hoặc ghi đè Evidence.

Xác nhận trong implementation: `PDFDetector._compose_confidence()`.

------------------------------------------------------------------------

## ADR-024 --- `Extractor` Chỉ Dispatch, Không Tự Quyết Định

**Status:** Accepted

`Extractor` nhận 1 `DocumentAnalysis` đã hoàn tất và dispatch chiến
lược extraction thuần túy dựa trên `analysis.mode`. Không bao giờ tự
đánh giá lại loại tài liệu (TDS §3.1: "quyết định chỉ được đưa ra 1
lần và tái sử dụng ở downstream").

Quy tắc dispatch:
- `DIGITAL` — trích từ `page.words` (text layer).
- `SCANNED` — trích qua `OCREngine`.
- `HYBRID` — quyết định theo từng trang (`page.has_text` → path
  Digital, ngược lại → path OCR). Xem ADR-029 (SESSION_SUMMARIES.md,
  Session 2026-07-31) cho giới hạn đã biết của cách này.
- `UNKNOWN` — không phải input hợp lệ; xem ADR-027.

Xác nhận trong implementation: `core/extraction/extractor.py::Extractor.extract()`.

------------------------------------------------------------------------

## ADR-025 --- Reader Đọc Thô, Extractor Chuẩn Hóa (Mở Rộng Sang Hình Học)

**Status:** Accepted

Mở rộng sự tách biệt Reader/Detector đã có (ADR-016) sang dữ liệu hình
học: `PDFReader` lưu `PDFPage.words` là tuple từ PyMuPDF thô, không
chỉnh sửa (`(x0, y0, x1, y1, text, block_no, line_no, word_no)`), không
chuẩn hóa tọa độ, không sửa rotation, không biến đổi cấu trúc.

`Extractor` là component **duy nhất** chuyển hình học thô thành
`WordToken` ở tầng domain (`normalized_bbox` trong `[0.0, 1.0]`). Điều
này phản chiếu đúng sự tách biệt đã có của `PDFReader`/`PDFDetector`:
Reader thu thập fact, giai đoạn reasoning/transform downstream diễn
giải chúng.

Xác nhận trong implementation: `core/domain/models.py::PDFPage.words`,
`core/extraction/extractor.py::Extractor._extract_digital_page()`.

------------------------------------------------------------------------

## ADR-026 --- Render `PageImage` Grayscale, Eager, Cho Mọi Trang

**Status:** Accepted (amended by ADR-048)

`PDFReader` render 1 `PageImage` (pixmap samples grayscale thô, tự mô
tả: `samples`, `width`, `height`, `dpi`) cho **mọi** trang của mọi tài
liệu, tại thời điểm render (`page.get_pixmap(dpi=Image.DPI,
colorspace=fitz.csGRAY)`, `Image.DPI = 300` lúc đó), bất kể tài liệu
sau này được phân loại là Digital, Scanned, hay Hybrid.

Lý do:
- Tránh phải mở lại file PDF sau này cho OCR (`Extractor`/`OCREngine`
  không bao giờ giữ tham chiếu `fitz.Page` — xem ADR-028).
- Chấp nhận chi phí bộ nhớ: `PDFDocument` theo từng tài liệu (và do
  đó mọi `PageImage` nó giữ) được giải phóng ngay sau khi
  `Worker._process_pdf()` trả về (ADR-007); chỉ `PDFResult` tồn tại
  xuyên suốt batch. Render eager vì vậy không vi phạm "Memory First" ở
  cấp batch, dù nó tăng chi phí bộ nhớ per-document đang xử lý.
- Chọn samples thô (không nén) thay vì lưu dạng PNG-encoded, ưu tiên
  sẵn sàng cho OCR hơn dung lượng lưu trữ.

`PageImage` tồn tại chuyên để tránh phụ thuộc ngầm vào tham số render
đã biết từ bên ngoài (DP-008, Explicit Over Implicit): consumer đọc
`width`/`height`/`dpi` trực tiếp từ object thay vì tự tính lại từ
`PageStatistics` và 1 DPI giả định.

> **Đã amend bởi ADR-048** (colorspace đổi sang RGB) và ADR-053 (DPI
> tăng 300→450).

------------------------------------------------------------------------

## ADR-027 --- `UNKNOWN` Là Sự Vắng Mặt Của Quyết Định

**Status:** Accepted

`AnalysisMode.UNKNOWN` đại diện cho sự *vắng mặt* của 1 quyết định
phân loại, không phải 1 loại tài liệu cần chiến lược extraction riêng.
Theo đó:

- `Extractor.extract()` raise `ValueError` nếu được gọi với
  `analysis.mode is AnalysisMode.UNKNOWN` — đây được coi là vi phạm
  hợp đồng lập trình (gọi Extractor khi không có quyết định nào để
  hành động theo), không phải warning ở cấp business.
- `Worker._process_pdf()` chịu trách nhiệm **không gọi** `Extractor`
  khi `analysis.mode is UNKNOWN`. Quyết định có extract hay không
  thuộc về orchestrator (ADR-004/005), không phải để `Extractor` tự
  phòng vệ 1 case vốn, theo định nghĩa, nằm ngoài domain của nó.

Điều này giữ ranh giới nghiêm ngặt giữa "Detector không quyết định
được" (kết quả business ở mức `WARNING`, theo logic `Worker` map
`UNKNOWN` → `ProcessStatus.WARNING`) và "Extractor bị gọi mà không có
quyết định hợp lệ" (vi phạm hợp đồng lập trình, ám chỉ bug ở caller).

> **Lưu ý lịch sử:** source thật ban đầu (tính đến Session 2026-08-09)
> KHÔNG raise `ValueError` như mô tả ở đây — trả về gracefully thay
> vào đó, gây sai lệch giữa tài liệu và code trong nhiều tuần. Đã phát
> hiện và xử lý tại Session 2026-08-12, xem ADR-056.

Xác nhận trong implementation: `core/extraction/extractor.py::Extractor.extract()`,
`ui/worker.py::Worker._process_pdf()`.

------------------------------------------------------------------------

## ADR-028 --- Rotation Reconciliation Tính Thủ Công, Không Qua `fitz.Page`

**Status:** Accepted

`Extractor` không bao giờ giữ tham chiếu `fitz.Page` sống — file PDF
nguồn đã bị đóng vào lúc `Extractor.extract()` chạy (`PDFReader.read()`
dùng `with fitz.open(...)`, và `PDFDocument` là domain model thuần túy,
độc lập với file). Do đó, `Page.rotation_matrix` có sẵn của PyMuPDF
không khả dụng cho `Extractor`.

Đã xác minh (tài liệu chính thức PyMuPDF, và phát biểu của maintainer
trong 1 GitHub discussion chính thức):
- `page.get_text("words")` trả tọa độ tương đối so với trang
  **chưa xoay** (unrotated).
- `page.rect` (nguồn của `PageStatistics.width/height`) và
  `page.get_pixmap()` đều phản ánh trang **đã xoay/hiển thị** (rotated/
  visual).

Đây là 1 sai lệch hệ tọa độ có thật, đã xác nhận, cho các trang có xoay
(`page.statistics.rotation != 0`).

Giải pháp: `Extractor._rotate_bbox()` implement 4 case xoay được
PyMuPDF đảm bảo (0/90/180/270°) một cách tường minh, không phụ thuộc
PyMuPDF bên trong `extractor.py`.

------------------------------------------------------------------------

## ADR-029 --- Parser = Orchestrator Mỏng + TemplateMatcher Engine Tách Biệt

**Status:** Accepted

`Parser` theo đúng sự tách biệt đã thiết lập bởi `Extractor` (ADR-024):
nó không bao giờ tự chứa logic Key Matching, Windowing, hay Value
Matching. Toàn bộ logic template-matching nằm trong `TemplateMatcher`;
`Parser` chỉ gọi `TemplateMatcher.select_template()` +
`.extract_fields()`, sau đó convert chuỗi thô sang field `InvoiceInfo`
đã đánh kiểu qua `ValueConverter`.

Lý do: chuẩn bị cho 1 engine LayoutLMv3 ở v2.0 có thể "drop-in" thay
thế `TemplateMatcher` sau cùng interface, không cần đổi `Parser` hay
`Worker`.

Xác nhận trong implementation: `core/parsing/parser.py`,
`core/parsing/template/template_matcher.py`.

------------------------------------------------------------------------

## ADR-030 --- Chọn Template Bằng Evidence-Weighted Scoring

**Status:** Accepted

`TemplateMatcher.select_template()` tái dùng đúng pattern Evidence →
Score → Decision đã có ở `PDFDetector` (ADR-020/021):

- Mỗi `TemplateDefinition` được chấm điểm độc lập:
  `score = Σ(identification_weight của field khớp key) / Σ(identification_weight của mọi field)`.
- Tie margin (`TemplateMatching.TEMPLATE_TIE_MARGIN`) ngăn việc chọn 1
  winner mập mờ khi 2 template có điểm quá sát nhau — phản chiếu
  `PDFDetector._DECISION_TIE_MARGIN`.
- Ngưỡng điểm tối thiểu (`TemplateMatching.TEMPLATE_MIN_SCORE`) loại bỏ
  các match yếu.
- Điểm được tính trên **toàn bộ** văn bản tài liệu (mọi trang), không
  giới hạn vùng, để tránh áp đặt giả định layout có thể gãy khi gặp
  loại tài liệu mới (chọn có chủ đích, đánh đổi hiệu năng).

`FieldDefinition.identification_weight` cho phép người viết template
đánh dấu field nào định danh nhà cung cấp (VD mã số thuế, tên công ty)
so với field chung chung (VD ngày hóa đơn) — field chung không ảnh
hưởng việc chọn template.

Xác nhận trong implementation:
`core/parsing/template/template_matcher.py::TemplateMatcher._score_template()`.

------------------------------------------------------------------------

## ADR-031 --- Template Definition Lưu Dạng JSON Ngoài

**Status:** Accepted

Template Definition tồn tại dạng file JSON dưới `resources/templates/`,
load qua `TemplateLoader` vào frozen dataclass (`TemplateDefinition`/
`FieldDefinition`/`SpatialRelation` trong `core/domain/models.py`). Nhờ
đó, người viết template có thể thêm/cập nhật loại hóa đơn mà không cần
đụng tới logic Python.

- File JSON lỗi parse/validate bị bỏ qua kèm log warning; việc load
  tiếp tục cho mọi file khác (fail-soft per file).
- Thư mục `resources/templates/` không tồn tại cũng được xử lý êm
  (log warning, tập template rỗng) thay vì crash ứng dụng — nhất quán
  với đối tượng người dùng mục tiêu (office user, PROJECT_CONTEXT.md
  §1).
- `FieldDefinition.__post_init__` validate `field_name` khớp 1 field
  thật của `InvoiceInfo` (qua `dataclasses.fields()`), fail sớm ở lỗi
  gõ sai tên field thay vì fail âm thầm lúc `InvoiceInfo(**values)`
  construct ở `Parser`.
- `value_pattern` lưu dạng chuỗi thuần trong `FieldDefinition`; việc
  compile regex diễn ra ở `TemplateMatcher` (có cache), không phải ở
  `core/domain/models.py`, giữ đúng quy tắc "không Regex" của
  `models.py`.

Xác nhận trong implementation: `core/parsing/template/template_loader.py`,
`core/domain/models.py`.

------------------------------------------------------------------------

## ADR-032 --- Field Của `InvoiceInfo` Là Optional; Convert Lỗi → `None`

**Status:** Accepted

Mọi field của `InvoiceInfo` trừ `source_file` đều `Optional`, mặc định
`None`. Khi `TemplateMatcher` không tìm được giá trị cho 1 field, hoặc
`ValueConverter` convert lỗi (chuỗi số sai định dạng, ngày không hợp
lệ), field `InvoiceInfo` tương ứng chỉ đơn giản là `None` — không bao
giờ raise exception, không bao giờ dùng giá trị placeholder/sentinel.

`ValueConverter` chủ đích stateless và không bao giờ raise: mọi lỗi
convert trả về `None`. Điều này cô lập 1 field lỗi khỏi làm hỏng toàn
bộ PDF.

Xác nhận trong implementation: `core/domain/models.py::InvoiceInfo`,
`core/parsing/template/value_converter.py`.

------------------------------------------------------------------------

## ADR-033 --- Gap Ở Cấp Invoice Là Vấn Đề Của Report, Không Phải Worker Status

**Status:** Accepted

2 tình huống chủ đích được giữ **ngoài** `PDFResult.status`/`.note`:

1. **1 field trong `InvoiceInfo` là `None`** (Value Matching hoặc
   convert lỗi cho 1 field) — theo ADR-032.
2. **`Parser.parse()` trả về `None` hoàn toàn** (không template nào
   đạt `TEMPLATE_MIN_SCORE`, hoặc winner hòa với runner-up) — đối xứng
   cách `AnalysisMode.UNKNOWN` là "vắng mặt quyết định" (ADR-027),
   không phải lỗi.

Lý do cho (2): nguyên nhân "không template nào khớp" vốn mập mờ từ góc
nhìn pipeline — có thể là thiếu template, template sai/cũ, PDF chất
lượng kém, hoặc thậm chí file bị nhầm. Hệ thống không thể phân biệt
đáng tin cậy các nguyên nhân này, nên không được đoán bằng cách gán
`WARNING`. Thay vào đó: `PDFResult.status`/`.note` chỉ do quyết định
của `PDFDetector` chi phối, y hệt trước khi có Parser. Cả 2 tình huống
chỉ hiển thị qua tính năng Report, nơi người vận hành quan sát được
**tần suất**: xuất hiện thấp/lẻ tẻ ám chỉ file lỗi hoặc input sai;
xuất hiện thường xuyên trên cùng 1 dạng ám chỉ template cần cập nhật.

Xác nhận trong implementation: `ui/worker.py::Worker._process_pdf()`
(khối tích hợp Parser).

------------------------------------------------------------------------

## ADR-034 --- `TemplateSelection` Giữ Kèm `page_index` Cùng Matched Key

**Status:** Accepted

`TemplateSelection.matched_keys` được đánh kiểu
`Mapping[str, tuple[int, WordToken]]`, không phải
`Mapping[str, WordToken]`.

Lý do: `WordToken.normalized_bbox` chỉ có ý nghĩa trong không gian tọa
độ của 1 trang duy nhất (`ExtractionResult.words_by_page` được key
theo trang). Thiếu `page_index`, `TemplateMatcher.extract_fields()`
không biết nên quét collection `WordToken` của trang nào khi dựng vùng
tìm kiếm Windowing từ 1 key đã match trước đó, và có thể so sánh nhầm
bounding box giữa các trang khác nhau.

Phương án bị loại: thêm `page_index` vào chính `WordToken`. Bị loại vì
`WordToken` là domain model đã frozen, dùng chung, được `Extractor`
tiêu thụ (ADR-024/025) — đổi nó sẽ lan sang `ExtractionResult`/
`Extractor`, phạm vi ảnh hưởng rộng hơn nhiều so với giới hạn fix ở
`TemplateSelection` (model mới, chỉ Parser dùng).

Xác nhận trong implementation: `core/domain/models.py::TemplateSelection`.

------------------------------------------------------------------------

## ADR-035 --- Bắt Buộc Chuẩn Hóa Dấu Tiếng Việt Trước Fuzzy Key Matching

**Status:** Accepted

`TemplateMatcher` strip dấu tiếng Việt (`_strip_diacritics()`, Unicode
NFKD decomposition + xử lý riêng `Đ/đ`, vì `Đ/đ` không tự decompose qua
NFKD) cho cả `FieldDefinition.key_tokens` và text quan sát trước khi
gọi `rapidfuzz.fuzz.ratio()`.

Xác nhận qua thực nghiệm khi implement: so sánh text có dấu ("Mã số
thuế") với dạng không dấu ("Ma so thue") khi chưa chuẩn hóa cho ratio
~70, dưới mọi `fuzzy_threshold` hợp lý (85-90) — nghĩa là key matching
sẽ âm thầm thất bại bất cứ khi nào `key_tokens` của template và text
thật của PDF khác nhau về dấu, bao gồm cả trường hợp thực tế: OCR làm
rớt dấu trên bản scan chất lượng thấp.

Xác nhận trong implementation:
`core/parsing/template/template_matcher.py::_strip_diacritics()`.

------------------------------------------------------------------------

## ADR-036 --- Extractor Cũng Chuẩn Hóa Whitespace Của Text

**Status:** Accepted

Mở rộng trách nhiệm chuẩn hóa của `Extractor` (trước đó chỉ về hình
học, theo ADR-024/025/028) sang cả whitespace của text:
`_extract_digital_page()`/`_extract_ocr_page()` nay strip khoảng trắng
đầu/cuối và gộp khoảng trắng bên trong text của mỗi token trước khi
construct `WordToken`. Token trở thành rỗng sau chuẩn hóa bị loại bỏ
hoàn toàn (không bao giờ tạo `WordToken` text rỗng).

Lý do đặt ở `Extractor` thay vì `Parser`: chuẩn hóa whitespace là vấn
đề định dạng độc lập với bất kỳ domain model downstream nào (Parser,
hay 1 engine LayoutLMv3 tương lai, sẽ phải lặp lại logic này nếu
không) — nhất quán với việc `Extractor` đã là nơi duy nhất chuẩn hóa
output thô từ PyMuPDF/OCR thành `WordToken` sạch cho mọi consumer
downstream.

Xác nhận trong implementation:
`core/extraction/extractor.py::Extractor._normalize_text()`.

------------------------------------------------------------------------

## ADR-037 --- `ExcelWriter`/`ReportWriter` Là 2 Module Tách Biệt

**Status:** Accepted

1 bản thiết kế nháp ban đầu (`Technical_Design_excel_writer.docx`) đề
xuất 1 tầng `ReportService` duy nhất giữa UI và `ExcelWriter`, gộp việc
ghi Excel và sinh `report.txt` vào 1 lệnh gọi `generateReport()` duy
nhất. Đề xuất này bị bác bỏ sau thảo luận.

Lý do: `Worker.__init__` đã sẵn có 2 thuộc tính placeholder tách biệt
(`self._excel_writer = None`, `self._report_writer = None`) từ các
session trước — thiết kế gốc đã dự tính 2 component riêng biệt, không
phải 1 component gộp. Điều này cũng nhất quán với 2 trigger vốn khác
bản chất:

- Ghi Excel xảy ra **tự động**, đúng 1 lần, cuối `Worker.process()`
  (thời điểm theo ADR-008).
- Sinh `report.txt` xảy ra **như 1 hệ quả phụ của đúng lần ghi tự động
  đó** (xem ADR-040) — không phải 1 hành động được trigger riêng.

`ExcelWriter` và `ReportWriter` không phụ thuộc lẫn nhau. `ExcelWriter`
không bao giờ import `ReportWriter` hay ngược lại; `Worker` điều phối
cả 2.

Xác nhận trong implementation: `ui/worker.py::Worker.__init__`,
`Worker._write_excel()`.

------------------------------------------------------------------------

## ADR-038 --- Excel Mapping Load Fail-Fast (Không Phải Fail-Soft)

**Status:** Accepted

`ExcelMapping` (`table`, `columns`) được load từ 1
`resources/excel_mapping.json` bên ngoài qua `core/export/excel_mapper.py::Mapper`,
theo đúng pattern "JSON ngoài → frozen dataclass" đã có với Template
Definition (ADR-031).

Khác `TemplateLoader` (fail-soft per file, ADR-031), `Mapper` coi mọi
lỗi là **fatal** — bất kỳ `mapping.json` nào lỗi định dạng đều raise
`MappingError` (định nghĩa trong `core/export/excel_mapper.py`, không
phải `excel_writer.py` — mỗi module tự sở hữu exception nó raise, để
tránh import chéo giữa `excel_mapper.py` và `excel_writer.py`).

Lý do bất đối xứng fail-fast/fail-soft: với template, 1 file JSON lỗi
trong nhiều file là mất mát cô lập, chấp nhận được (các template khác
vẫn hoạt động). Với Excel mapping, chỉ có đúng 1 file mapping và nó là
điều kiện tiên quyết cứng để `ExcelWriter` ghi được bất kỳ thứ gì — không
có khái niệm "mapping hợp lệ 1 phần" để fallback.

`Mapper.load()` được gọi lazy bên trong `Worker._write_excel()`,
**không** phải trong `Worker.__init__()` (khác `TemplateLoader`, được
load eager trong `__init__`). Lý do: load eager trong `__init__` sẽ
crash ứng dụng ngay lúc khởi động nếu `mapping.json` lỗi, trước khi
người dùng kịp làm gì. Load lazy ở cuối batch cho phép mapping lỗi
được xử lý như bất kỳ lỗi pipeline-stage nào khác: bắt được, báo qua
Signal `error`, không crash app, và vẫn tiếp tục sinh `report.txt`
(ADR-040) để người dùng thấy lý do vì sao không ghi được gì.

Validate `FieldDefinition.field_name` (ADR-031) được tái dùng cho
`ExcelMapping.columns`: `Mapper._build_mapping()` kiểm tra mọi
`field_name` được map so với `dataclasses.fields(InvoiceInfo)` tại
thời điểm load, bắt lỗi gõ sai trước khi `ExcelWriter` từng chạy.

Xác nhận trong implementation: `core/export/excel_mapper.py`,
`resources/excel_mapping.json`, `config.py::EXCEL_MAPPING_PATH`.

------------------------------------------------------------------------

## ADR-039 --- Cột Excel Không Khớp Là Soft-Fail Theo Từng Cột

**Status:** Accepted

`ExcelMapping.columns` được validate với tên field của `InvoiceInfo`
lúc load (ADR-038), nhưng không thể validate với header **thật** của
Excel Table trong workbook output do người dùng chọn — JSON mapping và
file `.xlsx` vật lý là 2 nguồn độc lập chỉ có thể đối chiếu chéo lúc
runtime.

`ExcelWriter._resolve_columns()` so sánh `mapping.columns` với header
row thật của Excel Table đích. 1 cột được map nhưng vắng mặt trong
workbook sẽ được ghi vào `ExcelWriteResult.errors` và bỏ qua; mọi cột
khớp đúng khác vẫn được ghi bình thường. Điều này phản chiếu nguyên tắc
"1 field lỗi không làm hỏng cả record" đã có (ADR-032) ở cấp cột, và
tránh `ExcelWriter.write()` raise cho 1 tình huống phổ biến và khắc phục
được 1 phần (VD người dùng đổi tên 1 cột trong template Excel của họ).

Lỗi toàn cục, không khắc phục được — không tìm thấy workbook
(`WorkbookNotFoundError`), không tìm thấy Table (`ExcelTableNotFoundError`),
lỗi lưu file (`WorkbookSaveError`) — vẫn `raise` cứng, vì không có gì
để ghi 1 phần trong các trường hợp đó.

Xác nhận trong implementation:
`core/export/excel_writer.py::ExcelWriter._resolve_columns()`.

------------------------------------------------------------------------

## ADR-040 --- `ReportWriter` Có 2 Kênh Output Tách Biệt Hoàn Toàn

**Status:** Accepted (amended by ADR-050)

`ReportWriter.write(results, excel_result)` nhận 2 input độc lập —
`list[PDFResult]` và `ExcelWriteResult` — và route mỗi cái tới 1 output
riêng biệt, không trộn nội dung:

1. `list[PDFResult]` (kết quả pipeline theo từng file: status + note)
   → `utils/logger.py` (console + `logs/app.log`, qua `FileHandler`).
   Đối tượng đọc: dev/admin. Mọi file đều được log, bất kể status;
   status `WARNING`/`FAILED` log ở mức `logging.WARNING`, còn lại ở
   `logging.INFO`.

2. `ExcelWriteResult` (Summary / Warnings / Errors của lần ghi Excel)
   → `reports/Report.txt` (tên file cố định, không timestamp). Đối
   tượng đọc: end-user, qua nút Report của UI. File này **bị ghi đè**
   mỗi lần chạy — luôn phản ánh đúng lần gọi `process()` gần nhất.

Lý do giữ 2 kênh tách biệt thay vì gộp dữ liệu `PDFResult` vào
`report.txt`: chúng phục vụ đối tượng khác nhau ở mức chi tiết khác
nhau. `PDFResult.note` là văn bản chẩn đoán nội bộ pipeline (confidence
phân loại, cảnh báo extraction); end-user không cần nó để hành động.
Thứ end-user cần từ `report.txt` chỉ đúng 2 điều: field hóa đơn nào ra
`None` (ADR-033) và việc ghi Excel có thành công hay không — cả 2 đều
nằm trong `ExcelWriteResult`, không phải trong `PDFResult`.

`ExcelWriter` tự nó không bao giờ ghi vào bất kỳ kênh nào (ADR-006) —
chỉ trả về `ExcelWriteResult` như dữ liệu thuần; `ReportWriter` là chủ
sở hữu duy nhất của cả 2 side effect.

> **Đã amend bởi ADR-050:** `app.log` sau này đổi từ tích lũy sang ghi
> đè mỗi lần chạy — chỉ còn khác nhau ở đối tượng đọc/mức chi tiết,
> không còn khác nhau ở vòng đời file.

Xác nhận trong implementation: `core/export/report_writer.py`,
`core/domain/constants.py::Report`, `utils/logger.py::_configure_root()`.

------------------------------------------------------------------------

## ADR-041 --- Nút Report Chỉ Mở File Đã Sinh Sẵn

**Status:** Accepted (amended by ADR-064)

`report.txt` được sinh đúng 1 lần mỗi lần chạy `process()`, tự động,
như 1 phần của `Worker._write_excel()` (thời điểm theo ADR-008, nội
dung theo ADR-040) — **không** phải khi người dùng bấm nút "Report".

`MainWindow._report()` chỉ đọc `Worker.report_path` (property expose
đường dẫn đã ghi sẵn) và mở nó qua `QDesktopServices.openUrl()`, dùng
handler mặc định của OS cho file `.txt`. Nếu `report_path` là `None`
(chưa có lần chạy nào hoàn tất), hiển thị `QMessageBox.information`
thay vào đó; nếu OS mở file thất bại, hiển thị `QMessageBox.warning`.
Nút này không bao giờ tự gọi `ExcelWriter` hay `ReportWriter`.

Điều này giữ `MainWindow` là 1 UI coordinator thuần túy (ADR-001) — nó
không có vai trò quyết định *khi nào* report được sinh ra, chỉ có vai
trò hiển thị 1 report đã tồn tại sẵn.

> **Đã amend bởi ADR-064:** phạm vi "đã tồn tại sẵn" mở rộng từ "trong
> phiên app hiện tại" sang "bất kỳ lúc nào trước đó, kể cả phiên mở app
> trước" — nguyên tắc "không tự trigger sinh report" vẫn giữ nguyên.

Xác nhận trong implementation: `ui/main_window.py::MainWindow._report()`,
`ui/worker.py::Worker.report_path`.

------------------------------------------------------------------------

## ADR-042 --- Excel Mapping Schema Giữ Nguyên `table` + `columns`, Không Thêm `sheet`

**Status:** Accepted

Trong phiên thảo luận `excel_mapping.json`, có đề xuất thêm trường
`sheet` để chỉ rõ Excel Table nằm ở sheet nào. Đề xuất này đã bị rút
lại sau khi phân tích `ExcelWriter._find_table()`:

```python
for worksheet in workbook.worksheets:
    if table_name in worksheet.tables:
        return worksheet, worksheet.tables[table_name]
```

Hàm này duyệt toàn bộ sheet để tìm Table theo tên — không cần biết tên
sheet để hoạt động đúng, vì Excel tự đảm bảo tên Table (`ListObject`)
là duy nhất trong toàn workbook. Thêm `sheet` sẽ dư thừa cho mục đích
"tìm được bảng"; nếu muốn dùng `sheet` như 1 điều kiện validate bổ sung
(fail-fast nếu Table bị dời sai sheet) thì cần quyết định thêm về ngữ
nghĩa lỗi — người dùng quyết định không cần thêm độ phức tạp này.

Xác nhận: `ExcelMapping` (`core/domain/models.py`), `Mapper`
(`core/export/excel_mapper.py`), `ExcelWriter._find_table()`
(`core/export/excel_writer.py`) — không đổi gì.

------------------------------------------------------------------------

## ADR-043 --- `ValueConverter` Bỏ Ký Hiệu `%` Cuối Chuỗi Trước Khi Convert Decimal

**Status:** Accepted

Phát hiện qua kiểm thử thực nghiệm trên PDF hóa đơn thật
(`HD2026-0003_digital.pdf`): field `vat_rate` trích được token "5%"
(dấu `%` dính liền, do PyMuPDF không tách khoảng trắng giữa số và ký
hiệu phần trăm). `Decimal("5%")` ném `InvalidOperation`, khiến field
`vat_rate` luôn ra `None` dù Key/Value Matching đã trích đúng vị trí.

`ValueConverter._to_decimal()` nay strip ký tự `%` ở cuối chuỗi (nếu
có) trước khi áp `thousand_separator`/`decimal_separator` và gọi
`Decimal()`. Strip vô điều kiện, không cần cấu hình gì thêm, vì `%`
không bao giờ là 1 phần hợp lệ khác của 1 số Decimal.

Xác nhận trong implementation:
`core/parsing/template/value_converter.py::ValueConverter._to_decimal()`.
Verify: `_to_decimal("5%", None)` → `Decimal('5')` (trước patch:
`None`). Không ảnh hưởng các field Decimal khác (subtotal, vat_amount,
total_amount) vì giá trị của chúng không có `%`.

------------------------------------------------------------------------

## ADR-044 --- Value Matching Ghép Nhiều Từ Bằng Gap-Based Line Clustering

**Status:** Accepted

Giải quyết Known Limitation "Value Matching chỉ trả về 1 `WordToken`
duy nhất" (ghi từ Session 2026-08-01/02): mọi field giá trị nhiều từ
(company_name, address, buyer_name, payment_method) từng bị cắt cụt
còn 1 từ. Xác nhận qua kiểm thử thực nghiệm trên PDF thật.

Thiết kế đã chọn (trong 3 hướng thảo luận: gap-based / cả dòng trong
window / dùng vị trí key field khác làm ranh giới): **gap-based**, tái
dùng 2 constant sẵn có — `LINE_Y_TOLERANCE` (xác định "cùng dòng") và
`WORD_GAP_TOLERANCE` (xác định "liền kề") — đối xứng với cơ chế
`_cluster_lines`/`_cluster_phrases` đã dùng ở Key Matching (ADR-035),
không thêm constant mới.

Chỉ áp dụng cho field `ValueType.TEXT` — Decimal/Date giữ nguyên hành
vi cũ (luôn 1 token), vì các giá trị này trên thực tế luôn là 1 token
liền mạch.

**Điều kiện dừng bổ sung:** không mở rộng qua token kết thúc bằng dấu
`:` — trong toàn bộ dữ liệu quan sát, token dạng này luôn là phần còn
lại của 1 nhãn (label), không bao giờ là giá trị thật (phát hiện phụ:
merge áp dụng cho mọi field Text có thể kéo nhầm token nhãn của field
khác trên cùng dòng vào giá trị, VD `tax_code` bị biến từ
`'0313828292'` thành `'mua: 0313828292'`).

**Rủi ro còn lại (chưa loại bỏ hoàn toàn):** nếu 1 dòng có 2 field liền
kề mà nhãn field thứ 2 KHÔNG kết thúc bằng `:`, merge vẫn có thể tràn
sang field kế bên. Đây là giới hạn cố hữu của gap-based clustering
(đánh đổi độ đầy đủ lấy rủi ro tràn), không phải lỗi implementation.

Xác nhận trong implementation:
`core/parsing/template/template_matcher.py::TemplateMatcher._select_best_value()`,
`TemplateMatcher._merge_same_line()`.

------------------------------------------------------------------------

## ADR-045 --- Section-Scoped Key Matching Giải Quyết Va Chạm `key_tokens` Giữa Các Khối Tài Liệu

**Status:** Accepted

Giải quyết 2 Known Limitation cùng gốc rễ (`TemplateMatcher._find_key_match()`
tìm kiếm toàn cục, phẳng trên mọi phrase của tài liệu, không có khái
niệm "khối"/"ngữ cảnh" để giới hạn phạm vi tìm):

- `tax_code` bị lấy nhầm MST bên mua: key "ma so thue" khớp cụm "Mã số
  thuế" tách từ dòng "Mã số thuế mua:" (ratio 100, do không dính dấu
  `:`) thay vì cụm đúng "Mã số thuế:" của bên bán (ratio 95.24, dính
  dấu `:`).
- `invoice_date` phụ thuộc may rủi thứ tự: key "ngay" khớp 3 vị trí
  (ngày lập + 2 ngày ký số cuối trang) với ratio bằng nhau tuyệt đối;
  chỉ đúng nhờ `_find_key_match` cập nhật theo `>` (không phải `>=`)
  nên cụm xuất hiện trước trong tài liệu thắng — không phải cơ chế
  phân biệt thật sự.

**Thiết kế đã chọn:** trong 4 cách thảo luận (Block/Section, Parent
Key, Anchor, Relative Position), chọn **Section/Block**:

- `SectionDefinition` mới (`core/domain/models.py`): `section_id`,
  `key_tokens` (`None` = khối ảo bắt đầu từ đỉnh trang, không cần
  marker thật), `fuzzy_threshold`.
- `FieldDefinition` thêm field bắt buộc `section: str` (không có
  default) — quyết định trong thảo luận: không cho phép field bỏ
  trống section.
- `TemplateDefinition` thêm `sections: tuple[SectionDefinition, ...]`,
  tự validate mọi `field.section` phải khớp 1 `section_id` đã khai
  (`__post_init__`, raise `ValueError` nếu không khớp — được
  `TemplateLoader` bắt và xử lý fail-soft per file, ADR-031).
- Section header dùng tie-margin riêng
  (`TemplateMatching.SECTION_TIE_MARGIN = 10`, thang 0-100 của
  `rapidfuzz.fuzz.ratio()`, khác thang với `TEMPLATE_TIE_MARGIN` 0-1)
  — section header cần chống va chạm chặt hơn field thường (field
  thường vẫn giữ best-match tuyệt đối, không đổi).
- `_find_key_match()` được refactor tách khỏi `FieldDefinition`, nhận
  trực tiếp `key_tokens`/`fuzzy_threshold`/`tie_margin` (mặc định
  `None`) — dùng chung cho cả Field (`tie_margin=None`, hành vi cũ
  không đổi) và Section (`tie_margin` bắt buộc).
- Thuật toán resolve: match từng section header trên toàn bộ phrase
  của tài liệu, sắp theo `(page_index, y_center)` tăng dần, dựng
  khoảng `[bắt đầu section, bắt đầu section kế tiếp)`. Field thuộc
  section nào chỉ được tìm `key_tokens` trong đúng khoảng đó.
- Section không resolve được (ambiguous do tie_margin, hoặc không tìm
  thấy) khiến mọi field thuộc section đó coi như "không tìm được" cho
  template này — đối xứng nguyên tắc "UNKNOWN là absence of decision"
  (ADR-027).

**Lợi ích phát hiện thêm:** `buyer_tax_code` giờ dùng lại được đúng
`key_tokens=["ma so thue"]` giống hệt `tax_code` (chỉ khác section),
không cần key dài riêng như thiết kế tạm thời trước đó.

**Rủi ro còn lại:**
- Section header tự nó vẫn có thể va chạm về mặt lý thuyết nếu 2
  section dùng `key_tokens` gần giống nhau.
- `MAX_KEY_WORDS = 4` giới hạn độ dài cụm sinh ra khi Key Matching
  (kể cả cho Section) — section header 5+ từ có thể không bao giờ đạt
  ratio 100, phải chọn `key_tokens` ngắn hơn.
- `SECTION_TIE_MARGIN = 10` là giá trị placeholder ban đầu.

Xác nhận trong implementation: `core/domain/models.py::SectionDefinition`,
`FieldDefinition.section`, `TemplateDefinition.sections`;
`core/parsing/template/template_matcher.py::TemplateMatcher._find_key_match()`,
`_resolve_sections()`, `_filter_phrases_by_range()`, `_score_template()`;
`core/parsing/template/template_loader.py::TemplateLoader._build_section()`;
`core/domain/constants.py::TemplateMatching.SECTION_TIE_MARGIN`.

Verify: toàn bộ 12/12 field của `sample_invoice_v1.json` (v3) ra đúng
kết quả trên `HD2026-0003_digital.pdf` thật, bao gồm `tax_code` (đúng
MST bên bán) và `invoice_date` (đảm bảo, không còn phụ thuộc thứ tự).

------------------------------------------------------------------------

## ADR-046 --- Lazy Loading OCREngine (PaddleOCR) & Tắt Tiền Xử Lý Phụ Của PaddleX

**Status:** Accepted (bối cảnh lịch sử — không còn áp dụng sau ADR-047)

Khắc phục lỗi crash ứng dụng ngay khi khởi động UI (`ui/main_window.py`)
do khởi tạo `_PaddleOCR` quá sớm trong `OCREngine.__init__()` và lỗi
xung đột thuộc tính `strides` trong Paddle 3.0.0 PIR engine.

Thiết kế đã chọn (bối cảnh OCR engine lúc đó là PaddleOCR):

1. **Lazy Loading:** `OCREngine.__init__()` chỉ thiết lập
   `self._ocr = None`. Hàm `_get_ocr()` trì hoãn việc khởi tạo
   `_PaddleOCR` đến lần đầu tiên `recognize()` thực sự được gọi. Instance
   được giữ lại và tái sử dụng cho toàn bộ trang/PDF tiếp theo trong batch.
2. **Tắt preprocessor thừa:** `USE_DOC_ORIENTATION_CLASSIFY = False`,
   `USE_DOC_UNWARPING = False`, `USE_TEXTLINE_ORIENTATION = False`.

> **Không còn áp dụng:** sau khi OCR engine chuyển hẳn sang Tesseract
> (ADR-047), Lazy Loading kiểu này KHÔNG mang sang được — Tesseract
> chạy qua `subprocess`, không giữ model nặng trong tiến trình, không
> có gì cần trì hoãn khởi tạo. Xem ADR-047 (mục "Hệ quả kiến trúc
> quan trọng") và ADR-061. ADR này chỉ còn giá trị lịch sử/tham khảo
> cho các OCR engine dạng "nạp model vào tiến trình" trong tương lai.

------------------------------------------------------------------------

## ADR-047 --- Chốt OCR Engine: Tesseract 5.x + tessdata_best

**Status:** Accepted (amended by ADR-061)

Sau khi thực nghiệm tuần tự 2 thư viện khác, `OCREngine`
(`core/extraction/ocr_engine.py`) chốt dùng **Tesseract 5.x +
tessdata_best** (qua `pytesseract`), thay thế Mock (ADR-013).

### Lịch sử lựa chọn (để tránh lặp lại thử nghiệm đã loại)

1. **PaddleOCR (`paddleocr==3.7.0`)** — loại bỏ. Xung đột version giữa
   `paddleocr==3.7.0` và `paddlepaddle` ở tầng PIR — lỗi
   `ValueError: Type of attribute: strides is not right` khi chạy thật
   trên PDF Scanned (xác nhận qua GitHub Issue #18162, chưa có fix
   chính thức tại thời điểm thử nghiệm). Tổ hợp duy nhất chạy được
   trên máy thật của người vận hành (macOS Ventura Intel, Python 3.12)
   là `paddleocr==2.7.3` + `paddlepaddle==2.6.2` — buộc hạ về API 2.x
   cũ, kèm nguy cơ xung đột `numpy`/`pandas`.

2. **RapidOCR (`rapidocr==3.9.2`, backend onnxruntime)** — loại bỏ.
   Ưu điểm: không phụ thuộc `paddlepaddle`, hỗ trợ tiếng Việt qua
   PP-OCRv6. Vấn đề triển khai đã tự sửa: `onnxruntime` không phải
   dependency chính thức của `rapidocr`; không có wheel
   `onnxruntime>=1.24` cho macOS Intel (hạ về `1.23.2`); lỗi lazy
   loading tự triển khai (`recognize()` gọi thẳng `self._ocr(...)`
   thay vì `self._get_ocr()(...)`). **Lý do loại bỏ cuối cùng: chất
   lượng nhận dạng tiếng Việt kém**, xác nhận qua debug thật trên
   `HD2026-0001_scanned.pdf` (không phải bug code — pipeline không
   crash, nhưng text OCR sai nhiều). Đây là lý do quyết định, vượt
   trên mọi ưu điểm về dependency/cài đặt.

3. **Tesseract 5.x + tessdata_best** — **chọn cuối cùng**. Verify thật
   bằng `pytesseract.image_to_data()` (Tesseract 5.3.4,
   `vie.traineddata` từ `tesseract-ocr/tessdata_best` chính thức) trên
   `HD2026-0001_scanned.pdf` — kết quả đọc đúng gần như tuyệt đối, giữ
   nguyên dấu tiếng Việt. Bounding box trả sẵn dạng rect trục-thẳng
   (`left,top,width,height`) — đơn giản hơn RapidOCR/PaddleOCR.

### Phương án cân nhắc nhưng không triển khai: Hybrid (Tesseract Det + VietOCR Rec)

VietOCR dùng PyTorch nhưng không khai báo `torch` là dependency chính
thức (giống pattern `rapidocr`/`onnxruntime`); model tải qua Google
Drive (`gdown`, rủi ro rate-limit). Kiến trúc Hybrid cộng dồn cả 2
nhược điểm. Quyết định: **hoãn sang Future Improvements** (Rule 9:
"Never optimize early") — Tesseract + tessdata_best đã đủ tốt qua thực
nghiệm.

### Hệ quả kiến trúc quan trọng: KHÔNG áp dụng Lazy Loading (khác ADR-046)

`ADR-046` (Lazy Loading, cho bản PaddleOCR) không mang sang Tesseract:
Tesseract hoạt động qua `subprocess` gọi binary hệ thống mỗi lần
`image_to_data()` được gọi — không giữ "model nặng" trong bộ nhớ tiến
trình, không có gì cần trì hoãn. `OCREngine.__init__()` (bản Tesseract)
chỉ fail-fast kiểm tra `vie.traineddata` tồn tại và dựng sẵn chuỗi cấu
hình `--tessdata-dir ... --psm ... --oem ...`.

> **Đã amend bởi ADR-061:** việc kiểm tra `vie.traineddata` sau này
> chuyển từ `__init__()` sang lazy-check lần đầu `recognize()` được
> gọi, để không crash app lúc mở nếu thiếu tessdata.

Xác nhận trong implementation: `core/extraction/ocr_engine.py`,
`requirements.txt` (`pytesseract==0.3.13`), `config.py::TESSDATA_DIR`,
`core/domain/constants.py::OCR`.

------------------------------------------------------------------------

## ADR-048 --- `PageImage` Render RGB Thay Vì Grayscale

**Status:** Accepted (amends ADR-026; amended by ADR-054)

`PDFReader._render_page_image()` nay render **RGB** (`fitz.csRGB`)
thay vì `fitz.csGRAY`.

**Lý do đổi (không phải vì tốc độ):** giữ màu thật cho OCR — hóa đơn
Việt Nam thường có con dấu đỏ, chữ ký mực màu; GRAY→RGB giả (R=G=B)
không phục hồi được màu đã mất, trong khi RGB thật giúp OCR tận dụng
độ tương phản màu thật. Chi phí: RGB tốn gấp 3 lần bộ nhớ/trang (~24.9
MB so với ~8.3 MB ở A4/300 DPI khi đó) áp dụng cho MỌI trang của MỌI
PDF (kể cả Digital-mode không bao giờ chạy OCR, vì `PDFReader` chạy
trước `PDFDetector`).

Đồng thời: `PageImage` (`core/domain/models.py`) thêm field
`channels: int = 3` (DP-008, Explicit Over Implicit).

> **Ghi chú số liệu:** con số "~24.9 MB/trang" tính ở 300 DPI, thời
> điểm ADR này được chốt. Sau ADR-053 tăng DPI 300→450 (hệ số diện
> tích 2.25x), con số đúng hiện tại là **~56 MB/trang** (đính chính tại
> Session 2026-08-13, xem PROJECT_CONTEXT.md).
>
> **Đã amend bởi ADR-054:** lý do giữ RGB đổi sang tính bất khả nghịch
> của chuyển đổi màu (không còn vì lợi ích OCR trực tiếp, do OCR engine
> đã chuyển sang Tesseract).

Xác nhận trong implementation:
`core/reading/pdf_reader.py::PDFReader._render_page_image()`,
`core/domain/models.py::PageImage`, `core/domain/constants.py::Image`.

------------------------------------------------------------------------

## ADR-049 --- Deskew: Giữ Nguyên Canvas + Ngưỡng Chặn Góc Giả

**Status:** Accepted

`OCREngine` tự triển khai bước làm thẳng trang (deskew) trước khi đưa
vào OCR engine. 2 ràng buộc thiết kế:

1. **Giữ nguyên kích thước canvas khi xoay** (`cv2.warpAffine` với
   `dsize` bằng đúng kích thước gốc, biên trống lấp trắng
   `DESKEW_FILL_VALUE=255`) — đảm bảo `page_image.width/height` vẫn là
   mẫu số chuẩn hóa hợp lệ cho `Extractor._normalize_bbox()`.

2. **`DESKEW_MAX_ANGLE = 10.0`** (phát hiện qua chạy thật) — ngưỡng
   chặn trên cho góc nghiêng ước lượng được. Nguyên nhân: thuật toán
   ước lượng góc (`cv2.minAreaRect()` bao toàn bộ điểm nội dung của cả
   trang) được thiết kế cho 1 khối văn bản đặc dày, KHÔNG phù hợp với
   tài liệu nhiều khối rải rác như hóa đơn. Với trang A4 dọc, nội dung
   rải theo chiều cao khiến `minAreaRect` bám theo tỷ lệ khung trang
   thay vì tỷ lệ 1 dòng chữ, trả về góc giả gần `-90°` → `_deskew` xoay
   ngang toàn bộ trang, làm hỏng vị trí mọi `WordToken`, dẫn đến Key
   Matching/Windowing thất bại toàn bộ (triệu chứng ban đầu: "Excel
   không ghi nhận dữ liệu nào").

   Giải pháp: nếu `abs(angle) > DESKEW_MAX_ANGLE` sau chuẩn hóa → coi
   là artifact của thuật toán, trả `0.0` (bỏ qua xoay). Hóa đơn scan
   văn phòng hiếm khi nghiêng thật quá 10°.

Xác nhận trong implementation:
`core/extraction/ocr_engine.py::OCREngine._estimate_skew_angle()`,
`core/domain/constants.py::OCR.DESKEW_MAX_ANGLE`.

------------------------------------------------------------------------

## ADR-050 --- `app.log` Ghi Đè Mỗi Lần Chạy

**Status:** Accepted (amends ADR-040)

`ADR-040` quy định `logs/app.log` **tích lũy** qua các lần chạy. Hành
vi này đổi thành **ghi đè mỗi lần chạy** (giống `reports/Report.txt`).

**Lý do đổi:** log tích lũy qua nhiều lần chạy khiến file phình to
theo thời gian, khó đọc log của lần chạy gần nhất — chi phí vận hành
thực tế phát sinh sau khi dùng thử.

**Lưu ý:** điều này làm mất lý do ban đầu ADR-040 khi tách 2 kênh
output — nay cả 2 kênh đều ghi đè, chỉ còn khác nhau ở đối tượng đọc
(dev/admin vs end-user) và mức độ chi tiết, không còn khác nhau ở vòng
đời file. Nếu sau này cần truy vết lịch sử nhiều lần chạy, sẽ cần cơ
chế khác (VD log xoay vòng theo timestamp) — chưa có kế hoạch.

Xác nhận trong implementation: `utils/logger.py::_configure_root()`.

------------------------------------------------------------------------

## ADR-051 --- `ValueConverter` Strip Hậu Tố Đơn Vị Tiền Tệ VND

**Status:** Accepted

Phát hiện qua debug thực nghiệm trên batch PDF Scanned thật (Report.txt:
13/~90 file, ~15% data, thiếu đều 3 field subtotal/vat_amount/total_amount).
Xác nhận: Windowing hoạt động đúng, nhưng `_select_best_value()` trả
`None` vì `value_pattern: "^[0-9.,]+$"` không khớp token OCR dạng
"4,842,303VND" — Tesseract gộp đơn vị tiền tệ dính liền số thành 1
token khi bản scan không có khoảng trắng rõ ràng. Cùng loại lỗi với
ADR-043 nhưng chặn sớm hơn: ở tầng `value_pattern`, trước khi
`ValueConverter` kịp chạy.

**Giải pháp 2 lớp:**
1. `value_pattern` của 3 field tiền tệ nới để chấp nhận hậu tố tùy
   chọn: `^[0-9.,]+\s*(?:(?i:vn[dđ])|₫|[đĐ])?$`.
2. `ValueConverter._to_decimal()` gọi `_strip_currency_suffix()` mới.

**7 biến thể, 2 nhóm theo mức rủi ro:**
- `vnd, VND, vnđ, VNĐ, ₫` — strip vô điều kiện (chuỗi ≥2 ký tự/Unicode
  riêng biệt không thể là 1 phần hợp lệ khác của Decimal).
- `đ, Đ` (1 ký tự) — CHỈ strip khi ký tự liền trước là chữ số. Lý do:
  1 ký tự chữ cái đơn lẻ có rủi ro trùng nội dung/nhiễu OCR cao hơn
  hẳn — cùng lớp rủi ro với "key_tokens 1 từ" đã ghi nhận trước đó.

**Rủi ro còn lại:** ràng buộc vị trí giảm đáng kể nhưng không triệt
tiêu khả năng OCR noise tạo đúng 1 ký tự đ/Đ ngay sau 1 chữ số hợp lệ
không phải ký hiệu tiền — dẫn đến strip nhầm, sai lệch số âm thầm
(không có warning, khác field ra `None`).

Xác nhận trong implementation:
`core/parsing/template/value_converter.py::ValueConverter._strip_currency_suffix()`,
`resources/templates/sample_invoice_v1.json` (v4).

------------------------------------------------------------------------

## ADR-052 --- `ValueConverter` Tự Phục Hồi Số Bị OCR Nhầm Lẫn Dấu `,`/`.`

**Status:** Accepted

Phát hiện tiếp theo ADR-051: sau khi xử lý hậu tố tiền tệ, batch PDF
Scanned vẫn còn <3% case OCR nhầm lẫn dấu phân cách `,` ↔ `.` trong
chuỗi số. Lỗi NGHIÊM TRỌNG hơn ADR-051/ADR-043 vì thường KHÔNG khiến
`Decimal()` raise — chuỗi sau xử lý vẫn đúng cú pháp nhưng SAI TRỊ SỐ
(silent corruption, có thể lệch tới hàng nghìn lần).

**Giải pháp:** `_to_decimal()` thêm bước kiểm tra cấu trúc chuỗi
(`_looks_ambiguous()`) TRƯỚC khi áp separator — độc lập với việc
`Decimal()` có raise hay không.

**6 dấu hiệu khả nghi** (dựa trên vị trí dấu, không dựa loại ký tự):
1. Có cả 2 loại dấu `,`/`.`, và dấu CUỐI không phải
   `decimal_separator` đã cấu hình.
2. `decimal_separator` xuất hiện nhiều hơn 1 lần.
3. Vi phạm quy tắc 3 chữ số (cụm không phải đầu/cuối-decimal không có
   đúng 3 chữ số).
4. Vị trí phi lý: dấu phân cách ở đầu/cuối chuỗi.
5. Double punctuation: 2 dấu phân cách liền nhau.
6. Decimal Tail Length: phần sau dấu cuối (khi là decimal_separator)
   dài hơn `NumberRepair.DECIMAL_TAIL_MAX_LENGTH` (mặc định = 3).

Khi khả nghi, `_normalize_number_separators()` suy luận lại: cụm cuối
độ dài hợp lý cho phần thập phân → coi là decimal; ngược lại → coi
TOÀN BỘ là thousand separator, ưu tiên giữ đúng ĐỘ LỚN số hơn đoán sai
vị trí thập phân.

**Giới hạn đã biết, chưa giải quyết:**
- Cụm cuối ĐÚNG 3 chữ số VÀ dấu cuối trùng ngẫu nhiên với
  `decimal_separator` đã cấu hình — không đủ tín hiệu cấu trúc để phân
  biệt với trường hợp hợp lệ thật.
- OCR làm MẤT HẲN dấu phân cách (VD "4842303" liền khối) — không có
  cấu trúc nào để suy luận, có thể silent corruption tương tự.
- `NumberRepair.DECIMAL_TAIL_MAX_LENGTH = 3` là giá trị ước lượng ban
  đầu, dự kiến cho người dùng tùy chỉnh ở v2.0.

Verify: kết hợp với ADR-053 (DPI + Preprocess), tỷ lệ lỗi giảm từ mức
quan sát ban đầu xuống dưới 0.5% — chưa về 0%.

Xác nhận trong implementation:
`core/parsing/template/value_converter.py::ValueConverter._looks_ambiguous()`,
`_normalize_number_separators()`, `_split_number_groups()`,
`_parse_plain_decimal()`; `core/domain/constants.py::NumberRepair`.

------------------------------------------------------------------------

## ADR-053 --- OCR: Tăng DPI 300→450 & Thêm Bước Preprocess

**Status:** Accepted

Cùng đợt điều tra với ADR-051/052: kể cả khi field được trích đúng vị
trí, nội dung số đôi khi vẫn sai vì Tesseract đọc nhầm dấu `,`/`.` —
nguyên nhân gốc 1 phần đến từ chất lượng ảnh đầu vào.

**Thay đổi 1 — DPI 300 → 450** (`Image.DPI`): mức 300 DPI tối ưu cho
độ chính xác OCR tổng thể theo báo cáo phổ biến, nhưng không xét riêng
ký tự cực nhỏ như dấu `,`/`.` — đuôi dấu phẩy chỉ chiếm vài pixel ở 300
DPI, xấp xỉ ngưỡng nhiễu. Qua nhiều vòng thực nghiệm thực tế, chốt
**450 DPI** (khác đề xuất ban đầu 400 DPI). Đánh đổi: chi phí bộ
nhớ/thời gian tăng ~2.25x, áp dụng cho MỌI trang của MỌI PDF (kể cả
Digital-mode).

**Thay đổi 2 — Preprocess trước Tesseract** (`OCREngine._preprocess()`,
chạy SAU `_deskew()`):
- CLAHE (Contrast Limited Adaptive Histogram Equalization) — tăng
  contrast cục bộ, giảm rủi ro khuếch đại nhiễu ở vùng chi tiết nhỏ so
  với cân bằng histogram toàn ảnh.
- Unsharp masking — sigma nhỏ, amount khởi đầu thận trọng để tránh
  ringing artifact quanh nét mảnh (đúng vấn đề đang cố cải thiện).
- Thứ tự deskew-trước-preprocess: xác nhận qua thực nghiệm không có
  khác biệt rõ ràng so với thứ tự ngược lại — giữ nguyên thứ tự sẵn có.

Toàn bộ tham số (`PREPROCESS_CLAHE_CLIP_LIMIT`,
`PREPROCESS_CLAHE_TILE_GRID_SIZE`, `PREPROCESS_SHARPEN_SIGMA`,
`PREPROCESS_SHARPEN_AMOUNT`) là giá trị ước lượng ban đầu, cần tinh
chỉnh khi có dữ liệu thật đa dạng hơn.

Verify: kết hợp ADR-052+053, tỷ lệ lỗi nhầm dấu giảm xuống dưới 0.5% —
chưa về 0%.

Xác nhận trong implementation: `core/domain/constants.py::Image.DPI`,
`core/domain/constants.py::OCR` (4 hằng số Preprocess),
`core/extraction/ocr_engine.py::OCREngine._preprocess()`.

------------------------------------------------------------------------

## ADR-054 --- Amend ADR-048: Lý Do Giữ RGB Đổi Sang Tính Bất Khả Nghịch

**Status:** Accepted (amends ADR-048)

ADR-048 quyết định trong bối cảnh OCR engine là PaddleOCR, lý do "giữ
màu thật giúp OCR tận dụng contrast màu thật". Từ ADR-047, OCR engine
đã chuyển sang Tesseract — cần đánh giá lại.

Tesseract (kể cả LSTM/tessdata_best) tự quy đổi ảnh về grayscale ở
bước xử lý nội bộ đầu tiên (nền tảng Leptonica), không có cơ chế học
đặc trưng màu như PaddleOCR. A/B test thực tế không cho thấy khác biệt
rõ ràng về độ chính xác.

**Quyết định: VẪN GIỮ RGB**, nhưng đổi lý do chính sang: tính bất khả
nghịch của chuyển đổi. Grayscale → RGB không khôi phục được thông tin
màu đã mất, trong khi RGB → Grayscale luôn thực hiện được ở bất kỳ
điểm nào trong pipeline khi cần. Giữ RGB ở tầng `PDFReader` bảo toàn
tùy chọn khai thác kênh màu riêng biệt trong tương lai (VD tách kênh
đỏ làm nổi bật con dấu/mực đỏ), đổi lại chấp nhận chi phí bộ nhớ ~3x/
trang.

**Lưu ý:** `OCREngine._preprocess()` (ADR-053) tự chuyển ảnh về
grayscale nội bộ rồi nhân bản lại 3 kênh giống hệt nhau — "RGB" thực
tế đưa vào Tesseract ở bước cuối KHÔNG còn mang thông tin màu thật
nào. Đây là hệ quả đã biết, không mâu thuẫn với quyết định giữ RGB ở
tầng `PDFReader` (2 tầng phục vụ 2 mục đích khác nhau).

Xác nhận trong implementation: không đổi `core/reading/pdf_reader.py`
(giữ nguyên như ADR-048); `core/extraction/ocr_engine.py::OCREngine._preprocess()`.

------------------------------------------------------------------------

## ADR-055 --- Thứ Tự Ưu Tiên Hiển Thị Warning Theo `RuleCategory`

**Status:** Accepted

`Worker._format_note()` từng chọn `analysis.warnings[0]`, nhưng
`DocumentAnalysis.warnings` được flatten theo đúng thứ tự rule chạy cố
định trong `_evaluate_rules()` — luôn đặt warning của `text_coverage`
lên đầu bất kể mức độ liên quan tới quyết định `mode` cuối cùng. Hệ
quả: có thể hiển thị cảnh báo "bằng chứng yếu" của 1 rule đơn lẻ cạnh
1 kết luận High confidence được củng cố bởi các rule khác, gây cảm
giác mâu thuẫn dù dữ liệu không sai.

**2 phương án được thảo luận:**
- Phương án A (đã chọn): sửa tại `PDFDetector.analyze()` — sắp lại thứ
  tự warnings theo `RuleCategory` trước khi trả về.
- Phương án B (không chọn): sửa tại `Worker._format_note()`.

**Lý do chọn A:** sửa đúng gốc, mọi consumer tương lai của
`DocumentAnalysis.warnings` (không chỉ `Worker`) đều nhận thứ tự hợp lý.

**Thiết kế:** `PDFDetector._WARNING_CATEGORY_PRIORITY` định nghĩa thứ
tự ưu tiên category (không hard-code tên rule): category về **chất
lượng tài liệu** (`QUALITY`, `LAYOUT`, `DOCUMENT`, `GRAPHICS`) ưu tiên
trước category mô tả **độ không chắc chắn của riêng 1 rule**
(`CONSISTENCY`, `IMAGE`, `TEXT`). `_evidence_warnings_ordered()` sort
`Evidence` theo category (dùng `sorted()` ổn định) trước khi flatten.

**Dọn kèm:** xóa nhánh `extraction.warnings` chết trong
`Worker._format_note()` (dead code — không bao giờ chạy tới trong
pipeline thật, vì `Worker` không bao giờ gọi `Extractor.extract()` khi
mode UNKNOWN). `_format_note()` nay chỉ nhận `analysis`.

Xác nhận trong implementation:
`core/detection/pdf_detector.py::PDFDetector._evidence_warnings_ordered()`,
`PDFDetector._WARNING_CATEGORY_PRIORITY`; `ui/worker.py::Worker._format_note()`.

------------------------------------------------------------------------

## ADR-056 --- `Extractor.extract()` Raise `ValueError` Khi UNKNOWN

**Status:** Accepted (đồng bộ hóa với ADR-027)

Phát hiện qua rà soát source thật: `core/extraction/extractor.py::Extractor.extract()`
**không hề raise** `ValueError` khi UNKNOWN như ADR-027 mô tả — code
thật trả về gracefully `ExtractionResult(words_by_page={}, warnings=(...))`.
Sai lệch tồn tại xuyên suốt ADR-027/CHANGELOG/SESSION_SUMMARIES (Session
2026-07-31) trong nhiều tuần, chỉ được phát hiện qua rà soát trực tiếp
source tại Session 2026-08-12 — không có cơ chế nào chủ động phát hiện
lệch pha này sớm hơn (xem DEVELOPMENT_WORKFLOW.md Rule 15).

**Quyết định:** sửa **code** khớp lại ADR-027 (thêm `raise ValueError`),
không sửa tài liệu khớp code. Lý do: ADR-027 là quyết định kiến trúc
có lập luận rõ ràng (phân định 2 tầng lỗi khác bản chất — business
outcome vs programming-contract violation), không phải mô tả tùy tiện.
Vì `Worker` đã chặn đúng ở tầng gọi, thêm `raise` không ảnh hưởng
pipeline thật — chỉ thêm 1 lớp phòng vệ (defense in depth) cho lỗi
lập trình tương lai.

**Hệ quả kèm theo:** `ExtractionResult.warnings` trở thành field chết
sau patch — đã xóa khỏi `core/domain/models.py`.

Xác nhận trong implementation:
`core/extraction/extractor.py::Extractor.extract()`,
`core/domain/models.py::ExtractionResult`.

------------------------------------------------------------------------

## ADR-057 --- Bổ Sung Document Rules & Graphics Rules Cho `PDFDetector`

**Status:** Accepted

TDS (`PDF_Detector_Technical_Design.docx` §7.2) định nghĩa 7 Rule
Category, nhưng `PDFDetector` trước patch này chỉ implement 5/7 (Text,
Image, Consistency, Quality, Layout) — Document (RC-001) và Graphics
(RC-004) còn thiếu.

**Xác nhận trước khi thiết kế:** TDS §7.2 chỉ đặc tả RC-001/RC-004 ở
mức định tính, cấp cao — không có công thức/ngưỡng cụ thể, kể cả cho 5
rule đã implement. Vì vậy 2 rule mới là **thiết kế mới hoàn toàn**
(không phải "khôi phục" nội dung TDS), dựa trên field đã có sẵn trong
`AnalysisContext` nhưng trước đó chưa được dùng để tạo `supports`.

**Document Rule** (`document_metadata`, category `DOCUMENT`): dùng
`AnalysisContext.metadata` (Producer/Creator). Nếu chứa từ khóa gợi ý
phần mềm scan (`_SCAN_METADATA_KEYWORDS`) → `supports={SCANNED: 0.20}`.
Không tạo `supports` cho DIGITAL khi thiếu từ khóa (vắng mặt tín hiệu
không phải bằng chứng).

**Graphics Rule** (`vector_graphics_coverage`, category `GRAPHICS`):
dùng `AnalysisContext.drawing_page_ratio`. PDF Scanned thuần túy về
bản chất không có vector drawing operations. Nếu
`drawing_page_ratio >= 0.50` → `supports={DIGITAL: 0.20}`. Tương tự,
không tạo `supports` cho SCANNED khi thiếu vector graphics.

**Trọng số 0.20 cho cả 2 rule (thấp, cố ý):** cả 2 rule chưa qua thực
nghiệm với PDF thật đa dạng — trọng số thấp để không làm lệch các
quyết định biên (DIGITAL/HYBRID) vốn đã ổn định. Đã tự kiểm tra: tổng
`supports` tối đa theo từng mode sau khi thêm 2 rule mới (DIGITAL
<= 0.90, SCANNED <= 1.15, HYBRID <= 1.00) đều dưới
`_EVIDENCE_SCORE_SCALE = 1.40` — không cần hiệu chỉnh scale.

**Placeholder (cùng nhóm `TemplateMatching.*`):**
`_DOCUMENT_RULE_WEIGHT`, `_GRAPHICS_RULE_WEIGHT`,
`_GRAPHICS_DRAWING_PAGE_RATIO = 0.50`, `_SCAN_METADATA_KEYWORDS` đều
là giá trị ước lượng ban đầu, cần tinh chỉnh khi có dữ liệu thật.

Verify: chạy thật trên PDF Digital và Scanned đã dùng trước đây —
`DocumentAnalysis.evidence` có đủ 7 phần tử, mode cuối cùng không đổi
so với trước patch (đúng kỳ vọng — trọng số thấp, chỉ ảnh hưởng case
biên gần tie-margin).

Xác nhận trong implementation:
`core/detection/pdf_detector.py::PDFDetector._evaluate_document_rule()`,
`PDFDetector._evaluate_graphics_rule()`, `PDFDetector._evaluate_rules()`.

------------------------------------------------------------------------

## ADR-058 --- Hiển Thị `relative_path` Thay Vì `file_name`

**Status:** Accepted

Khi Input Folder là 1 thư mục cha chứa nhiều thư mục con (VD "Quý 3"
chứa "Tháng 7"/"Tháng 8"/"Tháng 9", mỗi thư mục con có file trùng tên
như `HD_001.pdf`), tầng discovery (`rglob`) đã quét đúng, không sót/
không ghi đè. Nhưng mọi nơi hiển thị/ghi log (`ProcessingTableModel`,
`ReportWriter._log_results()`, `ReportWriter._format_report()` mục
Warnings) đều dùng `PDFResult.file_name` (chỉ basename) — khiến các
dòng từ thư mục con khác nhau hiển thị/log giống hệt nhau, mất khả
năng truy vết dù dữ liệu Excel không sai.

`PDFResult.relative_path` đã được tính sẵn từ đầu nhưng không nơi nào
tiêu thụ.

**Giải pháp (tối thiểu, không đổi contract dữ liệu):**
1. `ProcessingTableModel.data()` cột PDF: dùng
   `str(item.relative_path) or item.file_name`.
2. `ReportWriter._log_results()`: log `relative_path` thay vì
   `file_name`.
3. `ReportWriter._format_report()` mục Warnings: giữ nguyên full
   absolute path của `warning.source_file` (KHÔNG đổi
   `InvoiceInfo.source_file` sang relative — field này còn phục vụ
   mục đích khác, có thể map trực tiếp vào cột Excel).

Xác nhận trong implementation: `ui/models/processing_table_model.py::ProcessingTableModel.data()`,
`core/export/report_writer.py::ReportWriter._log_results()`, `_format_report()`.
Verify: chạy thật kịch bản "Quý 3 → Tháng 7/8/9 → HD_001...HD_100 trùng
tên" — UI Table/app.log/report.txt đều phân biệt đúng theo thư mục con.

------------------------------------------------------------------------

## ADR-059 --- Giới Hạn Kiến Trúc Của TemplateMatcher Với Giá Trị Đa Dòng

**Status:** Accepted (ghi nhận giới hạn, không triển khai giải pháp ở v1)

Đánh giá rủi ro (chưa gặp thật trên `HD2026-0003_digital.pdf` A4
chuẩn; đánh giá dựa trên suy luận cho layout chưa test: A5, bảng biểu
phụ).

**2 khía cạnh cùng gốc rễ:**
1. `max_distance`/`axis_tolerance` là tỉ lệ hình học TĨNH, tinh chỉnh
   thực nghiệm trên đúng 1 layout (A4). Với layout khác, tỉ lệ khoảng
   cách nhãn-giá trị thay đổi tương đối — `max_distance` cũ có thể quá
   rộng hoặc quá hẹp.
2. `_merge_same_line()` (ADR-044) chủ động giới hạn trong đúng 1 dòng
   — chưa từng xử lý "giá trị trải dài NHIỀU DÒNG".

Bản chất vấn đề: ranh giới đúng của 1 giá trị chỉ có thể suy ra từ ngữ
nghĩa/nội dung — không thể suy ra thuần túy từ tọa độ hình học. Bài
toán "gà và trứng": độ dài giá trị chỉ biết được SAU KHI xác định đúng
ranh giới, nhưng ranh giới lại cần biết trước độ dài.

**Đã cân nhắc và BÁC BỎ 2 hướng vá** (chi tiết lý do bác bỏ: xem
SESSION_SUMMARIES.md, Session 2026-08-13):
- Window động theo Key Token/Section kế tiếp làm biên.
- Multi-direction/khóa `direction=BELOW` cho field dễ wrap.

**Kết luận kiến trúc:** đây KHÔNG phải bug patch được bằng cách thêm
rule/tinh chỉnh tham số ở tầng `TemplateMatcher` hiện tại. Là giới hạn
NỀN TẢNG của phương pháp hình học tĩnh khi `SpatialRelation` được khai
báo cố định trước khi biết nội dung thật. Lời giải triệt để: engine
LayoutLM-class (v2.0, đã ghi nhận từ Session 2026-08-01/02) — không
phải điều chỉnh thêm heuristic cho v1.

Quyết định: KHÔNG triển khai giải pháp ở v1. Không xếp cùng nhóm "known
limitation cần tinh chỉnh tham số" (khác ADR-044/045/052) — đây là
giới hạn cấu trúc không patch được trong cùng kiến trúc.

Không có implementation nào để confirm (quyết định KHÔNG code).

------------------------------------------------------------------------

## ADR-060 --- Tái Cấu Trúc `core/` Theo Pipeline Stage

**Status:** Accepted

Từ khi khởi tạo dự án, `core/` chứa 13 file phẳng, gộp chung nhiều
tầng trách nhiệm pipeline khác nhau (Reading/Detection/Extraction/
Parsing/Export) đã có ADR riêng biệt (ADR-016/020/024/029/037) nhưng
không phản ánh qua cấu trúc thư mục.

Động lực triển khai trước khi bắt đầu v2.0: kế hoạch v2.0 dự kiến bổ
sung/thay đổi nhiều model cho các module hiện có (đặc biệt Parser: thêm
engine LayoutLM song song TemplateMatcher, xem ADR-059) — cấu trúc
phẳng sẽ càng khó quản lý khi số lượng file tăng.

**Cấu trúc mới:**
```
core/
    domain/        (models.py, enums.py, constants.py)
    reading/        (pdf_reader.py)
    detection/      (pdf_detector.py)
    extraction/     (extractor.py, ocr_engine.py)
    parsing/        (parser.py, template/*)
    export/         (excel_mapper.py, excel_writer.py, report_writer.py)
ui/
    models/         (processing_table_model.py)
```

Mỗi thư mục package mới đều có `__init__.py` rỗng — chọn regular
package (explicit `__init__.py`) thay vì namespace package (PEP 420)
để giữ tính tường minh và tương thích tool.

`config.py` ở root KHÔNG đổi.

Triển khai theo 7 bước tuần tự (đúng Rule 2/3): domain/ → ui/models/ →
reading/ → detection/ → extraction/ (+ di chuyển test) → parsing/ +
parsing/template/ → export/. Bước cuối: chạy lại toàn bộ `pytest -v` +
1 lượt UI thật end-to-end.

Xác nhận trong implementation: toàn bộ `core/*.py` đã di chuyển theo
cấu trúc trên; `ui/worker.py`/`utils/logger.py`/`ui/widgets.py`/
`ui/main_window.py` đã cập nhật import tương ứng.

------------------------------------------------------------------------

## ADR-061 --- OCREngine: Kiểm Tra tessdata_best Trì Hoãn Đến Lần Đầu `recognize()`

**Status:** Accepted (amends ADR-047)

`Worker.__init__` khởi tạo `Extractor()` (và qua đó `OCREngine()`) **vô
điều kiện** ngay khi `MainWindow` được tạo — trước khi biết batch nào
sẽ được xử lý, thậm chí trước khi biết có PDF Scanned/Hybrid nào cần
OCR hay không.

`OCREngine.__init__()` (theo ADR-047 gốc) fail-fast kiểm tra
`vie.traineddata` ngay trong constructor. Hệ quả: **toàn bộ ứng dụng
crash ngay lúc khởi động** nếu thiếu `tessdata_best` — kể cả người
dùng chỉ xử lý PDF Digital. Mâu thuẫn với đối tượng người dùng mục
tiêu (office user, không biết lập trình).

**Giải pháp:** chuyển kiểm tra `vie.traineddata` từ `__init__()` sang
lần đầu tiên `recognize()` được gọi (`OCREngine._ensure_traineddata()`,
cache qua `self._traineddata_checked`).

**Hành vi mới:**
- Batch toàn PDF Digital: không bao giờ gọi `recognize()`, app luôn
  mở được.
- Batch có PDF Scanned/Hybrid mà thiếu `tessdata_best`:
  `FileNotFoundError` raise tại `recognize()` → đã nằm trong try/except
  riêng của `Worker._process_pdf()` → đúng 1 file đó nhận
  `ProcessStatus.FAILED`, các file khác tiếp tục bình thường.

Xác nhận trong implementation:
`core/extraction/ocr_engine.py::OCREngine.__init__()`,
`OCREngine._ensure_traineddata()`, `OCREngine.recognize()`.

------------------------------------------------------------------------

## ADR-062 --- `TemplateDefinition` Validate Tổng `identification_weight` > 0

**Status:** Accepted

Nếu mọi field trong 1 Template Definition đều để
`identification_weight = 0.0` (kể cả do quên), `_score_template()`
tính `score = matched_weight / total_weight` với `total_weight = 0` →
luôn trả `score = 0.0` → luôn dưới `TEMPLATE_MIN_SCORE` →
`select_template()` luôn trả `None` cho template này, **im lặng,
không lỗi, không cảnh báo** — dù JSON hoàn toàn hợp lệ về schema.

**Giải pháp:** `TemplateDefinition.__post_init__()` thêm validate: nếu
tổng `identification_weight` của mọi field <= 0 → raise `ValueError`.
Đặt SAU validate section đã có (ADR-045). Theo cơ chế fail-soft per
file sẵn có (ADR-031): `TemplateLoader` tự bắt `ValueError` này, log
warning, bỏ qua file.

Lý do raise ngay tại `TemplateDefinition` (thời điểm load) thay vì ở
`TemplateMatcher._score_template()` (thời điểm chạy): phát hiện lỗi
authoring sớm nhất có thể.

Xác nhận trong implementation:
`core/domain/models.py::TemplateDefinition.__post_init__()`,
`resources/TEMPLATE_AUTHORING_GUIDE.md` Mục 5.2/9.

------------------------------------------------------------------------

## ADR-063 --- Tập Trung Hằng Số Threshold Vào `constants.py`

**Status:** Accepted

Dự án đã có tiền lệ tập trung các ngưỡng "placeholder cần tinh chỉnh"
vào `core/domain/constants.py` (`TemplateMatching`, `OCR`,
`NumberRepair`), nhưng 2 nhóm sau chưa theo quy ước này:

1. **`PDFDetector`**: 9 hằng số threshold/weight nằm inline làm class
   attribute (`_DIGITAL_TEXT_PAGE_RATIO`, `_DIGITAL_AVERAGE_TEXT_LENGTH`,
   `_HYBRID_CONTENT_PAGE_RATIO`, `_HIGH_EMPTY_PAGE_RATIO`,
   `_DECISION_TIE_MARGIN`, `_EVIDENCE_SCORE_SCALE`,
   `_DOCUMENT_RULE_WEIGHT`, `_GRAPHICS_RULE_WEIGHT`,
   `_GRAPHICS_DRAWING_PAGE_RATIO`).
2. **`ValueConverter`**: 4 hằng số module-level
   (`_DEFAULT_THOUSAND_SEPARATOR`, `_DEFAULT_DECIMAL_SEPARATOR`,
   `_CURRENCY_SUFFIXES`, `_SINGLE_CHAR_CURRENCY_SUFFIXES`).

**Giải pháp:** tạo 2 class mới trong `core/domain/constants.py`:
`PDFDetection` (9 hằng số của `PDFDetector`) và `Currency` (4 hằng số
của `ValueConverter`).

**Cố ý KHÔNG di chuyển:**
- `PDFDetector._SCAN_METADATA_KEYWORDS` — dữ liệu tra cứu, không phải
  threshold số học.
- `PDFDetector._WARNING_CATEGORY_PRIORITY` — logic sắp xếp (ADR-055),
  không phải giá trị cần tinh chỉnh theo dữ liệu.

Đây thuần túy là refactor tổ chức lại vị trí hằng số, KHÔNG đổi bất kỳ
giá trị hay hành vi runtime nào.

Xác nhận trong implementation: `core/domain/constants.py::PDFDetection`,
`Currency`; `core/detection/pdf_detector.py`,
`core/parsing/template/value_converter.py` (cập nhật tham chiếu).

------------------------------------------------------------------------

## ADR-064 --- `Worker.report_path` Fallback Về `report.txt` Trên Đĩa

**Status:** Accepted (amends ADR-041)

`Worker.report_path` trước patch chỉ trả `self._report_path` — field
này CHỈ được set trong `Worker._write_excel()`, tức chỉ có giá trị sau
khi `process()` đã chạy xong trong đúng lần mở app hiện tại. Mở lại
ứng dụng → `self._report_path = None` → bấm Report luôn báo
`REPORT_NOT_AVAILABLE`, dù `reports/Report.txt` từ lần chạy trước vẫn
còn nguyên trên đĩa.

**Giải pháp:** đường dẫn `report.txt` cố định, xác định trước
(`REPORTS_DIR/Report.FILE_PREFIX+FILE_EXTENSION`, không timestamp —
ADR-040), nên có thể kiểm tra tồn tại trên đĩa mà không cần đã chạy
`write()` trong phiên hiện tại:

- `ReportWriter.expected_path(reports_dir) -> Path` (staticmethod mới)
  — tách logic tính đường dẫn ra để dùng lại.
- `Worker.report_path` property: nếu `self._report_path is not None`
  thì trả như cũ (ưu tiên phiên hiện tại); ngược lại fallback kiểm tra
  `ReportWriter.expected_path(REPORTS_DIR).exists()`.
- `MainWindow._report()`: KHÔNG đổi gì — vẫn chỉ đọc
  `worker.report_path` (ADR-001: UI không tự quyết định file tồn tại).

**Amend ADR-041:** nguyên tắc "Report button chỉ mở file đã sinh sẵn,
không tự trigger sinh" VẪN GIỮ NGUYÊN — chỉ mở rộng phạm vi "đã tồn
tại sẵn" sang "bất kỳ lúc nào trước đó, kể cả phiên mở app trước".

Xác nhận trong implementation:
`core/export/report_writer.py::ReportWriter.expected_path()`,
`ui/worker.py::Worker.report_path`.

------------------------------------------------------------------------

## ADR-065 --- Sửa Lỗi Validate Input Rỗng (`Path()` Truthiness Bug)

**Status:** Accepted

`MainWindow._start()` validate input rỗng bằng
`if not self.input_widget.path(): ...`. `PathSelectorWidget.path()`
trả `Path()` (rỗng, mặc định) khi chưa chọn gì — nhưng `pathlib.Path`
KHÔNG override `__bool__`/`__len__`, nên `bool(Path())` luôn `True` bất
kể nội dung. Hệ quả: validate này chưa từng thật sự hoạt động — bấm
Start khi chưa chọn Input Folder/Output Excel không bị chặn.

**Hậu quả dây chuyền:** `Worker.configure(Path(), Path())` được gọi
với 2 `Path` rỗng (không phải `None`) → `process()` chạy
`Path().rglob("*.pdf")`, quét đệ quy từ working directory hiện tại của
tiến trình — nguy cơ chạy sai dữ liệu và treo app trên cây thư mục lớn
(xem ADR-066).

**Giải pháp:** thêm `PathSelectorWidget.is_empty() -> bool`, kiểm tra
trực tiếp trên text (`not self.edit_path.text().strip()`), KHÔNG qua
`Path()` để tránh bẫy truthiness. `MainWindow._start()` sửa dùng
`is_empty()` thay cho `not self.xxx_widget.path()`.

Xác nhận trong implementation: `ui/widgets.py::PathSelectorWidget.is_empty()`,
`ui/main_window.py::MainWindow._start()`.

------------------------------------------------------------------------

## ADR-066 --- PDF Discovery Chuyển Sang `os.walk()`

**Status:** Accepted

`Worker.process()` dùng `sorted(self._input_folder.rglob("*.pdf"))` —
`sorted()` ép generator của `rglob()` chạy hết ngay lập tức để tạo
list rồi sort, toàn bộ việc duyệt đệ quy diễn ra liền 1 mạch, KHÔNG có
điểm nào để kiểm tra `self._cancel_requested` giữa chừng.

Hệ quả: nếu Input Folder có cấu trúc lớn/sâu (VD ổ đĩa mạng công ty
hàng chục nghìn file — đúng đối tượng mục tiêu theo PROJECT_CONTEXT.md
§1), bấm Stop trong lúc discovery đang chạy KHÔNG có tác dụng cho đến
khi `rglob()` tự hoàn tất.

**Giải pháp:** `Worker._discover_pdf_files()` tự viết dựa trên
`os.walk()`, kiểm tra `self._cancel_requested` sau MỖI file — phản hồi
Stop gần như tức thời. Trả `None` nếu bị hủy giữa chừng (phân biệt với
list rỗng = quét xong, không tìm thấy PDF nào); `process()` kiểm tra
`None` và emit `cancelled` sớm nếu gặp.

**Thay đổi hành vi phụ (cố ý):** so khớp `.pdf` bằng
`name.lower().endswith(".pdf")` — case-insensitive trên MỌI hệ điều
hành, khác `rglob("*.pdf")` cũ (case-sensitive trên Linux/Mac). Chấp
nhận vì đối tượng người dùng chính là Windows office user, nơi hoa/
thường vốn không phân biệt.

Xác nhận trong implementation: `ui/worker.py::Worker._discover_pdf_files()`,
`Worker.process()`.

------------------------------------------------------------------------

## ADR-067 --- Worker v2.0: Xử Lý Đa Luồng Qua `QThreadPool`, Mô Hình Event-Driven

**Status:** Accepted

Bắt đầu v2.0 (từ Session 2026-08-15), `Worker.process()` chuyển từ vòng
lặp tuần tự (v1) sang dispatch `PDFTaskRunnable` (mới) vào
`QThreadPool`, theo `MULTI_THREAD_SPECIFICATION.md`. 5 quyết định kiến
trúc đã chốt trước khi implement (Rule 11):

1. **Non-blocking, event-driven** — `process()` dispatch toàn bộ task
   rồi return ngay, KHÔNG gọi `QThreadPool.waitForDone()` (blocking).
   Lý do: `Worker` là `QObject` trên `QThread` riêng, không có event
   loop phụ; blocking sẽ chặn dispatch Signal `completed`/`failed` từ
   Pool thread tới UI cho đến khi mọi task xong — Progress/Table sẽ
   không còn cập nhật real-time. Tổng hợp kết quả + trigger
   `_write_excel()`/`finished` chuyển hoàn toàn sang slot
   `_on_task_completed()`/`_on_task_failed()`, đếm `_processed_count`
   so với `_total_files`.
2. **ETA đơn giản hóa theo thông lượng thực tế** —
   `eta = (elapsed / processed) * remaining`, thay công thức
   exponential moving average riêng digital/OCR của v1 (vốn thiết kế
   cho tuần tự, không còn phản ánh đúng khi có concurrency).
3. **Cancellation ở mức task, không phải checkpoint giữa hàm** —
   `PDFTaskRunnable.run()` chỉ kiểm tra cờ hủy đúng 1 lần TRƯỚC khi
   gọi `_process_pdf()`. Task đã bắt đầu chạy tới khi xong tự nhiên;
   `QThreadPool.clear()` (gọi từ `Worker.cancel()`) loại task CHƯA
   chạy khỏi hàng đợi. Quyết định có chủ đích (Rule 9): không patch
   `_process_pdf()` để giữ nguyên khối business logic liền mạch
   (ADR-005).
4. **Thứ tự kết quả trên UI không còn xác định** — hệ quả tự nhiên,
   chấp nhận được, của xử lý song song (khác v1: luôn theo đúng thứ tự
   discovery).
5. **`OMP_THREAD_LIMIT`/`OMP_NUM_THREADS` set 1 lần, cấp process** —
   trong `Worker.__init__()`, trước khi bất kỳ `PDFTaskRunnable` nào
   gọi Tesseract (`MULTI_THREAD_SPECIFICATION.md` §5.1 — tránh N luồng
   Python × M luồng OpenMP con gây quá tải CPU).

**Xung đột với `MULTI_THREAD_SPECIFICATION.md` §4 bước 5 — đã giải
quyết theo Phương án A:** đặc tả gốc yêu cầu ghi Excel cho phần đã xử
lý được khi Stop giữa chừng — mâu thuẫn trực tiếp với ADR-008 (frozen
rule, `PROJECT_CONTEXT.md` §17: "Excel chỉ được ghi đúng 1 lần", "chỉ
sau khi MỌI PDF đã xử lý xong"). Quyết định: **giữ nguyên ADR-008**,
Stop → không ghi Excel, chỉ `cancelled.emit()`. §4 bước 5 của đặc tả
multi-thread bị coi là mô tả chưa cập nhật theo ADR-008, không áp dụng.

**Cancellation flag qua ranh giới luồng** — `PDFTaskRunnable` đọc
`Worker._cancel_requested` (kiểu `bool`) từ Pool thread qua closure,
không qua cơ chế đồng bộ hóa tường minh nào. An toàn trong CPython nhờ
GIL (không có torn read/write) và cách dùng hiện tại (đọc 1 lần, không
vòng lặp chờ) — nhưng đây là điểm duy nhất trong thiết kế dựa vào đảm
bảo ngầm của GIL thay vì API `threading` tường minh. **Ghi nhận, chưa
áp dụng** — xem Known Issue tương ứng ở `PROJECT_CONTEXT.md` §14.

Xác nhận trong implementation: `core/system/hardware.py` (Bước 1),
`ui/widgets.py::ThreadSelectorWidget` (Bước 2, dùng `QComboBox` giới
hạn `[1, recommended_threads]` — không mở rộng tới `total_cores` thật,
tránh người dùng chọn vượt mức an toàn), `ui/worker.py::PDFTaskSignals`,
`PDFTaskRunnable`, `Worker.process()`/`_on_task_completed()`/
`_on_task_failed()`/`_advance_progress()` (Bước 3).

------------------------------------------------------------------------

## ADR-068 --- Sửa Lỗi Treo Khi Stop Batch Lớn — Đảm Bảo Mọi `PDFTaskRunnable.run()` Luôn Emit Đúng 1 Signal

**Status:** Accepted

Phát hiện qua thực nghiệm thật (Bước 4, `MULTI_THREAD_SPECIFICATION.md`):
Stop trên batch PDF lớn khiến ứng dụng treo (mọi control ngoại trừ Exit),
`Elapsed` vẫn tiếp tục chạy — quan sát ban đầu của người dùng: hiện tượng
luôn xảy ra khi Stop rơi đúng vào 1 chuỗi tác vụ Digital.

### Quá trình chẩn đoán (3 vòng, mỗi vòng đều verify bằng chạy thật)

**Vòng 1 (đúng nhưng chưa đủ):** `_on_task_completed()`/`_on_task_failed()`
chặn sớm bằng `if self._cancel_requested: return` — khiến `_advance_progress()`
không bao giờ chạy sau Stop, trong khi điều kiện phát `cancelled` (dựa
trên `_processed_count >= _total_files`) chỉ được kiểm tra bên trong
`_advance_progress()`. Vì các task bị `QThreadPool.clear()` loại khỏi
hàng đợi sẽ không bao giờ gọi lại slot, điều kiện này không bao giờ đúng.
Sửa: gộp logic quyết định "khi nào phát `cancelled`" vào `_advance_progress()`,
dùng `QThreadPool.activeThreadCount() == 0` thay vì đếm theo `_total_files`.
Áp dụng thật vẫn còn treo ở một số tình huống — xác nhận chưa phải nguyên
nhân duy nhất.

**Vòng 2 (không phải nguyên nhân gốc, giữ lại làm phòng vệ):** giả thuyết
`PDFTaskSignals` (QObject không `parent`) bị GC trước khi event
`completed`/`failed` đã xếp hàng cross-thread kịp được Worker-thread
event loop xử lý (do `QRunnable.autoDelete()` xoá đối tượng C++ ngay sau
`run()` return). Fix: `Worker._active_tasks: set[PDFTaskRunnable]` giữ
tham chiếu Python tường minh tới từng `task` tới khi chính callback của
nó `discard()` nó ra. Áp dụng thật vẫn còn treo — xác nhận đây KHÔNG phải
nguyên nhân gốc rễ của bug đang gặp, dù vẫn là 1 rủi ro lifetime có thật
về mặt lý thuyết theo ngữ nghĩa PySide/Qt (queued cross-thread signal +
QObject không còn tham chiếu) — quyết định giữ nguyên patch này làm lớp
phòng vệ bổ sung, không gỡ bỏ.

**Vòng 3 (xác nhận đúng nguyên nhân gốc, tất định — không phải race):**
`PDFTaskRunnable.run()` có nhánh `if self._is_cancelled(): return` KHÔNG
emit bất kỳ signal nào. `QThreadPool.clear()` chỉ loại được task CHƯA
được dequeue khỏi hàng đợi — task đã dequeue (đang chờ CPU chạy `run()`)
đúng lúc Stop được bấm vẫn tiếp tục chạy, kiểm tra cờ hủy, return im
lặng. Nếu đây là task active cuối cùng, không còn lần gọi nào tới
`_advance_progress()`/bất kỳ slot nào để kiểm tra `activeThreadCount() == 0`
→ `cancelled` không bao giờ emit → treo vĩnh viễn.

Batch Digital hoàn tất cực nhanh (không qua Tesseract) khiến
`QThreadPool` liên tục dequeue dồn dập — xác suất "có task đang ở trạng
thái lưng chừng (đã dequeue, chưa chạy) đúng lúc Stop" cao hơn hẳn batch
OCR (chậm, rải rác theo thời gian) — giải thích đúng quan sát ban đầu
của người dùng.

### Giải pháp

Thêm signal `skipped` mới vào `PDFTaskSignals`. `PDFTaskRunnable.run()`
emit `skipped` trước khi return ở nhánh huỷ sớm. `Worker._on_task_skipped()`
(slot mới) đối xứng `_on_task_completed()`/`_on_task_failed()` nhưng
KHÔNG tăng `_processed_count` (PDF chưa từng được xử lý thật) — chỉ
`discard()` task khỏi `_active_tasks` và kiểm tra điều kiện phát `cancelled`.

**Bất biến (invariant) đạt được:** mọi lần `PDFTaskRunnable.run()` được
gọi, bất kể đi qua nhánh nào (thành công / lỗi / huỷ sớm), đều emit đúng
1 signal trước khi return — đảm bảo Worker luôn có cơ hội quan sát
`activeThreadCount() == 0` sau khi task active cuối cùng kết thúc.

**Đối chiếu với `MULTI_THREAD_SPECIFICATION.md` §4 bước 3:** đặc tả gốc
("task tự kết thúc nhanh, không gửi kết quả vào bộ nhớ") đã đúng ở việc
task bị huỷ sớm không tạo `PDFResult`, nhưng không lường trước rằng cơ
chế tracking tiến độ của `Worker` phụ thuộc vào việc MỌI task đều phát
tín hiệu gì đó — khoảng trống này nay đã đóng qua `skipped`.

Xác nhận trong implementation: `ui/worker.py::PDFTaskSignals.skipped`,
`PDFTaskRunnable.run()`, `Worker._on_task_skipped()`,
`Worker._advance_progress()`, `Worker.process()`,
`Worker.__init__._active_tasks`.

Verify: chạy thật batch 600 PDF (digital + OCR trộn), Stop nhiều lần ở
các thời điểm khác nhau, đặc biệt giữa chuỗi Digital dồn dập — không còn
treo, `Elapsed` dừng đúng lúc, UI mở khoá lại bình thường.

------------------------------------------------------------------------

## ADR-069 --- High-DPI Scaling Policy: `PassThrough` Cho Windows Scale Lẻ

**Status:** Accepted

`MULTI_THREAD_SPECIFICATION.md` §5 nguyên tắc 5 yêu cầu cấu hình PySide6
hỗ trợ scale 125%/150% chuẩn xác trên Windows. Rà soát `main.py` xác
nhận KHÔNG có bất kỳ cấu hình High-DPI nào — chỉ dựa vào hành vi mặc
định của Qt6 (tự bật High-DPI scaling, nhưng làm tròn hệ số scale phân
số về số nguyên gần nhất theo mặc định).

**Giải pháp:** gọi
`QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)`
**trước** khi khởi tạo `QApplication` (bắt buộc về thứ tự — policy chỉ
có hiệu lực nếu set trước instance `QApplication`/`QGuiApplication` đầu
tiên, theo tài liệu chính thức Qt).

**Lý do chọn `PassThrough` thay vì mặc định `Round`:** giữ đúng hệ số
scale phân số thật của hệ điều hành (VD 1.25, 1.5) thay vì Qt tự làm
tròn về số nguyên gần nhất — tránh layout/icon bị lệch đúng ở 2 mức
scale mà đặc tả nêu (125%/150% đều là hệ số lẻ, không nguyên).

**Rủi ro còn lại:** thay đổi này chỉ verify được bằng quan sát hình ảnh
thật trên Windows ở đúng scale 125%/150% — chưa có xác nhận trực quan
tại thời điểm ADR này được ghi (giới hạn môi trường phát triển). Cần
người dùng tự kiểm tra và xác nhận (đặc biệt `QTableView` — Processing
Table) trước khi coi nguyên tắc 5 là hoàn toàn đóng.

Xác nhận trong implementation: `main.py`.

------------------------------------------------------------------------

## ADR-070 --- Two-Pass ROI OCR Cho Field DECIMAL Nguồn OCR

**Status:** Accepted

Triển khai `OCR_ACCURACY_SPECIFICATION.md`: `TemplateMatcher` tự sở hữu 1
instance `OCREngine` riêng (`self._ocr_engine = OCREngine()` trong
`__init__`), thay vì chia sẻ instance với `Extractor` (Option B trong 2
phương án đã cân nhắc).

**Lý do chọn Option B (không chia sẻ instance với `Extractor`):**
`OCREngine.__init__()` không giữ tài nguyên nặng (không load model vào
tiến trình - Tesseract chạy qua subprocess mỗi lần gọi, xem ADR-047 "Hệ
quả kiến trúc quan trọng"), chỉ tốn vài trăm byte (1 chuỗi config + 1
bool). `TemplateMatcher` chỉ được khởi tạo đúng 1 lần trong
`Worker.__init__()` (không phải per-thread/per-task), nên chi phí Option
B là O(1) cố định, KHÔNG scale theo `thread_count` hay số PDF trong batch
- xác nhận qua phân tích kiến trúc `QThreadPool`/`PDFTaskRunnable`
(ADR-067): mọi task chia sẻ đúng 1 `TemplateMatcher` instance của
`Worker`. Đổi lại, tránh phải sửa `Extractor.__init__()`/`Worker.__init__()`
(phạm vi thay đổi hẹp hơn, đúng Rule 2).

`_resolve_decimal_value()` (mới, trong `TemplateMatcher`) quyết định kích
hoạt Pass 2 khi: `field_def.value_type is ValueType.DECIMAL` VÀ
`anchor.source == "ocr"` - không đụng PDF Digital (`source="digital"`
không bao giờ kích hoạt) hay field DATE. Fail-soft tuyệt đối (đối xứng
ADR-032/033): `page_image` thiếu, hoặc `recognize_numeric_roi()` raise
bất kỳ lỗi gì -> fallback về `anchor.text` (Pass 1), không propagate lên
Parser/Worker.

Xác nhận trong implementation: `core/parsing/template/template_matcher.py::TemplateMatcher.__init__()`,
`_extract_field_value()` (đổi tên từ `_select_best_value()`),
`_resolve_decimal_value()`; `core/extraction/ocr_engine.py::OCREngine.recognize_numeric_roi()`,
`_crop_roi()`.

------------------------------------------------------------------------

## ADR-071 --- Validate `roi_text` Theo `value_pattern` Trước Khi Chấp Nhận Pass 2

**Status:** Accepted

**Phát hiện qua debug thực nghiệm (không phải suy đoán trước):** sau khi
triển khai ADR-070, batch test thật xuất hiện regression nghiêm trọng -
nhiều field DECIMAL nguồn OCR trả về `None` (biểu hiện: ô Excel trống +
`Report.txt` ghi `field=None`) dù trước đó (baseline, chưa có Two-Pass)
hoạt động bình thường.

**Quá trình chẩn đoán (3 giả thuyết bị loại trừ bằng thực nghiệm thật
trước khi tìm đúng nguyên nhân):**
1. Giả thuyết sai lệch hệ tọa độ do thiếu deskew trong `recognize_numeric_roi()`
   - sửa (xem ADR-072) nhưng KHÔNG giải quyết được regression `None`.
2. Giả thuyết cấu hình Global Pass (`self._config`, DAWG-disable +
   `textord_heavy_nr`) làm hỏng token số ở Pass 1 - revert tạm để test,
   KHÔNG giải quyết được regression `None` (nhưng phát hiện phụ quan
   trọng, xem ADR-074).
3. Xác nhận đúng nguyên nhân qua thực nghiệm cô lập: tắt hẳn Pass 2
   (bypass `_resolve_decimal_value()`, chỉ dùng `anchor.text`) khôi phục
   đúng kết quả - xác nhận vấn đề nằm trong chính logic quyết định của
   Pass 2, không phải Pass 1/deskew.

**Nguyên nhân gốc:** `_resolve_decimal_value()` (bản gốc) chấp nhận
`roi_text` **vô điều kiện** nếu không rỗng
(`return roi_text or anchor.text`) - không có bước validate. Pass 2 (PSM=7,
context hẹp hơn Pass 1 nhiều) có xu hướng trả về chuỗi không rỗng nhưng
KHÔNG hợp lệ (VD lẫn ký tự thừa từ nội dung liền kề - xem ADR-073), ghi
đè lên `anchor.text` vốn đúng. Chuỗi rác này lọt qua `TemplateMatcher`
(không validate), tới `ValueConverter._to_decimal()` - theo đúng ADR-032
("convert lỗi -> field = None, không raise"), `Decimal()` không parse
được chuỗi rác nên trả `None`. Từ góc nhìn Report.txt, hiện tượng này
KHÔNG phân biệt được với "field không tìm thấy" - dễ gây hiểu nhầm là
lỗi ở tầng khác.

**Giải pháp:** `_resolve_decimal_value()` validate `roi_text` bằng chính
`field_def.value_pattern` (tái dùng `_get_compiled_pattern()` đã có sẵn
cho Pass 1 Value Matching - không thêm logic mới) trước khi chấp nhận.
Nếu `roi_text` không khớp pattern -> coi Pass 2 không đáng tin, fallback
về `anchor.text`.

**Giới hạn đã biết (chưa giải quyết, phát hiện qua case `vat_amount` cụ
thể - anchor sai `933.038`, roi đúng giá trị nhưng dư ký tự `933,038V`):**
validate theo `value_pattern` chỉ phát hiện được rác SAI CẤU TRÚC, KHÔNG
phát hiện được lỗi "đúng cấu trúc nhưng sai giá trị" (VD đọc nhầm `,`/`.`
mà chuỗi kết quả vẫn khớp `^[0-9.,]+...$`) - value_pattern hiện tại chấp
nhận cả 2 loại dấu. Đây là động lực trực tiếp dẫn tới ADR-073.

Xác nhận trong implementation:
`core/parsing/template/template_matcher.py::TemplateMatcher._resolve_decimal_value()`.

------------------------------------------------------------------------

## ADR-072 --- `recognize_numeric_roi()` Phải Deskew Trước Khi Crop

**Status:** Accepted

`WordToken.normalized_bbox` của mọi token nguồn OCR được `Extractor`
tính từ tọa độ pixel SAU khi `recognize()` (Pass 1) đã deskew nội bộ -
tức mô tả vị trí trên ảnh ĐÃ XOAY THẲNG. `page_image.samples` (lưu
trong `ExtractionResult.page_images`) là ảnh GỐC, CHƯA XOAY (theo
ADR-026/048 - Reader chỉ đọc thô). `recognize_numeric_roi()` (Pass 2)
bản đầu tiên cắt trực tiếp từ `page_image` chưa xoay bằng bbox đã tính
trong hệ tọa độ đã xoay - sai lệch hệ tọa độ có thật với mọi trang có độ
nghiêng >= `OCR.DESKEW_MIN_ANGLE` (0.5°).

**Lưu ý quan trọng:** thực nghiệm xác nhận đây KHÔNG phải nguyên nhân
của regression `None` hàng loạt (xem ADR-071) - fix này độc lập, giải
quyết đúng 1 lớp lỗi khác (misalignment khi trang nghiêng), không được
phép revert dù không phải nguyên nhân chính đang debug tại thời điểm đó.

**Giải pháp:** gọi lại `self._deskew(image)` (cùng hàm tất định, thuần
túy dùng bởi `recognize()`) ngay sau `_to_numpy_array()`, trước khi cắt
ROI - tái tạo chính xác cùng ảnh đã xoay dùng ở Pass 1, đảm bảo
`normalized_bbox` khớp đúng hệ tọa độ.

Xác nhận trong implementation:
`core/extraction/ocr_engine.py::OCREngine.recognize_numeric_roi()`.

------------------------------------------------------------------------

## ADR-073 --- ROI Padding Tính Theo Tỉ Lệ Chiều Cao Bbox, Không Theo Trang

**Status:** Accepted (giá trị `ROI_PADDING_RATIO` đang trong quá trình
tinh chỉnh - xem SESSION_SUMMARIES.md, chưa freeze giá trị cuối)

**Phát hiện qua debug log trực tiếp** (in `anchor.text`/`roi_text` trước
khi validate, trên 1 PDF cụ thể có 4 field DECIMAL): TOÀN BỘ 4/4
`roi_text` đều dư thêm ký tự (thường là mảnh đầu ký hiệu tiền tệ "V")
so với `anchor.text` đúng - mẫu lặp lại có hệ thống, không ngẫu nhiên.

**Nguyên nhân:** thiết kế gốc (`ROI_PADDING_X`/`ROI_PADDING_Y`, theo
Mục 4.2.A của `OCR_ACCURACY_SPECIFICATION.md`) tính padding theo TỈ LỆ
KÍCH THƯỚC TRANG (VD ở DPI 450/A4, `ROI_PADDING_X=0.02` => ~74px mỗi
bên) - hằng số tuyệt đối này KHÔNG tương quan với kích thước của chính
token đang cắt. Với field ngắn (VD `"10%"`, 3 ký tự), 74px padding là tỉ
lệ rất lớn so với chính bbox của nó -> tràn sang cột/nhãn liền kề trong
bảng chi tiết thanh toán (subtotal/vat_rate/vat_amount/total_amount
thường nằm sát nhau) - khớp đúng quan sát: field ngắn nhất (`vat_rate`)
là field DUY NHẤT vẫn sai xuyên suốt nhiều mức padding đã thử.

**Bác bỏ 1 phần lý giải sai ban đầu:** phát sinh trong thảo luận - nghi
ngờ vấn đề "phụ thuộc DPI". Xác nhận qua suy diễn toán học: cả 2 công
thức (theo trang lẫn theo bbox.height) đều tỉ lệ thuận với DPI đúng cách
(vì `bbox_height_px = normalized_height x page_height_px`, và
`page_height_px` tỉ lệ thuận DPI) - vấn đề thật KHÔNG phải "DPI", mà là
"kích thước token so với kích thước trang" (số ký tự khác nhau -> bbox
width khác nhau -> padding cố định theo trang chiếm tỉ lệ khác nhau).

**Giải pháp:** thay `ROI_PADDING_X`/`ROI_PADDING_Y` (2 hằng số theo
trang) bằng 1 hằng số `ROI_PADDING_RATIO` duy nhất, tính padding pixel
theo TỈ LỆ CHIỀU CAO BBOX (đại diện cỡ chữ/font size - ổn định giữa các
field cùng template, không phụ thuộc số ký tự):

```python
bbox_height_px = (y1 - y0) * page_height_px
pad_px = max(1, int(bbox_height_px * ROI_PADDING_RATIO))
```

Thiết kế này TỰ ĐỘNG bất biến theo DPI (đã chứng minh toán học - padding
vật lý tuyệt đối tăng đúng theo tỉ lệ DPI mà không cần code biết DPI cụ
thể là bao nhiêu) - quan trọng cho kế hoạch v2.0 "DPI thích ứng theo khổ
giấy" (xem PROJECT_CONTEXT.md §18, ADR-053).

**Quá trình tinh chỉnh thực nghiệm** (dò dần theo giá trị cũ, quy đổi
sang giá trị mới): `0.02 -> 0.005 -> 0.003 -> 0.002 -> 0.001 -> 0.0007-0.0004`
(theo trang) tương ứng khoảng `ROI_PADDING_RATIO ~ 0.06-0.08` (theo
bbox.height) cho kết quả đúng trên case debug ban đầu (4/4 field khớp
`anchor.text` đã xác nhận là giá trị thật). Chọn điểm giữa `0.07` để
tiếp tục thực nghiệm trên batch lớn hơn.

**CHƯA ĐÓNG:** chạy lại trên toàn bộ 18 PDF `high_noise` với
`ROI_PADDING_RATIO=0.07` cho kết quả 71/72 - nhưng field sai đã CHUYỂN
SANG PDF KHÁC so với lần chạy baseline (trước Two-Pass). Tình huống phức
tạp hơn dự kiến ban đầu - việc tinh chỉnh giá trị cuối cùng, và tìm hiểu
nguyên nhân "field sai di chuyển giữa các PDF", được dời sang phiên làm
việc riêng.

Xác nhận trong implementation:
`core/domain/constants.py::OCR.ROI_PADDING_RATIO`,
`core/extraction/ocr_engine.py::OCREngine._crop_roi()`.

**Nợ kỹ thuật cần xử lý ở phiên sau:** `tests/core/extraction/test_ocr_engine.py::TestCropRoi`
hiện viết theo công thức CŨ (`ROI_PADDING_X`/`Y` theo trang) - đã LỖI
THỜI, cần viết lại theo công thức mới sau khi `ROI_PADDING_RATIO` được
chốt giá trị cuối.

------------------------------------------------------------------------

## ADR-074 --- Bác Bỏ Cấu Hình Tắt DAWG/`textord_heavy_nr` Cho Global Pass

**Status:** Accepted

`OCR_ACCURACY_SPECIFICATION.md` Mục 4.1.C đề xuất tắt DAWG
(`load_system_dawg`/`load_freq_dawg`/`load_punc_dawg`) và bật
`textord_heavy_nr=1`/`classify_enable_learning=0` cho cấu hình Tesseract
TOÀN TRANG (`self._config` trong `OCREngine.__init__()`, dùng bởi
`recognize()` - Pass 1).

**Kiểm chứng thực nghiệm A/B trên tập `high_noise`** (18 PDF, 72 field
DECIMAL, cùng bộ dữ liệu, chỉ đổi đúng 1 biến số):

| Cấu hình | None | Sai dấu `,`/`.` |
|---|---|---|
| Baseline (không DAWG-disable/textord) | 0 | 1 |
| Áp dụng Mục 4.1.C (DAWG-disable + textord toàn trang) | 2 | 1 |

**Kết luận:** áp dụng đề xuất Mục 4.1.C gây HỒI QUY (2 field mất khả
năng đọc hoàn toàn) mà KHÔNG mang lại lợi ích đo được (số case sai dấu
không đổi). Quyết định: BÁC BỎ phần đề xuất này của spec cho pipeline
hiện tại, dựa trên bằng chứng thực nghiệm trực tiếp trên dữ liệu thật -
đối xứng cách dự án đã bác bỏ đề xuất Binarization tại Session
2026-08-13 (rủi ro lý thuyết không đủ, cần bằng chứng thực nghiệm).

**Giả thuyết kỹ thuật cho nguyên nhân hồi quy (chưa verify sâu, ghi nhận
để tham khảo):** tắt DAWG/bật `textord_heavy_nr` cho TOÀN TRANG có thể
khiến Pass 1 không tìm được BẤT KỲ token nào khớp `value_pattern` ở 1 số
field (regex match rỗng ngay từ bước tìm candidate, TRƯỚC KHI `anchor`
được xác lập) - lúc đó Pass 2 không có cơ hội chạy vì cần `anchor` làm
điểm neo. Cấu hình riêng của Pass 2 (`recognize_numeric_roi()`, đã có
sẵn DAWG-disable ở phạm vi HẸP - chỉ ROI số) đã đảm nhiệm đủ tốt lợi ích
"giảm thiên kiến từ điển" mà Mục 4.1.C nhắm tới, không cần áp cho toàn
trang.

**Quyết định:** `self._config` (Pass 1, `OCREngine.__init__()`) GIỮ
NGUYÊN baseline gốc (chỉ `--tessdata-dir --psm --oem`, không có cờ DAWG/
textord/classify-learning). `PREPROCESS_SHARPEN_SIGMA`/`AMOUNT` (Mục
4.1.B) và Median Blur (Mục 4.1.A) của spec - CHƯA thực nghiệm, dời sang
phiên sau (xem PROJECT_CONTEXT.md §15).

Xác nhận trong implementation: `core/extraction/ocr_engine.py::OCREngine.__init__()`
(không đổi so với trước khi triển khai `OCR_ACCURACY_SPECIFICATION.md`).

------------------------------------------------------------------------

## ADR-075 --- Cô Lập Ba Giai Đoạn Cải Thiện OCR Khi Thực Nghiệm

**Status:** Accepted

Mọi thay đổi accuracy OCR được phân thành ba giai đoạn độc lập: (1) tiền
xử lý ảnh; (2) kết quả trực tiếp của OCR; (3) hậu xử lý bằng heuristic.
Mỗi vòng thực nghiệm chỉ thay đổi một biến trong đúng giai đoạn đang tối
ưu và đánh giá theo ground truth. Không dùng heuristic hậu OCR để che lấp
lỗi còn tồn tại khi mục tiêu đang là output trực tiếp của Tesseract.

Việc cô lập này cho phép đánh giá độc lập model/PSM/ROI/upscale (giai đoạn
2) trước Median Blur/Unsharp Masking (giai đoạn 1) và trước khi mở rộng
`ValueConverter` (giai đoạn 3).

Xác nhận trong quy trình: `DEVELOPMENT_WORKFLOW.md::Rule 16`.

------------------------------------------------------------------------

## ADR-076 --- Pass 1 `vie`/tessdata_best, Pass 2 `eng`/tessdata_fast + PSM=8

**Status:** Accepted

Pass 1 tiếp tục dùng `vie.traineddata` từ `resources/tessdata_best/` để
nhận diện layout, anchor và văn bản tiếng Việt. Pass 2 chỉ nhận diện ROI
DECIMAL, nên dùng `eng.traineddata` integer từ `resources/tessdata_fast/`,
`PSM=8` và whitelist hẹp `0123456789.,%+-`.

Thực nghiệm cho thấy PSM=7 làm sai nhiều ROI dù crop đúng; PSM=8 xử lý tốt
hơn nhóm dấu `,`/`.` . `eng` tessdata_fast cho kết quả ổn định hơn
`eng` tessdata_best với các nhầm lẫn glyph `0`/`6`/`8` trong ROI số. Model
fast được đóng gói cùng project, không phụ thuộc tessdata hệ thống.

Hậu tố tiền tệ không nằm trong whitelist Pass 2: template cho phép hậu tố
vắng mặt và `ValueConverter` parse trực tiếp chuỗi số. `ROI_UPSCALE_FACTOR`
hiện tạm giữ `1.25`, không phải một phần giá trị đóng băng của ADR này.

Xác nhận trong implementation: `config.py::ROI_TESSDATA_DIR`,
`core/domain/constants.py::OCR.ROI_LANG`,
`core/extraction/ocr_engine.py::recognize()` và
`recognize_numeric_roi()`.

------------------------------------------------------------------------

## ADR-077 --- ROI Preprocess Riêng Cho Pass 2, Tách Khỏi `_preprocess()` Dùng Chung

**Status:** Accepted (điều kiện thực nghiệm: `interpolation=INTER_CUBIC`,
`ROI_UPSCALE_FACTOR=1.5` — xem Known Issues nếu 2 điều kiện này chưa
khớp với main/production tại thời điểm áp dụng)

Phát hiện qua thực nghiệm cô lập `ROI_UPSCALE_FACTOR` (tắt hẳn
`_preprocess()` ở Pass 2 để loại nhiễu): tắt preprocess làm tăng rõ
rệt số case nhầm lẫn hình dạng chữ số (0↔6↔8, 2↔7) trên ROI —
chứng minh CLAHE+Sharpen có đóng góp thật cho chất lượng Pass 2, dù
tham số cũ (`OCR.PREPROCESS_*`, tinh chỉnh cho ảnh toàn trang ~3000+px)
không tối ưu cho ROI (thường ~100px chiều cao sau upscale).

Nguyên nhân tham số Pass 1 không phù hợp Pass 2:
`PREPROCESS_CLAHE_TILE_GRID_SIZE=(8,8)` trên ROI ~100-200px khiến mỗi
ô lưới CLAHE chỉ còn ~15-25px — suy biến từ "tăng contrast cục bộ"
thành xử lý gần từng pixel, khuếch đại nhiễu thay vì làm rõ nét.

Giải pháp: tách `_preprocess()` thành 1 hàm lõi tham số hóa
(`_apply_clahe_sharpen()`, nhận đủ 4 tham số CLAHE/Sharpen) + 2
wrapper: `_preprocess()` (Pass 1, gọi với `OCR.PREPROCESS_*` — hành vi
không đổi so với trước patch) và `_preprocess_roi()` (Pass 2, gọi với
4 hằng số mới `OCR.ROI_PREPROCESS_*`).

Phương pháp thực nghiệm (ghi chi tiết đầy đủ trong
`ROI_PREPROCESS_EXPERIMENT_LOG.md`, không lặp lại ở đây theo Rule 14):
cô lập triệt để theo Rule 16 — cố định `ROI_UPSCALE_FACTOR=1.5`,
`INTER_CUBIC`, Pass 1 không đổi; dò riêng CLAHE (Sharpen tắt) rồi mới
dò Sharpen (CLAHE cố định). Ghi 3 nhóm số liệu mỗi vòng theo đúng yêu
cầu Rule 16 (sửa đúng / vẫn sai / hồi quy), tách biệt tuyệt đối field
từ Nhóm 1 (Pass 1 sai, có GT xác minh thủ công) và field Pass 1 vốn
đúng (GT ngầm định = `anchor.text`).

Kết quả: trên bộ 103 PDF / 412 field DECIMAL nguồn OCR, Pass 1
sai 7/412 field (Nhóm 1). Sau khi chốt CLAHE + Sharpen: sửa đúng
7/7, còn 1 hồi quy mới (field Pass 1 vốn đúng bị Pass 2 làm sai) —
tổng 411/412. Field hồi quy còn lại (GT='75,585', Pass 2 trả
'75,5865' — dư 1 chữ số 6) do chính CLAHE gây ra, không sửa được
bằng Sharpen — ghi nhận Known Issue, chưa xử lý (xem
`PROJECT_CONTEXT.md` §14).

Giá trị chốt:

```python
ROI_PREPROCESS_CLAHE_CLIP_LIMIT = 1.5
ROI_PREPROCESS_CLAHE_TILE_GRID_SIZE = (2, 2)
ROI_PREPROCESS_SHARPEN_SIGMA = 0.6
ROI_PREPROCESS_SHARPEN_AMOUNT = 0.4
```

Phát hiện phụ quan trọng (chưa xử lý, thuộc Pass 1 — xem ADR riêng
nếu điều tra ở phiên sau): toàn bộ 6/7 field lỗi glyph gốc của Pass 1
(trước khi có Pass 2) đều có dạng chữ số 6/8 bị đọc nhầm thành 0,
và tất cả xảy ra đúng tại vị trí ngay sau dấu phẩy phân cách hàng
nghìn (,) — xác nhận qua đối chiếu tần suất 6/8 tại đúng vị trí
này giữa subtotal/vat_amount/total_amount là tương đương nhau
(loại trừ giả thuyết "lỗi đặc thù riêng field vat_amount"; loại trừ
cả giả thuyết cỡ chữ, độ đậm nét, và dấu kẻ bảng liền kề — đã kiểm tra
trực tiếp qua bbox.height đồng nhất 104px và ảnh debug ROI). Trên bộ
test mở rộng, mẫu hình mở rộng thêm case 7 bị đọc sai, vẫn giữ đúng
vị trí "ngay sau dấu phẩy". Nguyên nhân gốc CHƯA xác định — nghi vấn
kỹ thuật: ranh giới phân đoạn (segmentation) giữa glyph dấu phẩy và
chữ số kế tiếp là vùng nhạy cảm nhất trong 1 chuỗi số đối với
Tesseract. Đã xác nhận qua rà soát source: Pass 2 hoàn toàn độc lập với
lỗi này (không dùng lại pixel/text đã qua xử lý của Pass 1, chỉ dùng
chung normalized_bbox — vị trí hình học, không phải nội dung).

Xác nhận trong implementation:
`core/extraction/ocr_engine.py::OCREngine._apply_clahe_sharpen()`,
`_preprocess()`, `_preprocess_roi()`, `recognize_numeric_roi()`;
`core/domain/constants.py::OCR.ROI_PREPROCESS_*`.

------------------------------------------------------------------------

## ADR-078 --- Hoãn Xây Dựng `ROI_UPSCALE_FACTOR = f(bbox.height)`

**Status:** Accepted (deferred sang phiên sau)

Giả thuyết ban đầu: `ROI_UPSCALE_FACTOR` nên là hàm theo `bbox.height`
(cỡ chữ) thay vì hằng số cố định, do quan sát hệ số "tối ưu" dịch
chuyển giữa các vòng thực nghiệm trước khi cô lập đúng biến số (Rule
16). Sau khi cô lập (`_preprocess()` tắt hẳn, `INTER_CUBIC` cố định),
`ROI_UPSCALE_FACTOR=1.5` đạt 411/412 trên bộ 103 PDF/412 field.

Quyết định hoãn: bộ PDF hiện tại (~10% quy mô mục tiêu, chưa đủ đa
dạng font/cỡ chữ theo xác nhận của người dùng) không đủ bằng chứng để
phân biệt 2 khả năng: (a) 1.5 phù hợp mọi field vì bộ test có phân bố
cỡ chữ hẹp (chưa bộc lộ nhu cầu thích ứng), hay (b) 1.5 thật sự tổng
quát tốt. Xây hàm height → factor trên dữ liệu chưa đủ đa dạng sẽ lặp
lại đúng rủi ro đã gặp ở `_preprocess()` (tối ưu cho phân bố hẹp, không
tổng quát). Quyết định: giữ `ROI_UPSCALE_FACTOR = 1.5` (hằng số) làm
baseline, hoãn thiết kế hàm tới khi có bộ PDF mở rộng, đa dạng font
hơn (người dùng xác nhận sẽ chuẩn bị ở phiên sau).

Không có implementation nào để xác nhận (quyết định KHÔNG code ở
phiên này).
