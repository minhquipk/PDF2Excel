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

---

## Session 2026-08-07 (Khắc phục lỗi OCREngine & Startup UI)

### Objective
Khắc phục lỗi crash ứng dụng ngay khi bật giao diện UI (`main_window.py`) do `OCREngine.__init__()` nạp `_PaddleOCR` quá sớm và xung đột thuộc tính `strides` trong Paddle 3.0.0 PIR engine (`ValueError: Type of attribute: strides is not right`).

### Completed
- **`core/ocr_engine.py`**: Chuyển sang cơ chế Lazy Loading (`self._ocr = None`, khởi tạo 1 lần duy nhất qua `_get_ocr()` khi `recognize()` được gọi lần đầu).
- **`core/constants.py`**: Bổ sung `USE_DOC_ORIENTATION_CLASSIFY = False` và `USE_DOC_UNWARPING = False` trong `class OCR` để tắt các tiền xử lý phụ thừa của PaddleX (deskew đã có OpenCV `_deskew()` đảm nhiệm).

### Architecture Decisions
- **ADR-046**: Lazy Loading OCREngine & Tắt Tiền Xử Lý Phụ Của PaddleX Đảm Bảo Khởi Động UI Không Crash.

### Validation
- Đã kiểm thử chạy offscreen `MainWindow()` thành công, ứng dụng khởi động tức thì, không bị freeze và không bị sập.

---

# Session 2026-08-08 / 2026-08-09

## Objective

Chạy UI thật lần đầu tiên với dữ liệu thật (kế hoạch 5 bước,
PROJECT_CONTEXT.md §15). Thiết kế và triển khai `OCREngine` thật (thay
Mock, ADR-013) cho luồng PDF Scanned/Hybrid.

## Completed

### First Real UI Run
- Chạy UI thật (Input Folder -> Start -> Report) lần đầu tiên qua ứng
  dụng thật - hoàn thành bước 3 kế hoạch 5 bước (PROJECT_CONTEXT.md
  §15). Chi tiết kết quả không phải trọng tâm phiên này (trọng tâm
  chuyển sang OCR ngay sau đó khi phát hiện file Scanned cần xử lý).

### OCR Engine - Thảo luận thiết kế + 3 vòng thực nghiệm thư viện

Thảo luận input/output/thư viện theo đúng Rule 11/12
(DEVELOPMENT_WORKFLOW.md: freeze thiết kế trước khi implement). Quyết
định ban đầu: PaddleOCR, input qua NumPy array, output
Text/BoundingBox/DocumentImage (đã thảo luận từ trước phiên này).

**Vòng 1 - PaddleOCR:** Triển khai đầy đủ (`constants.py`, `models.py`
thêm `PageImage.channels`, `pdf_reader.py` đổi RGB, `ocr_engine.py`).
Phát hiện qua chạy thật (không phải suy đoán): (a) API PaddleOCR 3.x
khác hẳn tri thức huấn luyện cũ (`use_angle_cls`/`use_gpu` đã đổi tên
thành `use_textline_orientation`/`device`; `model_type` phải là `Enum`
không phải string); (b) lỗi tương thích `paddlepaddle`/PIR
(`ValueError: strides is not right`) khi chạy thật trên PDF Scanned -
xác nhận qua GitHub Issue #18162 là lỗi đã biết, chưa có fix chính
thức; (c) trên máy thật (macOS Ventura Intel Python 3.12), chỉ
`paddleocr==2.7.3`+`paddlepaddle==2.6.2` chạy được - hạ cấp API và chất
lượng model đáng kể, kèm rủi ro xung đột `numpy`/`pandas`.

**Vòng 2 - RapidOCR:** Chuyển hướng sau khi đánh giá `paddlepaddle` là
rủi ro cấu trúc (framework đang chuyển đổi kiến trúc PIR, không phải
lỗi nhất thời). Verify thật: RapidOCR (backend `onnxruntime`) không cần
`paddlepaddle`, hỗ trợ tiếng Việt (Model List chính thức), output
`RapidOCROutput.boxes` dạng tứ giác `(N,4,2)` (cần tự quy về rect),
`LoadImage` giả định `ndarray` đầu vào là BGR (cần tự
`cv2.cvtColor(RGB2BGR)`, khác PaddleOCR). Phát hiện + sửa: `onnxruntime`
không phải dependency chính thức (phải thêm dòng riêng); không có wheel
`onnxruntime>=1.24` cho macOS Intel (hạ về `1.23.2`, verify qua venv
sạch); lỗi lazy loading tự triển khai (`self._ocr` gọi trực tiếp thay
vì qua `self._get_ocr()`) gây `TypeError: 'NoneType' object is not
callable`. Sau khi sửa hết lỗi kỹ thuật, pipeline chạy thành công
(không crash) nhưng **chất lượng nhận dạng tiếng Việt kém** - phát hiện
qua debug thật của người dùng trên `HD2026-0001_scanned.pdf`.

**Vòng 3 - Tesseract 5.x + tessdata_best (chốt):** Cân nhắc thêm 1
phương án Hybrid (Tesseract Detection + VietOCR Recognition) - tra cứu
thật cho thấy VietOCR dùng PyTorch không khai báo chính thức + tải model
qua Google Drive (`gdown`, rủi ro rate-limit) - cộng dồn nhược điểm của
cả 2 hướng, hoãn sang Future Improvements (Rule 9: không tối ưu sớm).
Verify Tesseract+tessdata_best bằng chạy thật (cài qua `apt` trong
sandbox để test, `vie.traineddata` tải từ repo chính thức
`tesseract-ocr/tessdata_best`) trên đúng `HD2026-0001_scanned.pdf` -
kết quả đọc đúng gần như tuyệt đối, giữ nguyên dấu tiếng Việt. Verify
thêm cấu trúc bounding box per-word qua `pytesseract.image_to_data()` -
rect trục-thẳng có sẵn (đơn giản hơn RapidOCR/PaddleOCR, không cần quy
đổi tứ giác). Triển khai đầy đủ 4 file (`requirements.txt`, `config.py`,
`core/constants.py::OCR`, `core/ocr_engine.py`) theo đúng Rule 2/3 (1
file/1 bước). Quyết định KHÔNG áp dụng Lazy Loading (ADR-046) cho bản
Tesseract - lý do: Tesseract chạy qua `subprocess`, không giữ model
nặng trong tiến trình, không có gì cần trì hoãn.

### Bug phát sinh sau khi người dùng tự chạy thật (đã sửa)

