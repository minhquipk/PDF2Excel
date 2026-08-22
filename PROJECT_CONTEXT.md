# PROJECT_CONTEXT.md

# PDF Invoice Extractor

> Tài liệu Bàn Giao Bối Cảnh & Kiến Trúc Dự Án
>
> File này là **living document** — luôn phản ánh trạng thái HIỆN TẠI
> của dự án (bức ảnh chụp tại thời điểm đọc), khác với
> `CHANGELOG.md`/`SESSION_SUMMARIES.md`/`ARCHITECTURE_DECISIONS.md`
> vốn là lịch sử. Mọi thay đổi kiến trúc phải được thảo luận trước khi
> implement (xem `DEVELOPMENT_WORKFLOW.md`).
>
> **Trạng thái tại thời điểm cập nhật gần nhất:** đã đóng xong v1 (đủ
> cả 3 Part, Session 2026-08-12/13/14) và hoàn tất lộ trình
> Multi-Threading v2.0 (5/5 bước, Session 2026-08-15/16). Đang ở giai
> đoạn chuẩn bị tài liệu chuyển giao ứng dụng và lên kế hoạch các hạng
> mục v2.0 khác (LayoutLM Parser, DPI thích ứng khổ giấy...).

------------------------------------------------------------------------

# 1. Mục Tiêu Dự Án

Xây dựng ứng dụng desktop bằng Python để tự động trích xuất thông tin
từ số lượng lớn hóa đơn PDF và ghi dữ liệu trích xuất được vào 1
template Excel có sẵn.

Yêu cầu chính:
- Quét toàn bộ 1 thư mục đệ quy.
- Hỗ trợ hàng nghìn file PDF.
- Tự động phát hiện PDF Digital / PDF OCR (scan).
- Trích xuất thông tin hóa đơn.
- Lưu kết quả trung gian trong bộ nhớ.
- Chỉ ghi Excel đúng 1 lần sau khi mọi file đã xử lý xong.
- Sinh báo cáo lỗi để rà soát thủ công.

Đối tượng người dùng: nhân viên văn phòng, không biết lập trình.

------------------------------------------------------------------------

# 2. Kiến Trúc Tổng Quan

```
MainWindow
    │
    ▼
Worker (QThread)
    │
    ▼
_process_pdf()
    │
    ▼
PDFReader
    │
    ▼
PDFDetector
    │
    ▼
Extractor ──(quyết định gọi khi cần OCR)──> OCREngine
    │
    ▼
Parser (TemplateMatcher + ValueConverter)
    │
    ▼
PDFResult
    │
    ▼
Bộ nhớ (list[PDFResult])
    │
    ▼
ExcelWriter
    │
    ▼
ReportWriter ──▶ logs/app.log (list[PDFResult]) + reports/Report.txt (ExcelWriteResult)
```

UI hoàn toàn tách biệt khỏi business logic. `Worker` không bao giờ
truy cập UI trực tiếp. Giao tiếp chỉ qua Qt Signal.

------------------------------------------------------------------------

# 3. Cấu Trúc Project Hiện Tại

```
config.py
main.py
requirements.txt
requirements-dev.txt

ui/
    base_widget.py
    widgets.py
    main_window.py
    theme.py
    worker.py
    models/
        processing_table_model.py

utils/
    logger.py

core/
    domain/
        models.py
        enums.py
        constants.py
    reading/
        pdf_reader.py
    detection/
        pdf_detector.py
    extraction/
        extractor.py
        ocr_engine.py
    parsing/
        parser.py
        template/
            template_loader.py
            template_matcher.py
            value_converter.py
    export/
        excel_mapper.py
        excel_writer.py
        report_writer.py

tests/
    core/
        extraction/
            test_extractor.py
        parsing/
            template/
                test_value_converter.py

resources/
    excel_mapping.json
    EXCEL_MAPPING_GUIDE.md
    TEMPLATE_AUTHORING_GUIDE.md
    templates/
        sample_invoice_v1.json
```

