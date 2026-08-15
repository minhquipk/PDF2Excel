# SESSION_SUMMARIES.md

# Tóm Tắt Các Phiên Làm Việc

## Mục đích

- Nhanh chóng nối lại công việc sau khi tạm dừng.
- Ghi lại **bối cảnh thảo luận** dẫn tới quyết định (phương án bị bác
  bỏ, lý do tranh luận, vướng mắc thực nghiệm) — thứ mà
  `ARCHITECTURE_DECISIONS.md` không có chỗ chứa vì ADR chỉ ghi quyết
  định cuối cùng.
- Bổ trợ (không thay thế) `CHANGELOG.md`.

**Phân công nội dung:** file này giữ phần "diễn biến" — không lặp lại
lý do kỹ thuật đầy đủ của quyết định cuối (đã có ở ADR, chỉ cần trỏ
`→ ADR-xxx`) và không lặp lại danh sách file/thay đổi (đã có ở
CHANGELOG).

------------------------------------------------------------------------

# Session 2026-07-22

## Mục tiêu

Dựng và validate khung ứng dụng (UI, Worker, QThread, MVC) trước khi
implement xử lý PDF thật — chạy hoàn toàn ở Mock Mode.

## Hoàn thành

Framework nền tảng (`constants.py`/`enums.py`/`models.py`), UI đầy đủ
(MainWindow/BaseWidget/widget tái sử dụng/Input-Output selector/
Progress/Processing Table/Report-Exit), Worker (QThread + Signal + Mock
pipeline), `ProcessingTableModel` kèm `clear()` trước mỗi lần Start.

## Quyết định kiến trúc

→ ADR-001 đến ADR-011.

## Vướng mắc gặp phải

- **ProcessingTable:** `setModel()` không khả dụng → đổi
  `ProcessingTable` sang kế thừa `QTableView`.
- **Column Enum:** `Column.COUNT` trùng lặp việc bảo trì số lượng cột
  → bỏ `COUNT`, dùng `len(Column)`.

## Validation

UI khởi động đúng; Worker chạy nền không chặn UI; Progress/Table cập
nhật đúng; Start/Stop hoạt động đúng.

## Phiên tiếp theo

Ưu tiên: `pdf_reader.py` → phát hiện Digital PDF → đọc text → tích hợp
regex parser.

## Ghi chú

Dự án chủ đích chạy ở Mock Mode. UI/Worker/QThread/MVC đã được validate
— mốc tiếp theo là thay Mock bằng pipeline PDF thật.

------------------------------------------------------------------------

# Session 2026-07-23

## Mục tiêu

Bắt đầu implement pipeline xử lý PDF thật.

## Hoàn thành

`models.py` frozen, chuẩn hóa khởi tạo timestamp UTC. `PDFReader` bản
đầu tiên. Thiết lập quy trình làm việc mới: source code là tham chiếu
implementation, "Freeze design before coding" được áp dụng.

## Quyết định kiến trúc

→ ADR-016, ADR-017, ADR-018 (Reader chỉ đọc, Domain drives
implementation).

## Vướng mắc gặp phải

- **API PyMuPDF:** IDE cảnh báo type/reference → giải quyết bằng verify
  trực tiếp với version thư viện đã cài trước khi implement.
- **Quy trình phát triển:** thảo luận kiến trúc quá nhiều trong lúc
  implement → giải quyết bằng "Freeze architecture before coding", ưu
  tiên code + review sau (tiền thân của Rule 11 trong
  DEVELOPMENT_WORKFLOW.md).

## Phiên tiếp theo

Ưu tiên: freeze `pdf_reader.py` → tích hợp `processor.py` → thay Mock
pipeline → bắt đầu Analyzer.

------------------------------------------------------------------------

# Session 2026-07-29

## Mục tiêu

Implement `pdf_detector.py` (reasoning engine) theo
`PDF_Detector_Technical_Design.docx`, tích hợp pipeline
PDFReader → PDFDetector thật vào Worker, thay Mock cho giai đoạn
detection.

## Hoàn thành

`PDFReader`/`PDFDetector` implement đầy đủ (5/7 Rule Category: Text,
Image, Consistency, Quality, Layout). Tích hợp vào `Worker._process_pdf()`.

## Quyết định kiến trúc

→ ADR-019 đến ADR-023.

## Vướng mắc gặp phải (mở, chưa giải quyết ở phiên này)

- **Rule Category coverage:** TDS §7.2 định nghĩa 7 category, mới có
  5/7 (thiếu Document, Graphics) — **giải quyết tại Session
  2026-08-12**, xem ADR-057.
- **`processor.py` vs `Worker.process()`:** `core/processor.py` chỉ có
  4 lời gọi placeholder (`start/stop/pause/resume`), trong khi vai trò
  orchestrator (ADR-004) thực chất do `Worker.process()` đảm nhiệm —
  cần làm rõ đây là mục tiêu tách ra trong tương lai hay dead code.
  **Giải quyết tại Session 2026-08-12** (xóa `processor.py`).
- **Nghi vấn import path:** `core/models.py` dùng
  `from enums import ...`, `ui/widgets.py` dùng
  `from base_widget import ...` (thiếu prefix `core.`/`ui.`) — cần
  verify có phải bug tiềm ẩn hay chỉ là cấu hình relative-import hoạt
  động. **Xác nhận không phải bug tại Session 2026-07-31** (đối chiếu
  qua chạy thật).

## Validation

Xác nhận qua source review (chưa có automated test): luồng
`PDFDetector.analyze()` khớp đúng thứ tự TDS (Build Context → Heuristic
Evaluation → Knowledge Lookup → Confidence Adjustment → Final
Decision); các model output bất biến đúng; `Worker._process_pdf()`
delegate đúng cho `PDFReader`/`PDFDetector`.

## Phiên tiếp theo

Ưu tiên: `parser.py` (regex-based) → `extractor.py` → resolve
`processor.py` → quyết định Document/Graphics Rules (implement ngay
hay hoãn có chủ đích).

------------------------------------------------------------------------

# Session 2026-07-31

## Mục tiêu

Thiết kế và implement module `Extractor`: chuyển `PDFDocument` +
`DocumentAnalysis` thành kết quả extraction cấp từ, chuẩn hóa hình
học, sẵn sàng cho Parser tương lai. Tích hợp vào `Worker`. Sửa 2 cảnh
báo type-checker tĩnh phát hiện qua source review.

## Hoàn thành

`Extractor`/`OCREngine` (Mock) module mới; `PDFReader` render
`PageImage` + đọc `words` thô cho mọi trang; đổi tên
`ExtractionResult` cũ → `SessionResult`.

## Quyết định kiến trúc

→ ADR-024 đến ADR-028.

## Vướng mắc gặp phải

### HYBRID pages với nội dung hỗn hợp (hoãn sang v2.0)

Trang có cả text layer và ảnh liên quan (con dấu, chữ ký, bảng scan
nhúng trong trang digital) hiện chỉ được route tới 1 nguồn duy nhất
(`page.has_text` → Digital, bỏ qua nội dung ảnh trên trang đó).

3 phương án đã cân nhắc:
1. **Chỉ Digital** (đang chọn) — rẻ nhất, nhưng âm thầm bỏ nội dung
   ảnh trên trang hỗn hợp.
2. **Chạy cả 2 nguồn rồi merge** — đầy đủ nhất, nhưng phát sinh vấn đề
   con chưa có lời giải: OCR đọc lại toàn bộ ảnh trang (kể cả phần
   text layer đã có), tạo `WordToken` trùng/chồng lấn mà chưa có cơ
   chế khử trùng.
3. **Chỉ OCR toàn trang** — tránh trùng lặp, nhưng bỏ dữ liệu text
   layer chính xác cao để đổi lấy OCR chất lượng thấp hơn, không có
   lợi ích rõ ràng.

**Quyết định:** hoãn sang v2.0, giữ phương án 1. Đây là quyết định có
chủ đích, không phải khiếm khuyết. Cần: dữ liệu hóa đơn thật mẫu (biết
tần suất pattern này và mức độ quan trọng của nội dung ảnh bị bỏ), và
nếu chọn phương án 2 — thiết kế khử trùng theo bbox-overlap.

### Đặt tên trùng `ExtractionResult`

