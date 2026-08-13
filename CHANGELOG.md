# CHANGELOG.md

All notable changes to this project are documented here.

The format is chronological and focuses on architectural milestones
rather than Git commits.

### Fixed
- `value_converter.py`: `_to_decimal()` xử lý hậu tố đơn vị tiền tệ VND
    dính liền chuỗi số (7 biến thể: vnd/VND/vnđ/VNĐ/₫/đ/Đ), phát hiện qua
    debug thực nghiệm trên batch PDF Scanned (~15% data thiếu field
    subtotal/vat_amount/total_amount). Cũng nới `value_pattern` tương ứng
    trong `sample_invoice_v1.json` (v3->v4). Xem ADR-051.
-   `value_converter.py`: thêm cơ chế tự phục hồi khi OCR đọc nhầm lẫn
    dấu ',' và '.' trong chuỗi số (silent corruption - Decimal() có thể
    "parse thành công" nhưng sai trị số). Heuristic dựa trên 6 dấu hiệu
    cấu trúc chuỗi (vị trí dấu, không dựa loại ký tự). Xem ADR-052.
-   `ocr_engine.py`: thêm bước `_preprocess()` (CLAHE + Unsharp Mask)
    chạy sau `_deskew()`, kết hợp tăng `Image.DPI` 300->450, cải thiện
    tỷ lệ nhầm lẫn ',' / '.' xuống dưới 0.5% (từ mức quan sát ban đầu).
    Xem ADR-053.

### Changed
-   `core/constants.py`: thêm class `NumberRepair` (`DECIMAL_TAIL_MAX_LENGTH`);
    `OCR` bổ sung 4 hằng số Preprocess (`PREPROCESS_CLAHE_CLIP_LIMIT`,
    `PREPROCESS_CLAHE_TILE_GRID_SIZE`, `PREPROCESS_SHARPEN_SIGMA`,
    `PREPROCESS_SHARPEN_AMOUNT`); `Image.DPI` 300 -> 450.
-   Đánh giá lại lý do giữ `PageImage` render RGB (ADR-048 gốc lập luận
    theo bối cảnh PaddleOCR) cho phù hợp với Tesseract - vẫn giữ RGB
    nhưng đổi lý do sang tính bất khả nghịch của chuyển đổi màu, không
    còn vì lợi ích trực tiếp cho OCR. Xem ADR-054 (amend ADR-048).

### Next

-   **Run the application end-to-end against real sample PDF data**
    (Direction 1, chosen over implementing OCR first — see
    SESSION_SUMMARIES.md, Session 2026-08-03, and
    PROJECT_CONTEXT.md §15 for the 5-step plan).
-   Fix `resources/templates/sample_invoice_v1.json`'s two known
    issues~~ — **Done, Session 2026-08-07** (phạm vi thực tế lớn hơn
    nhiều so với 2 lỗi đã biết ban đầu; xem SESSION_SUMMARIES.md,
    Session 2026-08-07, và ARCHITECTURE_DECISIONS.md ADR-043/044/045).
-   Đã thêm `resources/EXCEL_MAPPING_GUIDE.md` (Session 2026-08-07) -
    hướng dẫn viết `excel_mapping.json` cho người điều hành. Việc điều
    chỉnh `excel_mapping.json` khớp workbook thật (mục trên) vẫn CHƯA
    làm - guide chỉ giải thích cách viết, không tự động hoàn thành bước
    này.
-   Manually verify `core/excel_writer.py::WorkbookSaveError` against
    a real OS permission failure (could not be reproduced in the
    root-privileged test container this session).
-   Replace `OCREngine` Mock with a real backend (e.g. Tesseract) —
    after the above, and only for Scanned/Hybrid-mode PDFs found in
    real sample data.
-   Resolve `processor.py` role (currently placeholder — not just
    unimplemented but calls a `processor` variable that is never
    defined; orchestration logic actually lives in `Worker.process()`)
-   Resolve `main.py` (currently empty) vs `ui/main_window.py`
    (currently holds the real `if __name__ == "__main__":` entry
    point) discrepancy.
-   Remove dead code: `core/constants.py::UIText.REPORT_PENDING`, no
    longer referenced since `MainWindow._report()` was reimplemented
    (ADR-041).
-   Add Document Rules and Graphics Rules to pdf_detector Rule System
    (categories defined in TDS §7.2, not yet implemented)
-   **v2.0 planning:** dual-source extraction for mixed pages (pages
    with both text and images) — currently a page is routed to a
    single source (Digital or OCR), not both. See
    SESSION_SUMMARIES.md, Session 2026-07-31, "Issues Encountered."
-   **v2.0 planning:** LayoutLMv3-based Parser upgrade — will require
    a `[0, 1000]` scale adapter at the point of consumption;
    `WordToken.normalized_bbox` deliberately stays `[0.0, 1.0]` and
    model-agnostic (see ARCHITECTURE_DECISIONS.md).
-   **Từ Session 2026-08-07:** viết "Template Authoring Guide" (đã nêu
    từ Session 2026-08-01/02, vẫn thiếu) - nay cần bổ sung thêm cả quy
    tắc viết `sections`/`key_tokens` cho Section (VD giới hạn
    `MAX_KEY_WORDS=4` khi chọn section header dài) - phát hiện mới từ
    phiên 2026-08-07 (xem ADR-045).
-   **Từ Session 2026-08-07:** tinh chỉnh `TemplateMatching.SECTION_TIE_MARGIN`
    (hiện là 10, placeholder) khi có nhiều mẫu hóa đơn thật hơn - cùng
    nhóm với các hằng số `TemplateMatching.*` khác đã ghi nhận cần tinh
    chỉnh.
-   **Từ Session 2026-08-07:** đánh giá rủi ro tràn của cơ chế gap-based
    Value merge (ADR-044) trên nhiều mẫu hóa đơn thật hơn - hiện chỉ
    verify trên 1 PDF test, điều kiện dừng "token kết thúc bằng `:`"
    chưa chắc đủ cho mọi layout.
- (giữ nguyên các mục đã có, bổ sung thêm bên dưới)
-   **v2.0 planning:** DPI thích ứng theo khổ giấy/cỡ font (400 DPI cho
    font >10pt/A4 chuẩn, 600 DPI cho font <8pt/A5 hoặc A4 có bảng chỉ số
    phụ) thay vì `Image.DPI` cố định toàn cục - cho phép người dùng chọn
    khổ giấy ở UI. Chưa thiết kế chi tiết (xem ARCHITECTURE_DECISIONS.md
    ADR-053, PROJECT_CONTEXT.md §18).
-   **v2.0 planning:** tiếp tục cải thiện tỷ lệ nhầm lẫn ',' / '.' (hiện
    dưới 0.5%, chưa về 0%) - đặc biệt trường hợp OCR làm mất hẳn dấu
    phân cách (chưa có giải pháp, xem ADR-052) và ranh giới "cụm cuối
    đúng 3 chữ số" (rủi ro lý thuyết còn tồn, xem ADR-052).
-   Tinh chỉnh `NumberRepair.DECIMAL_TAIL_MAX_LENGTH` (hiện = 3,
    placeholder) và các hằng số `OCR.PREPROCESS_*` khi có thêm dữ liệu
    PDF Scanned đa dạng hơn.