Tái cấu trúc theo pipeline stage hoàn tất Session 2026-08-13 (xem
ADR-060). `models/` top-level cũ đã đổi thành `ui/models/`. `core/`
chia theo giai đoạn pipeline thay vì phẳng như trước.

------------------------------------------------------------------------

# 4. Trạng Thái Các Module

## Đã hoàn thành (production code, không còn Mock)

- **`core/domain/`** — `models.py` (toàn bộ domain model, frozen
  dataclass theo đúng chỗ), `enums.py`, `constants.py` (tập trung mọi
  hằng số threshold, xem ADR-063).
- **`core/reading/pdf_reader.py`** — đọc PDF qua PyMuPDF, dựng
  `PDFDocument`; đọc raw word tuples (`words`) và render `PageImage`
  RGB (450 DPI) cho mọi trang.
- **`core/detection/pdf_detector.py`** — reasoning engine đầy đủ 7/7
  Rule Category theo TDS §7.2 (Text, Image, Consistency, Quality,
  Layout, Document, Graphics). 2 rule cuối (Document/Graphics) mới,
  trọng số cố ý thấp, **chưa qua thực nghiệm với dữ liệu thật đa
  dạng** (xem §14 nhóm Detection).
- **`core/extraction/extractor.py`** — dispatch chiến lược extraction
  theo `DocumentAnalysis.mode` (Digital/OCR/per-page Hybrid); chuẩn
  hóa hình học + text whitespace thành `WordToken`.
- **`core/extraction/ocr_engine.py`** — **implementation thật**
  (Tesseract 5.x + tessdata_best qua `pytesseract`), thay Mock từ
  Session 2026-08-08/09 (ADR-047). Kiểm tra `vie.traineddata` trì
  hoãn đến lần đầu `recognize()` (ADR-061) — app không crash lúc mở
  nếu thiếu tessdata và batch chỉ toàn PDF Digital.
- **`core/parsing/`** — `parser.py` (orchestrator mỏng),
  `template/template_loader.py`, `template/template_matcher.py` (Key
  Matching + Section-scoped + Windowing + Value Matching gap-based),
  `template/value_converter.py` (TEXT/DECIMAL/DATE, stateless, không
  raise, tự phục hồi số OCR nhầm dấu).
- **`core/export/`** — `excel_mapper.py`, `excel_writer.py` (ghi vào
  Excel Table có sẵn qua openpyxl), `report_writer.py` (2 kênh output
  tách biệt, cả 2 đều ghi đè mỗi lần chạy — ADR-050).
- **`ui/`** — `base_widget.py`, `widgets.py`, `main_window.py`,
  `worker.py` (pipeline tích hợp end-to-end đầy đủ:
  Reader → Detector → Extractor → Parser → ExcelWriter → ReportWriter).
- **`ui/models/processing_table_model.py`**.
- **`utils/logger.py`** — console + `FileHandler` (`logs/app.log`,
  UTF-8, ghi đè mỗi lần chạy).
- **`requirements.txt`** — pin version đã xác nhận qua kiểm thử thực
  tế: `PySide6==6.11.1`, `PyMuPDF==1.28.0`, `rapidfuzz==3.14.5`,
  `openpyxl==3.1.5`, `pytesseract==0.3.13`.
- **`requirements-dev.txt`** — `pytest==8.3.4` (tách khỏi
  `requirements.txt` vì không cần cho end-user).
- **`resources/EXCEL_MAPPING_GUIDE.md`** — hướng dẫn viết
  `excel_mapping.json` cho người điều hành không biết lập trình.
- **`resources/TEMPLATE_AUTHORING_GUIDE.md`** — hướng dẫn viết
  Template Definition JSON, đúc kết toàn bộ quy tắc/ràng buộc phát
  sinh qua thực nghiệm nhiều phiên.
