# ARCHITECTURE_DECISIONS.md

# Architecture Decision Records (ADR)

This document records architectural decisions that have been accepted.
Any change to these decisions should be discussed before implementation.

------------------------------------------------------------------------

## ADR-001 --- UI and Business Logic Separation

**Status:** Accepted

-   UI is responsible only for user interaction.
-   Business logic must never be implemented inside UI classes.
-   MainWindow coordinates only.

------------------------------------------------------------------------

## ADR-002 --- Worker Uses QThread

**Status:** Accepted

-   All long-running work executes inside Worker.
-   Worker always runs in a dedicated QThread.
-   UI thread must remain responsive.

------------------------------------------------------------------------

## ADR-003 --- Communication by Qt Signals

**Status:** Accepted

Worker never updates widgets directly.

Signals include:

-   started
-   progress
-   file_processed
-   finished
-   cancelled
-   error

------------------------------------------------------------------------

## ADR-004 --- process() Is an Orchestrator

**Status:** Accepted

process() controls workflow only.

It must not contain:

-   PDF parsing
-   OCR
-   Regex
-   Excel writing logic

Its responsibility:

1.  Iterate PDFs
2.  Call \_process_pdf()
3.  Store PDFResult
4.  Emit progress
5.  Write Excel once

Note (2026-07-29): this orchestrator role is currently fulfilled by
`Worker.process()` in `ui/worker.py`. The relationship between this
ADR and `core/processor.py` (currently a placeholder) is an open
question — see PROJECT_CONTEXT.md §14 and SESSION_SUMMARIES.md,
Session 2026-07-29.

------------------------------------------------------------------------

## ADR-005 --- Business Logic in \_process_pdf()

**Status:** Accepted

All document processing belongs inside \_process_pdf() or dedicated
modules called from it.

------------------------------------------------------------------------

## ADR-006 --- One PDF at a Time

**Status:** Accepted

Only one PDF is processed at any moment.

Reason:

-   Low memory usage
-   Simpler debugging
-   Stable workflow

------------------------------------------------------------------------

## ADR-007 --- Keep Only Structured Data

**Status:** Accepted

Release PDF resources immediately after parsing.

Keep only PDFResult objects in memory.

------------------------------------------------------------------------

## ADR-008 --- Write Excel Once

**Status:** Accepted

Excel output occurs only after every PDF has been processed.

Never write row-by-row during processing.

------------------------------------------------------------------------

## ADR-009 --- InvoiceInfo Responsibility

**Status:** Accepted

InvoiceInfo contains invoice fields only.

No processing state or UI information.

------------------------------------------------------------------------

## ADR-010 --- PDFResult Responsibility

**Status:** Accepted

PDFResult combines:

-   PDF metadata
-   Processing status
-   Notes
-   InvoiceInfo

------------------------------------------------------------------------

## ADR-011 --- ProcessingTableModel

**Status:** Accepted

Use QAbstractTableModel.

Do not manipulate QTableWidget directly.

------------------------------------------------------------------------

## ADR-012 --- Incremental Development

**Status:** Accepted

Implement one small feature.

Compile.

Run.

Verify.

Then continue.

------------------------------------------------------------------------

## ADR-013 --- Mock First

**Status:** Accepted

Before implementing a real module:

-   Create Mock
-   Validate UI
-   Validate Worker
-   Validate Signals

Then replace Mock with production code.

Note (2026-07-29): applied for PDFReader/PDFDetector — Mock
processing has been replaced by the real pipeline for the detection
stage. Extraction, parsing, OCR, and Excel writing remain Mock/
pending per this ADR's sequencing.

------------------------------------------------------------------------

## ADR-014 --- Vietnamese Data

**Status:** Accepted

System must preserve Vietnamese Unicode text end-to-end.

------------------------------------------------------------------------

## ADR-015 --- Regular Expressions

**Status:** Accepted

Regex parsing belongs to a dedicated parser module.

Worker must not contain regex patterns.

------------------------------------------------------------------------

## ADR-016 --- PDFReader Responsibility Boundary