Tên `ExtractionResult` đã được dùng cho 1 class khác (kết quả cấp
session: invoices, pdf_results, errors), không liên quan output cấp
document mới của Extractor. **Giải quyết:** đổi tên class cũ thành
`SessionResult`. Xác nhận (trong phạm vi source đã review) không còn
file nào tham chiếu tên cũ, việc đổi tên an toàn.

### Xác nhận hành vi rotation của PyMuPDF

Cần xác định `get_text("words")` và `get_pixmap()` có cùng hệ tọa độ
tham chiếu đối với rotation hay không, trước khi thiết kế
`_normalize_bbox()`/`_rotate_bbox()`. Có claim không chắc chắn từ
nguồn thứ cấp (blog). **Giải quyết:** xác minh qua tài liệu chính thức
PyMuPDF + phát biểu của maintainer trong GitHub discussion — xác nhận
gốc tọa độ nhất quán, nhưng `get_text()` trả tọa độ **chưa xoay** trong
khi `page.rect`/`get_pixmap()` phản ánh trang **đã xoay** — sai lệch có
thật, cần `_rotate_bbox()` cho path Digital.

## Validation

`_rotate_bbox()` phủ đủ 4 case xoay được PyMuPDF đảm bảo (0/90/180/
270°). `ExtractionResult`/`WordToken`/`PageImage` theo đúng pattern
bất biến đã có. Chưa có automated test suite — `_rotate_bbox()` được
đánh dấu là ứng viên tốt cho unit test (thực hiện tại Session
2026-08-12).

## Phiên tiếp theo

Ưu tiên: `parser.py` → cân nhắc unit test cho `_rotate_bbox()` → thay
`OCREngine` Mock bằng backend thật → resolve `processor.py` → resolve
nghi vấn import path.

## Ghi chú

Theo yêu cầu người dùng, phiên này được đóng đầy đủ (source review +
đồng bộ log) trước khi sang module kế tiếp, thay vì code tiếp Parser
ngay. Cùng lưu ý về giới hạn ghi chép như phiên trước: entry này ghi
lại những gì đã quyết định/implement dựa trên thảo luận và xác nhận
của người dùng, không phải lịch sử commit từng dòng.

------------------------------------------------------------------------

# Session 2026-08-01 / 2026-08-02

## Mục tiêu

Thiết kế và implement đầy đủ module `Parser`: chuyển `WordToken` thô
từ Extractor thành `InvoiceInfo`, dùng Template Matching (Key Matching
+ Bounding Box Windowing + Value Matching), Template Definition lưu
JSON ngoài, chuẩn bị sẵn cho engine LayoutLMv3 ở v2.0.

## Hoàn thành

8 bước tuần tự (logger → enums → models → value_converter →
template_loader → template_matcher → parser → worker integration +
extractor text normalize), mỗi bước compile+run+verify trước khi sang
bước kế (đúng DEVELOPMENT_WORKFLOW.md).

## Quyết định kiến trúc

→ ADR-029 đến ADR-036.

## Vướng mắc gặp phải

### Diacritics tiếng Việt làm sập fuzzy matching

Phát hiện qua kiểm thử thực nghiệm (không phải suy đoán trước): so
sánh "Mã số thuế" (có dấu) với "Ma so thue" (không dấu) qua
`rapidfuzz.fuzz.ratio()` chỉ cho ratio ~70, dưới mọi ngưỡng
`fuzzy_threshold` hợp lý (85-90). Nghiêm trọng hơn: cùng vấn đề xảy ra
khi OCR làm rớt dấu trên bản scan chất lượng thấp — tình huống thực
tế, không phải edge case hiếm. **Giải quyết:** `_strip_diacritics()`
(NFKD decompose + xử lý riêng `Đ/đ`) áp dụng cho cả 2 phía trước khi so
khớp. Xem ADR-035.

### Key Token ngắn gây match nhầm dòng khác

Template mẫu có `key_tokens: ["so hoa don", "so"]` cho `invoice_number`;
biến thể `"so"` (1 từ) khớp 100% với từ "số" đứng độc lập trong cụm "Mã
số thuế" ở dòng khác, khiến Windowing dựng sai vị trí. Xác nhận đây
KHÔNG phải lỗi thuật toán (rapidfuzz trả kết quả đúng bản chất) mà là
vấn đề thiết kế template — ghi thành quy tắc vận hành (chưa có tài
liệu chính thức lúc này; chính thức hóa trong `TEMPLATE_AUTHORING_GUIDE.md`
tại Session 2026-08-12).

### `value_pattern` lỏng khiến dấu câu bị chọn nhầm làm Value

`value_pattern: ".+"` cho phép dấu `":"` (thường gần Key hơn giá trị
thật) được chọn do tie-break theo khoảng cách. **Giải quyết:** yêu cầu
pattern có ít nhất 1 ký tự không phải khoảng trắng/dấu câu cơ bản — ghi
thành quy tắc vận hành (cùng số phận với vấn đề trên).

### Môi trường thiếu dependency

`PySide6`/`PyMuPDF`/`rapidfuzz` phải tự cài trong workspace kiểm thử —
dự án chưa có `requirements.txt` lúc này (giải quyết tại Session
2026-08-03).

## Validation

Verify bằng kiểm thử trực tiếp (bash + Python), không phải review
tĩnh: `utils/logger.py`, `enums.py`, `models.py` (bao gồm `FieldDefinition`
tự validate `field_name`), `value_converter.py` (TEXT/DECIMAL/DATE +
stress test dữ liệu nhiễu OCR — không bao giờ raise), `template_loader.py`
(5 loại lỗi khác nhau đều bị bỏ qua đúng), `template_matcher.py`
(end-to-end với dữ liệu WordToken mô phỏng 1 trang hóa đơn thật),
`parser.py` (happy path, trả `None` đúng, 1 field lỗi không ảnh hưởng
field khác), tích hợp `Worker` (happy path + Parser trả `None` + Parser
raise Exception — cả 3 case đều đúng kỳ vọng).

## Phiên tiếp theo

Ưu tiên: viết Template Authoring Guide → sửa `sample_invoice_v1.json`
khi có PDF thật → thiết kế ghép cụm nhiều từ cho Value Matching →
`excel_writer.py` + Report export → bổ sung `rapidfuzz` vào dependency
file chính thức → thảo luận riêng tái cấu trúc thư mục → resolve
`processor.py`.

## Ghi chú

3 lỗi thiết kế thực chất (diacritics, key_tokens ngắn, value_pattern
lỏng) đều phát hiện qua kiểm thử thực nghiệm với dữ liệu mô phỏng,
không phải qua review tĩnh — xác nhận giá trị của việc chạy thử thực
tế thay vì chỉ đọc code (nguyên tắc xuyên suốt dự án từ đây trở đi).

------------------------------------------------------------------------

# Session 2026-08-03

## Mục tiêu

Thiết kế và implement `excel_writer.py` + `report_writer.py`, hoàn
thiện pipeline end-to-end lần đầu tiên. Kiểm thử toàn bộ trên source
đã push lên GitHub. Giải quyết dependency file còn thiếu.

## Hoàn thành

8 bước implement (xem CHANGELOG.md 2026-08-03). `requirements.txt`
được tạo, pin 4 version đã kiểm thử thành công.

## Quyết định kiến trúc

→ ADR-037 đến ADR-041.

## Bối cảnh thảo luận thiết kế (trước khi implement — Rule 11/12)

Người dùng cung cấp `Technical_Design_excel_writer.docx` làm điểm khởi
đầu. Qua nhiều vòng trao đổi:

1. **Bác bỏ `ReportService`** (đề xuất gộp Excel writing + report.txt
   vào 1 lệnh gọi trong tài liệu gốc) — dựa trên bằng chứng cụ thể
   trong source: `Worker.__init__` đã có sẵn 2 thuộc tính placeholder
   tách biệt (`self._excel_writer = None`, `self._report_writer =
   None`) từ trước, cho thấy thiết kế gốc đã dự tính 2 module riêng.
2. **Làm rõ vai trò nút Report:** không kích hoạt sinh report, chỉ mở
   file đã sinh tự động ở cuối `Worker.process()`.
3. **2 loại thông tin report tách biệt hoàn toàn:** ban đầu có nhầm
   lẫn gộp 2 luồng (`list[PDFResult]` và `ExcelWriteResult`) vào cùng
   nội dung `report.txt` — người dùng chỉnh lại rõ ràng qua 2 lượt
   trao đổi.