------------------------------------------------------------------------

## 2026-07

### Project Initialization

#### Added

-   Initial project structure
-   `constants.py`
-   `enums.py`
-   `models.py`

#### Decisions

-   Use `dataclass` for data models.
-   Use `Enum` for fixed values.

------------------------------------------------------------------------

### UI Framework

#### Added

-   `base_widget.py`
-   `widgets.py`
-   `main_window.py`

#### Features

-   Input Folder selector
-   Output Excel selector
-   Start / Stop buttons
-   Report / Exit buttons
-   Progress widget
-   Processing table

#### Changed

-   Start / Stop moved above Progress.
-   Report / Exit moved below the Processing Table.

------------------------------------------------------------------------

### Worker Framework

#### Added

-   `worker.py`
-   QThread integration
-   Qt Signal communication
-   Mock processing mode

#### Decisions

-   Worker is responsible for long-running tasks.
-   MainWindow never performs heavy processing.

------------------------------------------------------------------------

### Processing Table

#### Added

-   `ProcessingTableModel`
-   MVC data flow
-   Table reset support (`clear()`)

#### Changed

-   Processing table displays:
    -   PDF
    -   TYPE
    -   STATUS
    -   NOTE

------------------------------------------------------------------------

### Mock Validation

#### Completed

-   Mock PDF generation
-   Progress updates
-   Table updates
-   Start / Stop workflow
-   Worker ↔ UI communication

#### Verified

-   UI remains responsive.
-   QThread works correctly.
-   Results are appended to the table.
-   Mock pipeline is stable.

------------------------------------------------------------------------

## Architecture Milestones

-   Freeze UI layout.
-   Freeze Worker architecture.
-   Freeze `process()` as orchestrator.
-   Freeze `_process_pdf()` as business entry point.
-   Freeze "store in memory, write Excel once" strategy.
-   Freeze one-PDF-at-a-time processing.

------------------------------------------------------------------------

## Known Pending Work

-   Digital PDF reader — **done, see "PDF Reader — Full Implementation" below**
-   OCR reader
-   Regex extraction
-   Excel writer
-   Report exporter
-   ETA calculation
-   Elapsed time calculation

------------------------------------------------------------------------

2026-07
## Architecture Refinement

### Added

- Freeze PDF Reader responsibility.
- Freeze Domain-first implementation strategy.
- Freeze Knowledge Cache architecture.
- Freeze Source Code as the single implementation reference.

### Changed

- PDF processing workflow clarified.
- Development workflow updated.
- Reader/Analyzer responsibilities separated.

## Core

### Added

- Initial implementation of pdf_reader.py.

### Decisions

- Reader maps PyMuPDF objects to domain models only.
- Parser will operate on complete PDFDocument.
- Analyzer will reuse document statistics.

------------------------------------------------------------------------

## 2026-07 (continued)

### PDF Reader — Full Implementation

#### Added

-   `PDFReader.read()` fully implemented: opens PDF via PyMuPDF,
    reads metadata, reads every page and its statistics.
-   `PageStatistics` populated with text length, image count, font
    count, text block count, drawing count, annotation count, page
    size and rotation.

#### Decisions

-   `PDFReader` performs no OCR, parsing, or classification (ADR-016
    confirmed in implementation).

------------------------------------------------------------------------

### Domain Model — Reasoning Engine Support

#### Added

-   `core/enums.py`: `ConfidenceLevel`, `RuleCategory`.
-   `core/models.py`: `Evidence`, `Confidence`, `AnalysisContext`,
    `KnowledgeRecord`, `DocumentAnalysis`, `AnalysisMode` (frozen /
    immutable dataclasses per PDF_Detector_Technical_Design.docx).

#### Decisions

-   `AnalysisContext` and `DocumentAnalysis` are frozen dataclasses;
    collections are recursively frozen via `_freeze_value`.
-   `KnowledgeRecord` remains mutable at the storage layer but is
    treated as read-only during a single analysis (per TDS §9.5,
    DC-004).

------------------------------------------------------------------------

### PDF Detector — Reasoning Engine Implementation

#### Added

-   `core/pdf_detector.py`: full implementation of `PDFDetector`,
    replacing the placeholder/Mock analyzer referenced in earlier
    sessions.
-   Build Context stage (`_build_context`): converts `PDFDocument`
    into an immutable `AnalysisContext` (raw + derived metrics).
-   Heuristic Evaluation stage: 5 rules implemented —
    `text_coverage` (Text), `image_coverage` (Image),
    `mixed_content` (Consistency), `content_coverage` (Quality),
    `page_layout` (Layout). Document and Graphics rule categories
    are not yet implemented.
-   Knowledge Lookup + Confidence Composition
    (`_compose_confidence`): combines evidence-strength,
    consistency, and coverage confidence sources; optionally adjusts
    for a matching/conflicting `KnowledgeRecord`.
-   Deterministic structural fingerprinting (`_fingerprint`) via
    SHA-256 over rounded observed metrics.
-   Final Decision stage: produces an immutable `DocumentAnalysis`
    with reasons, warnings, evidence, and confidence explanation.

#### Decisions

-   Detector never accesses the raw PDF; input is limited to the
    immutable `PDFDocument` from `PDFReader`.
-   Confidence is decision-centric and evidence-driven per TDS
    Chapter 8; no fixed/arbitrary confidence values are assigned.
-   Rule Categories implemented so far: Text, Image, Consistency,
    Quality, Layout. Document and Graphics categories are open
    follow-up work (see Unreleased/Next).

------------------------------------------------------------------------

### Worker — Real Pipeline Integration

#### Changed

-   `Worker._process_pdf()` now calls `PDFReader.read()` and
    `PDFDetector.analyze()` directly — Mock processing mode has been
    replaced by the real pipeline for detection (extraction/parsing/
    Excel writing remain pending).
-   `PDFResult.pdf_type` and `.status` are now derived from
    `DocumentAnalysis.mode` and `.confidence`.

#### Decisions

-   `AnalysisMode.UNKNOWN` maps to `ProcessStatus.WARNING`, not
    `FAILED` — an inconclusive detection is not treated as an error.
-   Exceptions during read/analyze are caught in `_process_pdf()` and
    recorded as `ProcessStatus.FAILED` with the exception message in
    `note`, without stopping the batch (`process()` continues to the
    next file).

------------------------------------------------------------------------

## Known Issues / Open Questions (carried into Unreleased)

-   `core/processor.py` currently contains 4 placeholder calls
    (`start/stop/pause/resume`) with no implementation; actual
    orchestration logic resides in `Worker.process()`. Relationship
    between the two needs clarification (ADR-004 refers to
    `process()` as orchestrator — currently satisfied by
    `Worker.process()`, not `core/processor.py`).
-   Possible import path issues: `core/models.py` uses
    `from enums import ...` and `ui/widgets.py` uses
    `from base_widget import ...` (missing `core.` / `ui.` package
    prefix) — needs verification against actual run configuration.

------------------------------------------------------------------------

## 2026-07-31

### Domain Model — Extractor Support

#### Added

