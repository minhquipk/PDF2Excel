# SESSION_SUMMARIES.md

# Session Summaries

This document records the outcome of each development session.

## Purpose

- Quickly resume development after a break.
- Record implementation decisions.
- Preserve technical context.
- Complement (not replace) CHANGELOG.md.

---

# Session 2026-07-22

## Objective

Build and validate the application framework before implementing real PDF processing.

## Completed

### Foundation

- Project architecture initialized.
- constants.py completed.
- enums.py completed.
- models.py completed.

### UI

- MainWindow completed.
- BaseWidget completed.
- Reusable widgets completed.
- Input/Output selector completed.
- Progress widget completed.
- Processing table completed.
- Report / Exit buttons completed.

### Worker

- Worker framework completed.
- QThread integration completed.
- Qt Signals connected.
- Mock processing pipeline implemented.

### Processing Table

- ProcessingTableModel implemented.
- Model connected to table.
- clear() added before each Start.

## Architecture Decisions

- process() is orchestration only.
- _process_pdf() contains business logic.
- Worker never updates UI directly.
- Communication uses Qt Signals only.
- One PDF processed at a time.
- Store PDFResult in memory.
- Write Excel only once.
- ProcessingTable uses ProcessingTableModel (MVC).

## Issues Encountered

### ProcessingTable

Problem:

- setModel() unavailable.

Resolution:

- Change ProcessingTable to inherit from QTableView.

### Column Enum

Problem:

- Column.COUNT duplicated column count maintenance.

Resolution:

- Remove COUNT.
- Use len(Column).

## Validation

Verified:

- UI launches correctly.
- Worker executes in background thread.
- Progress updates correctly.
- Mock results displayed.
- Table reset before each run.
- Start/Stop workflow works.

## Next Session

Priority:

1. pdf_reader.py
2. Digital PDF detection
3. Read text
4. Regex parser integration

## Notes

The project is intentionally running in Mock Mode.

UI, Worker, QThread and MVC architecture are validated.

The next milestone is replacing mock processing with the real PDF pipeline.

---

# Session Template

## Session YYYY-MM-DD

### Objective

### Completed

### Architecture Decisions

### Issues Encountered

### Validation

### Next Session

### Notes

---

# Session 2026-07-23

## Objective
Begin implementation of the real PDF processing pipeline.

## Completed

### Domain

- models.py frozen.
- UTC timestamp initialization standardized.
- PDFDocument.text retained.

## Architecture

- Reader boundary finalized.
- Analyzer responsibility finalized.
- Knowledge Cache architecture defined.

## Development Process

- Source code becomes the implementation reference.
- New implementation workflow established.
- Design Freeze before coding adopted.

## PDF Reader

- Initial implementation completed.
- API review performed.
- Helper structure refined.
- Naming convention reviewed.

## Architecture Decisions

- Reader only reads.
- Parser owns invoice extraction. 
- Analyzer owns knowledge accumulation.
- Domain drives implementation.

## Issues Encountered

## PyMuPDF API

### Problem:

- IDE reference/type warnings.

### Resolution:

- Validate against installed library version before implementation.

## Development Process

### Problem:

- Excessive architectural discussion during implementation.

### Resolution:

- Freeze architecture before coding.
- Prioritize implementation and review.

## Validation

### Verified:

- models.py matches Reader design.
- One-PDF-at-a-time strategy remains unchanged.
- Complete document text retained for future parsing.

## Next Session

### Priority:

1. Freeze pdf_reader.py
2. Integrate processor.py
3. Replace Mock pipeline
4. Begin Analyzer

---

# Session 2026-07-29

## Objective

Implement the pdf_detector reasoning engine per
`PDF_Detector_Technical_Design.docx`, and integrate the real
PDFReader → PDFDetector pipeline into Worker, replacing Mock
processing for the detection stage.

## Completed

### Domain

- `core/enums.py`: added `ConfidenceLevel`, `RuleCategory`.
- `core/models.py`: added `Evidence`, `Confidence`,
  `AnalysisContext`, `KnowledgeRecord`, `DocumentAnalysis`,
  `AnalysisMode` — implemented as immutable (frozen) dataclasses
  where the TDS requires immutability (AnalysisContext,
  DocumentAnalysis, Evidence, Confidence).

### PDF Reader

- `core/pdf_reader.py` fully implemented: reads metadata and every
  page via PyMuPDF (`fitz`), builds `PDFPage` / `PageStatistics`,
  returns an immutable `PDFDocument`.
- No OCR, parsing, or classification logic present (ADR-016
  respected).

### PDF Detector

- `core/pdf_detector.py` fully implemented as a deterministic
  reasoning engine, following the TDS stage sequence:
  1. Build Context (`_build_context`) — raw + derived metrics.
  2. Heuristic Evaluation — 5 rules implemented: `text_coverage`,
     `image_coverage`, `mixed_content`, `content_coverage`,
     `page_layout`.
  3. Knowledge Lookup + Confidence Composition
     (`_compose_confidence`) — evidence / consistency / coverage
     sources, optional knowledge adjustment.
  4. Final Decision — produces immutable `DocumentAnalysis`.
- Deterministic fingerprinting via SHA-256 over rounded observed
  metrics (`_fingerprint`).

### Worker Integration

- `ui/worker.py`: `Worker._process_pdf()` now calls
  `PDFReader.read()` and `PDFDetector.analyze()` directly.
- `PDFResult.pdf_type` / `.status` / `.note` derived from
  `DocumentAnalysis`.
- Exceptions during read/analyze caught per-file; recorded as
  `ProcessStatus.FAILED` without stopping the batch.
- Mock processing mode has been replaced for the detection stage.
  (Extraction, parsing, OCR, Excel writing remain Mock/pending —
  not yet wired in.)

## Architecture Decisions

- Detector receives only the immutable `PDFDocument`; never accesses
  the raw PDF or file system directly.
- Confidence is decision-centric and evidence-driven (TDS Ch. 8);
  no fixed/arbitrary confidence values are assigned.
- `AnalysisMode.UNKNOWN` maps to `ProcessStatus.WARNING`, not
  `FAILED` — inconclusive detection is not treated as a processing
  error.
- KnowledgeRecord is treated as read-only during a single analysis
  (TDS DC-004); mismatched fingerprint triggers a warning rather
  than silent rejection.

