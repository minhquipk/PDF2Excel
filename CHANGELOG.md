# CHANGELOG.md

All notable changes to this project are documented here.

The format is chronological and focuses on architectural milestones
rather than Git commits.

------------------------------------------------------------------------

## Unreleased

### Next

-   Implement `excel_writer.py`
-   Implement Report export
-   Replace `OCREngine` Mock with a real backend (e.g. Tesseract)
-   Resolve `processor.py` role (currently placeholder; orchestration
    logic actually lives in `Worker.process()`)
-   Verify import paths in `core/models.py` (`from enums import ...`)
    and `ui/widgets.py` (`from base_widget import ...`)
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