-   `core/models.py`:
    -   Renamed the pre-existing `ExtractionResult` (session-wide
        results: invoices, pdf_results, errors) to `SessionResult` to
        free the name for the Extractor's per-document output.
    -   Added `WordToken` (`text`, `normalized_bbox` in `[0.0, 1.0]`,
        `confidence`, `source`).
    -   Added `PageImage` (`samples`, `width`, `height`, `dpi`) — a
        self-describing wrapper for raw pixmap bytes, avoiding an
        implicit dependency on externally-known render parameters.
    -   Extended `PDFPage` with `words` (raw PyMuPDF word tuples,
        unnormalized) and `page_image` (`PageImage | None`) — both
        additive, default empty/`None`, backward compatible.
    -   Added the new `ExtractionResult` (`source_mode`,
        `words_by_page`, `page_images`, `warnings`) — the Extractor's
        output contract, ready for Parser.

#### Decisions

-   `PDFPage.words` intentionally kept as raw PyMuPDF tuples (not
    `WordToken`) — Reader reads, Extractor normalizes (Single
    Responsibility, RP-001/DP-005).
-   `WordToken.normalized_bbox` uses a `[0.0, 1.0]` scale, chosen to
    stay model-agnostic. A future LayoutLMv3-based Parser (v2.0,
    requiring `[0, 1000]`) will convert at the point of consumption,
    not in the domain model (Domain-Oriented Design, DP-009).

------------------------------------------------------------------------

### PDF Reader — Word and Page Image Extraction

#### Added

-   `core/constants.py`: added `Image` class (`DPI = 300`,
    `COLORSPACE = "gray"`).
-   `core/pdf_reader.py`:
    -   `_read_pages()` return type corrected to
      `tuple[PDFPage, ...]` (was `list[PDFPage]`), matching
      `PDFDocument.pages`'s declared type.
    -   `_read_page()` now also reads `page.get_text("words")` into
        `PDFPage.words`, for every page regardless of detected type
        (Reader does not classify — Observation/Reasoning separation,
        TDS §4.1).
    -   Added `_render_page_image()`: renders every page to a raw
        grayscale pixmap via
        `page.get_pixmap(dpi=Image.DPI, colorspace=fitz.csGRAY)`,
        stored as `PageImage`.

#### Decisions

-   `page_image` is rendered eagerly for every page (not lazily on
    OCR demand). Accepted memory cost: a single `PDFDocument` is
    released immediately after `_process_pdf()` returns (ADR-007),
    so eager rendering does not violate the "Memory First" principle
    at the batch level.
-   Raw pixmap samples (uncompressed), grayscale, 300 DPI — chosen
    over PNG-encoded storage for OCR-readiness at the cost of larger
    in-memory footprint per page (~8.3 MB/page at A4/300 DPI,
    grayscale, uncompressed).

------------------------------------------------------------------------

### Extractor — New Module

#### Added

-   `core/extractor.py`: `Extractor` class.
    -   `extract(document, analysis)` dispatches per
        `analysis.mode`: `DIGITAL` uses `page.words` directly;
        `SCANNED` uses `OCREngine`; `HYBRID` decides per page
        (`page.has_text` → Digital path, else OCR path — single
        source per page, see Known Limitations below); `UNKNOWN`
        raises `ValueError` (Extractor must not be called for this
        mode — see Worker integration below).
    -   `_rotate_bbox()`: reconciles `get_text("words")`'s unrotated
        coordinate frame with the rotated/visual frame used by
        `page.statistics.width/height` (sourced from `page.rect`).
        Applies only to the Digital path.
    -   `_normalize_bbox()`: single, shared normalization function
        for both Digital and OCR sources, taking explicit reference
        width/height rather than assuming a source.
-   `core/ocr_engine.py`: `OCREngine` class (Mock, per ADR-013).
    `recognize(page_image)` returns raw, un-normalized OCR output
    (`(x0, y0, x1, y1, text, confidence)` tuples); currently always
    returns an empty tuple — no real OCR backend is wired in yet.

#### Decisions

-   OCR path applies **no** rotation transform: PyMuPDF's
    `get_pixmap()` renders according to `page.rect` (i.e., already
    reflects page rotation), so `page_image` and any OCR bbox derived
    from it already share the same, rotated reference frame as
    `page_image.width/height`. Applying `_rotate_bbox()` to OCR
    output would double-rotate and produce incorrect results.
-   `OCREngine` returns raw output symmetric to `PDFReader` (no
    normalization) — `Extractor` remains the single place where
    geometry is normalized for both sources.
-   `Extractor.extract()` raises `ValueError` if called with
    `AnalysisMode.UNKNOWN` — this is a programming-contract violation
    (the caller must filter `UNKNOWN` before invoking), not a
    business-level warning; contrasts with how `UNKNOWN` is handled
    one layer up, in `Worker` (see below).

#### Known Limitations (deferred to v2.0)

-   Pages with both text and images (`mixed_page_ratio` > 0) are
    routed to a single source per page (text-layer wins if present).
    Image content on such pages is currently dropped. A dual-source
    approach was discussed and intentionally deferred — see
    SESSION_SUMMARIES.md, Session 2026-07-31, for the three options
    considered and the open sub-problem (bbox-overlap deduplication)
    it would require.

------------------------------------------------------------------------

### Worker — Extractor Integration

#### Changed

-   `ui/worker.py`:
    -   `Worker.__init__` now constructs an `Extractor` instance.
    -   `Worker._process_pdf()` calls `self._extractor.extract()`
        only when `analysis.mode is not AnalysisMode.UNKNOWN` —
        `UNKNOWN` is treated as "no decision was made," so Extractor
        is not invoked at all, per the pipeline principle that a
        decision is made once and reused downstream (TDS §3.1).
        Wrapped in its own `try/except`, separate from the
        Reader/Detector block, so an Extractor failure is reported
        distinctly from a Read/Detect failure.
    -   `_format_analysis_note()` renamed to `_format_note()`, now
        takes both `analysis` and `extraction` (`ExtractionResult |
        None`). Displays the "highest-level" warning first
        (`extraction.warnings[0]` if present, else
        `analysis.warnings[0]`) — a deliberately simple, single-line
        summary for the UI table; full traceability is achieved
        through the pipeline's determinism (re-running the same file
        reproduces the same `DocumentAnalysis`/`ExtractionResult`),
        not through persisted state.

------------------------------------------------------------------------

### PDF Detector — Type Hint Fix

#### Fixed

-   `core/pdf_detector.py`: `_unique_strings()` parameter type
    changed from `object` to `Iterable[str]` (added
    `from collections.abc import Iterable`), matching actual usage
    (`dict.fromkeys(values)`) and eliminating a static type-checker
    warning at the function definition.

------------------------------------------------------------------------

### PDF Reader — Type Hint Fix

#### Fixed

-   `core/pdf_reader.py`: `_read_pages()` return type corrected from
    `list[PDFPage]` to `tuple[PDFPage, ...]`, matching
    `PDFDocument.pages`'s declared (and enforced, via
    `__post_init__`) type.

------------------------------------------------------------------------

## 2026-08-01 / 2026-08-02

### Parser — Full Implementation (Template Matching Engine)

#### Added