- **Test tự động (3 module, `tests/core/`):**
  `test_extractor.py` (9 case cho `_rotate_bbox()`),
  `test_value_converter.py` (9 nhóm test cho `ValueConverter`),
  `test_hardware.py` (9 test case cho `get_cpu_info()`).
- **`core/system/hardware.py`** — `get_cpu_info()`, pure function, đã
  có unit test (`tests/core/system/test_hardware.py`).

## Tính năng UI hiện tại

Input folder, Output Excel, Start, Stop, Report, Exit, Progress bar,
Processing table (hiển thị `relative_path` — ADR-058).

## Còn để ngỏ, có chủ đích (không phải bug)

- **`resources/excel_mapping.json`** vẫn là mapping mẫu (`tblInvoices`),
  chưa khớp workbook Excel thật của người dùng cuối — quyết định lùi
  sang giai đoạn làm tài liệu chuyển giao ứng dụng (không thuộc phạm
  vi đóng v1 code).
- **Tài liệu hướng dẫn cài đặt OCR cho end-user** (Tesseract binary hệ
  thống — không cài qua `pip`; `vie.traineddata` phải tự tải/đặt vào
  `TESSDATA_DIR`) — chưa có tài liệu dạng `EXCEL_MAPPING_GUIDE.md`
  tương đương. Lùi sang giai đoạn chuyển giao.
- **`core/processor.py`** — đã xóa hoàn toàn (Session 2026-08-12).
  Vai trò orchestrator (ADR-004) chính thức thuộc về `Worker.process()`.

------------------------------------------------------------------------

# 5. Luồng Dữ Liệu (Data Flow)

```
Path
  ↓ (PDFReader.read)
PDFDocument
  ↓ (PDFDetector.analyze)
DocumentAnalysis
  ↓ (Extractor.extract — bỏ qua nếu mode UNKNOWN, ADR-027)
ExtractionResult (words_by_page, page_images)
  ↓ (Parser.parse — TemplateMatcher + ValueConverter)
InvoiceInfo | None
  ↓
PDFResult (pdf_type/status/note từ DocumentAnalysis, invoice từ Parser)
  ↓ (tích lũy trong Worker.process(), 1 PDF/lần — ADR-006)
list[PDFResult]
  ↓ (ExcelWriter.write — đúng 1 lần cuối batch, ADR-008)
.xlsx + ExcelWriteResult
  ↓ (ReportWriter.write)
logs/app.log (list[PDFResult]) + reports/Report.txt (ExcelWriteResult)
```

Ứng dụng KHÔNG BAO GIỜ ghi Excel trong lúc xử lý từng PDF. Excel chỉ
được ghi đúng 1 lần sau khi mọi PDF đã xử lý xong.

------------------------------------------------------------------------

# 6. Các Quyết Định Thiết Kế Quan Trọng

Phần này tóm tắt các nguyên tắc thiết kế cốt lõi bằng ngôn ngữ đơn
giản. Lý do kỹ thuật đầy đủ: xem ADR tương ứng trong
`ARCHITECTURE_DECISIONS.md`.

## Memory First (→ ADR-006, ADR-007)

PDF được xử lý từng file một. Mỗi PDF được giải phóng khỏi bộ nhớ ngay
sau khi xử lý xong. Chỉ object `PDFResult` còn lại trong bộ nhớ —
giảm mạnh mức dùng bộ nhớ.

## Ghi Excel Đúng 1 Lần (→ ADR-008)

Ghi Excel tốn kém. Không bao giờ ghi sau mỗi PDF. Chỉ ghi 1 lần ở cuối.

## Trách Nhiệm Của `process()` (→ ADR-004)

`process()` là orchestrator. KHÔNG BAO GIỜ chứa logic parse PDF.

```
for pdf in pdf_files:
    result = _process_pdf(pdf)
    results.append(result)
_write_excel()
```

Trách nhiệm orchestrator này hiện được implement là
`Worker.process()` trong `ui/worker.py`.

## Trách Nhiệm Của `_process_pdf()` (→ ADR-005, ADR-024, ADR-029)