- Deskew nhầm trang A4 dọc thành góc nghiêng ~90° (`minAreaRect` toàn
  trang không phù hợp tài liệu nhiều khối như hoá đơn) - làm hỏng vị
  trí mọi `WordToken`, khiến `TemplateMatcher.select_template()` thất
  bại toàn bộ (triệu chứng: Excel/report.txt "Total: 0, Written: 0" dù
  `PDFResult.status = Success`). Người dùng tự phát hiện + tự sửa bằng
  ngưỡng `DESKEW_MAX_ANGLE=10.0`; hình thức hoá lại thành hằng số tường
  minh trong `core/constants.py::OCR` (xem ADR-049).
- Quá trình chẩn đoán: dựng lại thật `TemplateMatcher`/`TemplateLoader`
  + logic Extractor trong sandbox, chạy trực tiếp trên
  `HD2026-0001_scanned.pdf` qua Tesseract thật - lần đầu KHÔNG tái hiện
  được lỗi (vì script chẩn đoán bỏ qua bước deskew, nên không dính bug
  90°) - cho thấy rõ nguyên nhân nằm ở `OCREngine`, không phải
  `TemplateMatcher`/`Parser` như nghi ngờ ban đầu. Đã `git clone` trực
  tiếp repo GitHub thật (`https://github.com/minhquipk/PDF2Excel`) để
  đối chiếu `TemplateMatching.*`/`sample_invoice_v1.json` mới nhất,
  loại trừ khả năng lệch cấu hình trước khi kết luận đúng nguyên nhân.

## Architecture Decisions

Xem ARCHITECTURE_DECISIONS.md ADR-047 đến ADR-050. Tóm tắt: OCR Engine
chốt Tesseract+tessdata_best (ADR-047, kèm lịch sử loại PaddleOCR/
RapidOCR); PageImage render RGB thay Grayscale, amend ADR-026 (ADR-048);
Deskew giữ nguyên canvas + ngưỡng chặn góc giả DESKEW_MAX_ANGLE
(ADR-049); app.log ghi đè thay vì tích luỹ, amend ADR-040 (ADR-050).

## Issues Encountered

Đã mô tả chi tiết ở mục Completed (3 vòng thư viện + bug deskew). Bài
học chung: với các thư viện OCR/ML Python, backend nặng (framework suy
luận: `paddlepaddle`, `onnxruntime`, `torch`) thường KHÔNG được khai
báo là dependency chính thức của package wrapper cấp cao - đây là mẫu
hình lặp lại ít nhất 2 lần trong phiên này (`rapidocr`/`onnxruntime`,
`vietocr`/`torch`), cần luôn verify qua `pip show`/metadata thật trước
khi tin vào "chỉ cần pip install 1 gói là đủ".

## Validation

- PaddleOCR, RapidOCR: verify qua chạy thật trong sandbox VÀ trên máy
  thật của người dùng (macOS Ventura Intel Python 3.12) - cả 2 đều phát
  hiện vấn đề thật không thấy được qua review tài liệu/tĩnh.
- Tesseract+tessdata_best: verify qua chạy thật trong sandbox (cài qua
  `apt`, tải `tessdata_best` chính thức) trên `HD2026-0001_scanned.pdf`
  - kết quả đối chiếu trực tiếp với nội dung PDF gốc, khớp gần 100%.
- Bug deskew 90°: verify qua dựng lại `TemplateMatcher` thật trong
  sandbox (không phải giả lập) + đối chiếu trực tiếp source GitHub qua
  `git clone` - xác nhận đúng nguyên nhân trước khi người dùng xác nhận
  đã tự sửa.
- UI real run, logger.py (append->overwrite), processing_table_model.py
  (append->prepend), Elapsed/ETA: ghi nhận theo mô tả của người dùng,
  **CHƯA verify qua source thật trong phiên này** (người dùng chọn ghi
  trực tiếp theo mô tả thay vì đối chiếu qua `git clone`).

## Next Session

Priority:

1. Thảo luận riêng vấn đề `Worker._format_note()` chọn sai warning hiển
   thị (đã ghi nhận, hoãn từ phiên này - xem CHANGELOG.md, Known Issue
   mới).
2. Verify qua source thật 3 thay đổi đã ghi nhận theo mô tả (logger.py,
   processing_table_model.py, Elapsed/ETA) - đối chiếu byte-for-byte
   với GitHub khi có dịp, nhất quán cách các phiên trước đã làm (VD
   Session 2026-08-03 đối chiếu toàn bộ source trước khi coi là verify
   xong).
3. Đánh giá thêm dữ liệu PDF Scanned/Hybrid thật đa dạng hơn cho
   Tesseract+tessdata_best (hiện chỉ verify trên 1 file) - đặc biệt các
   trường hợp nghiêng thật gần ngưỡng `DESKEW_MAX_ANGLE=10.0`, để tinh
   chỉnh ngưỡng nếu cần.
4. Cân nhắc thêm tài liệu cài đặt cho end-user (Tesseract là binary hệ
   thống, không thuần `pip`; `vie.traineddata` phải tự tải/đặt vào
   `TESSDATA_DIR`) - hiện chưa có tài liệu dạng `EXCEL_MAPPING_GUIDE.md`
   tương đương cho bước cài đặt OCR.
5. Cân nhắc giới hạn version trên cho `opencv_python` trong tài liệu cài
   đặt (đề xuất của người dùng, chưa thảo luận sâu - ghi nhận từ phiên
   này).
6. Việc tồn đọng dài hạn không đổi: `processor.py` vs `Worker.process()`,
   `main.py` vs `ui/main_window.py`, `UIText.REPORT_PENDING` dead code.

## Notes

Phiên này có quy mô bất thường lớn do phải thử nghiệm tuần tự 3 thư
viện OCR khác nhau trước khi tìm được lựa chọn đạt yêu cầu chất lượng -
đây không phải vi phạm Rule 1 (kiến trúc không đổi tuỳ tiện): mỗi lần
đổi đều có bằng chứng thực nghiệm thật buộc phải đổi (lỗi tương thích
không thể sửa được ở tầng dự án với PaddleOCR; chất lượng không đạt với
RapidOCR), không phải thay đổi theo cảm tính. Nguyên tắc "chạy thật để
verify" (đã thiết lập từ các phiên Template Matching trước) tiếp tục
chứng minh giá trị - cả 3 vấn đề nghiêm trọng nhất trong phiên (PIR
error, chất lượng RapidOCR kém, bug deskew 90°) đều CHỈ phát hiện được
qua chạy thật, không thấy được qua review tài liệu/code tĩnh.

---

# Session 2026-08-09 / 2026-08-11

## Objective