-   `core/enums.py`: added `ValueType`, `SpatialDirection`.
-   `core/models.py`:
    -   `InvoiceInfo` fields (except `source_file`) changed to `Optional`,
        defaulting to `None` — see ADR-032.
    -   Added `SpatialRelation`, `FieldDefinition`, `TemplateDefinition`,
        `TemplateSelection` (frozen dataclasses; `FieldDefinition`
        validates `field_name` against `InvoiceInfo`'s actual fields at
        construction time).
-   `core/constants.py`: added `Logging` (logging format/level) and
    `TemplateMatching` (`LINE_Y_TOLERANCE`, `WORD_GAP_TOLERANCE`,
    `MAX_KEY_WORDS`, `TEMPLATE_TIE_MARGIN`, `TEMPLATE_MIN_SCORE`) — all
    placeholder values, flagged for tuning once real invoice PDFs are
    available.
-   `utils/logger.py`: minimal shared logger (`get_logger()`), console
    handler, configured once (root logger), used by `TemplateLoader`.
-   `core/value_converter.py`: `ValueConverter` — stateless TEXT/DECIMAL/
    DATE conversion, never raises (returns `None` on failure).
-   `core/template_loader.py`: `TemplateLoader` — reads all `*.json` under
    a directory, validates, builds `TemplateDefinition`; invalid files are
    skipped with a logged warning (fail-soft per file, not per batch).
-   `core/template_matcher.py`: `TemplateMatcher` — full Key Matching
    (Line/Phrase Clustering + diacritics-normalized rapidfuzz matching) →
    Template Scoring/Decision (Evidence-weighted, tie margin) → Windowing
    (directional search box from `SpatialRelation`) → Value Matching
    (regex + nearest-to-key tie-break).
-   `core/parser.py`: `Parser` — thin orchestrator; `parse()` returns
    `InvoiceInfo | None` (`None` when no template is confidently selected,
    ADR-033).
-   `config.py`: added `TEMPLATES_DIR`.
-   `resources/templates/`: new directory for Template Definition JSON
    files (sample template added for local testing; production templates
    still pending real invoice samples).

#### Changed

-   `core/extractor.py`: `_extract_digital_page()`/`_extract_ocr_page()`
    now also normalize token text whitespace (strip + collapse internal
    whitespace); empty-after-normalize tokens are dropped. See ADR-036.
-   `ui/worker.py`: `Worker.__init__` now constructs `TemplateLoader` +
    `TemplateMatcher` + `Parser`. `Worker._process_pdf()` calls
    `Parser.parse()` (own try/except block, consistent with
    Reader/Detector/Extractor) and assigns `result.invoice`. A `Parser`
    exception -> `ProcessStatus.FAILED` (same as other stages); `Parser`
    returning `None` -> `PDFResult.status`/`.note` untouched (ADR-033).

#### Decisions

-   Template Selection reuses `PDFDetector`'s Evidence → Score → Decision
    pattern (ADR-030), scored over the full document (all pages), not a
    restricted region.
-   `re.compile()` for `value_pattern` is cached inside `TemplateMatcher`,
    not stored on `FieldDefinition` — keeps `core/models.py`'s existing
    "no Regex" rule intact (ADR-031).
-   Vietnamese diacritics are stripped before fuzzy key matching
    (ADR-035) — without this, key matching silently fails whenever
    template `key_tokens` and actual PDF text differ in diacritics
    (including the realistic OCR-drops-diacritics case).
-   Neither a `None` field inside `InvoiceInfo` nor `Parser.parse()`
    returning `None` entirely affects `PDFResult.status`/`.note` — both
    are Report-only concerns (ADR-033), since the underlying cause
    (missing/wrong template vs. bad PDF vs. wrong file) cannot be
    reliably distinguished by the pipeline itself.

#### Known Limitations (found during empirical testing, deferred)

-   **Value Matching captures a single `WordToken` only.** Fields whose
    real value spans multiple words (company name, address) are
    truncated to the nearest single token to the matched key. Ghép cụm
    nhiều từ cho Value (không chỉ Key) cần thiết kế thêm — deferred,
    cần thảo luận riêng.
-   **Template authoring guidance needed (no code fix — operational
    rule):** single-word `key_tokens` (e.g. `"so"`) are prone to
    false-positive matches against unrelated occurrences of the same word
    elsewhere in the document (confirmed empirically: a generic
    `key_tokens` entry matched the wrong table row). Template authors
    should avoid single-word `key_tokens` unless the word is reliably
    unique to the intended field's context.
-   **`value_pattern` should exclude punctuation-only tokens (no code
    fix — operational rule):** an overly permissive pattern (e.g. `.+`)
    can match a stray punctuation token (e.g. `":"`) sitting closer to
    the key than the real value, since Value Matching tie-breaks by
    distance. Template authors should write patterns that require at
    least one alphanumeric character (e.g. `.*[^\s:.,\-].*`).
-   `LINE_Y_TOLERANCE`, `WORD_GAP_TOLERANCE`, `MAX_KEY_WORDS`,
    `TEMPLATE_TIE_MARGIN`, `TEMPLATE_MIN_SCORE` (all in
    `core/constants.py::TemplateMatching`) are placeholder values pending
    tuning against real invoice PDFs.
-   `resources/templates/sample_invoice_v1.json` intentionally still
    contains the two issues above (short `key_tokens`, loose
    `value_pattern`) — left as-is per explicit decision, to be corrected
    once real invoice data is available rather than fixed speculatively.
-   No formal "how to write a Template JSON" guidance document exists
    yet — needed before non-developers or other contributors author
    templates. See Next Tasks.

------------------------------------------------------------------------

## 2026-08-03

### ExcelWriter / ReportWriter — Full Implementation

#### Added

-   `core/models.py`: added `ExcelMapping` (frozen dataclass: `table`,
    `columns`), `InvoiceWarning` (`source_file`, `field_name`),
    `ExcelWriteResult` (`total`, `written`, `warnings`, `errors`).
-   `resources/excel_mapping.json`: sample Excel column mapping
    (`tblInvoices` Table, 8 columns → `InvoiceInfo` fields).
    `config.py`: added `EXCEL_MAPPING_PATH`.
-   `core/excel_mapper.py`: `Mapper` — loads/validates
    `excel_mapping.json` into `ExcelMapping`; raises `MappingError` on
    any error (fail-fast, unlike `TemplateLoader`'s fail-soft — see
    ADR-038). Validates every mapped `field_name` against
    `dataclasses.fields(InvoiceInfo)`.
-   `core/excel_writer.py`: `ExcelWriter.write(path, invoices, mapping)`
    — writes `list[InvoiceInfo]` into an existing Excel Table
    (openpyxl), expanding `table.ref` as rows are appended. Returns
    `ExcelWriteResult` (pure data — ADR-006). Three exception classes:
    `WorkbookNotFoundError`, `ExcelTableNotFoundError`,
    `WorkbookSaveError`. Column-mapping mismatches against the actual
    workbook header are soft-failed into `ExcelWriteResult.errors`,
    not raised (ADR-039).
-   `core/constants.py`: `Logging` extended (`FILE_NAME` was already
    present; now actually used). `config.py`: added `LOG_DIR`,
    `REPORTS_DIR`.
-   `utils/logger.py`: `_configure_root()` now also attaches a
    `FileHandler` (`logs/app.log`, UTF-8 — ADR-014) alongside the
    existing console `StreamHandler`. Still configured exactly once
    (`_CONFIGURED` guard unchanged).