## Issues Encountered

### Rule Category Coverage

Problem:

- TDS §7.2 defines 7 Rule Categories (Document, Text, Image,
  Graphics, Layout, Consistency, Quality). Only 5 are implemented
  (Text, Image, Consistency, Quality, Layout).

Resolution:

- Not yet resolved. Logged as pending work (see
  PROJECT_CONTEXT.md §14, CHANGELOG.md Unreleased/Next).

### processor.py vs Worker.process()

Problem:

- `core/processor.py` contains only placeholder calls
  (`start/stop/pause/resume`), while the actual ADR-004 orchestrator
  responsibility is fulfilled by `Worker.process()`.

Resolution:

- Not yet resolved. Needs discussion on whether `processor.py` is
  a planned extraction target or dead code.

### Possible Import Path Issues

Problem:

- `core/models.py` imports via `from enums import ...` and
  `ui/widgets.py` imports via `from base_widget import ...`,
  both missing the `core.` / `ui.` package prefix used elsewhere.

Resolution:

- Not yet resolved. Needs verification against the actual run
  configuration (may indicate a working relative-import setup, or
  a latent bug).

## Validation

Verified (via source review, not automated tests):

- `PDFDetector.analyze()` end-to-end flow matches TDS stage
  ordering (Build Context → Heuristic Evaluation → Knowledge Lookup
  → Confidence Adjustment → Final Decision).
- `DocumentAnalysis`, `AnalysisContext`, `Evidence`, `Confidence`
  are immutable (frozen dataclasses with recursive collection
  freezing via `_freeze_value`).
- `Worker._process_pdf()` correctly delegates to `PDFReader` and
  `PDFDetector` and maps results to `PDFResult`.

No automated test suite exists yet (see PROJECT_CONTEXT.md §18,
Future Improvements: "Unit tests").

## Next Session

Priority:

1. `parser.py` — regex-based invoice parsing from `PDFDocument.text`.
2. `extractor.py` — feed structured content to parser based on
   `DocumentAnalysis.mode`.
3. Resolve `processor.py` role vs `Worker.process()`.
4. Decide on Document Rules / Graphics Rules for pdf_detector
   (implement now vs. defer intentionally).

---

# Session 2026-07-31

## Objective

Design and implement the `Extractor` module: convert `PDFDocument` +
`DocumentAnalysis` into word-level, geometry-normalized extraction
results ready for a future Parser. Integrate `Extractor` into
`Worker`. Fix two pre-existing static type-checker warnings found
during source review.

## Completed

### Type Hint Fixes (pre-Extractor)

- `core/pdf_reader.py`: `_read_pages()` return type corrected from
  `list[PDFPage]` to `tuple[PDFPage, ...]`.
- `core/pdf_detector.py`: `_unique_strings()` parameter type
  corrected from `object` to `Iterable[str]`
  (`from collections.abc import Iterable` added).
- Both were static-typing mismatches only; `PDFDocument.__post_init__`
  already enforced immutability at runtime in the first case, so
  neither was a functional bug.

### Domain Model

- `core/models.py`:
  - Renamed pre-existing `ExtractionResult` (session-wide results) to
    `SessionResult`, freeing the name for the Extractor's per-document
    output. No other source file referenced the old name at the time
    of this session.
  - Added `WordToken`, `PageImage`.
  - Extended `PDFPage` with `words` (raw, unnormalized) and
    `page_image` (`PageImage | None`), both additive/backward
    compatible.
  - Added the new `ExtractionResult` (`source_mode`, `words_by_page`,
    `page_images`, `warnings`).

### PDF Reader

- `core/constants.py`: added `Image` class (`DPI = 300`,
  `COLORSPACE = "gray"`).
- `core/pdf_reader.py`: `_read_page()` now reads `page.get_text("words")`
  for every page (no per-type branching — Reader does not classify),
  and renders a raw grayscale `PageImage` per page via
  `page.get_pixmap(dpi=Image.DPI, colorspace=fitz.csGRAY)`.

### Extractor (new module)

- `core/extractor.py`: `Extractor.extract(document, analysis)`,
  dispatching per `AnalysisMode`; `_rotate_bbox()`; `_normalize_bbox()`.
- `core/ocr_engine.py`: `OCREngine.recognize()`, Mock implementation
  per ADR-013, always returns `()`.

### Worker Integration

- `ui/worker.py`: `Extractor` constructed in `__init__`; `_process_pdf()`
  calls `extractor.extract()` conditionally (skipped for `UNKNOWN`),
  in its own `try/except`; `_format_analysis_note()` renamed to
  `_format_note()`, now considers both `DocumentAnalysis.warnings` and
  `ExtractionResult.warnings`.

## Architecture Decisions

- **Reader vs. Extractor responsibility (reaffirmed):** `PDFPage.words`
  stays as raw PyMuPDF tuples; only `Extractor` produces `WordToken`.
- **`page_image` rendering strategy:** eager (every page, every
  document), not lazy-on-demand. Accepted memory cost given
  per-document release (ADR-007) and expected page counts.
- **Raw pixmap storage:** uncompressed grayscale samples, not PNG —
  optimizes for OCR readiness over storage size.
- **`WordToken.normalized_bbox` scale:** `[0.0, 1.0]`, deliberately
  model-agnostic. A future LayoutLMv3 Parser (v2.0, requiring
  `[0, 1000]`) converts at the point of consumption, not in the
  domain model.
- **Coordinate Transformer scope:** rotation reconciliation
  (`_rotate_bbox`) applies **only** to the Digital path.
  `get_text("words")` returns coordinates relative to the unrotated
  page, while `page.statistics.width/height` (from `page.rect`) and
  `page.get_pixmap()` both reflect the rotated/visual page — these
  two frames must be reconciled for Digital extraction.
