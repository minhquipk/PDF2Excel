# PROJECT_CONTEXT.md

# PDF Invoice Extractor

> Project Context & Architecture Handover
>
> This document is the single source of truth for the project.
> Any architectural change must be discussed before implementation.

---

# 1. Project Goal

Build a desktop application using Python to automatically extract information
from a large number of PDF invoices and write the extracted data into an
existing Excel template.

Main requirements:

- Scan an entire folder recursively.
- Support thousands of PDF files.
- Detect Digital PDF / OCR PDF automatically.
- Extract invoice information.
- Store intermediate results in memory.
- Write Excel only once after all files have been processed.
- Generate an error report for manual review.

Target users:

Office users with no programming knowledge.

---

# 2. Overall Architecture

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
Parser (pending)
    │
    ▼
PDFResult
    │
    ▼
Memory (list[PDFResult])
    │
    ▼
ExcelWriter (pending)
```

UI is completely separated from business logic.

Worker never accesses UI directly.

Communication is only through Qt Signals.

---

# 3. Current Project Structure

```
PDF2Excel/

    config.py
    main.py

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
        constants.py
        enums.py
        excel_writer.py
        extractor.py
        models.py
        ocr_engine.py
        parser.py
        pdf_detector.py
        pdf_reader.py
        processor.py
```

---

# 4. Modules Completed

Completed:

- constants.py
- enums.py
- models.py
- pdf_reader.py — reads PDF via PyMuPDF, builds `PDFDocument`;
  also reads raw word tuples (`words`) and renders a raw grayscale
  `PageImage` (300 DPI) for every page.
- pdf_detector.py — full reasoning engine (Build Context, Heuristic
  Evaluation, Knowledge Lookup, Confidence Composition, Final
  Decision) per `PDF_Detector_Technical_Design.docx`.
- extractor.py — dispatches extraction strategy per
  `DocumentAnalysis.mode` (Digital / OCR / per-page Hybrid);
  normalizes word geometry (incl. rotation reconciliation for the
  Digital path) into `WordToken`s ready for Parser.
- ocr_engine.py — Mock implementation only (ADR-013); contract is
  final, real OCR backend not yet wired in.
- base_widget.py
- widgets.py
- main_window.py
- worker.py — pipeline integration completed: Reader → Detector →
  Extractor (conditional on a valid mode). Excel writing and invoice
  parsing remain pending.
- processing_table_model.py

Current UI features:

- Input folder
- Output Excel
- Start
- Stop
- Report
- Exit
- Progress bar
- Processing table

Still pending (not yet implemented):

- parser.py (regex-based invoice parsing, consuming
  `ExtractionResult.words_by_page`)
- excel_writer.py
- Report export
- Real OCR backend (ocr_engine.py currently Mock only)
- config.py / main.py (entry point not yet assembled)

Note: `core/processor.py` currently contains only placeholder method
calls (`start/stop/pause/resume`) with no implementation. The actual
orchestrator responsibility (per ADR-004) is currently fulfilled by
`Worker.process()`, not by `processor.py`. This needs clarification
(see Section 14).

Known limitation (deferred to v2.0): pages with both a text layer and
materially relevant image content are extracted from a single source
only (text-layer wins). See CHANGELOG.md / SESSION_SUMMARIES.md,
Session 2026-07-31.

---

# 5. Data Flow

```
Path
  ↓ (PDFReader.read)
PDFDocument
  ↓ (PDFDetector.analyze)
DocumentAnalysis  ──┐
  ↓                 │ (cả 2 cùng làm input cho Extractor)
PDFDocument ─────────┘
  ↓ (Extractor.extract)
ExtractionResult
  ↓ (Parser — pending)
InvoiceInfo
  ↓
PDFResult
  ↓ (accumulate)
list[PDFResult]
  ↓ (ExcelWriter — pending)
