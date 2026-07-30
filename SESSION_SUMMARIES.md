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