Toàn bộ business logic nằm ở đây (`Worker._process_pdf()`):

```
PDF → PDFReader → PDFDetector → Extractor (nếu mode hợp lệ) →
Parser → PDFResult
```

`PDFDetector` là reasoning engine tất định. Nó nhận `PDFDocument` bất
biến, dựng `AnalysisContext` bất biến, giữ lại toàn bộ `Evidence`
heuristic, tùy chọn tham vấn `KnowledgeRecord` read-only, và trả về
`DocumentAnalysis` bất biến kèm `Confidence` giải thích được.

## Trách Nhiệm Của Reader (→ ADR-016, ADR-025)

`PDFReader` chỉ đọc nội dung PDF và chuyển object PyMuPDF thành domain
model bất biến. `PDFReader` KHÔNG được thực hiện: OCR, regex parsing,
trích xuất hóa đơn, phân loại PDF, phân tích dữ liệu, validate
business. `PDFReader` là ranh giới giữa PyMuPDF và domain của dự án.

## Chiến Lược `PDFDocument` (→ ADR-025)

`PDFDocument` giữ toàn bộ text của tài liệu. Lý do: Parser hưởng lợi
từ việc giữ quan hệ giữa các trang và ngữ cảnh tài liệu. Mức dùng bộ
nhớ vẫn chấp nhận được vì chỉ 1 PDF được xử lý tại 1 thời điểm.

## Chiến Lược Analyzer / Knowledge System (→ ADR-019, ADR-023)

Vai trò "Analyzer" (thu thập thống kê tài liệu, dựng knowledge cache
tái sử dụng) hiện được `PDFDetector` (Rule System + Confidence Model)
đảm nhiệm theo thiết kế trong `PDF_Detector_Technical_Design.docx`.
Việc lưu trữ/quản lý vòng đời `KnowledgeRecord` (TDS Chapter 9) mới
dừng ở mức thiết kế, **chưa implement trong source** (xem §14 nhóm
Detection).

## Source of Truth (→ ADR-018)

Implementation luôn dựa trên source code hiện tại. Lịch sử chat không
bao giờ là tham chiếu implementation.

------------------------------------------------------------------------

# 7. Thiết Kế UI

```
Input Folder
Output Excel
---------------------------
        Start   Stop
---------------------------
Progress
---------------------------
Processing Table
---------------------------
             Report Exit
```

Cột của Processing Table:

| Cột    | Mô tả                        |
|--------|-------------------------------|
| PDF    | Đường dẫn tương đối (relative_path — ADR-058) |
| TYPE   | Digital / OCR                 |
| STATUS | OK / ERROR / OCR...            |
| NOTE   | Thông điệp chi tiết            |

------------------------------------------------------------------------

# 8. Thiết Kế Worker

`Worker` chạy trong `QThread` riêng. `MainWindow` không bao giờ thực
hiện tác vụ nặng.

Signal: `started`, `progress`, `file_processed`, `finished`,
`cancelled`, `error`.

PDF discovery dùng `Worker._discover_pdf_files()` (dựa trên
`os.walk()`, cancellable, case-insensitive — ADR-066), không dùng
`Path.rglob()` (blocking, không hủy được giữa chừng).

------------------------------------------------------------------------

# 9. Chiến Lược Progress

Progress dựa trên `số PDF đã xử lý / tổng số PDF`. Elapsed time và ETA
được cập nhật riêng.

------------------------------------------------------------------------

# 10. Quy Ước Coding

- Python 3.12+
- Type hint mọi nơi.
- Dataclass cho data model.
- Enum cho giá trị cố định.
- Mỗi class 1 trách nhiệm.
- Tránh biến global.
- Ưu tiên composition hơn inheritance.

------------------------------------------------------------------------

# 11. Thư Viện