Xử lý Known Issue phát hiện qua thực nghiệm end-to-end sau khi hoàn
thiện OCR (Tesseract, Session 2026-08-08/09): Report.txt cho thấy ~15%
data PDF Scanned thiếu 3 field tiền tệ (subtotal/vat_amount/total_amount).
Debug xác nhận (debug.txt) nguyên nhân không phải ở Windowing/Key
Matching mà ở Value Matching/ValueConverter. Mở rộng thêm: xử lý vấn đề
OCR nhầm lẫn dấu ',' / '.' trong chuỗi số (silent corruption).

## Completed

### Debug & chẩn đoán (dựa trên debug.txt người dùng cung cấp)

Phân tích trực tiếp `TemplateMatcher.extract_fields()` theo đúng luồng
code: xác nhận Windowing hoạt động đúng (candidate token nằm đúng
trong window đã dựng), nhưng `_select_best_value()` trả None vì
`value_pattern: "^[0-9.,]+$"` không khớp token OCR dạng "4,842,303VND" -
Tesseract gộp đơn vị tiền tệ dính liền số thành 1 token khi bản scan
không có khoảng trắng rõ ràng. Đối chiếu Report.txt xác nhận toàn bộ
13 dòng cảnh báo đều thuộc PDF *_scanned.pdf, chỉ 3 field Decimal tiền
tệ - khớp giả thuyết.

### VND currency suffix (ADR-051)

Xác định 7 biến thể qua thống kê thực tế của người dùng: vnd, VND, vnđ,
VNĐ, ₫, đ, Đ. 2 nhóm xử lý khác nhau theo mức rủi ro:
- 5 biến thể dài (≥2 ký tự/Unicode riêng biệt): strip vô điều kiện.
- 2 biến thể 1 ký tự (đ/Đ): CHỈ strip khi liền sau chữ số - ràng buộc vị
  trí để giảm rủi ro strip nhầm (cùng lớp rủi ro với "key_tokens 1 từ"
  đã ghi nhận Session 2026-08-01/02).
Đồng thời nới `value_pattern` tương ứng trong `sample_invoice_v1.json`
(v3->v4). Verify: PASS toàn bộ test case đang có.

### Nhầm lẫn dấu ',' / '.' - 3 hướng giải pháp song song

Người dùng đề xuất 3 hướng, dự định kết hợp cả 3:

1.  **Tăng DPI** - qua nhiều vòng thực nghiệm thực tế, chốt 450 (khác
    đề xuất ban đầu 400). Có thêm cơ sở tham chiếu Tesseract/ABBYY:
    DPI phù hợp phụ thuộc cỡ font/khổ giấy (400 cho font >10pt/A4,
    600 cho font <8pt/A5) - ghi nhận làm kế hoạch v2.0 (DPI thích ứng
    theo lựa chọn khổ giấy ở UI), v1 dùng mức chung 450.
2.  **Preprocess trước Tesseract** (`OCREngine._preprocess()`, chạy
    sau `_deskew()`): CLAHE (tăng contrast cục bộ, tránh khuếch đại
    nhiễu ở vùng chi tiết nhỏ như đuôi dấu phẩy) + Unsharp Mask (sigma
    nhỏ, amount khởi đầu thận trọng để tránh ringing artifact làm xấu
    thêm chính vấn đề đang giải quyết). Thứ tự deskew-trước-preprocess
    được xác nhận qua thực nghiệm: không có khác biệt rõ ràng so với
    thứ tự ngược lại - giữ nguyên thứ tự sẵn có.
3.  **Heuristic phục hồi số** (`ValueConverter._normalize_number_separators()`):
    6 dấu hiệu khả nghi dựa trên vị trí dấu (không dựa loại ký tự):
    dấu cuối không khớp decimal_separator cấu hình, decimal_separator
    lặp lại, vi phạm quy tắc 3 chữ số, vị trí phi lý (đầu/cuối chuỗi),
    double punctuation, decimal tail quá dài. Tích hợp vào
    `_to_decimal()` KHÔNG chỉ dựa vào `Decimal()` raise exception (vì
    lỗi nhầm dấu thường KHÔNG raise - "silent corruption", nguy hiểm
    hơn field ra None).

Kết hợp cả 3 (DPI 450 + Preprocess + heuristic phục hồi): tỷ lệ nhầm
lẫn ',' / '.' giảm xuống dưới 0.5% qua thực nghiệm - PASS toàn bộ test
case hiện có. Ghi nhận đây là cải thiện, KHÔNG phải giải quyết triệt
để - còn 2 trường hợp biên chưa có giải pháp (mất hẳn dấu phân cách;
cụm cuối 3 chữ số trùng decimal_separator) - đưa vào kế hoạch v2.0.

### Đánh giá lại lý do giữ RGB (ADR-054, amend ADR-048)

Do OCR engine đã chuyển hẳn sang Tesseract (khác PaddleOCR lúc ADR-048
được quyết định), thảo luận lại: Tesseract có cần màu thật không? Xác
nhận về mặt kỹ thuật Tesseract tự quy grayscale nội bộ, không có cơ chế
học đặc trưng màu như PaddleOCR; A/B test trên dữ liệu hiện có không
cho thấy khác biệt rõ ràng. Quyết định: VẪN GIỮ RGB, nhưng đổi lý do
sang tính bất khả nghịch của chuyển đổi (Grayscale không khôi phục lại
được RGB, trong khi RGB luôn chuyển được sang Grayscale ở bất kỳ đâu
cần) - bảo toàn khả năng dùng lại kênh màu trong tương lai, không còn
vì lợi ích OCR trực tiếp.

## Architecture Decisions

Xem ARCHITECTURE_DECISIONS.md ADR-051 đến ADR-054. Tóm tắt:

-   ADR-051: Strip hậu tố VND (7 biến thể, 2 nhóm rủi ro khác nhau).
-   ADR-052: Heuristic phục hồi số bị OCR nhầm lẫn ',' / '.' (6 dấu
    hiệu cấu trúc, không chỉ dựa vào exception).
-   ADR-053: DPI 300->450 + Preprocess (CLAHE+Sharpen) trong OCREngine.
-   ADR-054 (amend ADR-048): lý do giữ RGB đổi sang tính bất khả nghịch
    của chuyển đổi màu, không còn vì lợi ích OCR trực tiếp với Tesseract.

## Issues Encountered

### Silent corruption khó phát hiện hơn field ra None