-   `core/report_writer.py`: `ReportWriter.write(results, excel_result)`
    — two fully separate output channels (ADR-040): `list[PDFResult]`
    logged via `utils/logger.py` (dev/admin, accumulates across runs);
    `ExcelWriteResult` formatted into `reports/Report.txt`
    (end-user, overwritten every run).
-   `requirements.txt` (project root): pins `PySide6==6.11.1`,
    `PyMuPDF==1.28.0`, `rapidfuzz==3.14.5`, `openpyxl==3.1.5` —
    versions confirmed working via this session's test suite.
    Resolves the missing-dependency-file issue open since Session
    2026-08-01/02.

#### Changed

-   `ui/worker.py`: `Worker.__init__` now constructs real
    `ExcelWriter()` and `ReportWriter(REPORTS_DIR)` instances (previously
    `None` placeholders); added `self._report_path` and the
    `report_path` property. `Worker._write_excel()` implemented
    (previously `pass`): loads `ExcelMapping` lazily (not in
    `__init__` — see ADR-038), calls `ExcelWriter.write()`, catches
    `MappingError`/`WorkbookNotFoundError`/`ExcelTableNotFoundError`/
    `WorkbookSaveError` and emits the (previously unused) `error`
    Signal on failure, then always calls `ReportWriter.write()`
    regardless of success/failure.