4. Đổi tên exception theo namespace dự án — tránh dùng lại từ
   "Template" (đã có nghĩa cố định: mẫu hóa đơn) cho khái niệm workbook
   Excel.

## Vướng mắc gặp phải

### Không có repo mount trong môi trường làm việc

8 bước implement ban đầu chỉ tồn tại dưới dạng code đề xuất trong
chat. **Giải quyết:** sau khi người dùng xác nhận đã push lên GitHub
(public), `git clone` trực tiếp vào container, đối chiếu từng file
khớp 100% trước khi chạy kiểm thử thật.

### `WorkbookSaveError` không tái hiện được

Container test chạy quyền root, bỏ qua kiểm tra permission của OS —
không ép `openpyxl.save()` thất bại được. **Chưa giải quyết ở phiên
này** — logic xử lý được đánh giá đúng về code, nhưng cần verify trên
máy thật (quyền user thường). **Giải quyết tại Session 2026-08-12**
(kỹ thuật `chattr +i`).

### Nhầm lẫn thiết kế report_writer qua nhiều vòng trao đổi

Assistant ban đầu đề xuất `ReportWriter` chỉ nhận `ExcelWriteResult`;
sau đó hiểu nhầm ý người dùng là gộp cả 2 luồng vào cùng nội dung
`report.txt`; người dùng phải chỉnh lại 2 lần để làm rõ 2 luồng dữ liệu
phải tách biệt hoàn toàn về xử lý (dù cùng nhận chung ở 1 lệnh gọi
`write()`).

## Validation

Verify bằng script tự động (không phải review tĩnh), trên source đã
clone từ GitHub thật. Chi tiết đầy đủ (thành phần đã verify, case chưa
verify): xem `CHANGELOG.md`, mục 2026-08-03.

## Phiên tiếp theo

Đã thống nhất chọn Hướng 1 (kiểm thử end-to-end với data thật) thay vì
Hướng 2 (implement OCR trước) — lý do ADR-013 (Mock First): Mock
`OCREngine` đã đủ cho PDF Digital-mode; làm OCR đồng thời với lần đầu
chạy thật sẽ gộp 2 rủi ro chưa kiểm chứng cùng lúc, vi phạm Rule 2/3.

Kế hoạch 5 bước (PROJECT_CONTEXT.md §15): chuẩn bị PDF mẫu thật → sửa
`excel_mapping.json` khớp workbook thật → chạy app thật end-to-end →
quan sát kết quả → sửa `sample_invoice_v1.json` dựa trên dữ liệu thật.
Sau đó mới quay lại OCR thật.

Việc tồn đọng khác: verify `WorkbookSaveError` trên máy thật; unit test
`_rotate_bbox()`; resolve `processor.py`; resolve discrepancy `main.py`/
`ui/main_window.py`; dọn dead code `UIText.REPORT_PENDING`.

## Ghi chú

Khác các phiên trước ở chỗ: bắt đầu từ 1 tài liệu Word do người dùng
cung cấp, trải qua nhiều vòng phản biện/điều chỉnh trước khi implement
(đúng tinh thần Rule 11 "Freeze design before implementation" — nhưng
"freeze" ở đây diễn ra qua nhiều lượt xác nhận tăng dần, không phải 1
lần duy nhất).

------------------------------------------------------------------------

# Session 2026-08-07

## Mục tiêu

Xây dựng `excel_mapping.json` và `sample_invoice_v1.json` dựa trên dữ
liệu thử nghiệm thật, theo kế hoạch 5 bước đã thống nhất ở Session
2026-08-03. Người dùng cung cấp PDF hóa đơn thật đầu tiên
(`HD2026-0003_digital.pdf`) để đối chiếu trực tiếp thay vì suy đoán.

## Hoàn thành

`resources/EXCEL_MAPPING_GUIDE.md` mới. `sample_invoice_v1.json` v2 →
v3 qua 3 vòng thực nghiệm (chi tiết thay đổi: xem `CHANGELOG.md`, mục
2026-08-07).

## Quyết định kiến trúc

→ ADR-042 đến ADR-045.

## Bối cảnh thảo luận

### excel_mapping.json: thảo luận thêm trường `sheet` — rút lại

Đề xuất thêm `sheet` để chỉ rõ Excel Table nằm ở sheet nào, rút lại sau
khi phân tích `ExcelWriter._find_table()` (đã duyệt toàn bộ sheet, tên
Table tự đảm bảo duy nhất trong workbook → `sheet` dư thừa). → ADR-042.

### 3 vòng thực nghiệm trên PDF thật

**Vòng 1 — Đối chiếu tĩnh với text PDF:** phát hiện 5 lỗi rõ ràng
trong template gốc (`key_tokens`/`value_pattern`/`direction` sai).

**Vòng 2 — Chạy thật, phát hiện thêm 3 vấn đề mới (không thấy được
qua review tĩnh):** `axis_tolerance` mặc định quá lớn so với khoảng
cách dòng thật; `max_distance` của field tiền tệ quá nhỏ so với
khoảng cách nhãn-giá trị thật; định dạng số của PDF test dùng dấu phẩy
ngăn nghìn ngược mặc định VN — xác nhận là quirk của data test (người
dùng xác nhận), không đổi mặc định toàn cục, chỉ override riêng cho
template này.

**Vòng 3 — Phát hiện 3 vấn đề cần sửa code (Nhóm 3), tạm hoãn ngay
trong vòng này:**
- 3.1: `tax_code` bị lấy nhầm MST bên mua (va chạm Key Matching).
- 3.2: `invoice_date` phụ thuộc may rủi thứ tự xuất hiện để thắng tie
  giữa 3 vị trí khớp cùng ratio.
- 3.3: Value Matching chỉ lấy 1 `WordToken` — field nhiều từ bị cắt
  cụt (giới hạn đã biết từ Session 2026-08-01/02, nay ảnh hưởng thêm 4
  field mới người dùng yêu cầu bổ sung).

Người dùng quyết định: (1) patch `value_converter.py` cho `%` ngay,
(2) mở rộng thêm 4 field mới dù biết sẽ cắt cụt tạm thời, (3) xử lý
Nhóm 3 trước khi tiếp tục.

### Giải quyết 3.3 — Value Matching nhiều từ

Thảo luận 3 hướng thiết kế (gap-based / cả dòng trong window / dùng vị
trí key field khác làm ranh giới) — chọn **gap-based**, chỉ áp dụng
field Text. Verify phát hiện thêm 1 hệ quả phụ (merge kéo nhầm token
nhãn "mua:" vào giá trị `tax_code`) → thêm điều kiện dừng ở token kết
thúc `:`. → ADR-044.

### Giải quyết 3.1 + 3.2 — Section-Scoped Key Matching

Người dùng nhận định 2 vấn đề cùng gốc rễ (thiếu ngữ cảnh khi Key
Matching), đề xuất 4 cách triển khai (Block/Section, Parent Key,
Anchor, Relative Position). Sau khi phân tích ưu/nhược từng cách
(Section mạnh nhất, giải quyết tận gốc; Parent Key là biến thể yếu hơn
của Section; Anchor chỉ là cơ chế mềm/tie-break; Relative Position
brittleness cao, trói field vào tọa độ tuyệt đối, đi ngược triết lý
`spatial_relation` tương đối theo Key), người dùng chọn **Section**,
kèm 3 quyết định thiết kế: section header dùng tie-margin riêng, field
bắt buộc khai `section` (không cho phép bỏ trống), áp dụng luôn vào
`sample_invoice_v1.json` trong phiên này. → ADR-045.

Phát hiện thêm trong lúc chọn `key_tokens` cho section "buyer": header
5 từ ("THÔNG TIN NGƯỜI MUA HÀNG:") vượt `MAX_KEY_WORDS=4`, không bao
giờ đạt ratio 100 — phải chọn key 4 từ.

## Vướng mắc gặp phải

### Thiếu sót khi xuất patch

Bộ patch đầu tiên cho Section thiếu patch cho `core/constants.py`
(`SECTION_TIE_MARGIN` đã dùng trong sandbox lúc test nhưng quên đưa
vào patch xuất cho người dùng). Người dùng phát hiện qua review trước
khi áp dụng. **Bài học:** cần liệt kê tường minh MỌI file đã sửa trong
sandbox trước khi xuất patch, không chỉ file "chính" của thay đổi.