- **OCR path needs no rotation transform:** PyMuPDF bakes page
  rotation into the pixmap at render time by design (confirmed via
  PyMuPDF's official documentation and maintainer statement — pixmap
  rendering follows `page.rect`, "because that is what a PDF viewer
  would show, too"). Applying `_rotate_bbox()` to OCR-derived bboxes
  would double-rotate them.
- **Rotation matrix computed manually, not via `fitz.Page`:**
  `Extractor` never holds a live `fitz.Page` reference (the PDF file
  is closed once `PDFReader.read()` returns, per ADR-007). Rotation
  reconciliation is implemented as explicit geometry (4 fixed cases:
  0/90/180/270°) derived from `page.statistics.rotation` and
  `page.statistics.width/height`, with no PyMuPDF dependency inside
  `extractor.py` (Domain-Oriented Design, DP-009).
- **`UNKNOWN` handling — decision boundary moved to `Worker`:**
  `Extractor.extract()` raises `ValueError` if called with
  `AnalysisMode.UNKNOWN` (a programming-contract violation, not a
  business case). `Worker._process_pdf()` is responsible for not
  calling `Extractor` at all when `analysis.mode is UNKNOWN` — this
  keeps the "a decision is made once, downstream stages never
  re-evaluate it" principle (TDS §3.1) intact: `UNKNOWN` is the
  *absence* of a decision, not a special extraction case for
  `Extractor` to handle.
- **`PDFResult.note` — no structural change:** kept as a single
  `str`. Displays only the "highest-level" warning
  (`ExtractionResult.warnings` first, else `DocumentAnalysis.warnings`)
  — sufficient for the UI's intended audience. Full traceability for
  developers is achieved through the pipeline's determinism (TDS G1):
  re-running the same input reproduces the same `DocumentAnalysis` /
  `ExtractionResult`, so nothing needs to be persisted beyond
  `PDFResult` for post-hoc investigation.

## Issues Encountered

### HYBRID Pages with Mixed Content (deferred to v2.0)

Problem:

- A page with both a text layer and materially relevant image content
  (e.g. a stamp, signature, or scanned table embedded in an otherwise
  digital page) is currently routed to a single source
  (`page.has_text` → Digital, discarding image content on that page).

Three options were considered:

1. Treat as Digital-only (current behavior) — cheapest, but silently
   drops image content on mixed pages.
2. Always run both sources and merge — most complete, but introduces
   an unsolved sub-problem: OCR re-reads the entire page image
   (including the text already covered by the text layer), producing
   duplicate/overlapping `WordToken`s with no deduplication mechanism
   designed yet.
3. Treat as image-only, OCR the whole page — avoids duplication, but
   discards already-accurate text-layer data in favor of
   lower-fidelity OCR output, for no benefit.

Resolution:

- **Deferred to v2.0.** Current code keeps option 1 (Digital-only
  when `page.has_text`) unchanged. Flagged as a known limitation, not
  a defect, since it was a deliberate, informed decision. Revisit
  requires: real invoice sample data (to know how often this pattern
  occurs and whether the dropped image content is business-relevant)
  and, if option 2 is chosen, a bbox-overlap deduplication design.

### Naming Collision: `ExtractionResult`

Problem:

- The name `ExtractionResult` was already used by an existing class
  (session-wide results: invoices, pdf_results, errors), unrelated to
  the new per-document Extractor output being designed.

Resolution:

- Renamed the pre-existing class to `SessionResult`. Verified (within
  the source reviewed in this session) that no other file referenced
  `ExtractionResult` under its old meaning, making the rename low-risk.

### Confirming PyMuPDF Rotation Behavior

Problem:

- Needed to determine whether `get_text("words")` and `get_pixmap()`
  share the same coordinate reference frame with respect to page
  rotation, before designing `_normalize_bbox()`/`_rotate_bbox()`.
  Uncertain claims existed in secondary sources (blog posts).

Resolution:

- Verified against PyMuPDF's official documentation and a maintainer
  statement in an official GitHub discussion. Confirmed: origin
  (top-left, y-down) is consistent between both APIs (no flip needed);
  but `get_text()` returns **unrotated** coordinates while
  `page.rect`/`get_pixmap()` reflect the **rotated** page — a real,
  confirmed discrepancy requiring `_rotate_bbox()` for the Digital
  path only.

## Validation

Verified (via design review and cross-referencing with existing
Detector evidence, not automated tests):

- `Extractor`'s mode dispatch is consistent with `PDFDetector`'s
  existing evidence signals (e.g. `mixed_content` rule anticipating
  `HYBRID` pages — confirming, not contradicting, the deferred v2.0
  limitation).
- `_rotate_bbox()` covers all four PyMuPDF-guaranteed rotation values
  (0/90/180/270°) as explicit cases.
- `ExtractionResult`, `WordToken`, `PageImage` follow the same
  immutability pattern (frozen dataclasses, recursive collection
  freezing) established for `AnalysisContext`/`DocumentAnalysis`/
  `Evidence`/`Confidence` in the prior session.

No automated test suite exists yet. `_rotate_bbox()` was flagged as a
good candidate for dedicated unit tests (known rotated-page fixtures
with a word at a known position) before further integration, but this
was not done in this session.

## Next Session

Priority:

1. `parser.py` — regex-based invoice parsing, consuming
   `ExtractionResult.words_by_page`.
2. Consider unit tests for `Extractor._rotate_bbox()` (four rotation
   cases) before building further logic on top of it.
3. Replace `OCREngine` Mock with a real backend.
4. Resolve `processor.py` role vs `Worker.process()` (still open from
   Session 2026-07-29).
5. Resolve possible import path issues (still open from Session
   2026-07-29).

## Notes

Per user request, this session is being fully closed out (source
review + log synchronization) before moving to the next module,
rather than continuing directly into Parser implementation. Same
reconstruction caveat as the previous session applies: this entry
documents what was decided and implemented, based on the discussion
and the user's explicit confirmations, not a live line-by-line
commit history.

---

# Session 2026-08-01 / 2026-08-02

## Objective

Thiết kế và triển khai đầy đủ module `Parser`: chuyển `ExtractionResult`
(WordToken thô từ Extractor) thành `InvoiceInfo`, dùng kỹ thuật Template
Matching (Key Matching + Bounding Box Windowing + Value Matching), với
Template Definition lưu ngoài dưới dạng JSON để dễ cập nhật và chuẩn bị
sẵn sàng cho một engine LayoutLMv3 ở v2.0.

## Completed

### Domain Model

- `core/enums.py`: thêm `ValueType`, `SpatialDirection`.
- `core/models.py`: `InvoiceInfo` chuyển hầu hết field sang `Optional`
  (trừ `source_file`); thêm `SpatialRelation`, `FieldDefinition` (tự
  validate `field_name` khớp `InvoiceInfo`), `TemplateDefinition`,
  `TemplateSelection` (matched_keys giữ kèm `page_index`).
- `core/constants.py`: thêm `Logging`, `TemplateMatching` (5 hằng số
  ngưỡng, đều là placeholder cần tinh chỉnh sau).

### Modules mới

- `utils/logger.py` — logger dùng chung, console handler, cấu hình 1
  lần (không nhân đôi handler khi gọi `get_logger()` nhiều lần).
- `core/value_converter.py` — convert TEXT/DECIMAL/DATE, stateless,
  không raise.
- `core/template_loader.py` — đọc/validate JSON template, fail-soft
  per file (log warning, bỏ qua, không dừng batch).
- `core/template_matcher.py` — lõi thuật toán: Line/Phrase Clustering,
  fuzzy Key Matching (rapidfuzz + chuẩn hoá dấu tiếng Việt), Template
  Scoring/Decision (tái dùng pattern Evidence→Score→Decision của
  `PDFDetector`), Windowing, Value Matching (tie-break theo khoảng
  cách gần nhất).
- `core/parser.py` — orchestrator mỏng, `parse()` trả
  `InvoiceInfo | None`.
- `config.py` — thêm `TEMPLATES_DIR`.
- `resources/templates/sample_invoice_v1.json` — template mẫu để test,
  cố ý còn 2 lỗi đã biết (key_tokens ngắn, value_pattern lỏng), chưa
  sửa — chờ dữ liệu PDF thật.

### Extractor

- `core/extractor.py`: mở rộng trách nhiệm sang chuẩn hoá whitespace
  của text token (`_normalize_text()`), ngoài hình học đã có từ trước.

### Worker Integration

- `ui/worker.py`: `Worker.__init__` khởi tạo `TemplateLoader` +
  `TemplateMatcher` + `Parser`; `_process_pdf()` gọi `Parser.parse()`
  trong try/except riêng, gán `result.invoice`.

## Architecture Decisions

Xem ARCHITECTURE_DECISIONS.md ADR-029 đến ADR-036, tóm tắt:

- Parser = orchestrator mỏng + TemplateMatcher engine tách biệt (chuẩn
  bị cho LayoutLMv3 v2.0).
- Template Selection dùng chấm điểm theo trọng số Evidence (tái dùng
  pattern của PDFDetector), có tie margin, tính trên toàn văn bản.
- Template Definition lưu JSON ngoài, validate + convert sang frozen
  dataclass; file lỗi bị bỏ qua, không dừng batch.
- InvoiceInfo hầu hết field Optional; convert/tìm value thất bại ->
  field = None, không raise, không phản ánh vào PDFResult.status.
- Parser.parse() trả None khi không xác định được template (đối xứng
  ADR-027) -> cũng KHÔNG phản ánh vào PDFResult.status/.note (quyết
  định của người dùng: nguyên nhân "không khớp template" không thể
  khẳng định chắc chắn là lỗi hệ thống hay dữ liệu/nhập sai file — xử
  lý qua Report, dựa vào tần suất lặp lại để phân biệt).
- TemplateSelection.matched_keys giữ kèm page_index (không sửa
  WordToken - phạm vi ảnh hưởng rộng hơn).
- Chuẩn hoá dấu tiếng Việt bắt buộc trước fuzzy match (phát hiện thực
  nghiệm: ratio ~70 nếu không chuẩn hoá, dưới mọi ngưỡng hợp lý).
- Extractor mở rộng trách nhiệm sang chuẩn hoá text whitespace.

## Issues Encountered

### Diacritics tiếng Việt làm sập fuzzy matching

Phát hiện qua kiểm thử thực nghiệm (không phải suy đoán trước): so
sánh "Mã số thuế" (có dấu) với "Ma so thue" (không dấu) qua
`rapidfuzz.fuzz.ratio()` chỉ cho ratio ~70, dưới mọi ngưỡng
`fuzzy_threshold` hợp lý (85-90). Nghiêm trọng hơn: cùng vấn đề xảy ra
khi OCR làm rớt dấu trên bản scan chất lượng thấp — một tình huống
thực tế, không phải edge case hiếm.

Giải quyết: thêm `_strip_diacritics()` (NFKD decompose + xử lý riêng
`Đ/đ`, vì ký tự này không tự decompose qua NFKD) áp dụng cho cả 2 phía
trước khi so khớp.

### Key Token ngắn gây match nhầm dòng khác trong tài liệu

Phát hiện qua kiểm thử: template mẫu có `key_tokens: ["so hoa don",
"so"]` cho field `invoice_number`; biến thể `"so"` (1 từ) khớp 100%
với từ "số" đứng độc lập trong cụm "Mã số thuế" ở dòng khác, khiến
Windowing dựng sai vị trí, kết quả trích xuất sai field. Xác nhận đây
KHÔNG phải lỗi thuật toán (rapidfuzz trả kết quả đúng bản chất) mà là
vấn đề thiết kế template — ghi thành quy tắc vận hành (xem CHANGELOG
Known Limitations), chưa có tài liệu chính thức.

### value_pattern lỏng khiến dấu câu bị chọn nhầm làm Value

Phát hiện qua kiểm thử: `value_pattern: ".+"` cho phép dấu `":"` đứng
ngay sau Key (thường gần Key hơn giá trị thật) được chọn do tie-break
theo khoảng cách. Sửa bằng cách yêu cầu pattern có ít nhất 1 ký tự
không phải khoảng trắng/dấu câu cơ bản — ghi thành quy tắc vận hành.

### PySide6/PyMuPDF không có sẵn trong môi trường kiểm thử

Phải cài đặt (`pip install PySide6 PyMuPDF rapidfuzz --break-system-
packages`) trong workspace kiểm thử; các dependency này (đặc biệt
`rapidfuzz`, mới thêm) cần được người dùng tự bổ sung vào dependency
file thật của project (project hiện chưa có requirements.txt/
pyproject.toml — chưa xác nhận).

## Validation

Verified bằng kiểm thử trực tiếp (bash + Python), không phải review
tĩnh:

- `utils/logger.py`: format đúng, level lọc đúng, không nhân đôi
  handler khi gọi nhiều lần từ nhiều module.
- `core/enums.py`: enum mới hoạt động đúng, enum cũ không bị ảnh hưởng
  (regression).
- `core/models.py`: `InvoiceInfo` Optional đúng, `FieldDefinition` tự
  validate `field_name` (raise `ValueError` rõ ràng khi sai), toàn bộ
  dataclass frozen/immutable đúng, regression cho dataclass cũ pass.
- `core/value_converter.py`: TEXT/DECIMAL (default VN + custom format)/
  DATE đều đúng; stress test với dữ liệu nhiễu OCR xác nhận không bao
  giờ raise Exception.
- `core/template_loader.py`: load đúng file hợp lệ, bỏ qua đúng 5 loại
  lỗi khác nhau (cú pháp JSON, thiếu key, key_tokens rỗng, sai enum,
  field_name sai), xử lý đúng thư mục không tồn tại/rỗng.
- `core/template_matcher.py`: verify end-to-end bằng dữ liệu WordToken
  mô phỏng 1 trang hóa đơn thật (có dấu tiếng Việt đầy đủ) — Key
  Matching, Score/Decision, Windowing (cả hướng RIGHT và BELOW), Value
  Matching đều cho kết quả đúng sau khi sửa 2 lỗi thiết kế template
  phát hiện được.
- `core/parser.py`: happy path đúng kiểu dữ liệu đích; trả None đúng
  khi không xác định được template; 1 field lỗi không ảnh hưởng field
  khác, không raise.
- `ui/worker.py`: tích hợp Parser đầy đủ — happy path, trường hợp
  Parser trả None (status/note không đổi, đúng quyết định), và trường
  hợp Parser raise Exception thật (status FAILED, nhất quán các stage
  khác) đều được verify qua monkeypatch 3 stage đầu (Reader/Detector/
  Extractor) và dùng Parser thật.
- `core/extractor.py` (text normalize): verify riêng + regression toàn
  bộ pipeline Worker+Parser sau khi thêm thay đổi — không phá vỡ gì.

## Next Session

Priority:

1. Viết tài liệu "Template Authoring Guide" (quy tắc key_tokens/
   value_pattern an toàn, đúc kết từ Issues Encountered phiên này).
2. Sửa lại `resources/templates/sample_invoice_v1.json` và bổ sung
   template thật khi có dữ liệu PDF hóa đơn thật; tinh chỉnh
   `TemplateMatching.*` trong `core/constants.py`.
3. Thiết kế ghép cụm nhiều từ cho Value Matching (hiện chỉ 1 WordToken
   đơn lẻ — company_name/address bị cắt cụt).
4. `excel_writer.py` + Report export (bao gồm hiển thị field
   `InvoiceInfo = None` và trường hợp Parser không xác định được
   template — theo ADR-033).
5. Bổ sung `rapidfuzz` (và các dependency khác) vào dependency file
   chính thức của project.
6. Thảo luận riêng: tái cấu trúc thư mục source theo module chức năng
   (core/parsing/template/, core/parsing/layoutlm/...) sau khi v1 hoàn
   thiện — đã đề xuất sơ bộ, chưa quyết định (xem PROJECT_CONTEXT.md
   §18).
7. Resolve `processor.py` role vs `Worker.process()` (vẫn mở từ các
   session trước).

## Notes

Toàn bộ module Parser (8 bước: logger → enums → models → value_converter
→ template_loader → template_matcher → parser → worker integration +
extractor text normalize) được implement và verify tuần tự theo
DEVELOPMENT_WORKFLOW.md (1 file/1 bước, compile+run+verify trước khi
sang bước kế). 3 lỗi thiết kế thực chất (diacritics, key_tokens ngắn,
value_pattern lỏng) được phát hiện qua kiểm thử thực nghiệm với dữ liệu
mô phỏng, không phải qua review tĩnh — xác nhận giá trị của việc chạy
thử thực tế thay vì chỉ đọc code.

---

# Session 2026-08-03

## Objective

Thiết kế và triển khai đầy đủ module `excel_writer.py` (ghi
`list[InvoiceInfo]` vào Excel Table có sẵn) và `report_writer.py` (xuất
báo cáo cho tính năng Report trên UI), hoàn thiện pipeline end-to-end
lần đầu tiên. Sau đó kiểm thử toàn bộ 8 bước triển khai trên source
thật đã push lên GitHub, và giải quyết vấn đề dependency file còn thiếu
(`requirements.txt`).

## Completed

### Thảo luận thiết kế (trước khi implement — Rule 11/12)

Người dùng cung cấp `Technical_Design_excel_writer.docx` làm điểm khởi
đầu thảo luận. Qua nhiều vòng trao đổi, thiết kế được tinh chỉnh dần:

1.  **Bác bỏ `ReportService`** (đề xuất ban đầu trong tài liệu, gộp
    Excel writing + report.txt generation vào 1 lệnh gọi) — dựa trên
    bằng chứng cụ thể trong source: `Worker.__init__` đã có sẵn 2
    thuộc tính placeholder tách biệt (`self._excel_writer = None`,
    `self._report_writer = None`) từ các session trước, cho thấy
    thiết kế gốc đã dự tính 2 module riêng biệt.
2.  **Làm rõ vai trò nút Report**: không kích hoạt sinh report, chỉ mở
    file đã được sinh tự động ở cuối `Worker.process()` (đối xứng ADR-008).
3.  **2 loại thông tin report tách biệt hoàn toàn** (theo yêu cầu người
    dùng, qua nhiều lần điều chỉnh): `list[PDFResult]` → log kỹ thuật
    (dev/admin, qua `utils/logger.py` + `FileHandler` mới); `ExcelWriteResult`
    → `report.txt` (end-user, ghi đè mỗi lần chạy). Ban đầu có nhầm lẫn
    gộp 2 luồng vào cùng nội dung report.txt — đã được người dùng chỉnh
    lại rõ ràng qua 2 lượt trao đổi.
4.  Đổi tên exception theo namespace dự án: tránh dùng lại từ "Template"
    (đã có nghĩa cố định là mẫu hóa đơn) cho khái niệm workbook Excel —
    `WorkbookNotFoundError`, `ExcelTableNotFoundError` thay vì
    `TemplateNotFoundError`/`TableNotFoundError` trong tài liệu gốc.

### Triển khai (8 bước, mỗi bước review source → giải thích → implement
→ compile/run/verify → xác nhận, theo đúng DEVELOPMENT_WORKFLOW.md)

