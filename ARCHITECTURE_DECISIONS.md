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