### MAX_KEY_WORDS giới hạn độ dài section header

Đã mô tả ở trên — cần đưa vào tài liệu hướng dẫn viết Template (còn
thiếu lúc này; hoàn thành tại Session 2026-08-12).

## Validation

Chạy thật (không phải review tĩnh) trên `HD2026-0003_digital.pdf` sau
mỗi thay đổi. Kết quả cuối: **12/12 field ra đúng giá trị**. Người
dùng đã áp dụng toàn bộ patch vào repo thật và xác nhận ổn sau mỗi
đợt.

**Chưa verify:** hành vi Section/merge trên các mẫu hóa đơn thật khác
(chỉ có 1 file test trong phiên này).

## Phiên tiếp theo

Hoàn thiện tính năng Report ở UI. Chạy thử nghiệm end-to-end thật (kế
hoạch 5 bước) — vẫn chưa có lượt chạy UI thật nào. Việc tồn đọng khác:
Template Authoring Guide, tinh chỉnh `SECTION_TIE_MARGIN`, đánh giá
rủi ro tràn gap-based merge, điều chỉnh `excel_mapping.json` khớp
workbook thật.

------------------------------------------------------------------------

# Session 2026-08-07 (b) — Khắc phục lỗi OCREngine & Startup UI

## Mục tiêu

Khắc phục lỗi crash ứng dụng ngay khi bật giao diện UI do
`OCREngine.__init__()` nạp `_PaddleOCR` quá sớm và xung đột thuộc tính
`strides` trong Paddle 3.0.0 PIR engine.

## Hoàn thành

Chuyển `OCREngine` sang Lazy Loading; tắt tiền xử lý phụ thừa của
PaddleX.

## Quyết định kiến trúc

→ ADR-046 (lưu ý: chỉ còn giá trị lịch sử sau khi OCR engine đổi hẳn
sang Tesseract tại Session 2026-08-08/09, xem ADR-047).

## Validation

Chạy offscreen `MainWindow()` thành công, khởi động tức thì, không
freeze, không crash.

------------------------------------------------------------------------

# Session 2026-08-08 / 2026-08-09

## Mục tiêu

Chạy UI thật lần đầu tiên với dữ liệu thật (kế hoạch 5 bước,
PROJECT_CONTEXT.md §15). Thiết kế và implement `OCREngine` thật (thay
Mock) cho luồng PDF Scanned/Hybrid.

## Hoàn thành

Lần chạy UI thật đầu tiên (Input Folder → Start → Report) — hoàn thành
bước 3 kế hoạch 5 bước. `OCREngine` thật (Tesseract) sau 3 vòng thực
nghiệm thư viện.

## Quyết định kiến trúc

→ ADR-047 đến ADR-050.

## Bối cảnh: 3 vòng thực nghiệm thư viện OCR

Thảo luận input/output/thư viện theo Rule 11/12 trước. Quyết định ban
đầu: PaddleOCR, input qua NumPy array.

**Vòng 1 — PaddleOCR:** triển khai đầy đủ. Phát hiện qua chạy thật
(không phải suy đoán): (a) API PaddleOCR 3.x khác hẳn tri thức huấn
luyện cũ (`use_angle_cls`/`use_gpu` đổi tên; `model_type` phải là
`Enum`); (b) lỗi tương thích `paddlepaddle`/PIR (`strides is not
right`) — xác nhận qua GitHub Issue #18162, chưa có fix chính thức;
(c) trên máy thật người dùng (macOS Ventura Intel Python 3.12), chỉ
`paddleocr==2.7.3`+`paddlepaddle==2.6.2` chạy được — hạ cấp API và
chất lượng model đáng kể.

**Vòng 2 — RapidOCR:** chuyển hướng sau khi đánh giá `paddlepaddle` là
rủi ro cấu trúc (framework đang chuyển đổi kiến trúc PIR, không phải
lỗi nhất thời). Verify thật: không cần `paddlepaddle`, hỗ trợ tiếng
Việt, output dạng tứ giác (cần tự quy về rect), input cần tự
`cv2.cvtColor(RGB2BGR)`. Phát hiện + sửa: `onnxruntime` không phải
dependency chính thức; không có wheel `onnxruntime>=1.24` cho macOS
Intel (hạ về `1.23.2`); lỗi lazy loading tự triển khai. Sau khi sửa
hết lỗi kỹ thuật, pipeline chạy thành công nhưng **chất lượng nhận
dạng tiếng Việt kém** — phát hiện qua debug thật trên
`HD2026-0001_scanned.pdf`. Đây là lý do quyết định loại bỏ, vượt trên
mọi ưu điểm về dependency/cài đặt.

**Vòng 3 — Tesseract 5.x + tessdata_best (chốt):** cân nhắc thêm
phương án Hybrid (Tesseract Detection + VietOCR Recognition) — tra cứu
thật cho thấy VietOCR dùng PyTorch không khai báo chính thức + tải
model qua Google Drive (rủi ro rate-limit) — cộng dồn nhược điểm của cả
2 hướng, hoãn sang Future Improvements (Rule 9: không tối ưu sớm).
Verify Tesseract bằng chạy thật trên đúng `HD2026-0001_scanned.pdf` —
kết quả đọc đúng gần như tuyệt đối, giữ nguyên dấu tiếng Việt.

## Vướng mắc gặp phải

### Bug deskew 90° (phát hiện + tự sửa bởi người dùng)

Deskew nhầm trang A4 dọc thành góc nghiêng ~90° (`minAreaRect` toàn
trang không phù hợp tài liệu nhiều khối như hóa đơn) — làm hỏng vị trí
mọi `WordToken`, khiến `select_template()` thất bại toàn bộ (triệu
chứng: Excel/report.txt "Total: 0, Written: 0" dù `PDFResult.status =
Success`). Người dùng tự phát hiện + tự sửa bằng ngưỡng
`DESKEW_MAX_ANGLE=10.0`; hình thức hóa lại thành hằng số tường minh.
→ ADR-049.

Quá trình chẩn đoán: dựng lại thật `TemplateMatcher`/`TemplateLoader`
+ logic Extractor trong sandbox, chạy trực tiếp trên
`HD2026-0001_scanned.pdf` qua Tesseract thật — lần đầu KHÔNG tái hiện
được lỗi (script chẩn đoán bỏ qua bước deskew) — cho thấy rõ nguyên
nhân nằm ở `OCREngine`, không phải `TemplateMatcher`/`Parser` như nghi
ngờ ban đầu. `git clone` repo GitHub thật để đối chiếu cấu hình mới
nhất, loại trừ khả năng lệch cấu hình trước khi kết luận đúng nguyên
nhân.

### Bài học chung

Với các thư viện OCR/ML Python, backend nặng (framework suy luận:
`paddlepaddle`, `onnxruntime`, `torch`) thường KHÔNG được khai báo là
dependency chính thức của package wrapper cấp cao — mẫu hình lặp lại
ít nhất 2 lần trong phiên này (`rapidocr`/`onnxruntime`,
`vietocr`/`torch`). Cần luôn verify qua `pip show`/metadata thật trước
khi tin "chỉ cần pip install 1 gói là đủ".

## Validation

PaddleOCR, RapidOCR: verify qua chạy thật trong sandbox VÀ trên máy
thật của người dùng — cả 2 đều phát hiện vấn đề thật không thấy được
qua review tài liệu/tĩnh. Tesseract: verify qua chạy thật, đối chiếu
trực tiếp với nội dung PDF gốc, khớp gần 100%. Bug deskew: verify qua
dựng lại `TemplateMatcher` thật + đối chiếu source GitHub qua
`git clone`.

**Chưa verify qua source thật trong phiên này** (ghi theo mô tả người
dùng): thay đổi `logger.py` (append→overwrite), `processing_table_model.py`
(append→prepend), Elapsed/ETA.

## Phiên tiếp theo

Ưu tiên: thảo luận riêng `Worker._format_note()` chọn sai warning ưu
tiên (hoãn từ phiên này). Đối chiếu qua source thật 3 thay đổi ghi
theo mô tả. Đánh giá thêm dữ liệu PDF Scanned/Hybrid đa dạng hơn cho
Tesseract (hiện chỉ verify 1 file). Cân nhắc tài liệu cài đặt OCR cho
end-user.

