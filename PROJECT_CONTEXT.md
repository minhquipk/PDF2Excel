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
    ├── PDF Reader
    ├── OCR Reader (future)
    ├── Regex Parser
    └── InvoiceInfo
            │
            ▼
        PDFResult
            │
            ▼
Memory (list[PDFResult])
            │
            ▼
Excel Writer
```

UI is completely separated from business logic.

Worker never accesses UI directly.

Communication is only through Qt Signals.

---

# 3. Current Project Structure

```
project/

constants.py
enums.py
models.py

main.py

ui/
    base_widget.py
    widgets.py
    main_window.py
    theme.py
    progress_dialog.py

models/
    processing_table_model.py

workers/
    worker.py

future/
    pdf_reader.py
    ocr_reader.py
    regex_parser.py
    excel_writer.py
```

---

# 4. Modules Completed

Completed:

- constants.py
- enums.py
- models.py
- base_widget.py
- widgets.py
- main_window.py
- worker.py (framework)
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

Mock workflow is operational.

---

# 5. Data Flow

```
PDF

↓

_process_pdf()

↓

PDFResult

↓

list[PDFResult]

↓

Excel Writer
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

---

## _process_pdf()

All business logic belongs here.

Future implementation:

PDF

↓

Digital ?

↓

YES → PDF Reader

↓

Regex

↓

InvoiceInfo

↓

PDFResult

or

PDF

↓

OCR

↓

Regex

↓

InvoiceInfo

↓

PDFResult

---

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

- pdfplumber (planned)

OCR

- pytesseract (planned)

Image

- pdf2image (planned)

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

Mock mode is mandatory before implementing real PDF processing.

Worker generates fake PDFResult objects.

Purpose:

- Test UI
- Test Thread
- Test Signals
- Test TableModel

No business logic.

---

# 14. Known Issues

Current:

- Elapsed Time not implemented.
- ETA not implemented.
- Report export not implemented.
- OCR not implemented.
- PDF Reader not implemented.
- Regex Parser not implemented.
- Excel Writer not implemented.

---

# 15. Next Tasks

Priority order:

1.

pdf_reader.py

↓

Read Digital PDF

↓

Return text

2.

regex_parser.py

↓

Text

↓

InvoiceInfo

3.

excel_writer.py

↓

list[PDFResult]

↓

Excel

4.

OCR Reader

5.

Error Report

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