-   `ui/main_window.py`: `_connect_signals()` now connects
    `self._worker.error` to a new `on_worker_error()` slot (previously
    unconnected since the signal's original declaration).
    `_report()` reimplemented (ADR-041): no longer shows a "pending"
    placeholder message — opens `Worker.report_path` via
    `QDesktopServices.openUrl()` if available, otherwise shows
    `REPORT_NOT_AVAILABLE`; shows `REPORT_OPEN_FAILED` if the OS
    fails to open the file.
-   `core/constants.py::UIText`: added `REPORT_NOT_AVAILABLE`,
    `REPORT_OPEN_FAILED`, `ERROR_TITLE`. (`REPORT_PENDING` left in
    place but is now dead code — see Unreleased/Next.)

#### Decisions

See `ARCHITECTURE_DECISIONS.md` ADR-037 through ADR-041 for full
rationale. Summary:

-   `ExcelWriter` and `ReportWriter` are two independent modules with
    no dependency on each other — not a single combined
    `ReportService` (an earlier design draft was rejected during
    discussion; see Session 2026-08-03 in SESSION_SUMMARIES.md).
-   `Mapper` fails fast (raises), unlike `TemplateLoader`'s fail-soft
    — there is no "partially valid" concept for a single mapping file
    that is the sole precondition for any Excel write.
-   Column-level mismatches between mapping and the real workbook are
    a soft failure (`ExcelWriteResult.errors`), not a hard raise —
    other valid columns still get written.
-   `report.txt` is generated automatically at the end of every
    `process()` run (same timing as the Excel write, ADR-008) — the
    Report button only opens the already-generated file, it never
    triggers generation.
-   `list[PDFResult]` (dev/admin) and `ExcelWriteResult` (end-user)
    are logged/reported through two entirely separate channels with
    no content mixing.

#### Testing (this session)

All 8 implementation steps were verified against the actual GitHub
source (`https://github.com/minhquipk/PDF2Excel`, cloned and reviewed
file-by-file before testing — confirmed byte-for-byte match with what
had been agreed during design discussion) using automated
scripted tests (not a full manual UI run):

-   `core/models.py` new dataclasses: frozen/immutable behavior,
    collection freezing — verified.
-   `core/excel_mapper.py`: happy path + 5 distinct error cases (file
    not found, bad JSON syntax, missing required key, invalid
    `field_name`, empty `columns`) — all raise `MappingError`
    correctly.
-   `core/excel_writer.py`: happy path (2 invoices, `None`-field
    warnings, Excel Table `ref` correctly expanded) — verified.
    `WorkbookNotFoundError`, `ExcelTableNotFoundError`, and
    column-mismatch soft-fail into `errors` — all verified.
    `WorkbookSaveError` — **could not be verified**; the test
    container runs as root, bypassing OS file-permission checks. The
    exception-handling code path is logically sound (catches
    `OSError`, a parent of `PermissionError`) but this specific
    failure mode remains unverified against a real permission denial.
    Flagged for manual verification (see Unreleased/Next).
-   `utils/logger.py`: `FileHandler` creates `logs/app.log`
    correctly, no duplicate handlers across repeated `get_logger()`
    calls, UTF-8 Vietnamese text preserved — verified.
-   `core/report_writer.py`: `report.txt` overwritten each run;
    `logs/app.log` accumulates (append) each run; correct log level
    (`WARNING` for `WARNING`/`FAILED` statuses, `INFO` otherwise) —
    verified.
-   `ui/worker.py::_write_excel()`: happy path and `MappingError`
    error path (via a deliberately broken `EXCEL_MAPPING_PATH`) —
    both verified, including correct `error` Signal emission and
    `report.txt` still being generated on failure.
-   `ui/main_window.py::_report()`: all 4 UI branches (no report yet,
    report opens successfully, OS fails to open, `error` Signal →
    warning popup) — verified via mocked `QMessageBox`/
    `QDesktopServices` calls under `QT_QPA_PLATFORM=offscreen`.
-   Full pipeline regression: a real minimal PDF was generated via
    PyMuPDF and run through the complete
    Reader→Detector→Extractor→Parser→ExcelWriter→ReportWriter chain
    with no crash (invoice fields came back `None`, as expected —
    the test PDF's content does not match the sample template, which
    is a data issue, not a code defect).

Not covered this session: a real, manual, UI-driven run against real
sample invoice PDFs (Input Folder → Start → Report, clicked by a
human through the actual running application). This is the explicit
plan for the next session (see Unreleased/Next and
PROJECT_CONTEXT.md §15).

------------------------------------------------------------------------

## 2026-08-07

### excel_mapping.json — Thảo luận thiết kế (không đổi schema)

#### Quyết định

-   Cân nhắc thêm trường `sheet` vào `ExcelMapping` để chỉ rõ Excel
    Table nằm ở sheet nào - **rút lại đề xuất** sau khi phân tích
    `ExcelWriter._find_table()`: hàm này đã duyệt toàn bộ sheet để tìm
    Table theo tên, và Excel tự đảm bảo tên Table duy nhất trong toàn
    workbook, nên `sheet` là dư thừa cho mục đích tìm kiếm (xem
    ADR-042).

#### Added

-   `resources/EXCEL_MAPPING_GUIDE.md` - hướng dẫn viết `excel_mapping.json`
    cho người điều hành (không yêu cầu biết lập trình): yêu cầu Excel
    Table thật (không phải range), cấu trúc JSON, danh sách field hợp
    lệ của `InvoiceInfo` kèm kiểu dữ liệu, quy tắc đặt tên cột, bảng
    phân loại lỗi (fatal / soft-fail / warning) kèm nơi xem kết quả,
    checklist trước khi chạy thật.

### sample_invoice_v1.json — Kiểm thử thực nghiệm toàn diện trên PDF thật

dùng cung cấp PDF hóa đơn thật (`HD2026-0003_digital.pdf`, PDF
Digital). Toàn bộ phần việc dưới đây được kiểm chứng bằng cách dựng lại
các module liên quan (`pdf_reader`, `extractor`, `template_matcher`,
`value_converter`) trong môi trường sandbox và chạy thật trên file này,
không suy đoán tĩnh - đúng tinh thần đã thiết lập từ các phiên trước.

#### Fixed (lỗi rõ ràng, đối chiếu trực tiếp với text PDF thật)

-   `company_name`: `key_tokens` sai (`"ten don vi ban"` → PDF thật ghi
    "Tên công ty:") → sửa thành `["ten cong ty"]`.
-   `invoice_number`: `value_pattern` chỉ cho số thuần, số hóa đơn thật
    có chữ + gạch ngang (`"HD2026-0003"`) → sửa pattern.
-   `invoice_date`: `key_tokens` sai (`"ngay lap hoa don"` → PDF chỉ ghi
    "Ngày:") → sửa thành `["ngay"]`.
-   `total_amount`: `spatial_relation.direction` sai (`"Below"` → giá
    trị thật nằm cùng dòng bên phải) → sửa thành `"Right"`.
-   `vat_rate`: `value_pattern` không cho phép `%` (giá trị thật dính
    liền `"5%"`) → sửa pattern + patch `value_converter.py` (xem dưới).

#### Fixed (phát hiện mới qua thực nghiệm, không thấy được nếu chỉ review tĩnh)

-   `axis_tolerance` mặc định (0.02-0.05) quá lớn so với khoảng cách
    dòng thật đo được trên PDF (~0.0168-0.0202) → window "Right"/"Below"
    tràn sang dòng liền kề (VD `buyer_name` từng ra `'mua:'` sai dòng).
    Hạ đồng loạt xuống `0.006`.
-   `max_distance` của 4 field tiền tệ quá nhỏ (0.1-0.2) so với khoảng
    cách thật giữa nhãn (sát lề trái) và số tiền (căn phải, x≈0.78-0.92)
    → field ra `None`. Tăng lên `0.85`.
-   Định dạng số của riêng file PDF test dùng dấu phẩy ngăn hàng nghìn
    (`"19,188,159"`), ngược mặc định VN (`.` ngăn nghìn) trong
    `value_converter.py`. Xác nhận đây là quirk của data test (không
    đại diện hóa đơn VN thật) - khai `decimal_format` override riêng
    cho 3 field tiền tệ trong `sample_invoice_v1.json`, KHÔNG đổi mặc
    định toàn cục.

#### Added — `core/value_converter.py`

-   `_to_decimal()` strip ký tự `%` cuối chuỗi trước khi parse `Decimal`
    (xem ADR-043).

#### Added — `core/template_matcher.py` (Value Matching nhiều từ)

-   `_select_best_value()` + `_merge_same_line()` mới: ghép nhiều
    `WordToken` liền kề cùng dòng thành 1 giá trị cho field `Text`
    (gap-based, tái dùng `LINE_Y_TOLERANCE`/`WORD_GAP_TOLERANCE`), dừng
    mở rộng khi gặp token kết thúc bằng `:` (xem ADR-044). Giải quyết
    triệt để giới hạn "chỉ lấy 1 WordToken" đã ghi từ Session
    2026-08-01/02.

#### Added — Section (giải quyết va chạm key_tokens giữa các khối tài liệu)

-   `core/models.py`: `SectionDefinition` mới; `FieldDefinition` thêm
    field bắt buộc `section: str`; `TemplateDefinition` thêm `sections`
    kèm validate `field.section` phải khớp 1 `section_id` đã khai.
-   `core/template_matcher.py`: `_find_key_match()` refactor tách khỏi
    `FieldDefinition`, nhận `key_tokens`/`fuzzy_threshold`/`tie_margin`
    trực tiếp - dùng chung cho Field (tie_margin=None, hành vi cũ không
    đổi) và Section (tie_margin bắt buộc). Thêm `_resolve_sections()`,
    `_filter_phrases_by_range()`. `_score_template()` nay giới hạn
    phạm vi Key Matching của mỗi field trong đúng section đã khai.
-   `core/template_loader.py`: parse `sections` + `field.section` từ
    JSON (`_build_section()` mới, `_build_field()` thêm `section`).
-   `core/constants.py`: thêm `TemplateMatching.SECTION_TIE_MARGIN = 10`
    (thang 0-100 của `rapidfuzz.fuzz.ratio()`, khác thang với
    `TEMPLATE_TIE_MARGIN`).
-   Giải quyết 2 Known Limitation cùng gốc rễ (xem ADR-045):
    -   `tax_code` từng bị lấy nhầm MST bên mua (va chạm key ở tầng
        Key Matching toàn cục).
    -   `invoice_date` từng phụ thuộc may rủi thứ tự xuất hiện trong
        tài liệu để thắng tie giữa 3 vị trí khớp cùng ratio.

#### sample_invoice_v1.json — version 2 → 3

-   Thêm 4 field mới: `address`, `buyer_name`, `buyer_tax_code`,
    `payment_method` (field đã tồn tại sẵn trong `InvoiceInfo`, trước
    đó chưa được khai trong template).
-   Thêm `sections`: `header` (khối ảo từ đỉnh trang, không cần marker),
    `seller` (key "don vi ban hang"), `buyer` (key "thong tin nguoi
    mua" - CHÚ Ý: không phải 5 từ đầy đủ "thong tin nguoi mua hang", vì
    vượt `MAX_KEY_WORDS=4`, xem ADR-045), `detail` (key "chi tiet thanh
    toan"). Mỗi field gán đúng 1 `section`.
-   `buyer_tax_code` nay dùng lại đúng `key_tokens=["ma so thue"]` giống
    `tax_code` (trước đó cần `key_tokens=["ma so thue mua"]` riêng để
    né va chạm) - đơn giản hóa nhờ Section tự phân biệt theo khối.

#### Testing (phiên này)

Toàn bộ thay đổi trên được verify bằng chạy thật, không phải review
tĩnh, trên `HD2026-0003_digital.pdf`: dựng lại `PDFReader`, `Extractor`
(Digital path), `TemplateMatcher`, `ValueConverter` trong sandbox, chạy
`select_template()` + `extract_fields()` + `ValueConverter.convert()`
đầy đủ. Kết quả cuối: **12/12 field ra đúng giá trị** so với nội dung
PDF gốc.

#### Known Limitations còn lại (chưa xử lý, ghi nhận rõ để phiên sau)

-   Gap-based Value merge (ADR-044) có thể tràn sang field khác nếu
    nhãn liền kề KHÔNG kết thúc bằng dấu `:` - chưa gặp trên data thật
    hiện có, nhưng là giới hạn cố hữu chưa loại bỏ hoàn toàn.
-   Section header (ADR-045) vẫn có thể va chạm về lý thuyết nếu 2
    section dùng `key_tokens` gần giống nhau - rủi ro giảm mạnh nhưng
    không bằng 0.
-   `SECTION_TIE_MARGIN = 10` là placeholder, cần tinh chỉnh khi có
    thêm mẫu hóa đơn thật.
-   `FieldDefinition.section` nay là bắt buộc - MỌI template JSON khác
    ngoài `sample_invoice_v1.json` (nếu phát sinh sau này) đều phải
    khai `section`, nếu không sẽ bị `TemplateLoader` skip fail-soft
    (thiếu key → `KeyError`, xử lý như lỗi schema khác theo ADR-031).

------------------------------------------------------------------------

## 2026-08-08 / 2026-08-09

### First Real UI Run

- Thực hiện lượt chạy UI thật đầu tiên (Input Folder -> Start ->
  Report) qua ứng dụng thật, hoàn thành bước 3 trong kế hoạch 5 bước ở
  PROJECT_CONTEXT.md §15 (trước đó chỉ verify qua script sandbox).

### OCR Engine — Real Backend (Thay thế Mock, ADR-013)

Xem ARCHITECTURE_DECISIONS.md ADR-047 (lịch sử lựa chọn đầy đủ: PaddleOCR
-> RapidOCR -> Tesseract), ADR-048 (RGB render), ADR-049 (deskew),
ADR-050 (app.log). Tóm tắt các thay đổi cuối cùng còn lại trong source:

#### Added
- `core/ocr_engine.py`: implement thật bằng Tesseract 5.x + tessdata_best
  (qua `pytesseract`). Fail-fast kiểm tra `vie.traineddata` tồn tại tại
  `TESSDATA_DIR`. Tự triển khai deskew (cv2, giữ nguyên canvas, ngưỡng
  `DESKEW_MIN_ANGLE`/`DESKEW_MAX_ANGLE`).
- `config.py`: thêm `TESSDATA_DIR` (`resources/tessdata_best/`).
- `core/constants.py::OCR`: viết lại cho Tesseract (`LANG="vie"`,
  `PSM=3`, `OEM=3`, `DESKEW_MIN_ANGLE=0.5`, `DESKEW_MAX_ANGLE=10.0`).
- `requirements.txt`: `pytesseract==0.3.13`.
- `core/models.py::PageImage`: thêm field `channels: int = 3`.

#### Changed
- `core/pdf_reader.py::_render_page_image()`: `fitz.csGRAY` ->
  `fitz.csRGB` (ADR-048).
- `core/constants.py::Image.COLORSPACE`: `"gray"` -> `"rgb"`.

#### Removed (không còn trong source cuối cùng, nhưng ghi nhận đã thử qua)
- PaddleOCR-based `ocr_engine.py` (loại bỏ do xung đột `paddlepaddle`
  PIR - GitHub Issue #18162).
- RapidOCR-based `ocr_engine.py` (loại bỏ do chất lượng nhận dạng tiếng
  Việt kém - xác nhận qua debug thật, không phải bug code).

### Bug Fixes phát sinh trong quá trình triển khai (đã sửa)

- RapidOCR: `Det.model_type`/`Rec.model_type` phải là `Enum`
  (`ModelType`), không phải string - sửa lỗi
  `TypeError: The value of Det.model_type must be Enum Type.`
- RapidOCR: `onnxruntime` không được khai báo dependency chính thức -
  thêm dòng riêng vào `requirements.txt`; hạ version `1.24.4` ->
  `1.23.2` do không có wheel cho macOS Intel.
- RapidOCR: lỗi lazy loading tự triển khai (`recognize()` gọi thẳng
  `self._ocr(...)` thay vì `self._get_ocr()(...)`) - sửa
  `TypeError: 'NoneType' object is not callable`.
- Tesseract: `_estimate_skew_angle()` nhầm trang A4 dọc thành góc
  nghiêng ~90° (minAreaRect toàn trang không phù hợp tài liệu nhiều
  khối) - gây `_deskew` xoay ngang toàn trang, làm hỏng vị trí mọi
  `WordToken`, khiến `TemplateMatcher.select_template()` thất bại toàn
  bộ (triệu chứng ban đầu tưởng là lỗi ở Parser/TemplateMatcher, thực
  chất bắt nguồn từ OCREngine). Sửa bằng `DESKEW_MAX_ANGLE=10.0` (ADR-049).

### Known Issue mới phát hiện (chưa sửa, ghi nhận)

- `ui/worker.py::Worker._format_note()` chọn warning đầu tiên theo thứ
  tự rule chạy trong `PDFDetector._evaluate_rules()` (luôn là
  `text_coverage`), không phải warning liên quan nhất đến quyết định
  cuối cùng - có thể hiển thị cảnh báo "bằng chứng yếu" (VD "Absence of
  text alone does not prove OCR is required") cạnh 1 kết luận High
  confidence, gây cảm giác mâu thuẫn dù dữ liệu không sai. Chưa sửa,
  chờ thảo luận riêng (ngoài phạm vi phiên OCR này).

### UI / Logging Behavior Changes (đã áp dụng, ghi nhận theo mô tả -
### CHƯA verify qua source thật, xem ghi chú)

- `utils/logger.py`: `app.log` đổi từ tích luỹ (append) sang ghi đè mỗi
  lần chạy (ADR-050, amend ADR-040).
- `models/processing_table_model.py`: hiển thị kết quả trên UI
  (Processing Status) đổi từ append sang **prepend** (kết quả mới nhất
  hiển thị đầu bảng thay vì cuối bảng).
- Elapsed/ETA: đã hoàn thiện (trước đó là Known Issue "not implemented"
  từ nhiều phiên trước - xem PROJECT_CONTEXT.md §14).

------------------------------------------------------------------------

## 2026-08-12 — Đóng v1, Part 1/3: Xử lý Known Issues từ nhật ký

### Removed
- `core/processor.py` — xóa hoàn toàn (dead code: 4 lời gọi top-level
  tham chiếu biến `processor` chưa từng định nghĩa, NameError nếu bị
  import/exec; không được reference ở bất kỳ đâu trong source thật).
  Vai trò orchestrator (ADR-004) xác nhận chính thức thuộc về
  `Worker.process()`, đóng câu hỏi mở từ Session 2026-07-29.
- Dead code trong `core/constants.py`: `UIText.REPORT_PENDING`,
  `FileDialog.PDF_FILTER`, `FileDialog.ALL_FILES`,
  `UIText.READY`/`PROCESSING`/`COMPLETED`/`CANCELLED`, `Report.FOLDER`
  — xác nhận không được reference ở bất kỳ đâu qua rà soát toàn bộ
  source.
- `core/models.py::ExtractionResult.warnings` — field không còn nơi
  nào gán giá trị khác rỗng sau khi `Extractor.extract()` đổi sang
  `raise ValueError` cho UNKNOWN (xem ADR-056).

### Fixed
- `core/extractor.py::Extractor.extract()` nay thật sự `raise
  ValueError` khi `analysis.mode is AnalysisMode.UNKNOWN`, khớp lại mô
  tả đã có từ đầu trong ADR-027 (source trước đây trả về gracefully,
  sai lệch với tài liệu — xem ADR-056).
- `Worker._format_note()`: warning hiển thị lên UI nay ưu tiên theo
  `RuleCategory` (QUALITY/LAYOUT/DOCUMENT/GRAPHICS trước
  CONSISTENCY/IMAGE/TEXT) thay vì luôn lấy warning của rule chạy đầu
  tiên (`text_coverage`) — xem ADR-055. Dọn kèm nhánh
  `extraction.warnings` chết (không bao giờ chạy tới trong pipeline
  thật).

### Added
- `resources/TEMPLATE_AUTHORING_GUIDE.md` — đóng Known Issue mở từ
  Session 2026-08-01/02.
- `tests/core/test_extractor.py` — unit test đầu tiên của dự án (9 test
  case cho `Extractor._rotate_bbox()`), `requirements-dev.txt`
  (`pytest==8.3.4`). `tests/core/` là chuẩn cấu trúc test cho các
  module khác sau này.
- `core/pdf_detector.py`: 2 rule mới — `_evaluate_document_rule()`
  (category `DOCUMENT`, RC-001) và `_evaluate_graphics_rule()`
  (category `GRAPHICS`, RC-004) — hoàn thiện đủ 7/7 Rule Category theo
  TDS §7.2 (trước đó 5/7). Xem ADR-057 cho thiết kế đầy đủ và giới hạn
  đã biết (chưa qua thực nghiệm dữ liệu thật đa dạng).

### Changed
- `main.py`: nay chứa khối `if __name__ == "__main__":` (trước đây
  rỗng) — trở thành entry point thật duy nhất của ứng dụng.
  `ui/main_window.py`: xóa khối `__main__` tương ứng, không còn chạy
  được độc lập. Đóng discrepancy mở từ Session 2026-07-29.

### Verified
- `core/excel_writer.py::WorkbookSaveError` — tái hiện thành công lỗi
  permission thật trong sandbox Linux bằng kỹ thuật `chattr +i`
  (immutable attribute, chặn được cả root — khác các lần thử `chmod`
  trước đây không hiệu quả với container chạy root). Xác nhận
  `except OSError` bắt đúng `PermissionError`, bọc đúng thành
  `WorkbookSaveError`, không leak exception gốc. Đồng thời verify UX
  trên môi trường Windows thật (người dùng tự test): popup
  `QMessageBox.warning` hiển thị đúng, ứng dụng không treo. Đóng Known
  Issue mở từ Session 2026-08-03.

### Next
- Đóng v1 Part 2/3: xử lý vấn đề do người dùng tự ghi nhận (chưa bắt
  đầu).
- Đóng v1 Part 3/3: xử lý vấn đề phát sinh khi quét trực tiếp mã nguồn
  (chưa bắt đầu).
- Sau khi hoàn tất cả 3 Part: `resources/excel_mapping.json` khớp
  workbook thật + tài liệu hướng dẫn cài đặt OCR cho end-user, thực
  hiện trong giai đoạn làm tài liệu chuyển giao ứng dụng (đã quyết
  định hoãn, không thuộc phạm vi đóng v1 code).

------------------------------------------------------------------------

## 2026-08-13 — Đóng v1, Part 2/3: Xử lý vấn đề người dùng tự ghi nhận

### Fixed
- `models/processing_table_model.py` (nay `ui/models/processing_table_model.py`)::`ProcessingTableModel.data()`
  cột PDF: hiển thị `relative_path` thay vì `file_name`, tránh trùng
  tên khi Input Folder chứa nhiều thư mục con lồng nhau (VD "Quý 3" ->
  "Tháng 7/8/9", mỗi thư mục có file trùng tên). Xem ADR-058.
- `core/report_writer.py` (nay `core/export/report_writer.py`)::`ReportWriter._log_results()`:
  log `relative_path` thay vì `file_name`. `_format_report()` mục
  Warnings: bỏ cắt `.name`, giữ nguyên full absolute path của
  `warning.source_file`. Xem ADR-058.

### Changed
- **Tái cấu trúc toàn bộ `core/` theo pipeline stage**
  (`domain/`, `reading/`, `detection/`, `extraction/`, `parsing/`
  + `parsing/template/`, `export/`), đổi `models/` top-level thành
  `ui/models/`. Triển khai theo 7 bước tuần tự, mỗi bước verify độc
  lập (`pytest -v` + chạy thật). Không đổi hành vi hệ thống, chỉ đổi
  vị trí file + đường dẫn import. Xem ADR-060, PROJECT_CONTEXT.md §3.
- `tests/core/test_extractor.py` di chuyển thành
  `tests/core/extraction/test_extractor.py`, mirror cấu trúc `core/`
  mới.

### Verified
- Memory lifecycle review: xác nhận `fitz.Document` đóng đúng qua
  context manager (`PDFReader.read()`), `PDFDocument`/`ExtractionResult`
  giải phóng đúng sau `_process_pdf()` (không leak, khớp ADR-006/007).
  Phát hiện phụ: số liệu chi phí `PageImage`/trang trong ADR-048 lỗi
  thời sau khi ADR-053 tăng DPI 300->450 - đã đính chính (~56 MB/trang
  thay vì ~24.9 MB, xem amend ADR-048).
- `excel_mapping.json` khai ít cột hơn `InvoiceInfo` (VD 6/12 field):
  xác nhận qua đọc source (`Mapper.load()`, `ExcelWriter._write_row()`,
  `_resolve_columns()`) - hệ thống hoạt động đúng theo thiết kế sẵn có,
  không cần sửa code (khớp mô tả EXCEL_MAPPING_GUIDE.md Mục 3).
- `_merge_same_line()` lookup `anchor_idx` bằng so sánh
  `normalized_bbox`+`text` (value-equality thay vì identity): xác nhận
  `StopIteration` không thể xảy ra kể cả khi có 2 `WordToken` trùng giá
  trị tuyệt đối (anchor luôn tự thỏa điều kiện tìm chính nó); rủi ro
  "nhầm object" tồn tại về lý thuyết nhưng vô hại (2 token trùng giá
  trị tuyệt đối cho kết quả merge giống hệt nhau). Không sửa code -
  rủi ro thuần lý thuyết, cùng nhóm ADR-044/045.
- PDFDetector confidence score tăng sau khi thêm Document/Graphics Rule
  (ADR-057): xác nhận là hệ quả cơ học đúng thiết kế (ADR-020/021,
  Evidence -> Score -> Decision), KHÔNG ảnh hưởng quyết định `mode`
  (confidence chỉ dùng hiển thị trong `PDFResult.note`, không gate
  logic nào). Lưu ý rủi ro circular validation (2 rule mới chỉ verify
  trên đúng 1-2 file PDF đã dùng tinh chỉnh mọi thứ khác) - cần thêm dữ
  liệu đa dạng trước khi tinh chỉnh weight khỏi trạng thái placeholder.

### Cancelled (đã thảo luận, quyết định không triển khai)
- Đề xuất tiền xử lý ảnh OCR nâng cao (Binarization/Otsu/Adaptive
  Thresholding, Denoising/Gaussian Blur riêng biệt, Border Removal) -
  huỷ bỏ triển khai ở v1, ghi nhận "tăng cường hiệu quả OCR" là ưu
  tiên quan trọng cho v2.0. Xem PROJECT_CONTEXT.md §18.
- 2 hướng giải quyết vấn đề multi-line value / `max_distance` tĩnh
  (window động theo Key/Section kế tiếp; khóa `direction=BELOW`) - bác
  bỏ sau phân tích, xác nhận đây là giới hạn kiến trúc không patch
  được ở v1. Xem ADR-059.

------------------------------------------------------------------------