Phát hiện quan trọng trong phiên: lỗi OCR nhầm lẫn ',' / '.' thường
KHÔNG khiến `Decimal()` raise exception - chuỗi sau xử lý vẫn đúng cú
pháp nhưng SAI TRỊ SỐ (có thể lệch tới hàng nghìn lần). Đây là loại lỗi
nguy hiểm hơn nhiều so với field ra None (đã có cơ chế ghi nhận qua
Report.txt theo ADR-032/033) vì không có bất kỳ dấu hiệu cảnh báo nào.
Thiết kế ban đầu dự định chỉ fallback khi exception xảy ra đã được điều
chỉnh lại thành kiểm tra cấu trúc chuỗi TRƯỚC, độc lập với exception.

### Rủi ro tự tạo ra vấn đề khi cố khắc phục nó (sharpen)

Thảo luận kỹ trước khi triển khai: Unsharp Mask có nguy cơ tạo ringing
artifact quanh nét mảnh - đúng nét mảnh nhất trong toàn bộ ký tự chính
là đuôi dấu phẩy (đối tượng đang cố cải thiện). Giải quyết bằng cách
bắt đầu tham số ở mức thận trọng (sigma nhỏ, amount thấp) thay vì mức
trung bình/mạnh, để tinh chỉnh tăng dần qua thực nghiệm.

## Validation

Toàn bộ thay đổi verify bằng thực nghiệm thực tế của người dùng (nhiều
vòng, không phải suy đoán tĩnh), nhất quán với nguyên tắc "chạy thật để
verify" xuyên suốt dự án:

-   ADR-051 (VND suffix): PASS toàn bộ test case đang có.
-   ADR-052+053 (DPI + Preprocess + heuristic phục hồi, kết hợp cả 3):
    tỷ lệ nhầm lẫn ',' / '.' giảm xuống dưới 0.5% - PASS toàn bộ test
    case hiện có, KHÔNG phải 0% - ghi nhận rõ ràng là cải thiện, không
    phải giải quyết triệt để.
-   Thứ tự deskew/preprocess: verify qua thực nghiệm - không có khác
    biệt kết quả rõ ràng giữa 2 thứ tự.

## Next Session

Ưu tiên:

1.  Tiếp tục theo dõi 2 trường hợp biên chưa có giải pháp của ADR-052
    (mất hẳn dấu phân cách; cụm cuối 3 chữ số trùng decimal_separator)
    qua dữ liệu thật nhiều hơn.
2.  v2.0: thiết kế DPI thích ứng theo khổ giấy/cỡ font (chọn khổ giấy ở
    UI) - chưa bắt đầu, cần phiên thảo luận riêng.
3.  Tinh chỉnh `NumberRepair.DECIMAL_TAIL_MAX_LENGTH` và
    `OCR.PREPROCESS_*` khi có thêm dữ liệu PDF Scanned đa dạng hơn.