1.  `core/models.py`: thêm `ExcelMapping`, `InvoiceWarning`,
    `ExcelWriteResult` (frozen dataclass, đối xứng pattern
    `TemplateDefinition`/`Evidence`/`Confidence` đã có).
2.  `resources/excel_mapping.json` + `config.py::EXCEL_MAPPING_PATH`.
3.  `core/excel_mapper.py`: `Mapper` — fail-fast (khác `TemplateLoader`
    fail-soft), raise `MappingError`.
4.  `core/excel_writer.py`: `ExcelWriter.write()` (openpyxl), 3
    exception class, cột mapping không khớp header thật → soft-fail
    vào `ExcelWriteResult.errors`.
5.  `core/constants.py` + `config.py::LOG_DIR` + `utils/logger.py`:
    thêm `FileHandler` (UTF-8, `logs/app.log`) cạnh `StreamHandler`
    có sẵn.
6.  `core/report_writer.py`: `ReportWriter.write()` — 2 kênh output
    tách biệt hoàn toàn (logger vs report.txt).
7.  `ui/worker.py`: khởi tạo `ExcelWriter()`/`ReportWriter()` thật,
    thêm `report_path` property, implement `_write_excel()` (load
    mapping lazy — không load ở `__init__` để tránh crash app khi
    mapping.json lỗi).
