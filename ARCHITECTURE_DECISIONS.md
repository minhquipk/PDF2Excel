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

## ADR-016 --- Regular Expressions

Status: Accepted

PDFReader converts PyMuPDF objects into domain models only.

No business logic.

No parser.

No OCR.

------------------------------------------------------------------------

## ADR-017 --- Regular Expressions

Status: Accepted

Implementation must follow frozen domain models.

Implementation never changes models during development.

------------------------------------------------------------------------

## ADR-018 --- Regular Expressions

Status: Accepted

Implementation decisions are based on the current source code.

Chat history is not authoritative.

------------------------------------------------------------------------

## ADR-019 --- Regular Expressions

Status: Accepted

Future document analysis will build a reusable knowledge cache.

Machine learning is intentionally excluded.

Knowledge grows deterministically from processed documents.