4.  Các việc tồn đọng dài hạn không đổi: `processor.py` vs
    `Worker.process()`, `main.py` vs `ui/main_window.py`, Template
    Authoring Guide (nay cần bổ sung thêm nhóm quy tắc "ký hiệu đơn vị
    dính liền giá trị số": %, VND, đ/Đ), `UIText.REPORT_PENDING` dead
    code, `WorkbookSaveError` chưa verify permission thật.

## Notes

Phiên này tiếp tục xác nhận giá trị của nguyên tắc "chạy thật để verify"
đã thiết lập từ các phiên trước: cả con số DPI cuối cùng (450, khác 400
ban đầu) lẫn kết luận "thứ tự deskew/preprocess không khác biệt" đều chỉ
xác định được qua nhiều vòng thực nghiệm thực tế của người dùng, không
phải suy đoán lý thuyết. Silent corruption (ADR-052) là phát hiện quan
trọng về mặt nguyên tắc: không phải mọi lỗi dữ liệu đều biểu hiện qua
exception hay field None - cần chủ động kiểm tra cấu trúc dữ liệu đầu
vào trong các trường hợp có rủi ro sai lệch âm thầm.

---

# Session 2026-08-12 — Đóng v1, Part 1/3

## Objective

Bắt đầu quy trình đóng v1 (chia 3 phần theo quyết định của người dùng:
Part 1 - Known Issues từ nhật ký; Part 2 - vấn đề người dùng tự ghi
nhận; Part 3 - vấn đề phát sinh khi quét trực tiếp mã nguồn). Phiên này
xử lý toàn bộ Part 1: 7 Known Issue được liệt kê sẵn trong
PROJECT_CONTEXT.md §14/CHANGELOG.md Unreleased-Next tại thời điểm bắt
đầu phiên.

## Completed

### 1. `core/processor.py` — xóa

Xác nhận qua rà soát source: 4 lời gọi top-level tham chiếu biến
`processor` chưa từng định nghĩa (NameError nếu exec), không được
import/reference ở bất kỳ đâu. Vai trò ADR-004 (orchestrator) đã được
`Worker.process()` đảm nhiệm đầy đủ từ lâu. Người dùng tự xóa file sau
khi thảo luận thống nhất.

### 2. `main.py` vs `ui/main_window.py` — resolve entry point

Chuyển khối `if __name__ == "__main__":` từ `ui/main_window.py` sang
`main.py` (trước đó rỗng). Verify chạy thật `python main.py` từ gốc dự
án, hành vi giữ nguyên.

### 3. Rà soát dead code toàn bộ source

Quét `core/`, `ui/`, `models/`, `utils/`, `config.py` tìm constant/
enum/dataclass/method không được reference. Chia 3 nhóm:
- Nhóm A (xóa): 5 mục trong `core/constants.py`
  (`UIText.REPORT_PENDING`, `FileDialog.PDF_FILTER`,
  `FileDialog.ALL_FILES`, `UIText.READY/PROCESSING/COMPLETED/
  CANCELLED`, `Report.FOLDER`).
- Nhóm B (giữ, có chủ đích): `SessionResult`, `ProcessError`,
  `ProcessStage`, `ErrorType` — domain model chưa wire vào pipeline
  nhưng có thể phục vụ ý đồ xử lý lỗi có cấu trúc trong tương lai,
  người dùng quyết định giữ lại thay vì coi là dead code.
- Nhóm C (giữ, không phải dead code): API interface chủ đích chưa dùng
  tới (`BaseWidget.clear()/reset()`, `ProcessingTableModel.items()`,
  `ProcessingTable.model()`, `App.VERSION`/`AUTHOR`).

### 4. `resources/TEMPLATE_AUTHORING_GUIDE.md`

Tổng hợp toàn bộ quy tắc/ràng buộc đã phát sinh qua thực nghiệm rải rác
trong ADR-030, ADR-043, ADR-044, ADR-045, ADR-051 và Session 2026-08-01/
02, 2026-08-07 thành 1 tài liệu Markdown đồng bộ style với
`EXCEL_MAPPING_GUIDE.md`. Gộp chung "spec + best practice" (schema đầy
đủ `TemplateDefinition`/`FieldDefinition`/`SectionDefinition`/
`SpatialRelation` kèm quy tắc an toàn ngay tại từng mục), dùng
`sample_invoice_v1.json` v4 làm ví dụ xuyên suốt. Người dùng xác nhận
nội dung.

### 5. Unit test đầu tiên của dự án

Xác nhận `Extractor._rotate_bbox()` là `@staticmethod` thuần túy, không
cần fixture PDF thật/mock `Extractor()` (tránh `OCREngine()` raise
`FileNotFoundError` nếu thiếu tessdata). Trước khi viết test, tự suy
diễn độc lập công thức hình học cho cả 3 case xoay (90/180/270) bằng
cách rotate 4 góc bbox quanh gốc và lấy lại bounding box - xác nhận
công thức trong code đúng toán học, không phát hiện sai sót. Viết 9
test case: 1 (rotation=0) + 2×3 (sample bbox + full-page edge case cho
mỗi góc 90/180/270, dùng số liệu suy diễn tay) + 2 (round-trip identity
90+270 và 180+180 - bắt lỗi dấu độc lập với việc suy diễn tay có đúng
hay không). Framework `pytest`, dependency mới `requirements-dev.txt`
(tách khỏi `requirements.txt` vì không cần cho end-user). Vị trí
`tests/core/test_extractor.py`, thống nhất `tests/core/` làm chuẩn cấu
trúc cho mọi test sau này. Người dùng xác nhận cài đặt, chạy `pytest
-v`, toàn bộ 9 test PASS thật trên máy.

### 6. `Worker._format_note()` chọn sai warning ưu tiên

Xác nhận root cause: `DocumentAnalysis.warnings` được flatten theo thứ
tự rule chạy cố định trong `_evaluate_rules()`, luôn đặt warning của
`text_coverage` lên đầu bất kể mức độ liên quan tới quyết định cuối.
Thảo luận 2 phương án (sửa tại `PDFDetector` vs sửa tại
`Worker._format_note()`) - người dùng chọn Phương án A (sửa tại
`PDFDetector`, tổng quát theo `RuleCategory` thay vì hard-code tên
rule). Implement `_evidence_warnings_ordered()` + constant
`_WARNING_CATEGORY_PRIORITY` trong `core/pdf_detector.py`. Dọn kèm
nhánh `extraction.warnings` chết trong `Worker._format_note()` (phát
hiện phụ: nhánh này không bao giờ chạy tới trong pipeline thật, vì
`Worker` không bao giờ gọi `Extractor.extract()` khi mode UNKNOWN).
Xem ADR-055.

### 7. Phát hiện & xử lý mismatch ADR-027

Khi rà soát nhánh `extraction.warnings`, phát hiện `core/extractor.py::
extract()` **không** raise `ValueError` khi UNKNOWN như ADR-027/
CHANGELOG.md/SESSION_SUMMARIES.md (Session 2026-07-31) đã mô tả từ đầu
- source thật trả về gracefully. Thảo luận 2 phương án (sửa tài liệu
khớp code, vs sửa code khớp tài liệu) - người dùng chọn sửa code (thêm
`raise ValueError`), theo đúng lập luận gốc của ADR-027 (phân biệt lỗi
"Detector không quyết định được" khỏi lỗi "Extractor bị gọi sai hợp
đồng lập trình" - đây là 2 tầng khác bản chất, nên xử lý khác nhau).
Hệ quả kèm theo: `ExtractionResult.warnings` (`core/models.py`) trở
thành field chết sau patch, được xóa. Xem ADR-056.

### 8. Document Rules & Graphics Rules (TDS §7.2 RC-001/RC-004)

Người dùng cập nhật `PDF_Detector_Technical_Design.docx` trong project
theo yêu cầu đối chiếu lại - xác nhận qua đọc trực tiếp: nội dung §7.2
không đổi so với bản đã có, chỉ mô tả định tính cấp cao cho RC-001/
RC-004, không có công thức/ngưỡng cụ thể (đúng bản chất TDS §5.4: diễn
giải luôn thuộc trách nhiệm reasoning engine, không phải TDS). Xác
nhận với người dùng: đây là thiết kế mới hoàn toàn (Hướng B), không
phải "khôi phục" nội dung TDS có sẵn.

Thiết kế 2 rule mới dựa trên field có sẵn trong `AnalysisContext`
nhưng trước đó chưa từng dùng cho `supports`:
- `document_metadata` (DOCUMENT): metadata Producer/Creator chứa từ
  khóa gợi ý phần mềm scan -> `supports={SCANNED: 0.20}`.
- `vector_graphics_coverage` (GRAPHICS): `drawing_page_ratio >= 0.50`
  -> `supports={DIGITAL: 0.20}`.

Nguyên tắc thiết kế: chỉ tạo `supports` từ tín hiệu DƯƠNG TÍNH rõ ràng,
không suy luận từ sự vắng mặt dữ liệu (đúng DP-003, nhất quán với 5
rule cũ). Trọng số cố ý thấp (0.20) vì chưa qua thực nghiệm dữ liệu
thật đa dạng - đã tự kiểm tra không vượt `_EVIDENCE_SCORE_SCALE = 1.40`
ở bất kỳ mode nào. Người dùng xác nhận cả 3 điểm thiết kế (trọng số,
ngưỡng, danh sách từ khóa) trước khi chốt code. Xem ADR-057.

### 9. Verify `WorkbookSaveError` (Known Issue mở từ Session 2026-08-03)

Các lần thử trước đều thất bại vì môi trường test chạy root (`chmod`
không chặn được root). Lần này thử kỹ thuật khác: `chattr +i`
(immutable attribute Linux, chặn được cả root trên filesystem ext) -
tự verify trực tiếp trong sandbox bằng bash: tạo file `.xlsx`, gắn
immutable, gọi `openpyxl.save()` -> xác nhận raise đúng
`PermissionError` (subclass `OSError`). Copy nguyên văn logic
`ExcelWriter._save_workbook()` thật, verify bắt đúng lỗi, bọc đúng
thành `WorkbookSaveError`, không leak exception gốc - **PASS**.

Lưu ý minh bạch: kỹ thuật `chattr +i` là Linux-only, không phản ánh
chính xác kịch bản Windows thật ("file đang mở trong Excel") - nhưng
về mặt Python, cả 2 kịch bản đều là `OSError`/subclass, nên
`except OSError` đã đủ tổng quát. Người dùng bổ sung: đã tự test trên
môi trường Windows thật, xác nhận popup `QMessageBox.warning` hiển thị
đúng, ứng dụng không treo.

## Architecture Decisions

Xem ARCHITECTURE_DECISIONS.md ADR-055 đến ADR-057. Tóm tắt:

- ADR-055: Thứ tự ưu tiên hiển thị warning theo `RuleCategory` trong
  `PDFDetector` (không phải theo thứ tự rule chạy).
- ADR-056: `Extractor.extract()` raise `ValueError` khi UNKNOWN - sửa
  code khớp lại ADR-027 (thay vì sửa tài liệu khớp code).
- ADR-057: Bổ sung Document Rules & Graphics Rules cho `PDFDetector`,
  hoàn thiện đủ 7/7 Rule Category theo TDS §7.2.

## Issues Encountered

### TDS không đủ chi tiết đặc tả rule cụ thể

Ban đầu dự định dựa vào `PDF_Detector_Technical_Design.docx` để lấy đặc
tả Document/Graphics Rules, nhưng xác nhận qua đọc trực tiếp: TDS §7.2
chỉ định nghĩa *khuôn khổ* (Rule Category là gì, Rule phải tuân
RP-00x nào), không đặc tả *nội dung cụ thể* của từng rule (công thức/
ngưỡng) - đây luôn là quyết định ở tầng implementation, đúng theo
chính TDS §5.4. Người dùng cập nhật lại file trong project theo yêu
cầu đối chiếu nhưng nội dung không đổi - xác nhận đây không phải thiếu
sót tài liệu, mà là bản chất thiết kế của TDS (mô tả nguyên tắc, không
mô tả tham số).

### Kỹ thuật tái hiện lỗi permission vượt qua giới hạn container root

Các phiên trước (Session 2026-08-03) từng thử `chmod` để giả lập lỗi
permission nhưng không thành công vì container test chạy root (`chmod`
không chặn được root theo mặc định Linux). Phiên này dùng `chattr +i`
(immutable attribute) - khác cơ chế permission thông thường, chặn được
cả root (trừ khi có capability `CAP_LINUX_IMMUTABLE` bị gỡ bỏ tường
minh) - giải quyết được giới hạn đã tồn đọng nhiều phiên.

## Validation

- 9 unit test `Extractor._rotate_bbox()`: PASS thật trên máy người
  dùng (`pytest -v`), xác nhận lại sau mỗi patch tiếp theo trong phiên
  (không bị ảnh hưởng bởi các thay đổi ở `PDFDetector`/`Worker`).
- `Worker._format_note()` + ADR-055: verify thực nghiệm thật trên PDF
  có đồng thời cảnh báo `content_coverage`/`page_layout` và cảnh báo
  `text_coverage` yếu - note hiển thị đúng thứ tự ưu tiên mới.
- ADR-056 (`raise ValueError`): verify qua chạy thật, pipeline không
  đổi hành vi (đúng kỳ vọng - `Worker` đã tự chặn).
- ADR-057 (Document/Graphics Rules): verify chạy thật trên PDF Digital
  và Scanned đã dùng trước đây - `DocumentAnalysis.evidence` có đủ 7
  phần tử, mode cuối cùng không đổi so với trước patch.
- `WorkbookSaveError`: verify kép - logic exception qua `chattr +i`
  trong sandbox (Assistant tự thực hiện) + UX thật trên Windows (người
  dùng tự thực hiện).

## Next Session

Ưu tiên theo đúng kế hoạch 3 Part đã thống nhất:

1. Đóng v1 Part 2/3 - xử lý vấn đề do người dùng tự ghi nhận (chưa xác
   định nội dung cụ thể, chờ người dùng liệt kê).
2. Đóng v1 Part 3/3 - xử lý vấn đề phát sinh khi quét trực tiếp mã
   nguồn (chưa bắt đầu).
3. Sau khi hoàn tất cả 3 Part: giai đoạn làm tài liệu chuyển giao ứng
   dụng (`resources/excel_mapping.json` khớp workbook thật, tài liệu
   hướng dẫn cài đặt OCR cho end-user - Tesseract binary hệ thống,
   `vie.traineddata`).

## Notes

Phiên này là phiên đầu tiên dự án có unit test tự động (trước đó hoàn
toàn dựa vào "chạy thật để verify" thủ công qua nhiều phiên) - không
thay thế nguyên tắc đó (vẫn tiếp tục áp dụng cho Document/Graphics
Rules, WorkbookSaveError), nhưng bổ sung 1 lớp bảo vệ hồi quy
(regression protection, đúng tinh thần TS-005 của TDS) cho phần logic
thuần túy, ổn định như `_rotate_bbox()`. Việc phát hiện mismatch
ADR-027 (Mục 7) cũng là 1 xác nhận giá trị của quy trình "đối chiếu
tài liệu với source thật" mà dự án đã áp dụng nhất quán từ đầu - phát
hiện được nhờ rà soát trực tiếp, không phải vì tài liệu tự báo lỗi.

------------------------------------------------------------------------

# Session 2026-08-13 — Đóng v1, Part 2/3

## Objective

Xử lý Part 2/3 trong kế hoạch đóng v1 (vấn đề do người dùng tự ghi
nhận qua rà soát/thảo luận trực tiếp, không phải từ log tồn đọng sẵn).
7 chủ đề được đặt ra tuần tự: memory management, PDFResult trùng tên,
confidence score tăng theo rule, excel_mapping.json thiếu cột, rủi ro
`_merge_same_line()`, multi-line value/max_distance, tiền xử lý ảnh
OCR nâng cao, và tái cấu trúc thư mục project (được người dùng xác
định là ưu tiên cao nhất để kết thúc v1).

## Completed

### 1. Rà soát cơ chế quản lý memory

Xác nhận `PDFReader.read()` đóng file PDF đúng qua context manager
(mọi thao tác đọc nằm trong `with fitz.open(...)`, return nằm ngoài).
`PDFDocument`/`ExtractionResult` là biến local của `Worker._process_pdf()`,
không bị giữ tham chiếu ngược từ `InvoiceInfo` - giải phóng đúng theo
ADR-006/007. Phát hiện phụ: số liệu ADR-048 (~24.9 MB/trang) lỗi thời
sau khi ADR-053 tăng DPI 300->450 - đính chính lại ~56 MB/trang.

### 2. `PDFResult` — vòng đời và ước lượng chi phí

Xác nhận việc tích lũy `list[PDFResult]` cho cả batch là có chủ đích
(không chỉ cần `list[InvoiceInfo]`) - phục vụ 2 kênh tiêu thụ khác
(`ReportWriter._log_results()` log MỌI file kể cả FAILED; UI
`ProcessingTable` hiển thị real-time). Ước lượng: ~770 bytes/file
(invoice=None) đến ~2.4 KB/file (có invoice đầy đủ) - ở quy mô 10.000
file ước ~24 MB, nhẹ hơn 3-4 bậc so với chi phí `PageImage` 1 trang.

Phát hiện phụ dẫn tới chủ đề tiếp theo: `source_file`/`relative_path`
được gán nhưng không thấy nơi nào đọc lại trong source thời điểm đó.

### 3. Vấn đề PDFResult trùng tên khi Input Folder có thư mục con lồng nhau

Người dùng xác nhận đây là tình huống thiết kế ban đầu dự tính xử lý
(VD "Quý 3" chứa "Tháng 7/8/9", mỗi tháng có HD_001...HD_100 trùng
tên). Xác nhận tầng discovery (`rglob`) đã đúng; `relative_path` đã
được tính sẵn nhưng không nơi nào tiêu thụ - mọi hiển thị/log đều dùng
`file_name` (basename only). Thảo luận 2 hướng (A: đổi sang dùng
relative_path; B: giữ file_name + thêm cột phụ) - chọn Hướng A, không
thêm cột, không đổi width. Với phần Warnings trong report.txt, thảo
luận thêm 2 phương án con (B1: giữ full absolute path; B2: đổi
`InvoiceInfo.source_file` sang relative) - chọn B1 (tối thiểu, không
đổi ý nghĩa field đang phục vụ mục đích khác là dữ liệu Excel). Đã
triển khai, người dùng xác nhận áp dụng và verify xong. Xem ADR-058.

### 4. Đánh giá confidence score tăng sau khi thêm Document/Graphics Rule

Người dùng quan sát score tăng sau khi triển khai ADR-057 (Session
2026-08-12), đặt câu hỏi đây có phải vấn đề cần quan tâm. Phân tích
công thức `_compose_confidence()` xác nhận đây là hệ quả cơ học đúng
thiết kế (Evidence -> Score -> Decision, ADR-020/021), và xác nhận qua
rà soát toàn bộ nơi đọc `DocumentAnalysis.confidence` trong source:
CHỈ dùng hiển thị trong `PDFResult.note`, không gate quyết định `mode`
hay bất kỳ logic nào khác trong pipeline - nên không phải vấn đề cấp
thiết. Lưu ý rủi ro circular validation (2 rule mới, ADR-057, mới chỉ
verify trên đúng 1-2 file PDF đã dùng tinh chỉnh mọi thứ khác trong dự
án) - ghi nhận cần thêm dữ liệu đa dạng trước khi tinh chỉnh weight.
Người dùng xác nhận không cần ghi nhận riêng.

### 5. `excel_mapping.json` khai ít cột hơn InvoiceInfo

Trả lời câu hỏi "nếu admin chỉ khai 6/12 field, hệ thống có hoạt động
đúng không" - xác nhận CÓ, bằng cách truy trực tiếp `Mapper.load()`
(chỉ validate `columns` không rỗng + field_name hợp lệ, không yêu cầu
đủ), `Parser` vẫn trích đủ 12 field (không phụ thuộc mapping),
`ExcelWriter._write_row()` chỉ duyệt đúng field đã mapping - khớp mô tả
sẵn có trong `EXCEL_MAPPING_GUIDE.md` Mục 3. Không cần sửa code.

### 6. Rủi ro `_merge_same_line()` — lookup `anchor_idx` bằng value-equality

Người dùng đặt vấn đề `next(... t.normalized_bbox == anchor.normalized_bbox and t.text == anchor.text)`
có thể `StopIteration` nếu 2 token trùng hoàn toàn. Phân tích xác nhận
KHÔNG THỂ xảy ra về mặt toán học (`anchor` luôn là phần tử của chính
`candidates`, tự thỏa điều kiện lọc `same_line` qua chính `anchor_y`).
Rủi ro thực chất hơn được xác nhận: nếu tồn tại 2 `WordToken` khác
instance nhưng trùng giá trị tuyệt đối (bbox+text), `next()` có thể trả
về "nhầm" object - nhưng vì 2 token trùng giá trị tuyệt đối, kết quả
merge giống hệt nhau bất kể chọn object nào -> vô hại. Người dùng xác
nhận không cần sửa, chuyển sang chủ đề tiếp theo.

### 7. Multi-line value / phụ thuộc `max_distance` tĩnh

Người dùng đặt vấn đề (dựa trên đánh giá rủi ro, chưa gặp thật trên A4,
nghi ngờ sẽ gặp với A5/bảng biểu phụ): 2 vấn đề liên quan
("hạn chế phụ thuộc max_distance"; "giá trị trải nhiều dòng"). Đề xuất
ban đầu (window động theo Key/Section kế tiếp; khóa direction=BELOW)
bị người dùng bác bỏ với lý do xác đáng (không đảm bảo có mốc chặn phía
sau; direction không thể khóa cứng vì độ dài giá trị phụ thuộc nội dung
thật). Xác nhận lại: đây là giới hạn KIẾN TRÚC của phương pháp hình học
tĩnh (`SpatialRelation` khai báo cố định, không đọc hiểu ngữ nghĩa),
không phải bug patch được ở tầng heuristic. Liên hệ với kế hoạch v2.0
LayoutLM đã ghi nhận sẵn từ Session 2026-08-01/02. Người dùng đồng ý
đánh giá, yêu cầu ghi nhận nghiêm túc (không phải "known limitation cần
tinh chỉnh tham số" như các mục khác). Xem ADR-059.

### 8. Đề xuất tiền xử lý ảnh OCR nâng cao — huỷ bỏ

Người dùng đề xuất 3 kỹ thuật bổ sung cho `OCREngine._preprocess()`:
Binarization (Otsu/Adaptive Thresholding), Denoising (Gaussian Blur
riêng trước sharpen), Border Removal. Phân tích từng kỹ thuật:
Binarization có rủi ro kỹ thuật rõ ràng (xung đột với cách Tesseract
LSTM/OEM=3 tự xử lý ảnh xám nội bộ, nguy cơ xóa mất đuôi dấu phẩy -
đúng vấn đề ADR-052/053 đang giải quyết) - khuyến nghị không thêm;
Denoising/Border Removal khả thi về kỹ thuật nhưng chưa có bằng chứng
thực nghiệm về nhiễu/viền đen trên dữ liệu thật hiện có. Người dùng
quyết định huỷ toàn bộ đề xuất, nhưng ghi nhận "tăng cường hiệu quả
OCR" là nội dung quan trọng cần làm ở v2.0.

### 9. Tái cấu trúc thư mục project (trọng tâm chính của phiên)

Người dùng xác định đây là việc quan trọng nhất để kết thúc v1, do kế
hoạch v2.0 sẽ bổ sung/thay đổi nhiều model cho các module hiện có, cấu
trúc `core/` phẳng (13 file) sẽ khó quản lý thêm. Quét toàn bộ import
dependency thật giữa các file `core/*.py` + `ui/worker.py` +
`utils/logger.py` + `tests/core/test_extractor.py` trước khi đề xuất,
xác nhận 13 file chia thành 5 giai đoạn pipeline độc lập (đã có ADR
riêng: Reading/Detection/Extraction/Parsing/Export) + 1 tầng domain
dùng chung (`models.py`/`enums.py`/`constants.py`, là hub, không tách
nhỏ thêm để tránh rủi ro import vòng).

Đề xuất cấu trúc `core/domain/`, `core/reading/`, `core/detection/`,
`core/extraction/`, `core/parsing/` + `core/parsing/template/`,
`core/export/`. Nêu 4 điểm cần quyết định: (a) xử lý nhập nhằng tên
"models" (models/ top-level vs core/models.py); (b) vị trí
tests/core/test_extractor.py trong cấu trúc mới; (c) có tạo sẵn
core/parsing/layoutlm/ placeholder không; (d) config.py có cần đổi
không. Người dùng quyết định: (a) đổi models/ -> ui/models/; (b) tiếp
tục mirror cấu trúc core/ mới; (c) không tạo sẵn; (d) không đổi.

Làm rõ thêm 2 câu hỏi kỹ thuật của người dùng trước khi triển khai:
"directory hay package" (xác nhận bắt buộc phải là package vì cú pháp
`from core.domain.models import X` yêu cầu); "`__init__.py` rỗng có
cần thiết" (xác nhận cần, đối chiếu tiền lệ `tests/__init__.py`/
`tests/core/__init__.py` đã rỗng từ trước - chọn regular package thay
vì namespace package để nhất quán toàn dự án).

Soạn kế hoạch chi tiết 8 bước (7 bước di chuyển tuần tự theo nhóm
module + 1 bước xác nhận cuối), liệt kê đầy đủ file di chuyển + import
cần sửa ở từng file phụ thuộc cho từng bước, theo đúng Rule 2/3
(DEVELOPMENT_WORKFLOW.md). Người dùng tự triển khai, xác nhận hoàn
thành, verify độc lập từng bước, và chạy UI thật end-to-end đầy đủ ở
bước cuối. Xem ADR-060.

## Architecture Decisions

Xem ARCHITECTURE_DECISIONS.md ADR-058 đến ADR-060, và amend ADR-048.
Tóm tắt:

- ADR-058: Hiển thị `relative_path` thay `file_name` ở UI Table/log/
  report - tránh trùng tên khi Input Folder có thư mục con lồng nhau.
- ADR-059: Giới hạn kiến trúc TemplateMatcher với multi-line value -
  không patch được ở v1, củng cố lý do kế hoạch v2.0 LayoutLM.
- ADR-060: Tái cấu trúc `core/` theo pipeline stage, `ui/models/` thay
  `models/` top-level.
- Amend ADR-048: đính chính số liệu chi phí PageImage/trang theo DPI
  450 hiện tại (~56 MB, không phải ~24.9 MB của 300 DPI cũ).

## Issues Encountered

Không phát sinh lỗi kỹ thuật ngoài dự kiến trong phiên này - toàn bộ
nội dung là thảo luận/rà soát/quyết định thiết kế, không có debug thực
nghiệm nào cần giải quyết bất ngờ (khác các phiên OCR/Template trước).

## Validation

- Memory lifecycle: xác nhận qua đọc trực tiếp source (`with fitz.open`,
  biến local trong `_process_pdf()`), không qua chạy thật đo RAM.
- PDFResult trùng tên (ADR-058): người dùng tự áp dụng + verify chạy
  thật kịch bản "Quý 3 -> Tháng 7/8/9" - xác nhận UI/log/report phân
  biệt đúng.
- excel_mapping.json thiếu cột: xác nhận qua đọc trực tiếp
  `Mapper.load()`/`ExcelWriter._write_row()`/`_resolve_columns()`,
  không chạy thật (logic đã rõ ràng từ source, không cần thực nghiệm
  thêm).
- Tái cấu trúc thư mục (ADR-060): người dùng tự triển khai theo 7 bước
  đã soạn, verify độc lập từng bước (`pytest -v` + chạy thật), và xác
  nhận 1 lượt UI thật end-to-end đầy đủ ở bước cuối cùng - PASS.

## Next Session

Theo đúng kế hoạch 3 Part:

1. Đóng v1 Part 3/3 - xử lý vấn đề phát sinh khi quét trực tiếp mã
   nguồn (chưa bắt đầu, cần quét lại toàn bộ source theo cấu trúc thư
   mục MỚI vừa tái cấu trúc).
2. Sau khi hoàn tất Part 3/3: giai đoạn làm tài liệu chuyển giao ứng
   dụng (`resources/excel_mapping.json` khớp workbook thật, tài liệu
   hướng dẫn cài đặt OCR cho end-user).
3. v2.0 planning (chưa bắt đầu thiết kế chi tiết, chỉ ghi nhận định
   hướng): LayoutLM Parser engine (ADR-059), tăng cường hiệu quả OCR
   (Binarization/Denoising/Border Removal - cần bằng chứng thực nghiệm
   trước khi quyết định), DPI thích ứng theo khổ giấy (ADR-053).

## Notes

Phiên này là phiên đầu tiên có tỷ trọng THẢO LUẬN/QUYẾT ĐỊNH KIẾN TRÚC
cao hơn hẳn phần triển khai code trực tiếp bởi Assistant - phù hợp với
mô hình làm việc mới được thiết lập từ đầu phiên (person đặt vấn đề dựa
trên mã nguồn + nhật ký, Assistant phân tích/phản biện dựa trên 4
nguyên tắc ưu tiên: Source of Truth mã nguồn > logic/tri thức > ý kiến
cá nhân người dùng trong phiên > nhật ký làm phụ trợ). 2 lần người dùng
bác bỏ đề xuất của Assistant với lý do kỹ thuật xác đáng (multi-line
value: "chưa chắc có Key Token chặn phía sau", "BELOW không đủ linh
động"; tiền xử lý ảnh: quyết định huỷ dựa trên đánh giá rủi ro đã trình
bày) - xác nhận giá trị của việc yêu cầu xác nhận trước khi triển khai
(theo đúng yêu cầu ban đầu của người dùng khi mở Project này).

------------------------------------------------------------------------