8.  `ui/main_window.py`: kết nối `error` Signal (tồn tại từ đầu dự án
    nhưng chưa từng được `connect`), implement lại `_report()` (mở
    file thay vì message "pending").

### Giải quyết dependency file còn thiếu

`requirements.txt` được tạo, pin đúng 4 version đã cài và kiểm thử
thành công trong phiên (`PySide6==6.11.1`, `PyMuPDF==1.28.0`,
`rapidfuzz==3.14.5`, `openpyxl==3.1.5`) — đóng Known Issue tồn đọng từ
Session 2026-08-01/02.

## Architecture Decisions

Xem `ARCHITECTURE_DECISIONS.md` ADR-037 đến ADR-041. Tóm tắt:

-   ADR-037: `ExcelWriter`/`ReportWriter` tách biệt, không phụ thuộc
    lẫn nhau, không có `ReportService` trung gian.
-   ADR-038: Mapping load fail-fast, lazy (không ở `__init__`).
-   ADR-039: Cột mapping không khớp workbook thật → soft-fail per
    column, không raise toàn cục.
-   ADR-040: `ReportWriter` 2 kênh output tách biệt hoàn toàn
    (logger tích lũy vs report.txt ghi đè).
-   ADR-041: Report button chỉ mở file đã sinh sẵn, không tự sinh.