| Nhóm | Thư viện |
|------|----------|
| GUI | PySide6 |
| PDF | PyMuPDF (fitz) — text, words, render page image |
| OCR | Tesseract 5.x + tessdata_best (qua `pytesseract`) — binary hệ thống, KHÔNG cài qua `pip`; `vie.traineddata` (tessdata_best) tự tải vào `TESSDATA_DIR` (`resources/tessdata_best/`) |
| Ảnh | Không cần thư viện riêng — `Page.get_pixmap()` của PyMuPDF đã đủ (ADR-026); `pdf2image` không cần |
| Excel | openpyxl — ghi vào Excel Table có sẵn |
| Regex | `re` |
| Data | `dataclasses` |
| Fuzzy Matching | rapidfuzz — dùng bởi `template_matcher.py` |
| Test | pytest (`requirements-dev.txt`, tách riêng) |

------------------------------------------------------------------------

# 12. Quy Trình Phát Triển

Xem đầy đủ ở `DEVELOPMENT_WORKFLOW.md`. Tóm tắt: phát triển tăng dần,
mỗi bước phải compile + run + verify trước khi tiếp tục; không bao
giờ implement nhiều module cùng lúc.

------------------------------------------------------------------------

# 13. Mock Mode (đã kết thúc vai trò)

Mock Mode được dùng trước khi implement xử lý PDF thật — mục đích lịch
sử: test UI, test Thread, test Signal, test TableModel.

**Trạng thái hiện tại:** không còn module nào ở trạng thái Mock. Toàn
bộ pipeline là production code: `PDFReader` → `PDFDetector` →
`Extractor` → `OCREngine` (Tesseract thật, thay Mock từ Session
2026-08-08/09) → `Parser` → `ExcelWriter` → `ReportWriter`, tất cả đã
wire vào `ui/worker.py`. Pipeline đã được verify qua chạy UI thật
end-to-end nhiều lần (Input Folder → Start → Report) với PDF Digital
và Scanned thật.

------------------------------------------------------------------------

# 14. Vấn Đề Đã Biết (Known Issues)

Phân nhóm theo pipeline stage để dễ tra cứu khi đang làm việc trên 1
module cụ thể. Mỗi mục có pointer `→ ADR-xxx` cho lý do kỹ thuật đầy
đủ.

## Detection (`PDFDetector`)

- **Document Rule / Graphics Rule** (`document_metadata`,
  `vector_graphics_coverage`) là thiết kế mới hoàn toàn, **chưa qua
  thực nghiệm với dữ liệu thật đa dạng**. Trọng số
  (`_DOCUMENT_RULE_WEIGHT`/`_GRAPHICS_RULE_WEIGHT` = 0.20), ngưỡng
  (`_GRAPHICS_DRAWING_PAGE_RATIO` = 0.50), và danh sách từ khóa
  (`_SCAN_METADATA_KEYWORDS`) đều là placeholder ban đầu. → ADR-057.
- **Knowledge System** (TDS Chapter 9: lifecycle, governance,
  nguồn dữ liệu) chỉ mới ở mức thiết kế — chưa có persistence/
  lifecycle management trong source. → ADR-019, ADR-023.

## Extraction / OCR

- **Extractor route trang hỗn hợp (text + ảnh) về 1 nguồn duy nhất**
  (text-layer thắng nếu có) — nội dung ảnh liên quan (con dấu, chữ ký)
  trên trang đó bị bỏ qua. Hoãn có chủ đích sang v2.0 (dual-source +
  cần thiết kế khử trùng bbox-overlap). → xem SESSION_SUMMARIES.md,
  Session 2026-07-31.
- **Tỷ lệ nhầm lẫn dấu `,`/`.` khi OCR** còn dưới 0.5%, **chưa về
  0%**. 2 trường hợp biên chưa có giải pháp: (a) OCR làm mất hẳn dấu
  phân cách (không còn dấu vết vị trí để suy luận); (b) cụm cuối đúng
  3 chữ số trùng ngẫu nhiên với `decimal_separator` đã cấu hình. →
  ADR-052, ADR-053.