## Ghi chú

Phiên này quy mô bất thường lớn do phải thử nghiệm tuần tự 3 thư viện
OCR khác nhau — không phải vi phạm Rule 1 (kiến trúc không đổi tùy
tiện): mỗi lần đổi đều có bằng chứng thực nghiệm thật buộc phải đổi,
không phải thay đổi theo cảm tính. Cả 3 vấn đề nghiêm trọng nhất trong
phiên (PIR error, chất lượng RapidOCR kém, bug deskew 90°) đều CHỈ phát
hiện được qua chạy thật, không thấy được qua review tài liệu/code tĩnh.

------------------------------------------------------------------------

# Session 2026-08-09 / 2026-08-11

## Mục tiêu

Xử lý Known Issue phát hiện qua thực nghiệm end-to-end sau khi hoàn
thiện OCR: Report.txt cho thấy ~15% data PDF Scanned thiếu 3 field
tiền tệ. Mở rộng thêm: xử lý OCR nhầm lẫn dấu `,`/`.` (silent
corruption).

## Hoàn thành

VND currency suffix stripping (7 biến thể); heuristic phục hồi số bị
OCR nhầm dấu; tăng DPI + Preprocess ảnh; đánh giá lại lý do giữ RGB.

## Quyết định kiến trúc

→ ADR-051 đến ADR-054.

## Bối cảnh: debug & chẩn đoán

Phân tích trực tiếp `TemplateMatcher.extract_fields()` theo debug.txt
người dùng cung cấp: xác nhận Windowing hoạt động đúng, nhưng
`_select_best_value()` trả `None` vì `value_pattern` không khớp token
OCR dạng "4,842,303VND" — Tesseract gộp đơn vị tiền tệ dính liền số
thành 1 token khi bản scan không có khoảng trắng rõ ràng. Đối chiếu
Report.txt xác nhận toàn bộ 13 dòng cảnh báo đều thuộc PDF
`*_scanned.pdf`, chỉ 3 field Decimal tiền tệ — khớp giả thuyết.

## Bối cảnh: 3 hướng giải pháp song song cho lỗi nhầm dấu `,`/`.`

Người dùng đề xuất 3 hướng, dự định kết hợp cả 3:

1. **Tăng DPI** — qua nhiều vòng thực nghiệm, chốt **450** (khác đề
   xuất ban đầu 400).
2. **Preprocess trước Tesseract** (CLAHE + Unsharp Mask). Thứ tự
   deskew-trước-preprocess được xác nhận qua thực nghiệm: không có
   khác biệt rõ ràng so với thứ tự ngược lại.
3. **Heuristic phục hồi số** — 6 dấu hiệu khả nghi dựa trên vị trí
   dấu, tích hợp KHÔNG chỉ dựa vào `Decimal()` raise exception (vì lỗi
   nhầm dấu thường KHÔNG raise).

Kết hợp cả 3: tỷ lệ nhầm dấu giảm xuống dưới 0.5% — PASS toàn bộ test
case hiện có. Ghi nhận đây là cải thiện, KHÔNG phải giải quyết triệt
để.

## Vướng mắc gặp phải

### Silent corruption khó phát hiện hơn field ra `None`

Phát hiện quan trọng: lỗi OCR nhầm dấu `,`/`.` thường KHÔNG khiến
`Decimal()` raise exception — chuỗi sau xử lý vẫn đúng cú pháp nhưng
SAI TRỊ SỐ (có thể lệch tới hàng nghìn lần). Nguy hiểm hơn nhiều so
với field ra `None` (đã có Report.txt ghi nhận qua ADR-032/033) vì
không có dấu hiệu cảnh báo nào. Thiết kế ban đầu dự định chỉ fallback
khi exception xảy ra đã được điều chỉnh lại thành kiểm tra cấu trúc
chuỗi TRƯỚC, độc lập với exception.

### Rủi ro tự tạo ra vấn đề khi cố khắc phục nó (sharpen)

Unsharp Mask có nguy cơ tạo ringing artifact quanh nét mảnh — đúng nét
mảnh nhất trong toàn bộ ký tự chính là đuôi dấu phẩy (đối tượng đang
cố cải thiện). Giải quyết bằng tham số khởi đầu thận trọng (sigma nhỏ,
amount thấp) để tinh chỉnh tăng dần qua thực nghiệm.

## Validation

ADR-051: PASS toàn bộ test case đang có. ADR-052+053 (kết hợp): giảm
xuống dưới 0.5% — KHÔNG phải 0%. Thứ tự deskew/preprocess: không khác
biệt kết quả rõ ràng giữa 2 thứ tự.

## Phiên tiếp theo

Tiếp tục theo dõi 2 case biên chưa có giải pháp của ADR-052. v2.0: DPI
thích ứng theo khổ giấy. Tinh chỉnh `DECIMAL_TAIL_MAX_LENGTH`/
`OCR.PREPROCESS_*`. Việc tồn đọng dài hạn không đổi: `processor.py`,
`main.py`/`ui/main_window.py`, Template Authoring Guide (nay cần thêm
nhóm quy tắc "ký hiệu đơn vị dính liền số": %, VND, đ/Đ), dead code
`UIText.REPORT_PENDING`, `WorkbookSaveError` chưa verify permission
thật.

## Ghi chú

Cả con số DPI cuối cùng (450, khác 400 ban đầu) lẫn kết luận "thứ tự
deskew/preprocess không khác biệt" đều chỉ xác định được qua nhiều
vòng thực nghiệm thực tế, không phải suy đoán lý thuyết. Silent
corruption là phát hiện quan trọng về nguyên tắc: không phải mọi lỗi
dữ liệu đều biểu hiện qua exception hay field `None` — cần chủ động
kiểm tra cấu trúc dữ liệu đầu vào ở các trường hợp có rủi ro sai lệch
âm thầm.

------------------------------------------------------------------------

# Session 2026-08-12 — Đóng v1, Part 1/3

## Mục tiêu

Bắt đầu quy trình đóng v1 (chia 3 phần theo quyết định của người dùng:
Part 1 — Known Issues từ nhật ký; Part 2 — vấn đề người dùng tự ghi
nhận; Part 3 — vấn đề phát sinh khi quét trực tiếp mã nguồn). Phiên
này xử lý toàn bộ Part 1: 7 Known Issue được liệt kê sẵn trong
PROJECT_CONTEXT.md/CHANGELOG.md tại thời điểm bắt đầu phiên.

## Hoàn thành

Xóa `core/processor.py`. Resolve entry point `main.py` vs
`ui/main_window.py`. Rà soát dead code toàn source (3 nhóm — xóa/giữ
có chủ đích/giữ vì là API interface chưa dùng). `TEMPLATE_AUTHORING_GUIDE.md`
mới. Unit test đầu tiên (`test_extractor.py`). Sửa `_format_note()`.
Sửa mismatch ADR-027. Document/Graphics Rules cho `PDFDetector`. Verify
`WorkbookSaveError`.

## Quyết định kiến trúc

→ ADR-055, ADR-056, ADR-057.

## Bối cảnh & vướng mắc gặp phải

### Rà soát dead code — phân loại 3 nhóm

Quét `core/`, `ui/`, `models/`, `utils/`, `config.py`: Nhóm A (xóa) —
5 mục trong `constants.py` không được reference ở bất kỳ đâu. Nhóm B
(giữ, có chủ đích) — `SessionResult`, `ProcessError`, `ProcessStage`,
`ErrorType`: domain model chưa wire vào pipeline nhưng người dùng
quyết định giữ lại cho ý đồ xử lý lỗi có cấu trúc tương lai, thay vì
coi là dead code. Nhóm C (giữ, không phải dead code) — API interface
chủ đích chưa dùng tới.

### TDS không đủ chi tiết đặc tả rule cụ thể

Ban đầu dự định dựa vào `PDF_Detector_Technical_Design.docx` để lấy
đặc tả Document/Graphics Rules, nhưng xác nhận qua đọc trực tiếp: TDS
§7.2 chỉ định nghĩa *khuôn khổ*, không đặc tả *nội dung cụ thể* của
từng rule — luôn là quyết định ở tầng implementation, đúng theo chính
TDS §5.4. Người dùng cập nhật lại file TDS trong project theo yêu cầu
đối chiếu nhưng nội dung không đổi — xác nhận đây không phải thiếu sót
tài liệu, mà là bản chất thiết kế của TDS (mô tả nguyên tắc, không mô
tả tham số).