## Issues Encountered

### Không có repo mount trong môi trường làm việc

Vấn đề: Toàn bộ 8 bước triển khai ban đầu chỉ tồn tại dưới dạng code
đề xuất trong chat — không có filesystem thật nào được ghi vào. Người
dùng tự áp dụng code vào repo GitHub cá nhân.

Giải quyết: Sau khi người dùng xác nhận đã push code lên GitHub
(public), tiến hành `git clone` trực tiếp vào container, đối chiếu
từng file với đúng nội dung đã thống nhất qua 8 bước (khớp 100%,
không lệch) trước khi chạy kiểm thử thật.

### `WorkbookSaveError` không tái hiện được trong môi trường test

Vấn đề: Container test chạy với quyền root, bỏ qua toàn bộ kiểm tra
permission của hệ điều hành — không thể ép `openpyxl.save()` thất bại
do quyền truy cập.

Giải quyết: Không giải quyết được trong phiên này — logic xử lý
(`_save_workbook()` bắt `OSError`, cha của `PermissionError`) được
đánh giá là đúng về mặt code, nhưng cần người dùng tự verify trên máy
thật (quyền user thường) trước khi coi là đã kiểm chứng đầy đủ. Ghi
nhận vào Known Issues, đưa vào kế hoạch phiên sau.

### Nhầm lẫn thiết kế report_writer qua nhiều vòng trao đổi

Vấn đề: Ban đầu tôi (Claude) đề xuất `ReportWriter` nhận `ExcelWriteResult`
duy nhất; sau đó hiểu nhầm ý người dùng là gộp `list[PDFResult]` +
`ExcelWriteResult` vào cùng nội dung report.txt; người dùng phải chỉnh
lại 2 lần để làm rõ 2 luồng dữ liệu phải tách biệt hoàn toàn về xử lý
(dù cùng nhận chung ở 1 lệnh gọi `write()`).

Giải quyết: Chốt lại đúng ý người dùng — `list[PDFResult]` chỉ ra
`logger`, `ExcelWriteResult` chỉ ra `report.txt`, không trộn nội dung.
Verify bằng test kiểm tra rõ 2 hành vi khác nhau (report.txt ghi đè,
log tích lũy).

## Validation

Verify bằng kiểm thử tự động thực tế (không phải review tĩnh), chạy
trên source đã clone từ GitHub (`https://github.com/minhquipk/PDF2Excel`):

-   `core/models.py` dataclass mới: frozen/immutable đúng.
-   `core/excel_mapper.py`: happy path + 5 case lỗi đều đúng.
-   `core/excel_writer.py`: happy path, 3/4 case lỗi verify được
    (`WorkbookSaveError` không tái hiện được — xem Issues Encountered).
-   `utils/logger.py`: `FileHandler` hoạt động đúng, không nhân đôi,
    giữ đúng dấu tiếng Việt.
-   `core/report_writer.py`: report.txt ghi đè, log tích lũy — đúng cả
    2 hành vi khác nhau đã thống nhất.
-   `ui/worker.py::_write_excel()`: happy path + error path (giả lập
    mapping.json lỗi) đều đúng.
-   `ui/main_window.py::_report()`: 4 nhánh UI đều đúng (mock
    QMessageBox/QDesktopServices, chạy offscreen).
-   Regression toàn pipeline với 1 PDF thật (tự tạo qua PyMuPDF): chạy
    hết Reader→Detector→Extractor→Parser→ExcelWriter→ReportWriter
    không crash.