*(Title corrected 2026-07-29; was previously mislabeled "Regular
Expressions" — content unchanged.)*

Status: Accepted

PDFReader converts PyMuPDF objects into domain models only.

No business logic.

No parser.

No OCR.

Confirmed in implementation: `core/pdf_reader.py` (2026-07-29 review).

------------------------------------------------------------------------

## ADR-017 --- Frozen Domain Models

*(Title corrected 2026-07-29; was previously mislabeled "Regular
Expressions" — content unchanged.)*

Status: Accepted

Implementation must follow frozen domain models.

Implementation never changes models during development.

------------------------------------------------------------------------

## ADR-018 --- Source Code as Implementation Reference

*(Title corrected 2026-07-29; was previously mislabeled "Regular
Expressions" — content unchanged.)*

Status: Accepted

Implementation decisions are based on the current source code.

Chat history is not authoritative.

------------------------------------------------------------------------

## ADR-019 --- Knowledge Cache Strategy

Status: Accepted

Future document analysis will build a reusable knowledge cache.

Machine learning is intentionally excluded.

Knowledge grows deterministically from processed documents.

Note (2026-07-29): `KnowledgeRecord` domain model exists
(`core/models.py`) and `PDFDetector` consults it read-only during
analysis (see ADR-023). Persistence, lifecycle, and governance of
the knowledge cache (TDS Chapter 9) are not yet implemented.

------------------------------------------------------------------------

## ADR-020 --- PDFDetector as Deterministic Reasoning Engine

**Status:** Accepted

`PDFDetector` is implemented as a staged, deterministic reasoning
engine, per `PDF_Detector_Technical_Design.docx`:

1.  Build Context — convert `PDFDocument` into an immutable
    `AnalysisContext` (raw + derived metrics only, no evaluation).
2.  Heuristic Evaluation — independent, stateless rules read only
    `AnalysisContext` and produce `Evidence`. Rules never decide the
    final mode.
3.  Knowledge Lookup — optional `KnowledgeRecord` consulted after
    evidence is formed; never mutates or overrides Evidence.
4.  Confidence Composition — combines independent confidence
    sources (evidence strength, consistency, coverage, and
    optionally knowledge) into a single `Confidence`.
5.  Final Decision — produces one immutable `DocumentAnalysis`.

No machine learning or non-explainable inference is used anywhere in
the detector (consistent with ADR-019).

Confirmed in implementation: `core/pdf_detector.py` (2026-07-29
review).

------------------------------------------------------------------------

## ADR-021 --- Confidence Is Decision-Centric and Evidence-Driven

**Status:** Accepted

Confidence produced by `PDFDetector`:

-   Is a property of the decision (`DocumentAnalysis`), not of the
    PDF document itself.
-   Is always derived from collected `Evidence` and, optionally,
    `KnowledgeRecord` — never assigned as a fixed or arbitrary value.
-   Is decomposed into independent, explainable sources (evidence
    strength, consistency, coverage, knowledge) before being
    composed into a single score and mapped to a `ConfidenceLevel`.

Confirmed in implementation: `PDFDetector._compose_confidence()`,
`core/enums.py::ConfidenceLevel` (2026-07-29 review).

------------------------------------------------------------------------

## ADR-022 --- Immutability of Analysis Output Models

**Status:** Accepted

`Evidence`, `Confidence`, `AnalysisContext`, and `DocumentAnalysis`
are implemented as frozen dataclasses. Nested collections (dict,
list, set) are recursively frozen (`MappingProxyType`, `tuple`,
`frozenset`) on construction.

Reason: guarantees that no stage of the reasoning pipeline — or any
downstream subsystem consuming `DocumentAnalysis` — can mutate
observation data or a finalized decision after the fact, satisfying
Determinism and Explainability goals (see
`PDF_Detector_Technical_Design.docx`, §1.3 G1/G2, §2 DP-004/DP-005).

`KnowledgeRecord` is intentionally **not** frozen (see ADR-023).

Confirmed in implementation: `core/models.py` (2026-07-29 review).

------------------------------------------------------------------------

## ADR-023 --- KnowledgeRecord Is Mutable at Storage but Read-Only During Analysis

**Status:** Accepted

`KnowledgeRecord` is a mutable dataclass at the storage/lifecycle
level (its content is expected to evolve over time, per ADR-019),
but `PDFDetector` treats it strictly as read-only input during a
single `analyze()` call: it is never created, updated, or deleted by
the detector, and a fingerprint mismatch produces a warning rather
than being silently ignored or overriding Evidence.

Confirmed in implementation: `PDFDetector._compose_confidence()`
(2026-07-29 review).

------------------------------------------------------------------------

## ADR-024 --- Extractor as Mode-Dispatching, Non-Deciding Component

**Status:** Accepted

`Extractor` receives an already-finalized `DocumentAnalysis` and
dispatches extraction strategy purely based on `analysis.mode`. It
never re-evaluates document type, per TDS §3.1 ("a decision is made
once and reused downstream").

Dispatch rules:

-   `DIGITAL` — extract from `page.words` (text layer).
-   `SCANNED` — extract via `OCREngine`.
-   `HYBRID` — decide per page (`page.has_text` → Digital path, else
    OCR path). See ADR-029 for the known limitation this implies.
-   `UNKNOWN` — not a valid input; see ADR-027.

Confirmed in implementation: `core/extractor.py::Extractor.extract()`
(2026-07-31 review).

------------------------------------------------------------------------

## ADR-025 --- Reader Reads Raw, Extractor Normalizes (Extended to Geometry)

**Status:** Accepted

Extends the Reader/Detector separation already established (ADR-016)
to geometric data: `PDFReader` stores `PDFPage.words` as raw,
unmodified PyMuPDF word tuples (`(x0, y0, x1, y1, text, block_no,
line_no, word_no)`), performing no coordinate normalization,
rotation correction, or structural transformation.

`Extractor` is the **only** component that converts raw geometry into
the domain-level `WordToken` (`normalized_bbox` in `[0.0, 1.0]`).
This mirrors `PDFReader`/`PDFDetector`'s existing separation: Reader
collects facts, a downstream reasoning/transformation stage
interprets them.

Confirmed in implementation: `core/models.py::PDFPage.words`,
`core/extractor.py::Extractor._extract_digital_page()` (2026-07-31
review).

------------------------------------------------------------------------

## ADR-026 --- Eager, Raw Grayscale Page Image Rendering

**Status:** Accepted

`PDFReader` renders a `PageImage` (raw grayscale pixmap samples,
self-describing: `samples`, `width`, `height`, `dpi`) for **every**
page of every document, at render time (`page.get_pixmap(dpi=Image.DPI,
colorspace=fitz.csGRAY)`, `Image.DPI = 300` in `core/constants.py`),
regardless of whether the document is later classified as Digital,
Scanned, or Hybrid.

Rationale:

-   Avoids reopening the PDF file later for OCR (`Extractor`/
    `OCREngine` never hold a `fitz.Page` reference — see ADR-028).
-   Accepted memory cost: per-document `PDFDocument` (and therefore
    every `PageImage` it holds) is released immediately after
    `Worker._process_pdf()` returns (ADR-007); only `PDFResult`
    persists across the batch. Eager rendering therefore does not
    violate "Memory First" at the batch level, even though it adds
    memory cost per in-flight document (~8.3 MB/page at A4/300 DPI,
    grayscale, uncompressed).
-   Raw (uncompressed) samples were chosen over PNG-encoded storage,
    prioritizing OCR-readiness over storage footprint.

`PageImage` exists specifically to avoid an implicit dependency on
externally-known render parameters (DP-008, Explicit Over Implicit):
consumers read `width`/`height`/`dpi` directly from the object rather
than recomputing them from `PageStatistics` and an assumed DPI.

Confirmed in implementation: `core/models.py::PageImage`,
`core/pdf_reader.py::PDFReader._render_page_image()` (2026-07-31
review).

------------------------------------------------------------------------

## ADR-027 --- UNKNOWN Is the Absence of a Decision, Not a Case to Handle

**Status:** Accepted

`AnalysisMode.UNKNOWN` represents the *absence* of a classification
decision, not a document type requiring its own extraction strategy.
Accordingly:

-   `Extractor.extract()` raises `ValueError` if called with
    `analysis.mode is AnalysisMode.UNKNOWN` — this is treated as a
    programming-contract violation (calling Extractor when no
    decision exists to act on), not a business-level warning.
-   `Worker._process_pdf()` is responsible for **not calling**
    `Extractor` at all when `analysis.mode is UNKNOWN`. The decision
    of whether to extract belongs to the orchestrator (ADR-004/005),
    not to Extractor defensively handling a case that, by definition,
    is outside its domain.

This keeps a strict separation between "Detector could not decide"
(a `WARNING`-level business outcome, per existing `Worker` logic
mapping `UNKNOWN` → `ProcessStatus.WARNING`) and "Extractor was asked
to act without a valid decision" (a contract violation, would
indicate a bug in the caller).

Confirmed in implementation: `core/extractor.py::Extractor.extract()`,
`ui/worker.py::Worker._process_pdf()` (2026-07-31 review).

------------------------------------------------------------------------

## ADR-028 --- Rotation Reconciliation Is Computed Explicitly, Not via fitz.Page

**Status:** Accepted

`Extractor` never holds a live `fitz.Page` reference — the source PDF
file is already closed by the time `Extractor.extract()` runs
(`PDFReader.read()` uses `with fitz.open(...)`, and `PDFDocument` is
a plain, file-independent domain model). Consequently, PyMuPDF's
built-in `Page.rotation_matrix` is not available to `Extractor`.

Verified (PyMuPDF official documentation, and a maintainer statement
in an official GitHub discussion, 2026-07-31):

-   `page.get_text("words")` returns coordinates relative to the
    **unrotated** page.
-   `page.rect` (the source of `PageStatistics.width/height`) and
    `page.get_pixmap()` both reflect the **rotated/visual** page
    ("get_pixmap() renders Page.rect... because that is what a PDF
    viewer would show, too" — PyMuPDF maintainer).

This is a real, confirmed coordinate-frame mismatch for rotated pages
(`page.statistics.rotation != 0` — already tracked by
`AnalysisContext.rotated_pages` and flagged by the existing
`page_layout` Evidence rule in `pdf_detector.py`).

Resolution: `Extractor._rotate_bbox()` implements the four
PyMuPDF-guaranteed

------------------------------------------------------------------------

## ADR-029 --- Parser as Orchestrator + TemplateMatcher Engine Separation

**Status:** Accepted

`Parser` follows the same separation established by `Extractor` (ADR-024):
it never contains Key Matching, Windowing, or Value Matching logic itself.
All template-matching logic lives in `TemplateMatcher`; `Parser` only calls
`TemplateMatcher.select_template()` + `.extract_fields()`, then converts
raw strings into typed `InvoiceInfo` fields via `ValueConverter`.

Reason: prepares for a v2.0 LayoutLMv3-based engine to be dropped in as an
alternative to `TemplateMatcher` behind the same interface, without
changing `Parser` or `Worker`.

Confirmed in implementation: `core/parser.py`, `core/template_matcher.py`.

------------------------------------------------------------------------

## ADR-030 --- Template Selection via Evidence-Weighted Scoring

**Status:** Accepted

`TemplateMatcher.select_template()` reuses the same Evidence → Score →
Decision pattern already established by `PDFDetector` (ADR-020/021):

- Each `TemplateDefinition` is scored independently: 
  `score = Σ(identification_weight of fields whose key matched) / Σ(identification_weight of all fields)`.
- A tie margin (`TemplateMatching.TEMPLATE_TIE_MARGIN`) prevents selecting
  an ambiguous winner when two templates score too closely — mirrors
  `PDFDetector._DECISION_TIE_MARGIN`.
- A minimum score threshold (`TemplateMatching.TEMPLATE_MIN_SCORE`) rejects
  weak matches outright.
- Score is computed over the **entire** document text (all pages), not a
  restricted region, to avoid baking in layout assumptions that would
  break under future document types (deliberate choice over performance).

`FieldDefinition.identification_weight` lets template authors mark which
fields are supplier-identifying (e.g. tax code, company name) versus
generic (e.g. invoice date) — generic fields do not influence template
selection.

Confirmed in implementation: `core/template_matcher.py::TemplateMatcher._score_template()`.

------------------------------------------------------------------------

## ADR-031 --- Template Definition Stored as External JSON

**Status:** Accepted

Template Definitions live as JSON files under `resources/templates/`,
loaded via `TemplateLoader` into frozen dataclasses
(`TemplateDefinition`/`FieldDefinition`/`SpatialRelation` in
`core/models.py`). This lets template authors add/update invoice formats
without touching Python logic (satisfies the "templates must be easy to
update without affecting logic" requirement).

- A JSON file that fails to parse or validate is skipped with a logged
  warning; loading continues for all other files (fail-soft per file).
- The `resources/templates/` directory itself missing is also handled
  gracefully (logged warning, empty template set) rather than crashing
  the application — consistent with the target audience (office users,
  PROJECT_CONTEXT.md §1).
- `FieldDefinition.__post_init__` validates that `field_name` matches an
  actual field of `InvoiceInfo` (via `dataclasses.fields()`), failing
  fast on template authoring typos rather than failing silently at
  `InvoiceInfo(**values)` construction time in `Parser`.
- `value_pattern` is stored as a plain string in `FieldDefinition`; regex
  compilation happens in `TemplateMatcher` (with a cache), not in
  `core/models.py`, preserving `models.py`'s existing "no Regex" rule.

Confirmed in implementation: `core/template_loader.py`, `core/models.py`.

------------------------------------------------------------------------

## ADR-032 --- InvoiceInfo Fields Are Optional; Convert Failures Become None

**Status:** Accepted

All `InvoiceInfo` fields except `source_file` are `Optional`, defaulting
to `None`. When `TemplateMatcher` cannot find a value for a field, or
`ValueConverter` fails to convert a matched raw string into its target
type (`Decimal`/`date`), the corresponding `InvoiceInfo` field is simply
`None` — never an exception, never a placeholder/sentinel value.

`ValueConverter` is deliberately stateless and never raises: any
conversion failure (malformed number, invalid date, OCR noise) returns
`None`. This isolates a single bad field from failing the entire PDF.

Confirmed in implementation: `core/models.py::InvoiceInfo`,
`core/value_converter.py`.

------------------------------------------------------------------------

## ADR-033 --- Invoice-Level Gaps Are a Report Concern, Not a Worker Status Concern

**Status:** Accepted

Two distinct situations were deliberately kept **out** of
`PDFResult.status`/`.note`:

1. **A field inside `InvoiceInfo` is `None`** (Value Matching or convert
   failure for one field) — per ADR-032.
2. **`Parser.parse()` returns `None` entirely** (no template scored above
   `TEMPLATE_MIN_SCORE`, or the winner tied with a runner-up) —
   symmetric to how `AnalysisMode.UNKNOWN` is "absence of a decision"
   (ADR-027), not an error.

Rationale for (2): the cause of "no template matched" is inherently
ambiguous from the pipeline's point of view — it could mean a missing
template, an incorrect/stale template, a low-quality PDF, or even a
misfiled document. The system cannot distinguish these causes reliably,
so it must not guess by asserting `WARNING`. Instead: `PDFResult.status`
and `.note` remain driven solely by `PDFDetector`'s decision, exactly as
before Parser existed. Both situations surface exclusively through the
Report feature (`ui/main_window.py`'s Report button — UI exists,
logic pending, see PROJECT_CONTEXT.md §14/§15), where the operator can
observe **frequency**: low/isolated occurrences point to a bad file or
wrong input; frequent/repeating occurrences on the same shape point to a
template that needs updating.

Confirmed in implementation: `ui/worker.py::Worker._process_pdf()`
(Parser integration block).

------------------------------------------------------------------------

## ADR-034 --- TemplateSelection Carries page_index Alongside Matched Key

**Status:** Accepted

`TemplateSelection.matched_keys` is typed
`Mapping[str, tuple[int, WordToken]]`, not `Mapping[str, WordToken]`.

Reason: `WordToken.normalized_bbox` is only meaningful within a single
page's coordinate space (`ExtractionResult.words_by_page` is keyed by
page). Without `page_index`, `TemplateMatcher.extract_fields()` would not
know which page's `WordToken` collection to scan when building a
Windowing search area from a previously-matched key, and could
incorrectly compare bounding boxes across different pages.

Rejected alternative: adding `page_index` to `WordToken` itself. Rejected
because `WordToken` is an already-frozen, shared domain model consumed by
`Extractor` (ADR-024/025) — changing it would ripple into
`ExtractionResult`/`Extractor`, a much wider blast radius than scoping the
fix to `TemplateSelection`, which is new and Parser-only.

Confirmed in implementation: `core/models.py::TemplateSelection`.

------------------------------------------------------------------------

## ADR-035 --- Vietnamese Diacritics Normalization Required for Fuzzy Key Matching

**Status:** Accepted

`TemplateMatcher` strips Vietnamese diacritics (`_strip_diacritics()`,
Unicode NFKD decomposition + explicit `Đ/đ` handling, since `Đ/đ` do not
decompose under NFKD) from both `FieldDefinition.key_tokens` and observed
text before calling `rapidfuzz.fuzz.ratio()`.

Verified empirically during implementation: comparing accented text
("Mã số thuế") against its unaccented form ("Ma so thue") without this
normalization yields a similarity ratio of ~70, below any reasonable
`fuzzy_threshold` (85-90) — meaning key matching would silently fail
whenever a template's `key_tokens` and the PDF's actual text differ in
diacritics, including the realistic case of OCR dropping diacritics on
low-quality scans.

Confirmed in implementation: `core/template_matcher.py::_strip_diacritics()`.

------------------------------------------------------------------------

## ADR-036 --- Extractor Also Normalizes Text Whitespace (Not Just Geometry)

**Status:** Accepted

Extends `Extractor`'s existing normalization responsibility (previously
geometry-only, per ADR-024/025/028) to also cover text whitespace:
`_extract_digital_page()`/`_extract_ocr_page()` now strip leading/
trailing whitespace and collapse internal whitespace in each token's text
before constructing `WordToken`. A token that becomes empty after
normalization is dropped entirely (no empty-text `WordToken` is ever
produced).

Reason for placing this in `Extractor` rather than `Parser`: whitespace
normalization is a format concern independent of any downstream domain
model (Parser, or a future LayoutLMv3 engine, would otherwise have to
duplicate it) — consistent with `Extractor` already being the single
place where raw PyMuPDF/OCR output is normalized into clean `WordToken`s
for any downstream consumer.

Confirmed in implementation: `core/extractor.py::Extractor._normalize_text()`.

------------------------------------------------------------------------

## ADR-037 --- ExcelWriter and ReportWriter Are Two Separate Modules, Not One ReportService

**Status:** Accepted

An early design draft (`Technical_Design_excel_writer.docx`) proposed a
single `ReportService` layer between the UI and `ExcelWriter`, combining
Excel writing and `report.txt` generation into one `generateReport()`
call. This was rejected during discussion.

Reason: `Worker.__init__` already carried two separate placeholder
attributes (`self._excel_writer = None`, `self._report_writer = None`)
from earlier sessions — the original design already anticipated two
distinct components, not a merged one. This is also consistent with the
two triggers being genuinely different in nature:

-   Excel writing happens **automatically**, exactly once, at the end of
    `Worker.process()` (ADR-008 timing).
-   `report.txt` generation happens **as a side effect of that same
    automatic write** (see ADR-040) — not as a separately-triggered
    action.

`ExcelWriter` and `ReportWriter` have no dependency on each other.
`ExcelWriter` never imports `ReportWriter` or vice versa; `Worker`
orchestrates both.

Confirmed in implementation: `ui/worker.py::Worker.__init__`,
`Worker._write_excel()`.

------------------------------------------------------------------------

## ADR-038 --- Excel Mapping Stored as External JSON, Loaded Fail-Fast (Not Fail-Soft)

**Status:** Accepted

`ExcelMapping` (`table`, `columns`) is loaded from an external
`mapping.json` (`resources/excel_mapping.json`) via `core/excel_mapper.py::Mapper`,
following the same "external JSON -> frozen dataclass" pattern already
established for Template Definitions (ADR-031).

Unlike `TemplateLoader` (fail-soft per file, ADR-031), `Mapper` treats
every error as **fatal** — any malformed `mapping.json` raises
`MappingError` (defined in `core/excel_mapper.py`, not in
`core/excel_writer.py` — each module owns the exceptions it raises, to
avoid a cross-import between `excel_mapper.py` and `excel_writer.py`).

Reason for the fail-fast/fail-soft asymmetry: with templates, a single
invalid JSON file among many is an isolated, tolerable loss (other
templates still work). With Excel mapping, there is exactly one mapping
file and it is a hard precondition for `ExcelWriter` to write anything
at all — there is no "partially valid mapping" concept to fall back to.

`Mapper.load()` is called lazily inside `Worker._write_excel()`, **not**
in `Worker.__init__()` (unlike `TemplateLoader`, which is loaded eagerly
in `__init__`). Reason: loading eagerly in `__init__` would crash the
application at startup if `mapping.json` is malformed, before the user
can do anything. Loading lazily at the end of the batch allows a bad
mapping to be handled like any other pipeline-stage error: caught,
reported via the `error` signal, without crashing the app, and still
followed by `report.txt` generation (ADR-040) so the user sees why
nothing was written.

`FieldDefinition.field_name` validation (ADR-031) is reused for
`ExcelMapping.columns` values: `Mapper._build_mapping()` checks every
mapped `field_name` against `dataclasses.fields(InvoiceInfo)` at load
time, catching authoring typos before `ExcelWriter` ever runs.

Confirmed in implementation: `core/excel_mapper.py`, `resources/excel_mapping.json`,
`config.py::EXCEL_MAPPING_PATH`.

------------------------------------------------------------------------

## ADR-039 --- Excel Table Column Mismatch Is a Per-Column Soft Failure

**Status:** Accepted

`ExcelMapping.columns` is validated against `InvoiceInfo` field names at
load time (ADR-038), but cannot be validated against the **actual**
Excel Table headers in the user-selected output workbook — the JSON
mapping and the physical `.xlsx` file are two independent sources that
can only be cross-checked at runtime.

`ExcelWriter._resolve_columns()` compares `mapping.columns` against the
real header row of the target Excel Table. A mapped column absent from
the workbook is recorded in `ExcelWriteResult.errors` and skipped; all
other, correctly-matched columns are still written. This mirrors the
existing "one bad field does not fail the whole record" principle
(ADR-032) at the column level, and keeps `ExcelWriter.write()` from
raising for a condition that is common and partially recoverable (e.g.
a user's Excel template has renamed one column).

Global, non-recoverable failures — workbook not found
(`WorkbookNotFoundError`), Table not found (`ExcelTableNotFoundError`),
save failure (`WorkbookSaveError`) — remain hard `raise`s, since there
is nothing partial to write in those cases.

Confirmed in implementation: `core/excel_writer.py::ExcelWriter._resolve_columns()`.

------------------------------------------------------------------------

## ADR-040 --- ReportWriter Has Two Fully Separate Output Channels

**Status:** Accepted

`ReportWriter.write(results, excel_result)` receives two independent
inputs — `list[PDFResult]` and `ExcelWriteResult` — and routes each to
a distinct output with no content mixing between them:

1.  `list[PDFResult]` (per-file pipeline outcome: status + note) ->
    `utils/logger.py` (console + `logs/app.log`, via `FileHandler`
    added in this module's implementation). Intended audience: dev/
    admin. Every file is logged, regardless of status; `WARNING`/
    `FAILED` statuses are logged at `logging.WARNING`, others at
    `logging.INFO`. This file **accumulates** across runs (standard
    `FileHandler` append behavior) — a full history is intentional.

2.  `ExcelWriteResult` (Summary / Warnings / Errors from the Excel
    write) -> `reports/Report.txt` (fixed filename, no timestamp,
    per `core/constants.py::Report`). Intended audience: end-user, via
    the UI's Report button. This file is **overwritten** on every run —
    it always reflects only the most recent `process()` call.

Rationale for keeping the two channels separate rather than merging
`PDFResult` data into `report.txt`: they serve different audiences at
different levels of detail. `PDFResult.note` is pipeline-internal
diagnostic text (detection confidence, extraction warnings); an
end-user does not need it to take action. What the end-user needs from
`report.txt` is exactly two things: which invoice fields came out
`None` (ADR-033) and whether the Excel write itself succeeded — both
of which live in `ExcelWriteResult`, not in `PDFResult`.

`ExcelWriter` itself never writes to either channel (ADR-006) — it only
returns `ExcelWriteResult` as plain data; `ReportWriter` is the sole
owner of both side effects.

Confirmed in implementation: `core/report_writer.py`,
`core/constants.py::Report`, `utils/logger.py::_configure_root()`
(FileHandler added), `config.py::LOG_DIR`/`REPORTS_DIR`.

------------------------------------------------------------------------

## ADR-041 --- The Report Button Opens an Already-Generated File; It Never Triggers Generation

**Status:** Accepted

`report.txt` is generated exactly once per `process()` run, automatically,
as part of `Worker._write_excel()` (ADR-008 timing, ADR-040 content) —
**not** when the user clicks the "Report" button.

`MainWindow._report()` only reads `Worker.report_path` (a property
exposing the path already written) and opens it via
`QDesktopServices.openUrl()`, using the OS's default handler for
`.txt` files. If `report_path` is `None` (no run has completed yet), a
`QMessageBox.information` is shown instead; if the OS fails to open
the file, a `QMessageBox.warning` is shown. The button never calls
`ExcelWriter` or `ReportWriter` itself.

This keeps `MainWindow` a pure UI coordinator (ADR-001) — it has no
role in deciding *when* a report is produced, only in surfacing one
that already exists.

Confirmed in implementation: `ui/main_window.py::MainWindow._report()`,
`ui/worker.py::Worker.report_path`.

------------------------------------------------------------------------

ADR-042 --- Excel Mapping Schema Giữ Nguyên table + columns, Không Thêm 'sheet'

Status: Accepted

Trong phiên thảo luận excel_mapping.json, có đề xuất thêm trường sheet để chỉ rõ Excel Table nằm ở sheet nào. Đề xuất này đã bị rút lại sau khi phân tích ExcelWriter._find_table():

python
for worksheet in workbook.worksheets:
    if table_name in worksheet.tables:
        return worksheet, worksheet.tables[table_name]

Hàm này duyệt toàn bộ sheet để tìm Table theo tên - không cần biết tên sheet để hoạt động đúng, vì Excel tự đảm bảo tên Table (ListObject) là duy nhất trong toàn workbook. Thêm sheet sẽ dư thừa cho mục đích "tìm được bảng", trong khi nếu muốn dùng sheet như một điều kiện validate bổ sung (fail-fast nếu Table bị dời sai sheet) thì cần quyết định thêm về ngữ nghĩa lỗi (raise cứng / soft-fail / chỉ dùng để tìm nhanh hơn) - người dùng quyết định không cần thêm độ phức tạp này.

Confirmed: ExcelMapping (core/models.py), Mapper (core/excel_mapper.py), ExcelWriter._find_table() (core/excel_writer.py) - không đổi gì.

------------------------------------------------------------------------

ADR-043 --- ValueConverter Bỏ Ký Hiệu '%' Cuối Chuỗi Trước Khi Convert Decimal

Status: Accepted

Phát hiện qua kiểm thử thực nghiệm trên PDF hóa đơn thật (HD2026-0003_digital.pdf): field vat_rate trích được token "5%" (dấu % dính liền, do PyMuPDF không tách khoảng trắng giữa số và ký hiệu phần trăm). Decimal("5%") ném InvalidOperation, khiến field vat_rate luôn ra None dù Key/Value Matching đã trích đúng vị trí.

ValueConverter._to_decimal() nay strip ký tự % ở cuối chuỗi (nếu có) trước khi áp thousand_separator/decimal_separator và gọi Decimal(). Strip vô điều kiện, không cần cấu hình gì thêm trong FieldDefinition/ decimal_format, vì % không bao giờ là 1 phần hợp lệ của số Decimal.

Confirmed trong implementation: core/value_converter.py::ValueConverter._to_decimal(). Verify: ValueConverter._to_decimal("5%", None) → Decimal('5') (trước patch: None). Không ảnh hưởng các field Decimal khác (subtotal, vat_amount, total_amount) vì giá trị của chúng không có %.

------------------------------------------------------------------------

ADR-044 --- Value Matching Ghép Nhiều Từ Cho Field Text Bằng Gap-Based Line Clustering

Status: Accepted

Giải quyết Known Limitation đã ghi từ Session 2026-08-01/02 ("Value Matching captures a single WordToken only"): TemplateMatcher._select_best_value() trước đây chỉ trả về đúng 1 token gần Key nhất, khiến mọi field giá trị nhiều từ (company_name, address, buyer_name, payment_method) bị cắt cụt còn 1 từ. Xác nhận qua kiểm thử thực nghiệm trên PDF thật.

Thiết kế đã chọn (trong 3 hướng thảo luận: gap-based / cả dòng trong window / dùng vị trí key field khác làm ranh giới): gap-based, tái dùng 2 constant đã có sẵn trong TemplateMatching - LINE_Y_TOLERANCE (xác định "cùng dòng") và WORD_GAP_TOLERANCE (xác định "liền kề") - đối xứng với cơ chế _cluster_lines/_cluster_phrases đã dùng ở Key Matching (ADR-035), không thêm constant mới.

Chỉ áp dụng cho field ValueType.TEXT - Decimal/Date giữ nguyên hành vi cũ (luôn 1 token), vì trên thực tế các giá trị này luôn là 1 token liền mạch.

Bổ sung phát hiện qua thực nghiệm: merge áp dụng cho MỌI field Text (kể cả field có value_pattern chỉ nhận số, như tax_code) có thể kéo nhầm token nhãn (label) của field khác trên cùng dòng vào giá trị (VD: tax_code bị biến từ '0313828292' thành 'mua: 0313828292', do token 'mua:' nằm liền kề, gap nhỏ). Thêm điều kiện dừng: không mở rộng qua token kết thúc bằng dấu : - trong toàn bộ dữ liệu quan sát, token dạng này luôn là phần còn lại của 1 nhãn, không bao giờ là giá trị thật.

Rủi ro còn lại (chưa loại bỏ hoàn toàn): nếu 1 dòng có 2 field liền kề mà nhãn field thứ 2 KHÔNG kết thúc bằng : (khác quy ước đã quan sát), merge vẫn có thể tràn sang field kế bên. Đây là giới hạn cố hữu của gap-based clustering (đánh đổi độ đầy đủ lấy rủi ro tràn), không phải lỗi implementation - cần thêm dữ liệu hóa đơn thật đa dạng hơn để đánh giá tần suất rủi ro này.

Confirmed trong implementation: core/template_matcher.py::TemplateMatcher._select_best_value(), TemplateMatcher._merge_same_line().

------------------------------------------------------------------------

ADR-045 --- Section-Scoped Key Matching Giải Quyết Va Chạm key_tokens Giữa Các Khối Tài Liệu

Status: Accepted

Giải quyết 2 Known Limitation phát hiện qua kiểm thử thực nghiệm trên PDF thật, cùng chung 1 gốc rễ: TemplateMatcher._find_key_match() tìm kiếm toàn cục, phẳng trên mọi phrase của tài liệu, không có khái niệm "khối"/ "ngữ cảnh" để giới hạn phạm vi tìm.

tax_code bị lấy nhầm MST bên mua: key "ma so thue" khớp cụm "Mã số thuế" tách từ dòng "Mã số thuế mua:" (ratio 100 tuyệt đối, do không dính dấu :) thay vì cụm đúng "Mã số thuế:" của bên bán (ratio 95.24, dính dấu :).
invoice_date phụ thuộc may rủi thứ tự: key "ngay" khớp 3 vị trí (ngày lập + 2 ngày ký số cuối trang) với ratio bằng nhau tuyệt đối; chỉ đúng nhờ _find_key_match cập nhật theo > (không phải >=) nên cụm xuất hiện trước trong tài liệu thắng - không phải cơ chế phân biệt thật sự.
Thiết kế đã chọn

Trong 4 cách thảo luận (Block/Section, Parent Key, Anchor, Relative Position), chọn Section/Block:

Thêm SectionDefinition (core/models.py): section_id, key_tokens (None = khối ảo bắt đầu từ đỉnh trang, không cần marker thật - dùng cho phần đầu tài liệu chưa có section header rõ ràng), fuzzy_threshold.
FieldDefinition thêm field bắt buộc section: str (không có default) - quyết định trong thảo luận: không cho phép field bỏ trống section, đổi lại phải cập nhật MỌI template JSON hiện có.
TemplateDefinition thêm sections: tuple[SectionDefinition, ...], tự validate mọi field.section phải khớp 1 section_id đã khai (__post_init__, raise ValueError nếu không khớp - được TemplateLoader bắt và xử lý fail-soft per file như mọi lỗi schema khác, ADR-031).
Section header tự nó dùng cơ chế tie-margin riêng (TemplateMatching.SECTION_TIE_MARGIN = 10, thang 0-100 của rapidfuzz.fuzz.ratio(), khác thang với TEMPLATE_TIE_MARGIN 0-1) - quyết định trong thảo luận: section header cần chống va chạm chặt hơn field thường (field thường vẫn giữ best-match tuyệt đối, không đổi).
_find_key_match() được refactor tách khỏi FieldDefinition, nhận trực tiếp key_tokens/fuzzy_threshold/tie_margin (mặc định None) - dùng chung cho cả Field (tie_margin=None, hành vi cũ không đổi) và Section (tie_margin bắt buộc).
Thuật toán resolve: match từng section header trên toàn bộ phrase của tài liệu, sắp theo (page_index, y_center) tăng dần, dựng khoảng [bắt đầu section, bắt đầu section kế tiếp). Field thuộc section nào chỉ được tìm key_tokens trong đúng khoảng đó.
Section không resolve được (ambiguous do tie_margin, hoặc không tìm thấy) khiến mọi field thuộc section đó coi như "không tìm được" cho template này - đối xứng nguyên tắc "UNKNOWN là absence of decision" (ADR-027), không raise, không crash.
Lợi ích phát hiện thêm khi thực nghiệm

Section giải quyết cả 2 vấn đề bằng đúng 1 cơ chế (đúng nhận định ban đầu: "cùng gốc rễ"). Ngoài ra, buyer_tax_code giờ dùng lại được đúng key_tokens=["ma so thue"] giống hệt tax_code (chỉ khác section) - không cần key dài "ma so thue mua" riêng như thiết kế tạm thời trước đó, đơn giản hóa template.

Rủi ro còn lại
Section header tự nó vẫn có thể va chạm về mặt lý thuyết nếu 2 section dùng key_tokens gần giống nhau - Section giảm đáng kể diện va chạm (header thường dài/đặc trưng hơn field key) nhưng không loại bỏ hoàn toàn lớp vấn đề.
MAX_KEY_WORDS = 4 giới hạn độ dài cụm sinh ra khi Key Matching (kể cả cho Section) - phát hiện qua thực nghiệm: section header 5 từ ("THÔNG TIN NGƯỜI MUA HÀNG:") không bao giờ đạt ratio 100 vì candidate phrase dài nhất chỉ 4 từ; phải chọn key_tokens ngắn hơn ("thong tin nguoi mua", 4 từ) để tránh fail tie-margin. Cần ghi chú vào tài liệu hướng dẫn viết Template (còn thiếu, xem PROJECT_CONTEXT.md §14).
SECTION_TIE_MARGIN = 10 là giá trị placeholder ban đầu, cùng loại với các hằng số khác trong TemplateMatching - cần tinh chỉnh khi có nhiều mẫu hóa đơn thật hơn.

Confirmed trong implementation: core/models.py::SectionDefinition, FieldDefinition.section, TemplateDefinition.sections; core/template_matcher.py::TemplateMatcher._find_key_match(), _resolve_sections(), _filter_phrases_by_range(), _score_template(); core/template_loader.py::TemplateLoader._build_section(); core/constants.py::TemplateMatching.SECTION_TIE_MARGIN.

Verify: toàn bộ 12/12 field của sample_invoice_v1.json (v3) ra đúng kết quả trên HD2026-0003_digital.pdf thật, bao gồm tax_code ('0104101075', đúng MST bên bán) và invoice_date (đảm bảo, không còn phụ thuộc thứ tự - xác nhận trong phạm vi section "header" chỉ còn đúng 1 candidate khớp "ngày").

------------------------------------------------------------------------

ADR-046 --- Lazy Loading OCREngine & Tắt Tiền Xử Lý Phụ Của PaddleX Đảm Bảo Khởi Động UI Không Crash

Status: Accepted

Khắc phục lỗi crash ứng dụng ngay khi khởi động UI (`ui/main_window.py`) do khởi tạo `_PaddleOCR` quá sớm trong `OCREngine.__init__()` và lỗi xung đột thuộc tính `strides` trong Paddle 3.0.0 PIR engine.

Thiết kế đã chọn:
1. Lazy Loading: `OCREngine.__init__()` chỉ thiết lập `self._ocr = None`. Hàm `_get_ocr()` trì hoãn việc khởi tạo `_PaddleOCR` đến lần đầu tiên hàm `recognize()` thực sự được gọi (chỉ xảy ra khi gặp PDF Scanned/Hybrid trong tiến trình Worker). Instance này được giữ lại và tái sử dụng 100% cho toàn bộ các trang/PDF tiếp theo trong batch (đảm bảo đúng nguyên tắc khởi tạo 1 lần duy nhất).
2. Tắt preprocessor thừa: Trong `core/constants.py`, thêm các cờ `USE_DOC_ORIENTATION_CLASSIFY = False`, `USE_DOC_UNWARPING = False`, `USE_TEXTLINE_ORIENTATION = False`. Bước làm thẳng trang (deskew) vẫn được `OCREngine._deskew()` xử lý nội bộ bằng OpenCV.

Lợi ích:
- Khởi động ứng dụng UI mượt mà, không bị khựng hay crash lúc vừa bật ứng dụng.
- Tiết kiệm tài nguyên khi chạy batch PDF Digital (không tốn dung lượng RAM/CPU để nạp mô hình OCR).
- Loại bỏ hoàn toàn lỗi PIR C++ attribute `strides` trong PaddlePaddle 3.0.0.

Confirmed trong implementation: `core/constants.py::OCR`, `core/ocr_engine.py::OCREngine`.

------------------------------------------------------------------------

## ADR-047 --- OCR Engine Final Selection: Tesseract 5.x + tessdata_best

**Status:** Accepted

Sau khi thực nghiệm tuần tự 2 thư viện khác trong cùng phiên, `OCREngine`
(`core/ocr_engine.py`) chốt dùng **Tesseract 5.x + tessdata_best** (qua
`pytesseract`), thay thế Mock (ADR-013).

### Lịch sử lựa chọn (đầy đủ, để tránh lặp lại thử nghiệm đã loại)

1. **PaddleOCR (paddleocr==3.7.0)** — loại bỏ. Nguyên nhân thật: xung đột
   version giữa `paddleocr==3.7.0` và `paddlepaddle` ở tầng PIR (Paddle
   Intermediate Representation) — lỗi `ValueError: Type of attribute:
   strides is not right` khi chạy thật trên PDF Scanned. Xác nhận qua
   GitHub Issue #18162 (PaddleOCR repo, cùng loại lỗi, chưa có fix chính
   thức tại thời điểm thử nghiệm). Trên môi trường thật của người vận
   hành (macOS Ventura, Intel, Python 3.12), tổ hợp duy nhất chạy được là
   `paddleocr==2.7.3` + `paddlepaddle==2.6.2` — buộc hạ về API 2.x cũ
   (PP-OCR đời thấp hơn nhiều so với PP-OCRv6 mà bản 3.x dùng), đồng thời
   có nguy cơ xung đột `numpy`/`pandas` do ràng buộc version cũ.

2. **RapidOCR (rapidocr==3.9.2, backend onnxruntime)** — loại bỏ.
   - Ưu điểm đã xác nhận: không phụ thuộc `paddlepaddle` (loại bỏ tận gốc
     rủi ro PIR), hỗ trợ tiếng Việt (`vi`) qua model PP-OCRv6 (xác nhận
     qua tài liệu Model List chính thức), cấu trúc I/O verify được qua
     source thật (`RapidOCROutput.boxes` dạng tứ giác `(N,4,2)`,
     `LoadImage` giả định `numpy.ndarray` đầu vào là BGR - cần tự
     `cv2.cvtColor(RGB2BGR)`).
   - Vấn đề triển khai đã gặp và tự sửa trong phiên: (a) `onnxruntime`
     KHÔNG được khai báo là dependency chính thức của `rapidocr` (kể cả
     dạng extras) - phải tự thêm dòng riêng vào `requirements.txt`; (b)
     `onnxruntime>=1.24` không có wheel cho macOS Intel - phải hạ về
     `onnxruntime==1.23.2` (verify thật qua venv sạch); (c) lỗi lazy
     loading tự triển khai: `recognize()` gọi thẳng `self._ocr(...)`
     thay vì `self._get_ocr()(...)`, khiến `self._ocr` luôn là `None` ->
     `TypeError: 'NoneType' object is not callable`.
   - **Lý do loại bỏ cuối cùng: chất lượng nhận dạng tiếng Việt kém**,
     xác nhận qua debug thật của người vận hành trên `HD2026-0001_scanned.pdf`
     (không phải do bug code - pipeline chạy không crash, nhưng text OCR
     ra sai nhiều). Đây là lý do quyết định, vượt trên mọi ưu điểm về
     dependency/cài đặt.

3. **Tesseract 5.x + tessdata_best** — **chọn cuối cùng**. Verify thật
   bằng cách chạy `pytesseract.image_to_data()` (Tesseract 5.3.4,
   `vie.traineddata` tải từ `tesseract-ocr/tessdata_best` chính thức)
   trên đúng `HD2026-0001_scanned.pdf` - kết quả đọc đúng gần như tuyệt
   đối, giữ nguyên dấu tiếng Việt, khớp gần 100% với nội dung PDF gốc.
   Bounding box trả về sẵn dạng rect trục-thẳng (`left,top,width,height`)
   - đơn giản hơn RapidOCR/PaddleOCR (không cần bước quy tứ giác->rect).

### Phương án cân nhắc nhưng không triển khai: Hybrid (Tesseract Det + VietOCR Rec)

Được đề xuất giữa phiên, đánh giá qua tra cứu thật (PyPI, GitHub source
`pbcquoc/vietocr`): VietOCR dùng PyTorch (`import torch`/`torchvision`
xác nhận qua source) nhưng **không khai báo `torch` là dependency chính
thức** (giống hệt mẫu hình `rapidocr`/`onnxruntime`) - phải tự cài
riêng, nặng hơn nhiều so với `onnxruntime`. Model weight tải qua Google
Drive (`gdown`) - nguồn tải thứ 3 (khác `bcebos.com` của PaddleOCR,
`modelscope.cn` của RapidOCR), có rủi ro rate-limit thật của Google
Drive với file phổ biến. Kiến trúc Hybrid cộng dồn CẢ HAI nhược điểm
(Tesseract: binary hệ thống; VietOCR: framework nặng), không né được
nhược điểm nào. Quyết định: **hoãn sang Future Improvements** - Tesseract
+ tessdata_best đã đủ tốt qua thực nghiệm thật (Rule 9 DEVELOPMENT_WORKFLOW:
"Never optimize early"), chỉ quay lại Hybrid nếu có dữ liệu thật cho
thấy `tessdata_best` không đủ (chữ viết tay, font lạ, ảnh chất lượng
kém).

### Hệ quả kiến trúc quan trọng: KHÔNG áp dụng Lazy Loading (khác ADR-046)

`ADR-046` (Lazy Loading cho `OCREngine`, áp dụng cho bản PaddleOCR) đã
được xem xét lại và **không mang sang Tesseract**: Tesseract hoạt động
qua `subprocess` gọi binary hệ thống mỗi lần `image_to_data()` được gọi
- không giữ "model nặng" nào trong bộ nhớ tiến trình, nên không có gì
cần trì hoãn khởi tạo. `OCREngine.__init__()` (bản Tesseract) chỉ làm 1
việc: fail-fast kiểm tra `vie.traineddata` tồn tại (raise
`FileNotFoundError` kèm URL tải + đường dẫn đích nếu thiếu) và dựng
sẵn chuỗi cấu hình `--tessdata-dir ... --psm ... --oem ...` dùng lại cho
mọi lần gọi. ADR-046 vẫn giữ nguyên giá trị lịch sử/tham khảo cho các
OCR engine dạng "nạp model vào tiến trình" trong tương lai, nhưng không
còn áp dụng cho `OCREngine` hiện tại.

Confirmed trong implementation: `core/ocr_engine.py`, `requirements.txt`
(`pytesseract==0.3.13`), `config.py::TESSDATA_DIR`,
`core/constants.py::OCR`.

------------------------------------------------------------------------

## ADR-048 --- PageImage Render RGB (Amend ADR-026), Kèm PageImage.channels

**Status:** Accepted (amends ADR-026)

`ADR-026` (Eager, Raw **Grayscale** Page Image Rendering) được sửa lại:
`PDFReader._render_page_image()` nay render **RGB** (`fitz.csRGB`) thay
vì `fitz.csGRAY`.

**Lý do đổi (không phải vì tốc độ):** giữ màu thật cho OCR - hoá đơn
Việt Nam thường có con dấu đỏ, chữ ký mực màu; GRAY->RGB giả (R=G=B)
không phục hồi được màu đã mất, trong khi RGB thật giúp OCR tận dụng độ
tương phản màu thật. Cân nhắc chi phí: RGB tốn gấp 3 lần bộ nhớ/trang
(~24.9 MB so với ~8.3 MB ở A4/300 DPI) áp dụng cho MỌI trang của MỌI
PDF (kể cả Digital-mode không bao giờ chạy OCR, do `PDFReader` chạy
trước `PDFDetector`, không biết trước trang nào cần OCR - ADR-016). Chấp
nhận đánh đổi này vì mục tiêu chất lượng màu, không phải vì "tránh
convert 2 lần" (lợi ích tốc độ không đáng kể so với chi phí bộ nhớ).

**Đồng thời:** `PageImage` (`core/models.py`) được thêm field
`channels: int = 3` - tự mô tả số kênh màu (DP-008, Explicit Over
Implicit, đúng tinh thần ADR-026 gốc), tránh giả định ngầm 1 hay 3 kênh
tại nơi tiêu thụ (`OCREngine._to_numpy_array()`). Docstring `PageImage`
đổi "Raw grayscale pixmap" -> "Raw pixmap" (không còn cố định grayscale).

Đồng thời sửa `core/constants.py::Image.COLORSPACE` từ `"gray"` ->
`"rgb"` (hằng số đã tồn tại từ trước nhưng không thực sự được
`pdf_reader.py` sử dụng - sửa để không sai lệch thêm với thực tế, dù
vẫn là constant chưa dùng tới).

Confirmed trong implementation: `core/pdf_reader.py::PDFReader._render_page_image()`,
`core/models.py::PageImage`, `core/constants.py::Image`.

------------------------------------------------------------------------

## ADR-049 --- OCR Deskew: Giữ Nguyên Canvas + Ngưỡng Chặn Góc Giả (DESKEW_MAX_ANGLE)

**Status:** Accepted

`OCREngine` tự triển khai bước làm thẳng trang (deskew) trước khi đưa
vào OCR engine (độc lập với engine nào được chọn - đã giữ nguyên logic
qua cả 3 lần đổi thư viện). 2 ràng buộc thiết kế:

1. **Giữ nguyên kích thước canvas khi xoay** (`cv2.warpAffine` với
   `dsize` bằng đúng `(width, height)` gốc, biên trống lấp màu trắng
   `DESKEW_FILL_VALUE=255`) - đảm bảo `page_image.width/height` vẫn là
   mẫu số chuẩn hoá hợp lệ cho `Extractor._normalize_bbox()`, không cần
   đổi contract `recognize()`.

2. **`DESKEW_MAX_ANGLE = 10.0`** (mới, phát hiện qua chạy thật) - ngưỡng
   chặn trên cho góc nghiêng ước lượng được. Nguyên nhân: thuật toán ước
   lượng góc (`cv2.minAreaRect()` bao toàn bộ điểm nội dung của cả
   trang) được thiết kế cho 1 khối văn bản đặc dày (kỹ thuật phổ biến,
   nguồn gốc pyimagesearch), KHÔNG phù hợp với tài liệu nhiều khối rải
   rác như hoá đơn (header/block bán/block mua/bảng chi tiết/chữ ký).
   Với trang A4 khổ đứng, nội dung rải theo chiều cao khiến
   `minAreaRect` bám theo tỷ lệ khung trang (cao hơn rộng) thay vì tỷ lệ
   1 dòng chữ, trả về góc giả gần `-90°` theo quy ước OpenCV -> `_deskew`
   xoay ngang toàn bộ trang 90°, làm hỏng vị trí mọi `WordToken`, dẫn
   đến Key Matching/Windowing thất bại toàn bộ ở tầng `TemplateMatcher`
   (không phải lỗi ở `TemplateMatcher` - triệu chứng "Excel không ghi
   nhận dữ liệu nào" bắt nguồn từ đây).

   Giải pháp: sau khi chuẩn hoá góc về khoảng chuẩn, nếu `abs(angle) >
   DESKEW_MAX_ANGLE` -> coi là artifact của thuật toán (không phải
   nghiêng thật), trả `0.0` (bỏ qua xoay). Hoá đơn scan văn phòng hiếm
   khi nghiêng thật quá 10° - góc lớn hơn gần như chắc chắn là nhầm lẫn
   của `minAreaRect`, không phải nghiêng thật.

Đây là giới hạn cố hữu đã biết của kỹ thuật minAreaRect-toàn-trang khi
áp dụng cho tài liệu nhiều khối, không phải lỗi implementation - cùng
loại phát hiện với gap-based merge (ADR-044)/section collision
(ADR-045): phát hiện qua chạy thật, không thấy được qua review tĩnh.

Confirmed trong implementation: `core/ocr_engine.py::OCREngine._estimate_skew_angle()`,
`core/constants.py::OCR.DESKEW_MAX_ANGLE`.

------------------------------------------------------------------------

## ADR-050 --- app.log Ghi Đè Mỗi Lần Chạy (Amend ADR-040)

**Status:** Accepted (amends ADR-040)

`ADR-040` quy định `logs/app.log` **tích luỹ** qua các lần chạy
(`FileHandler` append mặc định, chủ đích giữ lịch sử đầy đủ). Hành vi
này được đổi thành **ghi đè mỗi lần chạy** (giống `reports/Report.txt`
đã có từ đầu).

**Lý do đổi:** log tích luỹ qua nhiều lần chạy khiến file phình to theo
thời gian và gây khó đọc log của lần chạy gần nhất - đây là chi phí vận
hành thực tế phát sinh sau khi dùng thử, không phải lỗi thiết kế ban
đầu.

**Lưu ý:** điều này làm mất đi lý do ban đầu của ADR-040 khi tách 2 kênh
output (`app.log` cho dev/admin tích luỹ dài hạn vs `report.txt` cho
end-user ghi đè mỗi lần) - nay cả 2 kênh đều ghi đè, chỉ còn khác nhau ở
đối tượng đọc (dev/admin vs end-user) và mức độ chi tiết (log kỹ thuật
per-file vs summary Excel), không còn khác nhau ở vòng đời file. Ghi
nhận để cân nhắc nếu sau này cần truy vết lịch sử nhiều lần chạy (sẽ cần
cơ chế khác, ví dụ log xoay vòng theo timestamp - chưa có kế hoạch,
chưa cần quyết định ngay).

Confirmed trong implementation: `utils/logger.py::_configure_root()`.

------------------------------------------------------------------------

## ADR-051 --- ValueConverter Strip Hậu Tố Đơn Vị Tiền Tệ VND Trước Khi Convert Decimal

**Status:** Accepted

Phát hiện qua debug thực nghiệm trên batch PDF Scanned thật (Report.txt:
13/~90 file, ~15% data, thiếu đều 3 field subtotal/vat_amount/total_amount).
Debug trực tiếp TemplateMatcher.extract_fields() (xem debug.txt) xác nhận:
Windowing hoạt động đúng (candidate token nằm đúng trong window), nhưng
_select_best_value() trả None vì value_pattern: "^[0-9.,]+$" không khớp
token OCR dạng "4,842,303VND" - Tesseract gộp đơn vị tiền tệ dính liền số
thành 1 token duy nhất khi bản scan không có khoảng trắng rõ ràng.

Đây là lỗi cùng loại với ADR-043 (% dính liền vat_rate), nhưng chặn sớm
hơn: ở tầng value_pattern (TemplateMatcher), trước khi ValueConverter kịp
chạy - không chỉ là vấn đề của _to_decimal().

Giải pháp - 2 lớp, đối xứng nhau:

1. value_pattern của 3 field tiền tệ trong sample_invoice_v1.json (v3->v4)
   nới để chấp nhận hậu tố tiền tệ tùy chọn:
   ^[0-9.,]+\s*(?:(?i:vn[dđ])|₫|[đĐ])?$
2. ValueConverter._to_decimal() gọi _strip_currency_suffix() mới, strip
   hậu tố trước khi Decimal() parse.

7 biến thể được xử lý, chia 2 nhóm theo mức độ rủi ro:

- vnd, VND, vnđ, VNĐ, ₫ - strip vô điều kiện (case-insensitive qua
  .lower()), vì chuỗi ≥2 ký tự hoặc ký tự Unicode riêng biệt không thể là
  1 phần hợp lệ khác của số Decimal.
- đ, Đ (1 ký tự) - CHỈ strip khi ký tự liền trước là chữ số (0-9), không
  strip vô điều kiện. Lý do: 1 ký tự chữ cái tiếng Việt đơn lẻ có rủi ro
  trùng nội dung/nhiễu OCR khác cao hơn hẳn so với chuỗi dài hơn - cùng
  lớp rủi ro với "key_tokens 1 từ" đã ghi nhận ở Session 2026-08-01/02
  (Known Limitations), dù xảy ra ở bước khác (Value parsing, không phải
  Key Matching).

Rủi ro còn lại (ghi nhận minh bạch, không loại bỏ hoàn toàn): ràng buộc
vị trí giảm đáng kể nhưng không triệt tiêu khả năng OCR noise tạo đúng 1
ký tự đ/Đ ngay sau 1 chữ số hợp lệ không phải ký hiệu tiền - dẫn đến
strip nhầm, sai lệch số âm thầm (không có warning, khác với field ra None
được ghi nhận ở Report.txt qua ADR-032/033). Cùng nhóm rủi ro cố hữu đã
ghi nhận ở ADR-044 (gap-based merge tràn field) / ADR-045 (section
collision lý thuyết) - cần thêm dữ liệu thật đa dạng hơn để đánh giá tần
suất.

Verify: áp dụng patch, chạy lại đúng batch PDF từng tạo ra Report.txt gốc
(13 dòng cảnh báo vat_amount/subtotal/total_amount) - PASS toàn bộ test
case đang có.

Confirmed trong implementation: core/value_converter.py::ValueConverter._strip_currency_suffix(),
resources/templates/sample_invoice_v1.json (v4).

------------------------------------------------------------------------

## ADR-052 --- ValueConverter Tự Phục Hồi Số Bị OCR Đọc Nhầm Lẫn Dấu ',' và '.'

**Status:** Accepted

Phát hiện qua thực nghiệm tiếp theo ADR-051: sau khi xử lý hậu tố đơn vị
tiền tệ, batch PDF Scanned vẫn còn <3% case bị OCR đọc nhầm lẫn dấu phân
cách ',' <-> '.' trong chuỗi số. Đây là lỗi NGHIÊM TRỌNG hơn các lỗi
trước (VND, %) vì thường KHÔNG gây Decimal() raise exception - chuỗi sau
khi áp thousand_sep/decimal_sep vẫn đúng cú pháp Decimal nhưng SAI TRỊ SỐ
(silent corruption, có thể lệch tới hàng nghìn lần), khác hẳn field ra
None đã được Report.txt ghi nhận qua ADR-032/033.

Giải pháp: ValueConverter._to_decimal() thêm bước kiểm tra cấu trúc
chuỗi (_looks_ambiguous()) TRƯỚC khi áp thousand_sep/decimal_sep - độc
lập với việc Decimal() có raise exception hay không, vì exception không
phải tín hiệu đáng tin cậy cho loại lỗi này.

6 dấu hiệu khả nghi (_looks_ambiguous(), dựa trên VỊ TRÍ dấu, không dựa
loại ký tự - vì bản thân loại ký tự là điểm OCR hay đọc nhầm):

1. Có cả 2 loại dấu ',' và '.' cùng xuất hiện, và dấu CUỐI CÙNG không
   phải decimal_separator đã cấu hình trong template.
2. decimal_separator đã cấu hình xuất hiện nhiều hơn 1 lần.
3. Vi phạm quy tắc 3 chữ số: cụm chữ số không phải cụm đầu (và không
   phải cụm cuối nếu cụm cuối là decimal) không có đúng 3 chữ số.
4. Vị trí phi lý: dấu phân cách đứng ở đầu hoặc cuối chuỗi.
5. Double punctuation: 2 dấu phân cách đứng liền nhau.
6. Decimal Tail Length: phần sau dấu cuối (khi dấu cuối là
   decimal_separator) dài hơn NumberRepair.DECIMAL_TAIL_MAX_LENGTH
   (mặc định = 3) - nhiều khả năng thực ra là 1 nhóm nghìn bị đọc nhầm
   thành decimal.

Khi khả nghi, _normalize_number_separators() suy luận lại: nếu cụm cuối
có độ dài hợp lý cho phần thập phân -> coi là decimal, còn lại strip
làm thousand; ngược lại -> coi TOÀN BỘ là thousand separator, ưu tiên
giữ đúng ĐỘ LỚN số hơn đoán sai vị trí thập phân (rủi ro đoán sai vị trí
thập phân được đánh giá thấp hơn rủi ro sai lệch độ lớn số).

Giới hạn đã biết, không giải quyết được (ghi nhận minh bạch):

- Trường hợp cụm cuối có ĐÚNG 3 chữ số VÀ dấu cuối trùng ngẫu nhiên với
  decimal_separator đã cấu hình (do đọc nhầm) - không đủ tín hiệu cấu
  trúc để phân biệt với trường hợp hợp lệ thật (phần thập phân dài đúng
  3 chữ số, dữ liệu VND đã xác nhận CÓ THỂ có phần lẻ, không giả định số
  nguyên). Giữ nguyên hành vi cũ (không đoán) ở đúng ranh giới này.
- Trường hợp OCR làm MẤT HẲN dấu phân cách (VD "4842303" liền khối,
  không dấu vết vị trí) - không có cấu trúc nào để suy luận. Nếu chuỗi
  liền khối vẫn đúng cú pháp Decimal, sẽ KHÔNG bị flag khả nghi và KHÔNG
  raise exception -> có thể silent corruption tương tự nếu xảy ra. Chưa
  ghi nhận qua thực nghiệm tại thời điểm ADR này được chấp thuận - cần
  theo dõi qua dữ liệu thật tương lai, chưa có giải pháp.
- NumberRepair.DECIMAL_TAIL_MAX_LENGTH = 3 là giá trị ước lượng ban đầu
  (không có cơ sở xác định chính xác độ dài phần thập phân VND trong dữ
  liệu thật) - dự kiến cho người dùng tuỳ chỉnh theo loại hóa đơn ở
  version sau (xem PROJECT_CONTEXT.md §18).

Verify: sau khi áp dụng kết hợp với ADR-053 (DPI + Preprocess), tỷ lệ
lỗi nhầm lẫn ',' / '.' giảm từ mức quan sát ban đầu xuống dưới 0.5% trên
batch thực nghiệm. Chưa về 0% - ghi nhận là hướng cải thiện tiếp tục ở
v2.0 (xem PROJECT_CONTEXT.md §18), không coi là đã giải quyết triệt để.

Confirmed trong implementation: core/value_converter.py::ValueConverter._looks_ambiguous(),
_normalize_number_separators(), _split_number_groups(), _parse_plain_decimal();
core/constants.py::NumberRepair.

------------------------------------------------------------------------

## ADR-053 --- OCR: Tăng DPI 300→450 & Thêm Bước Preprocess (CLAHE + Sharpen) Trước Tesseract

**Status:** Accepted

Cùng đợt điều tra với ADR-051/052 (Report.txt cho thấy ~15% data thiếu
field tiền tệ trên PDF Scanned), phát hiện thêm: kể cả sau khi field
được trích đúng vị trí, nội dung số đôi khi vẫn sai vì Tesseract đọc
nhầm dấu ',' và '.' - nguyên nhân gốc một phần đến từ chất lượng ảnh đầu
vào (DPI, độ tương phản/sắc nét), không chỉ do logic parse.

**Thay đổi 1 - DPI 300 -> 450** (`core/constants.py::Image.DPI`):

Mức 300 DPI là mức tối ưu cho độ chính xác OCR tổng thể theo các báo cáo
hiệu năng phổ biến (Tesseract/ABBYY, khảo sát dải 1-600 DPI), nhưng các
báo cáo đó đánh giá trên toàn bộ ký tự nói chung, không xét riêng các
ký tự cực nhỏ như dấu ',' / '.' - đuôi dấu phẩy (điểm phân biệt duy nhất
với dấu chấm) chỉ chiếm vài pixel ở 300 DPI, xấp xỉ ngưỡng nhiễu/
anti-aliasing.

Qua nhiều vòng thực nghiệm thực tế (không phải suy đoán lý thuyết), giá
trị cuối cùng được xác nhận là **450 DPI** (khác đề xuất ban đầu 400 DPI
- điều chỉnh dựa trên kết quả đo thật qua nhiều lần test, đúng tinh thần
"chạy thật để verify" nhất quán trong dự án). Có thêm cơ sở tham chiếu
từ tài liệu Tesseract/ABBYY: mức DPI phù hợp phụ thuộc cỡ font/khổ giấy
- font >10pt (hóa đơn A4 chuẩn) phù hợp khoảng 400 DPI, font <8pt (hóa
đơn A5 hoặc A4 có bảng chỉ số phụ chữ nhỏ) cần tới 600 DPI. Giá trị 450
được chọn làm mức chung cho v1 (không phân biệt khổ giấy) - kế hoạch
DPI thích ứng theo khổ giấy được ghi nhận cho v2.0 (xem
PROJECT_CONTEXT.md §18).

Đánh đổi đã biết: chi phí bộ nhớ/thời gian tăng theo diện tích
(DPI² ~ (450/300)² ≈ 2.25x so với mức cũ), áp dụng cho MỌI trang của MỌI
PDF (kể cả Digital-mode không bao giờ gọi OCR - do PDFReader render
page_image trước khi PDFDetector quyết định mode, ADR-026). Chấp nhận
đánh đổi này dựa trên kết quả thực nghiệm của người vận hành.

**Thay đổi 2 - Preprocess trước Tesseract** (`OCREngine._preprocess()`,
mới, chạy SAU `_deskew()`):

- CLAHE (Contrast Limited Adaptive Histogram Equalization) tăng contrast
  cục bộ - chọn thay vì equalizeHist toàn cục vì hoá đơn thường có vùng
  sáng/tối không đều, và CLAHE giảm rủi ro khuếch đại nhiễu ở vùng chi
  tiết nhỏ (đuôi dấu phẩy) so với cân bằng histogram toàn ảnh.
- Unsharp masking làm sắc nét cạnh ký tự, sigma nhỏ (bán kính hẹp) để
  tránh lan halo sang vùng nét mảnh; mức tăng cường (amount) khởi đầu ở
  mức thận trọng vì amount cao có nguy cơ tạo ringing artifact quanh nét
  mảnh - có thể LÀM XẤU THÊM chính vấn đề đang giải quyết thay vì cải
  thiện.
- Thứ tự gọi `_deskew()` trước `_preprocess()` được xác nhận qua nhiều
  lần thực nghiệm thực tế: KHÔNG có sự khác biệt kết quả rõ ràng so với
  thứ tự ngược lại. Giữ nguyên thứ tự deskew-trước (đã có sẵn trong
  pipeline từ ADR-049) để không phát sinh thay đổi không cần thiết.
- Toàn bộ tham số (`PREPROCESS_CLAHE_CLIP_LIMIT`,
  `PREPROCESS_CLAHE_TILE_GRID_SIZE`, `PREPROCESS_SHARPEN_SIGMA`,
  `PREPROCESS_SHARPEN_AMOUNT`) khai báo tường minh trong
  `core/constants.py::OCR`, cùng loại "giá trị ước lượng ban đầu, cần
  tinh chỉnh khi có dữ liệu thật đa dạng hơn" như `TemplateMatching.*`/
  `OCR.DESKEW_*` đã có.

Verify: kết hợp ADR-052 (heuristic sửa lỗi dấu) + ADR-053 (DPI 450 +
Preprocess), tỷ lệ lỗi nhầm lẫn ',' / '.' giảm xuống dưới 0.5% trên
batch thực nghiệm - PASS toàn bộ test case hiện có. Chưa về 0%, ghi nhận
tiếp tục cải thiện ở v2.0.

Confirmed trong implementation: core/constants.py::Image.DPI,
core/constants.py::OCR (4 hằng số Preprocess mới),
core/ocr_engine.py::OCREngine._preprocess().

------------------------------------------------------------------------

## ADR-054 --- Amend ADR-048: Lý Do Giữ RGB Điều Chỉnh Lại Cho Phù Hợp Với Tesseract

**Status:** Accepted (amends ADR-048)

ADR-048 (đổi PageImage sang render RGB thay vì Grayscale) được quyết
định trong bối cảnh OCR engine tại thời điểm đó là PaddleOCR, với lý do
"giữ màu thật giúp OCR tận dụng độ tương phản màu thật". Từ ADR-047, OCR
engine đã chuyển hẳn sang Tesseract - cần đánh giá lại lý do này có còn
đúng không.

Về mặt kỹ thuật, Tesseract (kể cả LSTM/tessdata_best) tự quy đổi ảnh về
grayscale/nhị phân ở bước xử lý nội bộ đầu tiên (nền tảng Leptonica),
không có cơ chế học đặc trưng màu trong việc nhận diện ký tự như các
detection model dạng CNN (VD PaddleOCR). A/B test thực tế trên bộ dữ
liệu hiện có giữa GRAY và RGB không cho thấy khác biệt rõ ràng về độ
chính xác nhận diện.

**Quyết định: VẪN GIỮ RGB**, nhưng đổi lý do chính sang: tính bất khả
nghịch của việc chuyển đổi. Grayscale -> RGB không khôi phục lại được
thông tin màu đã mất, trong khi RGB -> Grayscale luôn thực hiện được ở
bất kỳ điểm nào trong pipeline khi cần (VD `_estimate_skew_angle()` đã
tự chuyển RGB->GRAY nội bộ). Về lâu dài, không thể dự đoán chắc chắn
liệu có bước xử lý tương lai nào cần khai thác kênh màu riêng biệt hay
không (VD: tách kênh đỏ để làm nổi bật con dấu/mực đỏ trước khi OCR) -
giữ RGB ở tầng PDFReader bảo toàn tùy chọn này, đổi lại chấp nhận chi
phí bộ nhớ ~3x/trang so với Grayscale (đã ghi nhận ở ADR-048 gốc).

Lưu ý: `OCREngine._preprocess()` (ADR-053) hiện tại tự chuyển ảnh về
grayscale nội bộ để xử lý CLAHE/sharpen, sau đó nhân bản lại 3 kênh
giống hệt nhau nếu input là RGB - nghĩa là "RGB" thực tế đưa vào
Tesseract tại bước cuối cùng của pipeline hiện KHÔNG còn mang thông tin
màu thật nào. Đây là hệ quả đã biết, không phải mâu thuẫn với quyết định
giữ RGB ở tầng PDFReader (2 tầng phục vụ 2 mục đích khác nhau: PDFReader
bảo toàn dữ liệu gốc cho khả năng dùng lại tương lai; OCREngine tối ưu
riêng cho pipeline Tesseract hiện tại).

Confirmed trong implementation: không đổi core/pdf_reader.py (giữ
nguyên như ADR-048); core/ocr_engine.py::OCREngine._preprocess() (ADR-053).

------------------------------------------------------------------------

## ADR-055 --- Thứ Tự Ưu Tiên Hiển Thị Warning Theo RuleCategory (PDFDetector)

**Status:** Accepted

`Worker._format_note()` từng chọn `analysis.warnings[0]` để hiển thị lên
UI, nhưng `DocumentAnalysis.warnings` được `PDFDetector.analyze()` tạo
bằng cách flatten `Evidence.warnings` theo đúng thứ tự các rule chạy
trong `_evaluate_rules()` - luôn cố định `(text_coverage, image_coverage,
mixed_content, content_coverage, page_layout, ...)`. Hệ quả: warning
đầu tiên luôn là của `text_coverage` (nếu có), bất kể rule này có thật
sự đóng góp vào quyết định `mode` cuối cùng hay không - có thể hiển thị
cảnh báo "bằng chứng yếu" của 1 rule đơn lẻ cạnh 1 kết luận High
confidence được củng cố bởi các rule khác, gây cảm giác mâu thuẫn dù dữ
liệu không sai. Phát hiện qua thực nghiệm Session 2026-08-08/09.

**2 phương án được thảo luận:**
- Phương án A (đã chọn): sửa tại `PDFDetector.analyze()` - sắp lại thứ
  tự warnings theo độ ưu tiên `RuleCategory` trước khi trả về.
- Phương án B (không chọn): sửa tại `Worker._format_note()` - tự duyệt
  `analysis.evidence`, ưu tiên category tại tầng UI, không đổi
  `PDFDetector`.

**Lý do chọn Phương án A:** sửa đúng gốc, mọi consumer tương lai của
`DocumentAnalysis.warnings` (không chỉ `Worker`) đều nhận thứ tự hợp lý
mà không phải tự cài lại logic lọc riêng.

**Thiết kế:** `PDFDetector._WARNING_CATEGORY_PRIORITY` định nghĩa thứ
tự ưu tiên category (không hard-code tên rule, để tự tương thích khi
Document/Graphics Rules được thêm - xem ADR-057): category liên quan
**chất lượng tài liệu** (`QUALITY`, `LAYOUT`, `DOCUMENT`, `GRAPHICS`)
ưu tiên trước category mô tả **độ không chắc chắn của riêng 1 rule**
(`CONSISTENCY`, `IMAGE`, `TEXT`). `_evidence_warnings_ordered()` (method
mới) sort `Evidence` theo `key=priority` (dùng `sorted()` ổn định -
Evidence cùng category giữ nguyên thứ tự tương đối ban đầu) trước khi
flatten thành `warnings`.

**Dọn kèm:** nhánh `extraction.warnings` trong
`Worker._format_note()` bị xóa (dead code - `Worker._process_pdf()`
không bao giờ gọi `Extractor.extract()` khi `mode is UNKNOWN`, nên
nhánh set `warnings` khác rỗng trong `Extractor.extract()` không bao
giờ chạy tới trong pipeline thật). `_format_note()` nay chỉ nhận
`analysis`, không còn nhận `extraction`.

Confirmed trong implementation: `core/pdf_detector.py::PDFDetector._evidence_warnings_ordered()`,
`PDFDetector._WARNING_CATEGORY_PRIORITY`; `ui/worker.py::Worker._format_note()`.

------------------------------------------------------------------------

## ADR-056 --- Extractor.extract() Raise ValueError Khi UNKNOWN (Sửa Code Khớp Lại ADR-027)

**Status:** Accepted (đồng bộ hóa với ADR-027)

Phát hiện qua rà soát source thật (đóng v1, Part 1): `core/extractor.py::
Extractor.extract()` **không hề raise** `ValueError` khi
`analysis.mode is AnalysisMode.UNKNOWN` như ADR-027 đã mô tả - code thật
trả về gracefully `ExtractionResult(words_by_page={}, warnings=(...))`.
Sai lệch này tồn tại xuyên suốt `ARCHITECTURE_DECISIONS.md` (ADR-027),
`CHANGELOG.md` (mục "Extractor — New Module") và `SESSION_SUMMARIES.md`
(Session 2026-07-31) - cả 3 đều mô tả giống nhau (raise), khác thực tế
source.

**2 phương án được thảo luận:**
- Phương án 1 (không chọn): sửa tài liệu cho khớp code (giữ hành vi
  graceful). Vấn đề: nhánh graceful này là dead code trong pipeline
  thật (`Worker._process_pdf()` đã tự chặn, không bao giờ gọi
  `extract()` với UNKNOWN) - nếu giữ graceful, 1 lỗi lập trình tương lai
  (VD sửa `Worker` gây gọi nhầm) sẽ bị "nuốt" âm thầm thay vì lộ ra
  ngay, vi phạm chính tinh thần ADR-027 (phân biệt "Detector không
  quyết định được" vs "Extractor bị gọi sai hợp đồng").
- Phương án 2 (đã chọn): sửa code cho khớp ADR-027 - thêm
  `raise ValueError`.

**Lý do chọn Phương án 2:** ADR-027 là quyết định kiến trúc có lập luận
rõ ràng (phân định 2 tầng lỗi khác bản chất - business outcome vs
programming-contract violation), không phải mô tả tùy tiện. Sự lệch pha
nhiều khả năng do lúc implement code được viết graceful hơn dự định rồi
quên đồng bộ lại. Vì `Worker` đã chặn đúng ở tầng gọi, việc thêm `raise`
không ảnh hưởng pipeline thật hiện tại - chỉ thêm 1 lớp phòng vệ
(defense in depth) cho lỗi lập trình tương lai.

**Hệ quả kèm theo:** `ExtractionResult.warnings` (`core/models.py`)
sau patch này không còn nơi nào gán giá trị khác rỗng trong
`core/extractor.py` - trở thành field chết. Đã xóa khỏi
`ExtractionResult` (khác quyết định giữ lại Nhóm B các model dự phòng
khác - xem PROJECT_CONTEXT.md §14, field này không có ý đồ dự phòng
nào được ghi nhận, khác `SessionResult`/`ProcessError`).

Confirmed trong implementation: `core/extractor.py::Extractor.extract()`,
`core/models.py::ExtractionResult`.

------------------------------------------------------------------------

## ADR-057 --- Bổ Sung Document Rules & Graphics Rules Cho PDFDetector (RC-001/RC-004)

**Status:** Accepted

TDS (`PDF_Detector_Technical_Design.docx` §7.2) định nghĩa 7 Rule
Category, nhưng `PDFDetector` trước patch này chỉ implement 5/7 (Text,
Image, Consistency, Quality, Layout) - Document (RC-001) và Graphics
(RC-004) còn thiếu, ghi nhận là Known Issue từ Session 2026-07-29.

**Xác nhận quan trọng trước khi thiết kế:** TDS §7.2 chỉ đặc tả RC-001/
RC-004 ở mức **định tính, cấp cao** ("đánh giá đặc điểm tổng quát của
tài liệu...", "đánh giá đối tượng đồ họa và vector...") - không có công
thức/ngưỡng cụ thể nào, kể cả cho 5 rule đã implement (TDS Chương 5.4
xác nhận: *"không phải mọi dữ liệu có thể thu thập đều cần trở thành
metric... mọi diễn giải vẫn thuộc trách nhiệm của reasoning engine"*).
Vì vậy 2 rule mới là **thiết kế mới hoàn toàn** (không phải "khôi phục"
nội dung TDS), dựa trên field đã có sẵn trong `AnalysisContext` nhưng
trước đó chưa được dùng để tạo `supports`.

**Document Rule (`document_metadata`, category `DOCUMENT`):** dùng
`AnalysisContext.metadata` (Producer/Creator). Nếu chứa từ khóa gợi ý
phần mềm scan (`_SCAN_METADATA_KEYWORDS`: scan/scanner/scanned/
camscanner/adobe scan/naps2/vuescan/scansnap) -> `supports={SCANNED:
0.20}`. **Không** tạo `supports` cho DIGITAL khi thiếu từ khóa (vắng
mặt tín hiệu không phải bằng chứng - metadata có thể mất/ghi đè qua
nhiều lần re-save, đúng DP-003 "Explainability First"/nguyên tắc chỉ
suy luận từ tín hiệu dương tính đã áp dụng nhất quán ở 5 rule cũ).

**Graphics Rule (`vector_graphics_coverage`, category `GRAPHICS`):**
dùng `AnalysisContext.drawing_page_ratio` (đã tồn tại sẵn, trước đó chỉ
nằm trong `metrics` phụ của `content_coverage`, chưa từng ảnh hưởng
`supports`). Cơ sở: PDF Scanned thuần túy (ảnh raster phủ trang) về bản
chất không có vector drawing operations
(`page.get_drawings()` không tính pixel ảnh). Nếu
`drawing_page_ratio >= 0.50` -> `supports={DIGITAL: 0.20}`. Tương tự,
không tạo `supports` cho SCANNED khi thiếu vector graphics (nhiều hóa
đơn Digital cũng không dùng khung/bảng vector - không phải bằng chứng).

**Trọng số 0.20 cho cả 2 rule (thấp, cố ý):** cả 2 rule đều **chưa qua
thực nghiệm với PDF thật đa dạng** (khác 5 rule cũ đã verify trên PDF
thật) - trọng số thấp để không làm lệch các quyết định biên (DIGITAL/
HYBRID) vốn đã ổn định. Đã tự kiểm tra: tổng `supports` tối đa theo
từng mode sau khi thêm 2 rule mới (DIGITAL <= 0.90, SCANNED <= 1.15,
HYBRID <= 1.00) đều dưới `_EVIDENCE_SCORE_SCALE = 1.40` - không cần
hiệu chỉnh scale này.

**Đánh dấu placeholder (cùng nhóm `TemplateMatching.*`):**
`_DOCUMENT_RULE_WEIGHT`, `_GRAPHICS_RULE_WEIGHT`,
`_GRAPHICS_DRAWING_PAGE_RATIO = 0.50`, `_SCAN_METADATA_KEYWORDS` đều là
giá trị ước lượng ban đầu, CẦN TINH CHỈNH khi có dữ liệu PDF thật đa
dạng hơn - danh sách từ khóa scan dựa trên tri thức chung, chưa verify
đối chiếu với metadata PDF Scanned thật của dự án.

Verify: chạy thật trên PDF Digital và PDF Scanned đã dùng trước đây -
`DocumentAnalysis.evidence` có đủ 7 phần tử, mode cuối cùng không đổi
so với trước patch (đúng kỳ vọng do trọng số thấp, chỉ ảnh hưởng case
biên gần tie-margin).

Confirmed trong implementation: `core/pdf_detector.py::PDFDetector._evaluate_document_rule()`,
`PDFDetector._evaluate_graphics_rule()`, `PDFDetector._evaluate_rules()`.

------------------------------------------------------------------------