- **`NumberRepair.DECIMAL_TAIL_MAX_LENGTH`** (= 3) và 4 hằng số
  `OCR.PREPROCESS_*` là giá trị ước lượng ban đầu, cần tinh chỉnh khi
  có thêm dữ liệu PDF Scanned thật đa dạng hơn. → ADR-052, ADR-053.
- **`OCR_ACCURACY_SPECIFICATION.md` (Two-Pass ROI OCR) đang triển khai
  dở dang, CHƯA đóng** (cập nhật Session 2026-08-21). Giai đoạn 2
  (output trực tiếp của OCR) hiện dùng Pass 1 `vie`/tessdata_best và Pass
  2 `eng`/tessdata_fast, PSM=8, whitelist số/dấu. Trên tập test hiện hành,
  Pass 1 còn 6 field sai; `ROI_UPSCALE_FACTOR=1.25` tạm sửa đúng 5/6 mà
  không làm xấu field Pass 1 đúng. Các giá trị `1.25`, `1.3`, `1.45`,
  `1.85`, `1.9` có cùng số field sửa đúng nên `1.25` chưa là giá trị final.
  `ROI_PADDING_RATIO` vẫn là `0.07` và chưa chốt. Giai đoạn 1 (Median
  Blur/Unsharp Masking) và giai đoạn 3 (heuristic hậu OCR) chưa được trộn
  vào thực nghiệm hiện tại. Performance (<50ms/trang) và Memory chưa đo.
  → ADR-070 đến ADR-076.
- **`tests/core/extraction/test_ocr_engine.py::TestCropRoi` lỗi thời**
  sau ADR-073 (công thức padding đổi từ theo-trang sang theo-bbox.height)
  - 4 test case hiện viết theo công thức cũ, cần viết lại. → ADR-073.

## Parsing / Template Matching

- **Giới hạn kiến trúc với giá trị đa dòng (multi-line value) và phụ
  thuộc `max_distance` tĩnh** — KHÔNG phải bug patch được ở tầng
  heuristic v1; là giới hạn nền tảng của phương pháp hình học tĩnh
  (chưa gặp thật trên dữ liệu test A4 hiện có, đánh giá rủi ro cho
  layout A5/bảng biểu phụ). Lời giải triệt để thuộc kế hoạch v2.0
  (LayoutLM). → ADR-059.
- **Gap-based merge có thể tràn field** (ADR-044) nếu 1 dòng có 2
  field liền kề mà nhãn field thứ 2 KHÔNG kết thúc bằng `:` (khác quy
  ước đã quan sát) — chưa gặp thật trên dữ liệu hiện có.
- **Section header vẫn có thể va chạm lý thuyết** (ADR-045) nếu 2
  section dùng `key_tokens` gần giống nhau trên 1 tài liệu khác.
- **`TemplateMatching.SECTION_TIE_MARGIN`** (= 10) và các hằng số
  `TemplateMatching.*` khác là giá trị placeholder ban đầu, cần tinh
  chỉnh khi có nhiều mẫu hóa đơn thật hơn.
- **Section header 5+ từ** có thể không bao giờ đạt fuzzy ratio tuyệt
  đối do `MAX_KEY_WORDS = 4` — cần rút gọn `key_tokens`. Đã ghi vào
  `TEMPLATE_AUTHORING_GUIDE.md`.
- **`resources/templates/sample_invoice_v1.json`** hiện là template
  duy nhất của dự án (v4) — chưa có template thứ 2 để verify tính tổng
  quát của thiết kế Section/Value Matching trên layout khác A4.

## Export (`ExcelWriter` / `ReportWriter`)

- **`ExcelWriter._is_total_row_present()`** dùng thuộc tính nội bộ của
  `openpyxl` (`totalsRowCount`/`totalsRowShown`), không thuộc API công
  khai ổn định lâu dài — an toàn tại version đã pin (`openpyxl==3.1.5`),
  **cần re-verify nếu nâng cấp version `openpyxl`** trong tương lai.
  → ADR-039.