**Chưa verify**: một lượt chạy thật qua UI (người dùng tự bấm Input
Folder → Start → Report) với dữ liệu PDF hóa đơn thật — đây là kế
hoạch chính của phiên tiếp theo.

## Next Session

Đã thống nhất chọn **Hướng 1** (kiểm thử end-to-end với data thật)
thay vì Hướng 2 (triển khai OCR trước), lý do: ADR-013 (Mock First) —
Mock `OCREngine` đã đủ cho PDF Digital-mode; làm OCR đồng thời với lần
đầu chạy thật sẽ gộp 2 rủi ro chưa kiểm chứng cùng lúc, vi phạm
Rule 2/3.

Kế hoạch 5 bước (xem chi tiết PROJECT_CONTEXT.md §15):

1.  Chuẩn bị PDF mẫu thật (ưu tiên Digital-type).
2.  Sửa `resources/excel_mapping.json` khớp workbook Excel thật.
3.  Chạy app thật end-to-end (lưu ý: entry point thật đang ở
    `ui/main_window.py`, không phải `main.py` rỗng — cần làm rõ).
4.  Quan sát kết quả Excel/report.txt/template match.
5.  Sửa `sample_invoice_v1.json` (2 lỗi đã biết) dựa trên dữ liệu thật.

Sau đó mới quay lại Hướng 2 (OCR thật) cho các PDF Scanned/Hybrid nếu
có trong bộ data mẫu.

Việc tồn đọng khác: verify `WorkbookSaveError` trên máy thật; unit
test `Extractor._rotate_bbox()`; giải quyết vai trò `processor.py`;
giải quyết discrepancy `main.py`/`ui/main_window.py`; dọn dead code
`UIText.REPORT_PENDING`.

## Notes

Toàn bộ quá trình thiết kế lần này khác các session trước ở chỗ: bắt
đầu từ 1 tài liệu Word do người dùng cung cấp, trải qua nhiều vòng
phản biện/điều chỉnh thiết kế trước khi implement (đúng tinh thần Rule 11
"Freeze design before implementation" — nhưng ở đây "freeze" diễn ra
qua nhiều lượt xác nhận tăng dần, không phải 1 lần duy nhất). Sau khi
implement xong, toàn bộ 8 bước được kiểm chứng lại trên source GitHub
thật (không phải chỉ trên code đề xuất trong chat) — xác nhận source
khớp 100% với thiết kế đã thống nhất, không có sai lệch nào phát sinh
trong quá trình người dùng tự áp dụng code.

---

Session 2026-08-07
Objective

Xây dựng resources/excel_mapping.json và resources/templates/sample_invoice_v1.json dựa trên data thử nghiệm thật, theo đúng kế hoạch 5 bước đã thống nhất ở Session 2026-08-03 (PROJECT_CONTEXT.md §15). Người dùng cung cấp PDF hóa đơn thật (HD2026-0003_digital.pdf, PDF Digital) để đối chiếu trực tiếp thay vì chỉnh sửa dựa trên suy đoán.

Completed
excel_mapping.json
Thảo luận thêm trường sheet - rút lại sau khi phân tích ExcelWriter._find_table() (đã duyệt toàn bộ sheet, Excel tự đảm bảo tên Table duy nhất trong workbook → sheet dư thừa). Xem ADR-042.
Tạo mới resources/EXCEL_MAPPING_GUIDE.md - hướng dẫn viết excel_mapping.json cho người điều hành không biết lập trình.
Kiểm thử thực nghiệm sample_invoice_v1.json trên PDF thật

Toàn bộ phần việc dưới đây dựng lại các module liên quan (pdf_reader.py, extractor.py, template_matcher.py, value_converter.py) trong sandbox, chạy thật trên HD2026-0003_digital.pdf sau mỗi thay đổi - không suy đoán tĩnh.

Vòng 1 - Đối chiếu tĩnh với text PDF: phát hiện 5 lỗi rõ ràng trong template gốc (company_name key_tokens sai, invoice_number value_pattern không cho chữ+gạch ngang, invoice_date key_tokens sai, total_amount direction sai "Below" thay vì "Right", vat_rate value_pattern không cho %).

Vòng 2 - Chạy thật, phát hiện thêm 3 vấn đề mới (không thấy được qua review tĩnh):

axis_tolerance mặc định (0.02-0.05) quá lớn so với khoảng cách dòng thật (~0.0168-0.0202) - window tràn dòng liền kề.
max_distance của field tiền tệ quá nhỏ so với khoảng cách nhãn-giá trị thật (label sát trái, số tiền căn phải).
Định dạng số của PDF test dùng dấu phẩy ngăn nghìn, ngược mặc định VN trong value_converter.py - xác nhận là quirk của data test (người dùng xác nhận), không đổi mặc định toàn cục, chỉ override decimal_format riêng cho template này.

Vòng 3 - Phát hiện 3 vấn đề cần sửa code (Nhóm 3), tạm hoãn:

3.1: tax_code bị lấy nhầm MST bên mua (va chạm Key Matching).
3.2: invoice_date phụ thuộc may rủi thứ tự xuất hiện để thắng tie giữa 3 vị trí khớp cùng ratio.
3.3: Value Matching chỉ lấy 1 WordToken - field nhiều từ bị cắt cụt (giới hạn đã biết từ Session 2026-08-01/02, nay ảnh hưởng thêm 3 field mới người dùng yêu cầu bổ sung: address, buyer_name, payment_method).

Người dùng quyết định: (1) patch value_converter.py cho % ngay, (2) mở rộng thêm 4 field mới dù biết sẽ cắt cụt tạm thời, (3) xử lý Nhóm 3 trước khi tiếp tục.

Giải quyết 3.3 - Value Matching nhiều từ

Thảo luận 3 hướng thiết kế (gap-based / cả dòng trong window / dùng vị trí key field khác làm ranh giới) - chọn gap-based, chỉ áp dụng field Text. Implement TemplateMatcher._merge_same_line(), verify phát hiện thêm 1 hệ quả phụ (merge kéo nhầm token nhãn 'mua:' vào giá trị tax_code) → thêm điều kiện dừng ở token kết thúc :. Verify lại: 4 field trước đó bị cắt cụt nay ra đúng giá trị đầy đủ. Xem ADR-044.

Giải quyết 3.1 + 3.2 - Section-Scoped Key Matching