### Phát hiện mismatch ADR-027 với source thật

Khi rà soát nhánh `extraction.warnings` (dead code liên quan
ADR-055), phát hiện `core/extractor.py::extract()` **không hề raise**
`ValueError` khi UNKNOWN như ADR-027/CHANGELOG/SESSION_SUMMARIES
(Session 2026-07-31) đã mô tả từ đầu — source thật trả về gracefully.
Sai lệch này tồn tại xuyên suốt 3 file nhật ký trong nhiều tuần mà
không ai phát hiện, vì không có cơ chế nào buộc đối chiếu định kỳ giữa
"nhật ký nói gì" và "code thật là gì" — chỉ phát hiện được nhờ rà soát
trực tiếp có chủ đích ở phiên này.

2 phương án được thảo luận: (1) sửa tài liệu khớp code (giữ hành vi
graceful) — bị bác bỏ vì nhánh graceful là dead code trong pipeline
thật, nếu giữ sẽ khiến 1 lỗi lập trình tương lai bị "nuốt" âm thầm
thay vì lộ ra ngay, đi ngược đúng tinh thần ADR-027; (2) sửa code khớp
tài liệu (đã chọn) — ADR-027 là quyết định kiến trúc có lập luận rõ
ràng, không phải mô tả tùy tiện.

### Kỹ thuật tái hiện lỗi permission vượt qua giới hạn container root