- **`resources/excel_mapping.json` vẫn là mapping mẫu**
  (`tblInvoices`), chưa khớp workbook Excel thật của người dùng cuối —
  quyết định hoãn xử lý sang giai đoạn làm tài liệu chuyển giao ứng
  dụng (không thuộc phạm vi đóng v1 code).

## UI / Worker

Không có Known Issue nào đang mở ở nhóm này tính đến cuối v1 — các bug
UI đã phát hiện (Report chỉ mở được sau khi Start, Start không validate
input rỗng, Stop không hủy được PDF discovery) đều đã xử lý tại Session
2026-08-14 (ADR-064/065/066).

## Multi-Threading (v2.0, `Worker`/`PDFTaskRunnable`)

- **Cancellation flag (`Worker._cancel_requested`) đọc qua ranh giới
  luồng bằng kiểu `bool` thô, không qua `threading.Event`** — an toàn
  trong CPython nhờ GIL với cách dùng hiện tại (đọc 1 lần trước khi
  task bắt đầu, không polling/vòng lặp chờ), nhưng phụ thuộc đảm bảo
  ngầm của GIL thay vì API đồng bộ hóa tường minh. Cân nhắc đổi sang
  `threading.Event` nếu sau này cần task tự ngắt GIỮA CHỪNG khi đang
  chạy (không chỉ check trước khi bắt đầu), hoặc cần logic chờ đồng bộ
  phức tạp hơn giữa các luồng. **Ghi nhận, chưa áp dụng** theo quyết
  định của người dùng (Session 2026-08-15). → ADR-067.
- **High-DPI Scaling (ADR-069) chưa verify bằng hình ảnh thật trên
  Windows** ở scale 125%/150% — patch đã áp dụng (`main.py`), chỉ chờ
  xác nhận trực quan từ người dùng.

## Kiến trúc / Cross-cutting

- **Test coverage tự động mới có 2 module** (`Extractor._rotate_bbox()`,
  `ValueConverter`) — phần lớn pipeline vẫn dựa vào "chạy thật để
  verify" thủ công thay vì automated test. Chưa có test cho
  `PDFDetector`, `TemplateMatcher`, `ExcelWriter`, `ReportWriter`.
- **Cơ chế đối chiếu định kỳ tài liệu vs source** (Rule 15,
  `DEVELOPMENT_WORKFLOW.md`) mới được thêm — chưa từng được áp dụng
  thực tế lần nào kể từ khi thêm. Sự kiện gốc khiến rule này ra đời
  (mismatch ADR-027 tồn tại nhiều tuần không ai phát hiện, xem
  ADR-056) là bài học nền cho rule, không phải bằng chứng rule đã hoạt
  động.

------------------------------------------------------------------------

# 15. Việc Tiếp Theo (Next Tasks)

Pipeline end-to-end đã hoàn thiện, verify qua chạy thật. **Đóng v1: đã
HOÀN TẤT CẢ 3 PHẦN** (Part 1/3 — Session 2026-08-12; Part 2/3 —
Session 2026-08-13; Part 3/3 — Session 2026-08-14).

## Giai đoạn tiếp theo (chưa bắt đầu)

0. **Tiếp tục `OCR_ACCURACY_SPECIFICATION.md`**: hoàn tất đánh giá độc
   lập giai đoạn 2 và chốt `ROI_UPSCALE_FACTOR`/các tham số ROI; viết lại
   `TestCropRoi`. Sau đó mới thử riêng giai đoạn 1 (Median Blur, Sharpen)
   và cuối cùng đo Performance/Memory.
1. **Tài liệu chuyển giao ứng dụng:**
   - `resources/excel_mapping.json` khớp workbook Excel thật của
     người dùng cuối.
   - Tài liệu hướng dẫn cài đặt OCR cho end-user (Tesseract binary hệ
     thống, `vie.traineddata`).