Người dùng nhận định 2 vấn đề cùng gốc rễ (thiếu ngữ cảnh khi Key Matching), đề xuất 2 hướng khái niệm (Context+Key→Value, Section+Key→Value) và 4 cách triển khai (Block/Section, Parent Key, Anchor, Relative Position). Sau khi phân tích ưu/nhược từng cách (Section mạnh nhất, giải quyết tận gốc; Parent Key là biến thể yếu hơn của Section; Anchor chỉ là cơ chế mềm/tie-break; Relative Position brittleness cao, trói field vào tọa độ tuyệt đối, đi ngược triết lý spatial_relation tương đối theo Key), người dùng chọn Section, kèm 3 quyết định thiết kế: section header dùng tie-margin riêng (SECTION_TIE_MARGIN), field bắt buộc khai section (không cho phép bỏ trống), áp dụng luôn vào sample_invoice_v1.json trong phiên này.

Implement: SectionDefinition mới, FieldDefinition.section bắt buộc, TemplateDefinition.sections + validate, refactor TemplateMatcher._find_key_match() dùng chung Field/Section, thêm _resolve_sections()/_filter_phrases_by_range(), sửa _score_template(). Phát hiện thêm trong lúc chọn key_tokens cho section "buyer": header 5 từ ("THÔNG TIN NGƯỜI MUA HÀNG:") vượt MAX_KEY_WORDS=4, không bao giờ đạt ratio 100 - phải chọn key 4 từ ("thong tin nguoi mua") để qua được tie-margin.

Verify: 12/12 field ra đúng giá trị, bao gồm tax_code (đúng MST bên bán) và invoice_date (xác nhận đảm bảo, không còn may rủi - chỉ còn 1 candidate trong phạm vi section "header"). Bonus phát hiện: buyer_tax_code dùng lại được key_tokens giống hệt tax_code, không cần key riêng biệt như thiết kế tạm trước đó. Xem ADR-045.

Lỗi phát sinh trong lúc người dùng áp dụng patch

Bộ patch đầu tiên cho Section (models_patch.md, template_matcher_section_patch.md, template_loader_patch.md) bị thiếu patch cho core/constants.py (TemplateMatching.SECTION_TIE_MARGIN đã dùng trong sandbox lúc test nhưng quên đưa vào patch xuất cho người dùng). Người dùng phát hiện qua review trước khi áp dụng. Bổ sung constants_patch.md ngay sau đó, người dùng xác nhận áp dụng thành công.

Architecture Decisions

Xem ARCHITECTURE_DECISIONS.md ADR-042 đến ADR-045. Tóm tắt:

ADR-042: Không thêm sheet vào ExcelMapping (dư thừa với cơ chế tìm Table hiện có).
ADR-043: ValueConverter strip % cuối chuỗi trước khi convert Decimal.
ADR-044: Value Matching ghép nhiều từ cho field Text bằng gap-based line clustering, dừng ở token kết thúc :.
ADR-045: Section-scoped Key Matching - giới hạn phạm vi tìm key_tokens của field trong đúng khối tài liệu đã khai, giải quyết va chạm giữa các khối (bên bán/bên mua) và rủi ro tie-break theo thứ tự.
Issues Encountered
Thiếu sót khi xuất patch

Đã mô tả ở mục Completed ("Lỗi phát sinh trong lúc người dùng áp dụng patch"). Nguyên nhân: thay đổi trong sandbox (core/constants.py) không được đối chiếu lại đầy đủ với danh sách file patch xuất ra cho người dùng. Bài học: cần liệt kê tường minh MỌI file đã sửa trong sandbox trước khi xuất patch, không chỉ các file "chính" của thay đổi.

MAX_KEY_WORDS giới hạn độ dài section header

Đã mô tả ở mục Completed. Phát hiện qua thực nghiệm khi chọn key_tokens cho section "buyer" - không phải suy đoán trước. Cần đưa vào tài liệu hướng dẫn viết Template (còn thiếu) như 1 ràng buộc khi thiết kế section header, tương tự các "quy tắc vận hành" đã ghi từ Session 2026-08-01/02 (tránh key 1 từ, tránh value_pattern quá lỏng).

Validation

Toàn bộ thay đổi trong phiên này được verify bằng chạy thật (không phải review tĩnh) trên HD2026-0003_digital.pdf, dựng lại các module liên quan trong sandbox theo đúng nội dung source đã có. Kết quả cuối: sample_invoice_v1.json (v3) cho ra đúng 12/12 field so với nội dung PDF gốc. Người dùng đã áp dụng toàn bộ patch (value_converter.py, template_matcher.py x2 đợt, models.py, template_loader.py, constants.py, sample_invoice_v1.json v2 rồi v3) vào repo thật và xác nhận kết quả ổn sau mỗi đợt.

Chưa verify: hành vi Section/merge trên các mẫu hóa đơn thật khác (chỉ có 1 file test trong phiên này) - rủi ro tràn của gap-based merge và va chạm section header lý thuyết vẫn còn, cần thêm dữ liệu đa dạng hơn để đánh giá đầy đủ.

Next Session

Theo đúng kế hoạch ban đầu của phiên này (chưa thực hiện):

Hoàn thiện tính năng Report ở UI.
Chạy thử nghiệm toàn bộ chương trình end-to-end thật (kế hoạch 5 bước, PROJECT_CONTEXT.md §15) - vẫn chưa có lượt chạy UI thật nào (Input Folder → Start → Report) qua ứng dụng thật.

Việc tồn đọng khác:

Viết "Template Authoring Guide" (mở từ Session 2026-08-01/02) - nay cần bổ sung quy tắc về sections/MAX_KEY_WORDS.
Tinh chỉnh SECTION_TIE_MARGIN và các hằng số TemplateMatching.* khác khi có thêm mẫu hóa đơn thật.
Đánh giá rủi ro tràn của gap-based Value merge trên nhiều layout hơn.
Điều chỉnh resources/excel_mapping.json khớp workbook thật (vẫn mở từ Session 2026-08-03).
Các việc tồn đọng dài hạn khác không đổi: processor.py vs Worker.process(), main.py vs ui/main_window.py, OCR backend thật, UIText.REPORT_PENDING dead code, Document/Graphics Rules cho PDFDetector.