Các phiên trước (Session 2026-08-03) từng thử `chmod` nhưng không
thành công vì container chạy root. Phiên này dùng `chattr +i`
(immutable attribute Linux) — chặn được cả root — giải quyết được giới
hạn tồn đọng nhiều phiên. Lưu ý minh bạch: kỹ thuật này Linux-only,
không phản ánh chính xác kịch bản Windows thật ("file đang mở trong
Excel"), nhưng cả 2 kịch bản đều là `OSError`/subclass nên
`except OSError` đã đủ tổng quát. Người dùng bổ sung: đã tự test trên
Windows thật, xác nhận popup hiển thị đúng, ứng dụng không treo.

## Validation

9 unit test `_rotate_bbox()`: PASS thật trên máy người dùng, xác nhận
lại sau mỗi patch tiếp theo trong phiên. `_format_note()`/ADR-055:
verify thực nghiệm trên PDF có đồng thời nhiều loại cảnh báo — thứ tự
hiển thị đúng ưu tiên mới. ADR-056: pipeline không đổi hành vi (đúng
kỳ vọng). ADR-057: `DocumentAnalysis.evidence` có đủ 7 phần tử, mode
cuối không đổi. `WorkbookSaveError`: verify kép — logic qua `chattr
+i` trong sandbox + UX thật trên Windows.

## Phiên tiếp theo

Đóng v1 Part 2/3 (vấn đề người dùng tự ghi nhận — chưa xác định nội
dung cụ thể). Đóng v1 Part 3/3 (quét trực tiếp mã nguồn). Sau khi hoàn
tất cả 3 Part: giai đoạn tài liệu chuyển giao ứng dụng.

## Ghi chú

Phiên đầu tiên dự án có unit test tự động — không thay thế nguyên tắc
"chạy thật để verify" (vẫn tiếp tục áp dụng song song), nhưng bổ sung
1 lớp bảo vệ hồi quy cho phần logic thuần túy, ổn định. Việc phát hiện
mismatch ADR-027 là 1 xác nhận giá trị của quy trình "đối chiếu tài
liệu với source thật" mà dự án áp dụng nhất quán từ đầu — phát hiện
được nhờ rà soát trực tiếp, không phải vì tài liệu tự báo lỗi.

------------------------------------------------------------------------

# Session 2026-08-13 — Đóng v1, Part 2/3

## Mục tiêu

Xử lý Part 2/3: 7 chủ đề do người dùng tự đặt ra qua rà soát/thảo luận
trực tiếp (khác Part 1 — vốn từ log tồn đọng sẵn): memory management,
PDFResult trùng tên, confidence score tăng theo rule, excel_mapping.json
thiếu cột, rủi ro `_merge_same_line()`, multi-line value/max_distance,
tiền xử lý ảnh OCR nâng cao, và tái cấu trúc thư mục project (ưu tiên
cao nhất để kết thúc v1).

## Hoàn thành

Xem `CHANGELOG.md`, mục 2026-08-13, cho danh sách file thay đổi. Tái
cấu trúc `core/` theo pipeline stage là nội dung chính (7 bước tuần
tự, người dùng tự triển khai và verify).

## Quyết định kiến trúc

→ ADR-058, ADR-059, ADR-060, và amend ADR-048.

## Bối cảnh thảo luận theo từng chủ đề

### 1-2. Memory management & vòng đời PDFResult

Xác nhận `PDFReader.read()` đóng file đúng qua context manager;
`PDFDocument`/`ExtractionResult` là biến local, không bị giữ tham
chiếu ngược từ `InvoiceInfo`. Phát hiện phụ: số liệu ADR-048 (~24.9
MB/trang) lỗi thời sau khi ADR-053 tăng DPI — đính chính lại ~56
MB/trang. Xác nhận việc tích lũy `list[PDFResult]` cho cả batch là có
chủ đích (phục vụ log MỌI file + UI real-time), không chỉ cần
`list[InvoiceInfo]`. Ước lượng chi phí ở quy mô 10.000 file: ~24 MB,
nhẹ hơn 3-4 bậc so với chi phí `PageImage` 1 trang. Phát hiện phụ dẫn
tới chủ đề 3: `source_file`/`relative_path` được gán nhưng không thấy
nơi nào đọc lại.

### 3. PDFResult trùng tên

Người dùng xác nhận đây là tình huống thiết kế ban đầu dự tính xử lý.
Thảo luận 2 hướng (A: đổi sang dùng `relative_path`; B: giữ `file_name`
+ thêm cột phụ) — chọn Hướng A, không thêm cột, không đổi width. Với
Warnings trong report.txt, thảo luận thêm 2 phương án con (B1: giữ
full absolute path; B2: đổi `InvoiceInfo.source_file` sang relative)
— chọn B1 (tối thiểu, không đổi ý nghĩa field đang phục vụ mục đích
khác là dữ liệu Excel). → ADR-058.

### 4. Confidence score tăng sau Document/Graphics Rule

Người dùng quan sát score tăng sau ADR-057, đặt câu hỏi có phải vấn đề
cần quan tâm. Phân tích công thức `_compose_confidence()` xác nhận đây
là hệ quả cơ học đúng thiết kế; rà soát toàn bộ nơi đọc
`DocumentAnalysis.confidence` xác nhận CHỈ dùng hiển thị trong
`PDFResult.note`, không gate quyết định `mode` hay logic nào khác —
không phải vấn đề cấp thiết. Lưu ý rủi ro circular validation (2 rule
mới chỉ verify trên đúng 1-2 file PDF đã dùng tinh chỉnh mọi thứ khác
trong dự án) — cần thêm dữ liệu đa dạng trước khi tinh chỉnh weight.
Người dùng xác nhận không cần ghi nhận riêng.

### 5. excel_mapping.json khai ít cột hơn InvoiceInfo

Trả lời câu hỏi "nếu admin chỉ khai 6/12 field, hệ thống có hoạt động
đúng không" — xác nhận CÓ qua truy trực tiếp `Mapper.load()`/`Parser`/
`ExcelWriter._write_row()` — khớp mô tả sẵn có trong
`EXCEL_MAPPING_GUIDE.md`. Không cần sửa code.

### 6. Rủi ro `_merge_same_line()` — lookup bằng value-equality

Người dùng đặt vấn đề `next(...)` có thể `StopIteration` nếu 2 token
trùng hoàn toàn. Phân tích xác nhận KHÔNG THỂ xảy ra về mặt toán học
(`anchor` luôn tự thỏa điều kiện tìm chính nó). Rủi ro thực chất hơn:
nếu tồn tại 2 `WordToken` khác instance nhưng trùng giá trị tuyệt đối,
`next()` có thể trả "nhầm" object — nhưng vì 2 token trùng giá trị
tuyệt đối, kết quả merge giống hệt nhau bất kể chọn object nào → vô
hại. Người dùng xác nhận không cần sửa.

### 7. Multi-line value / phụ thuộc max_distance tĩnh

Người dùng đặt vấn đề (dựa trên đánh giá rủi ro, chưa gặp thật trên
A4, nghi ngờ sẽ gặp với A5/bảng biểu phụ). Đề xuất ban đầu của
Assistant (window động theo Key/Section kế tiếp; khóa
`direction=BELOW`) bị người dùng **bác bỏ với lý do kỹ thuật xác
đáng**: window động không đảm bảo có mốc chặn phía sau (khác Section
— luôn có giả định layout hóa đơn có khối kế tiếp); `direction` không
thể khóa cứng vì độ dài giá trị phụ thuộc nội dung thật của từng hóa
đơn. Xác nhận lại: đây là giới hạn KIẾN TRÚC của phương pháp hình học
tĩnh, không phải bug patch được ở tầng heuristic. Người dùng yêu cầu
ghi nhận nghiêm túc (không phải "known limitation cần tinh chỉnh tham
số" như các mục khác). → ADR-059.

### 8. Đề xuất tiền xử lý ảnh OCR nâng cao — hủy bỏ

Người dùng đề xuất Binarization (Otsu/Adaptive Thresholding), Denoising
(Gaussian Blur riêng trước sharpen), Border Removal. Phân tích:
Binarization có rủi ro kỹ thuật rõ ràng (xung đột với cách Tesseract
LSTM/OEM=3 tự xử lý ảnh xám nội bộ, nguy cơ xóa mất đuôi dấu phẩy —
đúng vấn đề ADR-052/053 đang giải quyết) — khuyến nghị không thêm;
Denoising/Border Removal khả thi kỹ thuật nhưng chưa có bằng chứng
thực nghiệm về nhiễu/viền đen trên dữ liệu thật hiện có. Người dùng
quyết định hủy toàn bộ đề xuất, ghi nhận "tăng cường hiệu quả OCR" là
nội dung quan trọng cho v2.0.

### 9. Tái cấu trúc thư mục project (trọng tâm chính của phiên)

Người dùng xác định đây là việc quan trọng nhất để kết thúc v1, do kế
hoạch v2.0 sẽ bổ sung nhiều model cho các module hiện có. Quét toàn bộ
import dependency thật trước khi đề xuất, xác nhận 13 file chia thành
5 giai đoạn pipeline độc lập + 1 tầng domain dùng chung.

4 điểm cần quyết định, người dùng chốt: (a) đổi `models/` top-level →
`ui/models/`; (b) tiếp tục mirror cấu trúc `core/` mới cho test; (c)
không tạo sẵn `core/parsing/layoutlm/` placeholder; (d) `config.py`
không đổi. Làm rõ thêm 2 câu hỏi kỹ thuật của người dùng: bắt buộc
phải là package (cú pháp `from core.domain.models import X` yêu cầu);
`__init__.py` rỗng cần thiết (đối chiếu tiền lệ `tests/__init__.py` đã
rỗng từ trước — chọn regular package để nhất quán). → ADR-060.

## Vướng mắc gặp phải

Không phát sinh lỗi kỹ thuật ngoài dự kiến trong phiên này — toàn bộ
nội dung là thảo luận/rà soát/quyết định thiết kế, không có debug thực
nghiệm nào cần giải quyết bất ngờ (khác các phiên OCR/Template trước).

## Validation

Memory lifecycle: xác nhận qua đọc trực tiếp source, không qua chạy
thật đo RAM. PDFResult trùng tên: người dùng tự áp dụng + verify chạy
thật kịch bản "Quý 3 → Tháng 7/8/9". excel_mapping.json thiếu cột: xác
nhận qua đọc source, không cần chạy thật thêm. Tái cấu trúc thư mục:
người dùng tự triển khai 7 bước, verify độc lập từng bước
(`pytest -v` + chạy thật), xác nhận 1 lượt UI thật end-to-end đầy đủ ở
bước cuối.

## Phiên tiếp theo

Đóng v1 Part 3/3 (quét lại toàn bộ source theo cấu trúc thư mục MỚI).
Sau đó: tài liệu chuyển giao ứng dụng. v2.0 planning (chưa bắt đầu
thiết kế chi tiết): LayoutLM Parser engine, tăng cường OCR, DPI thích
ứng.

## Ghi chú

Phiên đầu tiên có tỷ trọng THẢO LUẬN/QUYẾT ĐỊNH KIẾN TRÚC cao hơn hẳn
phần triển khai code trực tiếp — phù hợp mô hình làm việc mới được
thiết lập từ đầu phiên (người dùng đặt vấn đề dựa trên mã nguồn + nhật
ký, Assistant phân tích/phản biện dựa trên 4 nguyên tắc ưu tiên: Source
of Truth mã nguồn > logic/tri thức > ý kiến người dùng trong phiên >
nhật ký làm phụ trợ). 2 lần người dùng bác bỏ đề xuất của Assistant
với lý do kỹ thuật xác đáng (chủ đề 7 và 8) — xác nhận giá trị của
việc yêu cầu xác nhận trước khi triển khai.

------------------------------------------------------------------------

# Session 2026-08-14 — Đóng v1, Part 3/3

## Mục tiêu

Hoàn tất Part 3/3: Assistant quét trực tiếp toàn bộ source theo cấu
trúc thư mục mới (ADR-060), tự đề xuất danh sách vấn đề (nguy cơ logic,
dead code, tham số cấu hình rải rác, thiếu unit test), người dùng xác
nhận từng nhóm trước khi triển khai.

## Hoàn thành

5 nhóm vấn đề (A-E), xử lý tuần tự (chi tiết file thay đổi: xem
`CHANGELOG.md`, mục 2026-08-14). Ngoài phạm vi quét gốc: 2 vấn đề UI
phát sinh trong phiên (Report fallback, Start validation bug + PDF
discovery cancellable).

## Quyết định kiến trúc

→ ADR-061 đến ADR-066.

## Bối cảnh theo từng nhóm

### Nhóm A — Nguy cơ logic (ưu tiên cao)

**A1 (app crash thiếu tessdata):** `Worker.__init__` khởi tạo
`Extractor()`/`OCREngine()` vô điều kiện ngay lúc mở app;
`OCREngine.__init__()` fail-fast kiểm tra file ngay trong constructor
— chặn cả người dùng chỉ xử lý PDF Digital. → ADR-061.

**A2 (template mọi field weight=0 không bao giờ được chọn, không cảnh
báo):** → ADR-062.

### Nhóm B — Dead code / thuộc tính thừa

Xác nhận qua rà soát tham chiếu toàn source, xóa 4 mục không được
dùng ở bất kỳ đâu. Giữ nguyên `ui/theme.py` (trống nhưng có định
hướng rõ trong §18 Future Improvements — "Dark Mode", không phải dead
code theo nghĩa viết rồi bỏ quên).

### Nhóm C — Tham số cấu hình rải rác

Tập trung 9 hằng số của `PDFDetector` và 4 hằng số của `ValueConverter`
vào `constants.py`, theo đúng quy ước đã có với `TemplateMatching`/
`OCR`/`NumberRepair`. Cố ý KHÔNG di chuyển `_SCAN_METADATA_KEYWORDS`
(dữ liệu tra cứu, không phải threshold) và `_WARNING_CATEGORY_PRIORITY`
(logic sắp xếp, không phải giá trị cần tinh chỉnh). → ADR-063.

### Nhóm D — Unit test cho ValueConverter

`tests/core/parsing/template/test_value_converter.py` — unit test thứ
2 của dự án, cùng nguyên tắc với `test_extractor.py`: giá trị
`expected` tự suy diễn tay theo đặc tả ADR-032/043/051/052, không copy
ngược từ code đang test. 9 nhóm test. Phát hiện phụ: 1 test case tái
tạo chính xác giới hạn đã ghi ở ADR-052 ("cụm cuối 3 chữ số trùng
ngẫu nhiên với decimal_separator") — đưa vào test như xác nhận hành vi
đã biết, không phải bug mới.

### Nhóm E — Ghi nhận mức thấp (không sửa code)

3 mục phân tích và quyết định KHÔNG xử lý ở v1, mỗi mục có lý do rõ
ràng: `_autofit_columns()` magic number (thuần túy thẩm mỹ, không có
driver thực nghiệm); `_is_total_row_present()` dùng API nội bộ
`openpyxl` (rủi ro thật nhưng an toàn ở version đã pin, chỉ ghi nhận
Known Issue cho tương lai); `FieldDefinition`/`SpatialRelation` thiếu
validate range (khác A2 — range hợp lệ của `max_distance`/
`axis_tolerance` phụ thuộc layout thật, không có ranh giới cứng có thể
validate mà không rủi ro false positive).

### Ngoài phạm vi quét ban đầu — 2 vấn đề UI người dùng đặt thêm trong phiên

**Report chỉ mở được sau khi đã Start trong phiên hiện tại:** →
ADR-064.

**Bug Start khi chưa chọn Input/Output:** phát hiện gốc rễ là
`pathlib.Path` không override `__bool__` khiến validate chưa từng hoạt
động. → ADR-065.

Từ đó phát hiện thêm vấn đề liên quan (Stop không có tác dụng): thảo
luận riêng, xác nhận nguyên nhân `Path.rglob()` bị `sorted()` ép chạy
hết 1 mạch. Người dùng xác nhận rủi ro tồn tại thật (dựa trên yêu cầu
khách hàng + phân tích hành vi người dùng) và chọn phương án "phản hồi
tức thời". → ADR-066.

## Vướng mắc gặp phải

Không có lỗi kỹ thuật ngoài dự kiến phát sinh trong lúc triển khai
patch — toàn bộ nội dung phiên này là phát hiện qua **rà soát tĩnh
trực tiếp source** (khác các phiên OCR/Template trước, vốn phát hiện
qua debug thực nghiệm), sau đó verify lại bằng chạy thật trước khi coi
là đóng. Điểm khác biệt về phương pháp này cho thấy giá trị bổ sung
của việc rà soát source có chủ đích, không chỉ dựa vào phát hiện bị
động qua chạy thật.

## Validation

Toàn bộ patch đều được người dùng tự áp dụng và xác nhận test thành
công trước khi chuyển mục tiếp theo (Rule 2/3/12): A1/A2 verify đúng
kỳ vọng, không regression. B/C: `pytest -v` + UI thật, không
regression. D: 43 test case (parametrize) PASS toàn bộ. Report
fallback: 3 kịch bản đúng kỳ vọng. Start validation + PDF discovery: 5
kịch bản đúng kỳ vọng, không regression.

## Phiên tiếp theo

**Đóng v1 hoàn tất cả 3 Part.** Giai đoạn tiếp theo: tài liệu chuyển
giao ứng dụng (`excel_mapping.json` khớp workbook thật, tài liệu cài
đặt OCR cho end-user). v2.0 planning: LayoutLM Parser engine (ADR-059),
DPI thích ứng theo khổ giấy (ADR-053), tăng cường hiệu quả OCR. Theo
dõi Known Issue mới: `_is_total_row_present()` cần re-verify nếu nâng
cấp `openpyxl` khỏi `3.1.5`.

## Ghi chú

Phiên này áp dụng mô hình làm việc nhất quán suốt toàn phiên: Assistant
chủ động quét source và đề xuất TOÀN BỘ danh sách vấn đề trước (thay
vì chờ người dùng phát hiện từng cái), người dùng xác nhận phạm vi xử
lý và thứ tự ưu tiên, sau đó xác nhận từng patch cụ thể trước khi áp
dụng — không có trường hợp nào Assistant tự ý sửa code hoặc nhật ký mà
chưa qua xác nhận.

------------------------------------------------------------------------

# Session 2026-08-15 — Mở v2.0: Multi-Threading (Bước 1-3/5)

## Mục tiêu

Bắt đầu chính thức v2.0 của dự án (người dùng xác nhận đầu phiên).
Triển khai `MULTI_THREAD_SPECIFICATION.md` theo đúng lộ trình 5 bước,
tuần tự từng bước, verify trước khi sang bước kế (Rule 2/3/12).

## Hoàn thành

Bước 1 (`core/system/hardware.py` + test), Bước 2
(`ThreadSelectorWidget`), Bước 3 (`PDFTaskSignals`/`PDFTaskRunnable`/
tái cấu trúc `Worker.process()`).

## Quyết định kiến trúc

→ ADR-067.

## Bối cảnh thảo luận

### Bước 2: điều chỉnh sau thực nghiệm — QSpinBox → QComboBox

Sau khi verify Bước 2 lần đầu (QSpinBox, giới hạn `[1, total_cores]`),
người dùng phát hiện qua thực nghiệm 2 vấn đề: (1) muốn ComboBox thay
SpinBox; (2) giới hạn `[1, total_cores]` cho phép chọn vượt mức
`recommended_threads` — rủi ro người dùng chọn nhầm số luồng cao hơn
mức an toàn đã tính toán. Sửa: `QComboBox` giới hạn
`[1, recommended_threads]`, bỏ hẳn `total_cores` khỏi phạm vi lựa
chọn; bỏ luôn `lbl_hint`/`THREAD_HINT_FORMAT` (không còn cần thiết vì
giới hạn đã tự thân đóng vai trò khuyến nghị).

### Bước 3: xung đột `MULTI_THREAD_SPECIFICATION.md` §4 vs ADR-008

Trước khi code Bước 3, Assistant tự phát hiện (không phải người dùng
đặt câu hỏi) mâu thuẫn giữa đặc tả gốc (§4 bước 5: ghi Excel cho phần
đã xử lý được khi Stop) và ADR-008/`PROJECT_CONTEXT.md` §17 (frozen
rule: Excel chỉ ghi 1 lần, sau khi MỌI PDF xong). Trình bày 2 phương
án (A: giữ ADR-008; B: amend ADR-008 cho v2.0) — không tự chọn theo
Rule 1. Người dùng chọn **Phương án A** (giữ nguyên ADR-008).

### Thảo luận sau Bước 3: `bool` vs `threading.Event` cho cancellation flag

Người dùng hỏi lợi ích của việc đổi `bool` (đọc qua closure từ Pool
thread) sang `threading.Event`. Giải thích: GIL của CPython đảm bảo an
toàn ở mức bytecode (không torn read/write) cho cách dùng hiện tại
(đọc 1 lần, không polling); `threading.Event` có 2 lợi ích lý thuyết
chưa cần dùng đến ở thiết kế hiện tại — (1) "happens-before" guarantee
tường minh qua API `threading` thay vì phụ thuộc chi tiết implementation
GIL; (2) khả năng `wait(timeout)` hiệu quả, không cần trong thiết kế
hiện tại (chỉ check 1 lần, không loop chờ). Khuyến nghị giữ `bool` cho
v2.0 hiện tại (Rule 9). Người dùng chọn: ghi nhận vào nhật ký, không
áp dụng ngay.

## Validation

Bước 1: `pytest -v` PASS toàn bộ (người dùng tự verify, không có chi
tiết log cụ thể trong phiên). Bước 2: chạy UI thật 2 vòng (trước và
sau điều chỉnh QComboBox), người dùng xác nhận thành công. Bước 3:
người dùng xác nhận "đã triển khai và chạy thực nghiệm" — chưa có mô
tả chi tiết kịch bản test cụ thể (số file, số luồng, kết quả đo được)
trong phiên này.

## Phiên tiếp theo

Bước 4 (hoàn thiện Stop — test kịch bản 100 file, Stop giữa chừng,
xác nhận UI không đơ + Excel xuất đúng số lượng hoàn thành TRƯỚC thời
điểm Stop theo đúng Phương án A vừa chốt, tức là **không** ghi gì nếu
Stop trước khi tất cả xong). Bước 5 (test tương thích đa nền tảng +
đo hiệu năng v1 vs v2, theo §5 của đặc tả — 5 nguyên tắc tương thích
macOS/Windows chưa được rà soát riêng trong phiên này). Cân nhắc:
`bool` vs `threading.Event` cho cancellation flag (ghi nhận, chưa áp
dụng — xem PROJECT_CONTEXT.md §14).

## Ghi chú

Phiên này chính thức đánh dấu chuyển sang v2.0 theo yêu cầu người
dùng đầu phiên. Quy trình đóng băng thiết kế trước khi code (Rule 11)
được áp dụng nghiêm ngặt ở Bước 3 — trình bày đủ 5 quyết định kiến
trúc + 1 xung đột phát hiện độc lập trước khi viết bất kỳ dòng code
nào, theo đúng mô hình đã thiết lập từ v1.