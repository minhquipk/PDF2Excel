# CHANGELOG.md

All notable changes to this project are documented here.

The format is chronological and focuses on architectural milestones
rather than Git commits.

------------------------------------------------------------------------

## Unreleased

### Next

-   Implement `pdf_reader.py`
-   Implement `regex_parser.py`
-   Implement `excel_writer.py`
-   Replace Mock mode with real PDF processing
-   Implement OCR pipeline
-   Implement Report export

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

-   Digital PDF reader
-   OCR reader
-   Regex extraction
-   Excel writer
-   Report exporter
-   ETA calculation
-   Elapsed time calculation