2. **v2.0 planning** (chỉ mới ghi nhận định hướng, chưa thiết kế chi
   tiết):
   - LayoutLM-based Parser engine, thay thế/bổ sung song song
     `TemplateMatcher` cho giá trị đa dòng và layout đa dạng. → ADR-059.
   - Dual-source extraction cho trang hỗn hợp (text + ảnh).
   - DPI thích ứng theo khổ giấy/cỡ font thay vì `Image.DPI` cố định.
     → ADR-053.
   - Tăng cường hiệu quả OCR (Binarization/Denoising/Border Removal —
     cần bằng chứng thực nghiệm mới trước khi quyết định, đã cân nhắc
     và hoãn tại Session 2026-08-13).
   - Cho phép người dùng tùy chỉnh `NumberRepair.DECIMAL_TAIL_MAX_LENGTH`
     theo loại hóa đơn.

------------------------------------------------------------------------

# 16. Vấn Đề & Giải Pháp Trước Đây (tóm tắt)

| Vấn đề | Giải pháp |
|--------|-----------|
| Ghi Excel sau mỗi PDF | Lưu `PDFResult` trong bộ nhớ, ghi 1 lần |
| UI bị treo (freeze) | `Worker` + `QThread` |
| Dùng bộ nhớ quá lớn | Giải phóng từng PDF ngay sau xử lý, chỉ giữ `PDFResult` |
| Thread cập nhật UI trực tiếp | Chỉ dùng Qt Signal |

------------------------------------------------------------------------

# 17. KHÔNG ĐƯỢC THAY ĐỔI (Frozen)

Các quy tắc kiến trúc sau đã được đóng băng. KHÔNG thay đổi trừ khi
thật sự cần thiết (và phải thảo luận trước — Rule 1/11).

- `process()` chỉ là orchestrator.
- Business logic thuộc về `_process_pdf()`.
- UI không bao giờ truy cập business logic trực tiếp.
- `Worker` không bao giờ truy cập UI trực tiếp.
- Excel chỉ được ghi đúng 1 lần.
- PDF được xử lý từng file một.
- Kết quả giữ trong bộ nhớ.
- Giao tiếp chỉ qua Qt Signal.
- `ProcessingTable` dùng `ProcessingTableModel`.
- Quy trình phát triển tăng dần.

------------------------------------------------------------------------

# 18. Cải Tiến Tương Lai (Future Improvements)

- Config file cho người dùng tùy chỉnh.
- Drag & Drop.
- Đa ngôn ngữ UI.
- Dark Mode (`ui/theme.py` đã có sẵn, hiện còn trống — không phải dead
  code, có định hướng rõ).
- Mở rộng test coverage (hiện chỉ 2/nhiều module).
- Plugin parser.
- Batch report.
- Tái cấu trúc thư mục source theo module chức năng — **đã hoàn tất**
  (Session 2026-08-13, xem ADR-060). Mục này giữ lại như ghi chú lịch
  sử, không còn là việc cần làm.
- **DPI thích ứng theo khổ giấy/cỡ font hóa đơn** (v2.0) — 400 DPI cho
  font >10pt/A4 chuẩn, 600 DPI cho font <8pt/A5 hoặc A4 có bảng chỉ số
  phụ — cho phép người dùng chọn khổ giấy ở UI. → ADR-053.
- **Tăng cường hiệu quả OCR** (v2.0, ưu tiên quan trọng) — Binarization/
  Denoising/Border Removal đã thảo luận và hoãn ở v1 (xem §14 nhóm
  Extraction/OCR và SESSION_SUMMARIES.md, Session 2026-08-13). Cần
  đánh giá lại có/không có bằng chứng thực nghiệm mới trước khi quyết
  định triển khai.
- **LayoutLM-based Parser** (v2.0) — xem §15 và ADR-059.
- **Dual-source extraction** cho trang hỗn hợp (v2.0) — xem §14 nhóm
  Extraction/OCR.

------------------------------------------------------------------------