.xlsx
```

The application NEVER writes Excel while processing each PDF.

Excel is written only once after all PDFs have been processed.

---

# 6. Important Design Decisions

## Memory First

PDFs are processed one by one.

Each PDF is immediately released from memory after processing.

Only PDFResult objects remain in memory.

This greatly reduces memory usage.

---

## Single Excel Write

Excel writing is expensive.

Never write after each PDF.

Write only once at the end.

---

## process() Responsibility

process() is an orchestrator.

It must NEVER contain PDF parsing logic.

Correct structure:

```
for pdf in pdf_files:

    result = _process_pdf(pdf)

    results.append(result)

_write_excel()
```
This orchestrator responsibility is currently implemented as
`Worker.process()` in `ui/worker.py`.

---

## _process_pdf()

All business logic belongs here.

Current implementation (`Worker._process_pdf()`):

PDF

↓

PDF Reader

↓

PDF Detector

↓

PDFResult (pdf_type / status / note derived from DocumentAnalysis)

The detector is a deterministic reasoning engine. It receives only an
immutable PDFDocument, builds an immutable AnalysisContext, preserves all
heuristic Evidence, optionally consults a read-only KnowledgeRecord, and
returns an immutable DocumentAnalysis with explainable Confidence.

This integration is now real (not Mock) — `Worker._process_pdf()` calls
`PDFReader.read()` and `PDFDetector.analyze()` directly. Extraction,
regex parsing, and Excel writing are still pending and not yet wired
into this method.

---

## Reader Responsibility

PDFReader is responsible only for reading PDF content and converting
PyMuPDF objects into immutable domain models.

PDFReader MUST NOT perform:

- OCR
- Regex parsing
- Invoice extraction
- PDF classification
- Data analysis
- Business validation

PDFReader is the boundary between PyMuPDF and the project domain.

## PDFDocument Strategy

PDFDocument keeps the complete document text.

Reason:

Parser benefits from preserving page relationships and document context.

Memory usage remains acceptable because only one PDF is processed at a time.

## Analyzer Strategy

Analyzer is responsible for collecting document statistics and building
a reusable knowledge cache.

Analyzer does not perform OCR or machine learning.

Knowledge grows incrementally from previous processing sessions.

Note: in the current source, this "Analyzer" role is fulfilled by
`PDFDetector` (Rule System + Confidence Model) as designed in
`PDF_Detector_Technical_Design.docx`. `KnowledgeRecord` accumulation /
lifecycle management (Knowledge System, TDS Chapter 9) is defined at
the design level but not yet implemented in source.

## Source of Truth

Implementation must always be based on the current project source code.

Chat history must never be treated as the implementation reference.

# 7. UI Design

Layout:

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

Processing Table columns:

| Column | Description |
|----------|-------------|
| PDF | File name |
| TYPE | Digital / OCR |
| STATUS | OK / ERROR / OCR... |
| NOTE | Detailed message |

---

# 8. Worker Design

Worker runs in its own QThread.

MainWindow never performs heavy work.

Signals:

- started
- progress
- file_processed
- finished
- cancelled
- error

---

# 9. Progress Strategy

Progress is based on

processed PDFs / total PDFs

Elapsed time and ETA are updated separately.

---

# 10. Coding Conventions

- Python 3.12+
- Type hints everywhere.
- Dataclass for data models.
- Enum for fixed values.
- One responsibility per class.
- No business logic inside UI.
- Avoid global variables.
- Prefer composition over inheritance.

---

# 11. Libraries

GUI

- PySide6

PDF

- PyMuPDF (fitz) — in use by pdf_reader.py (text, words, and page
  image rendering)

OCR

- Backend not yet chosen; `ocr_engine.py` currently a Mock (ADR-013).
  `pytesseract` remains the leading candidate (planned).

Image

- No separate library needed for rendering — PyMuPDF's
  `Page.get_pixmap()` covers this (see ADR-026). `pdf2image` is not
  currently required.

Excel

- openpyxl

Regex

- re

Data

- dataclasses

---

# 12. Development Workflow

Always develop incrementally.

Each step must compile.

Each step must run.

Never implement multiple modules simultaneously.

Typical workflow:

1.

Implement

↓

Compile

↓

Run

↓

Verify

↓

Commit

2.

Continue.

---

# 13. Mock Mode

Mock mode was used before implementing real PDF processing.

Worker generated fake PDFResult objects during early UI/Worker/Thread
validation.

Purpose (historical):

- Test UI
- Test Thread
- Test Signals
- Test TableModel

Current status: Mock processing has been replaced by the real
PDFReader → PDFDetector pipeline in `Worker._process_pdf()` for the
detection stage. Extraction, parsing, OCR and Excel writing are not
yet implemented, so the pipeline is not yet end-to-end functional.

---

# 14. Known Issues

Current:

- Elapsed Time not implemented.
- ETA not implemented.
- Report export not implemented.
- Regex Parser not implemented.
- Excel Writer not implemented.
- Real OCR backend not implemented (`ocr_engine.py` is Mock only).
- `core/processor.py` is a placeholder (4 undefined method calls);
  its relationship to `Worker.process()` (which currently acts as
  the real orchestrator) needs clarification.
- Possible import path issues to verify: `core/models.py` uses
  `from enums import ...` and `ui/widgets.py` uses
  `from base_widget import ...` (missing package prefix).
- PDFDetector Rule System currently implements 5 of 7 Rule
  Categories defined in the TDS (§7.2): Text, Image, Consistency,
  Quality, Layout are implemented; Document and Graphics rule
  categories are not yet implemented.
- Knowledge System (TDS Chapter 9: lifecycle, governance, sources)
  is defined at the design level only; no persistence/lifecycle
  management exists in source yet.
- Extractor routes mixed-content pages (text + image) to a single
  source only; dual-source extraction deferred to v2.0 (see
  Section 4).
- No automated test suite exists; `Extractor._rotate_bbox()` in
  particular is a good candidate for dedicated unit tests before
  further logic is built on top of it.

Resolved (previously listed here, now implemented — see Section 4):

- PDF Reader — implemented (`core/pdf_reader.py`).
- PDF Detector reasoning engine — implemented (`core/pdf_detector.py`).
- Extractor — implemented (`core/extractor.py`).

---

# 15. Next Tasks

Priority order:

1.

parser.py (regex-based invoice parsing)

↓

ExtractionResult.words_by_page

↓

InvoiceInfo

2.

Unit tests for Extractor._rotate_bbox() (four rotation cases)

3.

excel_writer.py

↓

list[PDFResult]

↓

Excel

4.

Real OCR backend (replace ocr_engine.py Mock)

5.

Error Report

6.

Resolve processor.py role vs Worker.process()

---

# 16. Previous Problems & Solutions

Problem:

Writing Excel after each PDF.

Solution:

Store PDFResult in memory.

Write once.

---

Problem:

UI freezes.

Solution:

Worker + QThread.

---

Problem:

Huge memory usage.

Solution:

Release each PDF immediately.

Keep only PDFResult.

---

Problem:

Thread updating UI directly.

Solution:

Qt Signals only.

---

# 17. DO NOT CHANGE

These architectural rules are frozen.

DO NOT change unless absolutely necessary.

- process() is only an orchestrator.
- Business logic belongs to _process_pdf().
- UI never accesses business logic directly.
- Worker never accesses UI directly.
- Excel is written only once.
- PDF is processed one at a time.
- Results remain in memory.
- Communication uses Qt Signals only.
- ProcessingTable uses ProcessingTableModel.
- Incremental development workflow.

---

# 18. Future Improvements

- Logging system
- Config file
- Drag & Drop
- Multi-language UI
- Dark Mode
- Unit tests
- Plugin parser
- OCR optimization
- Batch report
